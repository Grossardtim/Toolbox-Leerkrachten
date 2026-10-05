"""Entry point for the standalone desktop distribution (also runnable as Python)."""
import argparse
from contextlib import closing
from datetime import datetime
import os
from pathlib import Path
import socket
import sqlite3
import sys
import threading
import time
import webbrowser


def default_data_directory():
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData/Local'))) / 'Leerkrachtenportaal'
    return Path.home()/'Library/Application Support/Leerkrachtenportaal' if sys.platform=='darwin' else Path.home()/'.local/share/leerkrachtenportaal'


def initialize_database():
    from django.conf import settings
    from django.core.management import call_command
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    executor=MigrationExecutor(connection)
    targets=executor.loader.graph.leaf_nodes()
    if not executor.migration_plan(targets):return
    database=Path(settings.DATABASES['default']['NAME'])
    if database.exists() and database.stat().st_size:
        backups=settings.DATA_DIR/'backups';backups.mkdir(exist_ok=True)
        backup=backups/f'voor-update-{datetime.now():%Y%m%d-%H%M%S-%f}.sqlite3'
        with closing(sqlite3.connect(database)) as source, closing(sqlite3.connect(backup)) as target:
            source.backup(target)
        print(f'Back-up voor update: {backup}',flush=True)
    call_command('migrate',interactive=False,verbosity=0)


def acquire_lock(directory):
    handle=open(directory/'.running.lock','a+b')
    handle.seek(0);handle.write(b'0');handle.flush();handle.seek(0)
    try:
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise RuntimeError('Deze gegevensmap is al geopend. Sluit de andere instantie eerst.')
    return handle


def main():
    parser=argparse.ArgumentParser(description='Leerkrachten Tool: lokale toepassing')
    parser.add_argument('--data-dir',type=Path,default=default_data_directory())
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--browser',action='store_true',help='Open in de gewone browser in plaats van het appvenster.')
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--demo',action='store_true',help='Maak fictieve gegevens aan, alleen in een lege gegevensmap.')
    parser.add_argument('--check',action='store_true',help='Controleer database, pagina en Excel zonder server te starten.')
    args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error('Kies een poort tussen 1 en 65535.')
    directory=args.data_dir.expanduser().resolve();directory.mkdir(parents=True,exist_ok=True)
    lock=acquire_lock(directory)
    try:
        os.environ['DATA_DIR']=str(directory)
        os.environ['APP_ENV']='standalone'
        os.environ['PORTAL_STANDALONE']='1'
        os.environ['ALLOWED_HOSTS']='127.0.0.1,localhost,testserver'
        if os.environ.get('PGHOST'):
            raise RuntimeError('Deze lokale executable gebruikt SQLite. Verwijder PGHOST uit deze opstartsessie.')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE','schoolportal.settings')
        import django
        django.setup()
        initialize_database()
        from django.core.management import call_command
        from accounts.models import User
        if args.demo:
            if User.objects.exists():
                print('Bestaande accounts behouden; demo wordt niet opnieuw aangemaakt.',flush=True)
            else:call_command('create_demo')
        if args.check:
            from django.test import Client
            from exports.workbook import build_workbook
            from django.conf import settings
            call_command('check')
            response=Client().get('/aanmelden/')
            assert response.status_code in (200,302)
            payload={'mode':'class','school':'Controle','schoolYear':'2026','className':'Test','direction':'Test',
                     'studentName':None,'lessons':[]}
            assert build_workbook(payload,settings.BASE_DIR/'static/school-logo.png').startswith(b'PK')
            print('CONTROLE OK: database, pagina en zelfstandige Excel-export.',flush=True)
            return 0
        from django.core.wsgi import get_wsgi_application
        from django.contrib.staticfiles.handlers import StaticFilesHandler
        from waitress import create_server
        url=f'http://127.0.0.1:{args.port}/'
        try:
            server=create_server(StaticFilesHandler(get_wsgi_application()),host='127.0.0.1',port=args.port,threads=4)
        except OSError as error:
            raise RuntimeError(f'Poort {args.port} is bezet. Sluit de andere server of start met --port 8001.') from error
        print(f'Gegevens: {directory}\nOpen: {url}\nLaat dit venster open. Stoppen: Ctrl+C.',flush=True)
        if args.demo:print(f'Demowachtwoorden: {directory / "demo-toegang.txt"}',flush=True)
        from accounts.local_app import register_shutdown
        stop_event=threading.Event()
        def stop():
            stop_event.set()
            server.close()
        register_shutdown(stop)
        app_mode=not args.browser and not args.no_browser
        if app_mode:
            try:
                import webview
            except ImportError:
                print('Appvenster niet geïnstalleerd; de gewone browser wordt geopend.',flush=True)
                app_mode=False
        try:
            if app_mode:
                from tools.start_local import portal_ready
                runner=threading.Thread(target=server.run,daemon=True)
                runner.start()
                for _ in range(100):
                    if portal_ready(url):break
                    time.sleep(.1)
                else:raise RuntimeError('De lokale server werd niet gereed.')
                webview.settings['ALLOW_DOWNLOADS']=True
                from schoolportal.releases import VERSION
                window=webview.create_window(f'Leerkrachten Tool {VERSION}',url,maximized=True,min_size=(900,600),confirm_close=True)
                window.events.closed += stop
                def await_shutdown():
                    stop_event.wait()
                    window.destroy()
                webview.start(await_shutdown,gui='edgechromium' if os.name=='nt' else None,
                              private_mode=True)
            else:
                if not args.no_browser:
                    from tools.start_local import portal_ready
                    def open_when_ready():
                        for _ in range(100):
                            if portal_ready(url):webbrowser.open(url);return
                            time.sleep(.2)
                    threading.Thread(target=open_when_ready,daemon=True).start()
                server.run()
        except KeyboardInterrupt:pass
        finally:
            register_shutdown(None)
            stop()
        return 0
    finally:
        lock.close()


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as error:
        print(f'Opstarten mislukt: {error}',file=sys.stderr,flush=True)
        if os.name=='nt' and (getattr(sys,'frozen',False) or sys.stderr is None):
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,str(error),'Leerkrachten Tool',0x10)
        if getattr(sys,'frozen',False) and sys.stdin and sys.stdin.isatty():
            input('Druk op Enter om af te sluiten...')
        sys.exit(1)
