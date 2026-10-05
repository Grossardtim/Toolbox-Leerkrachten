"""Local SQLite backup and explicitly confirmed restore."""
from contextlib import closing
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import uuid
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core import signing
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .models import User
from evaluations.models import AuditEvent

TABLES = ['accounts_user', 'evaluations_classroom', 'evaluations_lesson', 'evaluations_score', 'evaluations_goal']

def snapshot(source, destination):
    with closing(sqlite3.connect(str(source))) as src, closing(sqlite3.connect(str(destination))) as dst:
        src.backup(dst)

def inspect_backup(path):
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('De database is beschadigd.')
        existing = set(db.execute('SELECT app,name FROM django_migrations'))
        with connection.cursor() as cursor:
            cursor.execute('SELECT app,name FROM django_migrations')
            current = set(cursor.fetchall())
        if existing != current:
            raise ValueError('Deze back-up hoort bij een andere databaseversie. Gebruik eerst de bijpassende programmaversie.')
        if not db.execute('SELECT COUNT(*) FROM accounts_user WHERE is_superuser=1 AND is_active=1').fetchone()[0]:
            raise ValueError('De back-up bevat geen actieve beheerder.')
        return dict(zip(['Accounts','Klassen','Lessen','Scores','Leerplandoelen'],
                        [db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in TABLES]))

@never_cache
@login_required
def backups(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    local = connection.vendor == 'sqlite' and (settings.DEBUG or settings.STANDALONE)
    context = {'nav':'backups', 'local':local}
    if request.method == 'POST' and not local:
        raise PermissionDenied('Herstel via deze pagina is alleen beschikbaar voor lokale SQLite-installaties.')
    if request.method == 'POST':
        action = request.POST.get('action')
        database = Path(settings.DATABASES['default']['NAME'])
        directory = settings.DATA_DIR/'backups'
        directory.mkdir(parents=True, exist_ok=True)
        try:
            if action == 'backup':
                filename = f'leerkrachten-tool-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}.sqlite3'
                target_dir = Path(request.POST['path']).expanduser() if request.POST.get('path') else directory
                if not target_dir.is_absolute():
                    raise ValueError('Kies een volledig pad naar een map op de server.')
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir/filename
                snapshot(database,target)
                from evaluations.views import log
                log(request.user,'databaseback-up gemaakt',request.user)
                if request.POST.get('path'):
                    messages.success(request, f'Back-up opgeslagen: {target}')
                    return redirect('backups')
                response = HttpResponse(target.read_bytes(),content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Cache-Control'] = 'no-store'
                return response
            if action == 'inspect':
                upload = request.FILES.get('backup')
                if not upload or upload.size > 200*1024*1024:
                    raise ValueError('Kies een SQLite-back-up van maximaal 200 MB.')
                pending = directory/'pending'
                pending.mkdir(exist_ok=True)
                filename = uuid.uuid4().hex+'.sqlite3'
                target = pending/filename
                with target.open('wb') as stream:
                    for chunk in upload.chunks(): stream.write(chunk)
                try:
                    context['counts'] = inspect_backup(target)
                except Exception:
                    target.unlink(missing_ok=True)
                    raise
                context['restore_token'] = signing.dumps({'file':filename,'user':request.user.pk},salt='backup.restore')
            elif action == 'restore':
                if request.POST.get('confirm') != 'yes' or not request.user.check_password(request.POST.get('password','')):
                    raise ValueError('Bevestig de vervanging en vul je huidige beheerderswachtwoord in.')
                token = signing.loads(request.POST.get('token',''),salt='backup.restore',max_age=600)
                if token['user'] != request.user.pk or not __import__('re').fullmatch(r'[a-f0-9]{32}\.sqlite3',token['file']):
                    raise ValueError('Ongeldige herstelbevestiging.')
                source = directory/'pending'/token['file']
                inspect_backup(source)
                safety = directory/f'voor-herstel-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}.sqlite3'
                snapshot(database,safety)
                username = request.user.username
                request.session.flush()
                connection.close()
                snapshot(source,database)
                # Restored browser sessions must never remain signed in.
                from django.contrib.sessions.models import Session
                Session.objects.all().delete()
                restored_admin = User.objects.filter(username=username,is_superuser=True).first()
                if restored_admin:
                    AuditEvent.objects.create(actor=restored_admin,action='database hersteld',object_type='database',object_id=restored_admin.pk)
                source.unlink(missing_ok=True)
                return redirect('login')
        except (ValueError,OSError,sqlite3.DatabaseError,signing.BadSignature,KeyError) as error:
            context['error'] = str(error)
    return render(request,'accounts/backups.html',context)

@login_required
def audit(request):
    if not request.user.is_superuser: raise PermissionDenied
    events = AuditEvent.objects.select_related('actor').order_by('-timestamp')
    table = {'columns':['Tijdstip','Leerkracht','Actie','Onderdeel','Record'], 'rows':[
        {'cells':[e.timestamp.strftime('%Y-%m-%d %H:%M:%S'),e.actor.get_full_name() or e.actor.username,e.action,e.object_type,e.object_id]}
        for e in events]}
    return render(request,'accounts/audit.html',{'table':table,'nav':'audit'})

