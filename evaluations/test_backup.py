import sqlite3
from contextlib import closing
import tempfile
from pathlib import Path
from io import StringIO
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

class BackupTests(SimpleTestCase):
    def test_backup_can_be_restored_and_preserves_records(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.sqlite3'
            with closing(sqlite3.connect(source)) as db:
                db.execute('CREATE TABLE evaluations (score INTEGER, feedback TEXT)')
                db.execute('INSERT INTO evaluations VALUES (?, ?)', (60, 'Bewaarde feedback'))
                db.commit()
            config = {'default': {'ENGINE':'django.db.backends.sqlite3', 'NAME':str(source)}}
            with override_settings(DATABASES=config):
                call_command('backup_local', output=str(Path(directory) / 'backups'), stdout=StringIO())
            backup = next((Path(directory) / 'backups').glob('*.sqlite3'))
            restored = Path(directory) / 'restored.sqlite3'
            restored.write_bytes(backup.read_bytes())
            with closing(sqlite3.connect(restored)) as db:
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(db.execute('SELECT * FROM evaluations').fetchall(), [(60, 'Bewaarde feedback')])
