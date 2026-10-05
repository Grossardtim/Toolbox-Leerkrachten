"""Read-only comparison of pre-migration columns with the local backup."""
from pathlib import Path
import sqlite3

backup=next(Path('data/backups/voor-studierichtingen.sqlite3').glob('*.sqlite3'))
with sqlite3.connect(f'file:{backup.as_posix()}?mode=ro',uri=True) as before, sqlite3.connect('file:data/schoolportal.sqlite3?mode=ro',uri=True) as after:
    checked=0
    for (table,) in before.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'evaluations_%'"):
        if table=='evaluations_auditevent':
            continue
        columns=[row[1] for row in before.execute(f'PRAGMA table_info("{table}")')]
        selection=', '.join('"'+column+'"' for column in columns)
        old=before.execute(f'SELECT {selection} FROM "{table}" ORDER BY id').fetchall()
        new=after.execute(f'SELECT {selection} FROM "{table}" ORDER BY id').fetchall()
        assert old==new, f'Controleer gewijzigde records in {table}; niets automatisch herstellen.'
        checked+=1
    print(f'{checked} oorspronkelijke onderwijstabellen ongewijzigd; nieuwe relaties staan in aanvullende velden/tabellen.')
