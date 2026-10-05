"""Upgrade a copy of AppData; verify every existing application row is unchanged."""
from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
source=Path(os.environ['LOCALAPPDATA'])/'Leerkrachtenportaal'/'schoolportal.sqlite3'


def digest(db, table, columns):
    query='SELECT '+','.join('"'+c+'"' for c in columns)+' FROM "'+table+'" ORDER BY 1'
    return hashlib.sha256(repr(db.execute(query).fetchall()).encode()).hexdigest()


with tempfile.TemporaryDirectory(prefix='curriculum-upgrade-',dir=root/'outputs') as work:
    destination=Path(work)/'schoolportal.sqlite3'
    with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)
    with closing(sqlite3.connect(destination)) as db:
        tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'") if r[0].startswith(('accounts_','evaluations_'))]
        columns={t:[r[1] for r in db.execute('PRAGMA table_info("'+t+'")')] for t in tables}
        before={t:digest(db,t,columns[t]) for t in tables}
    os.environ['DATA_DIR']=work
    os.environ['DJANGO_SETTINGS_MODULE']='schoolportal.settings'
    import django
    django.setup()
    from desktop import initialize_database
    initialize_database()
    from django.db import connections
    connections.close_all()
    with closing(sqlite3.connect(destination)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        for table in tables:
            assert digest(db,table,columns[table])==before[table],table
        print('PASS: alle bestaande account- en evaluatievelden exact behouden op AppData-kopie.')
        print('Gekoppelde lespunten:',db.execute('SELECT COUNT(*) FROM evaluations_lessonpoint WHERE source_point_id IS NOT NULL').fetchone()[0])
        print('Historische lespunten zonder zekere koppeling:',db.execute('SELECT COUNT(*) FROM evaluations_lessonpoint WHERE source_point_id IS NULL').fetchone()[0])
    print('Originele AppData-database niet gewijzigd.')
