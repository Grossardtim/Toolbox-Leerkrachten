"""Destructive restore smoke test, confined to an automatically created temporary database."""
import os,sys,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if '--inner' not in sys.argv:
    with tempfile.TemporaryDirectory(prefix='leerkrachten-restore-test-') as directory:
        env={**os.environ,'DATA_DIR':directory,'APP_ENV':'development','DJANGO_SETTINGS_MODULE':'schoolportal.settings','PYTHONPATH':str(ROOT)}
        subprocess.run([sys.executable,'manage.py','migrate','--noinput'],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable,__file__,'--inner'],cwd=ROOT,env=env,check=True)
else:
    import django
    django.setup()
    from django.test import Client
    from django.test.utils import setup_test_environment
    from django.core.files.uploadedfile import SimpleUploadedFile
    from accounts.models import User
    from evaluations.models import Year
    setup_test_environment()
    admin=User.objects.create_superuser('testadmin',password='Temporary-Test-Password-42')
    client=Client();client.force_login(admin)
    response=client.post('/beheerder/backups/',{'action':'backup'})
    assert response.status_code==200 and response.content.startswith(b'SQLite format 3')
    backup=response.content
    Year.objects.create(owner=admin,name='Na de back-up')
    response=client.post('/beheerder/backups/',{'action':'inspect','backup':SimpleUploadedFile('backup.sqlite3',backup)})
    assert response.context['counts']['Accounts']==1
    token=response.context['restore_token']
    response=client.post('/beheerder/backups/',{'action':'restore','token':token,'confirm':'yes','password':'wrong'})
    assert Year.objects.count()==1
    response=client.post('/beheerder/backups/',{'action':'restore','token':token,'confirm':'yes','password':'Temporary-Test-Password-42'})
    assert response.status_code==302 and response.url=='/aanmelden/'
    assert Year.objects.count()==0
    assert User.objects.get(username='testadmin').check_password('Temporary-Test-Password-42')
    assert list((Path(os.environ['DATA_DIR'])/'backups').glob('voor-herstel-*.sqlite3'))
    assert client.get('/beheerder/backups/').status_code==302
    print('PASS: back-up, controle, wachtwoordbevestiging, herstel, veiligheidskopie en afmelden; uitsluitend tijdelijke database.')

