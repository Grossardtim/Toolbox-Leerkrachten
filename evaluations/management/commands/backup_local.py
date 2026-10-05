import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Maak een consistente back-up van de lokale SQLite-ontwikkeldatabase.'
    def add_arguments(self, parser):
        parser.add_argument('--output', required=True, help='Map buiten een gesynchroniseerde actieve database.')
    def handle(self, *args, **options):
        db = settings.DATABASES['default']
        if db['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('Gebruik voor PostgreSQL de beheerde back-upvoorziening of pg_dump.')
        root = Path(options['output'])
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"schoolportal-{datetime.now():%Y%m%d-%H%M%S-%f}.sqlite3"
        with closing(sqlite3.connect(db['NAME'])) as source, closing(sqlite3.connect(path)) as target:
            source.backup(target)
        self.stdout.write(str(path))
