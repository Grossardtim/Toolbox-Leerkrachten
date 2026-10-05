"""Explicit deletion with owner checks, dependency protection and stale-form checks."""
import hashlib
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from accounts.models import User
from .models import Year, Subject, Classroom, Student, Goal, Lesson, Score, AuditEvent, StudyDirection

MODELS = {'studierichtingen': (StudyDirection, 'Studierichting'), 'schooljaren': (Year, 'Schooljaar'), 'vakken': (Subject, 'Vak'),
          'klassen': (Classroom, 'Klas'), 'leerlingen': (Student, 'Leerling'),
          'doelen': (Goal, 'Leerplandoel'), 'lessen': (Lesson, 'Les'),
          'leerkrachten': (User, 'Leerkracht')}
SALT = 'portal.delete-record.v1'


def dependencies(obj):
    blockers, effects = [], []
    def block(query, label):
        count = query.count()
        if count:
            blockers.append(f'{count} {label}')
    if isinstance(obj, Year):
        block(obj.subject_set, 'gekoppelde vakken')
        block(obj.classroom_set, 'gekoppelde klassen')
    elif isinstance(obj, StudyDirection):
        block(obj.goal_set, 'gekoppelde leerplandoelen')
        block(obj.classroom_set, 'gekoppelde klassen')
        block(obj.subject_set, 'gekoppelde vakken')
    elif isinstance(obj, Subject):
        block(obj.lesson_set, 'gekoppelde lessen')
        effects.append(f'{obj.classroom_set.count()} klaskoppelingen worden verwijderd.')
    elif isinstance(obj, Classroom):
        block(obj.students, 'ingeschreven leerlingen')
        block(obj.lesson_set, 'gekoppelde lessen')
        effects.append('De koppelingen met vakken worden verwijderd. Leerplandoelen van de studierichting blijven bewaard.')
    elif isinstance(obj, Student):
        block(obj.lessonstudent_set, 'bestaande lesinschrijvingen')
    elif isinstance(obj, Goal):
        effects.append(f'{obj.points.count()} subdoelen / evaluatiepunten worden mee verwijderd.')
        effects.append('Kopieën van dit doel en alle scores in bestaande lessen blijven bewaard.')
    elif isinstance(obj, Lesson):
        effects.extend([f'{obj.goals.count()} lesdoelen, {obj.roster.count()} lesinschrijvingen en '
                        f'{Score.objects.filter(point__goal__lesson=obj).count()} beoordelingen worden mee verwijderd.',
                        'Ook alle klasfeedback en persoonlijke feedback van deze les worden gewist.',
                        'De klas, leerlingen en leerplandoelen in Beheer blijven bestaan.'])
    elif isinstance(obj, User):
        for model, label in ((StudyDirection, 'studierichtingen'), (Year, 'schooljaren'), (Subject, 'vakken'), (Classroom, 'klassen'),
                             (Goal, 'leerplandoelen'), (Lesson, 'lessen')):
            block(model.objects.filter(owner=obj), f'eigen {label}')
        block(AuditEvent.objects.filter(actor=obj), 'historische logvermeldingen')
        effects.append('Deze gebruiker kan na het wissen niet meer aanmelden.')
    return blockers, effects


def fingerprint(obj):
    data = {field.attname: str(getattr(obj, field.attname)) for field in obj._meta.concrete_fields}
    for field in obj._meta.many_to_many:
        data[field.name] = sorted(getattr(obj, field.name).values_list('pk', flat=True))
    if isinstance(obj, Goal):
        data['points'] = list(obj.points.values('pk', 'title', 'position'))
    data['dependencies'] = dependencies(obj)
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


@login_required
@require_http_methods(['GET', 'POST'])
def delete_record(request, kind, pk):
    if kind not in MODELS:
        raise Http404
    model, label = MODELS[kind]
    if model == User:
        if not request.user.is_superuser:
            raise PermissionDenied
        queryset = User.objects.filter(is_superuser=False).exclude(pk=request.user.pk)
    else:
        if model == Lesson and not (request.user.can_evaluate or request.user.is_superuser):
            raise PermissionDenied
        queryset = model.objects.all()
        if model == Lesson and not request.user.is_superuser:
            queryset = queryset.filter(owner=request.user)
    error, status = None, 200
    with transaction.atomic():
        obj = get_object_or_404(queryset.select_for_update(), pk=pk)
        name = obj.title if isinstance(obj, Lesson) else str(obj)
        if isinstance(obj, User):
            name = obj.get_full_name() or obj.username
        if model == User:
            back_url = reverse('teachers')
            edit_url = reverse('teacher_edit', args=[pk])
            year = None
        elif model == Lesson:
            year = obj.classroom.year
            back_url = reverse('dashboard') + f'?year={year.pk}&classroom={obj.classroom_id}'
            edit_url = reverse('lesson', args=[pk])
        else:
            year = obj if model == Year else (obj.classroom.year if model == Student else getattr(obj, "year", None))
            back_kind = 'klassen' if model == Student else kind
            back_url = reverse('manage', args=[back_kind])
            if model not in (Year, StudyDirection, Goal):
                back_url += f'?year={year.pk}'
            if model == Student:
                back_url += f'&classroom={obj.classroom_id}#leerlingen'
            edit_url = reverse('manage_edit', args=[kind, pk]) + (f'?year={year.pk}' if year else '')
        blockers, effects = dependencies(obj)
        state = {'kind': kind, 'pk': pk, 'actor': request.user.pk, 'fingerprint': fingerprint(obj)}
        if request.method == 'POST':
            try:
                supplied = signing.loads(request.POST.get('token', ''), salt=SALT, max_age=3600)
                if supplied != state:
                    raise signing.BadSignature
            except signing.BadSignature:
                error = 'De gegevens zijn gewijzigd of de bevestiging is verlopen. Controleer de actuele gegevens hieronder en bevestig opnieuw.'
                status = 409
            if request.POST.get('confirm') != 'yes' and not error:
                error = 'Vink de bevestiging aan om deze ingave te wissen.'
                status = 400
            if not error and blockers:
                error = 'Deze ingave wordt nog gebruikt en kan niet worden gewist.'
                status = 409
            if not error:
                try:
                    with transaction.atomic():
                        AuditEvent.objects.create(actor=request.user, action=f'{label.lower()} gewist',
                                                  object_type=obj._meta.model_name, object_id=obj.pk)
                        obj.delete()
                except ProtectedError:
                    error = 'Er zijn inmiddels gekoppelde gegevens. Er is niets gewist. Ga terug naar het overzicht en probeer opnieuw.'
                    status = 409
                else:
                    messages.success(request, f'{label} “{name}” is gewist.')
                    return redirect(back_url)
        token = signing.dumps(state, salt=SALT)
    return render(request, 'evaluations/delete_confirm.html', {'label': label, 'object_name': name,
        'back_url': back_url, 'edit_url': edit_url, 'blockers': blockers, 'effects': effects,
        'token': token, 'error': error, 'kind': kind, 'year': year,
        'nav': 'teachers' if model == User else ('lessons' if model == Lesson else 'manage')}, status=status)
