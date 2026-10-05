"""Migrate an isolated backup copy, check historical data, then optionally compare live data."""
from pathlib import Path
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import json
from contextlib import closing

ROOT=Path(__file__).resolve().parent.parent
backup=sorted((ROOT/'data/backups/voor-doelen-graad').glob('*.sqlite3'))[-1]

def verify(target):
    with closing(sqlite3.connect(backup)) as old, closing(sqlite3.connect(target)) as new:
        for table in ['evaluations_lesson','evaluations_lessongoal','evaluations_lessonpoint','evaluations_lessonstudent',
                      'evaluations_score','evaluations_point','evaluations_classroom','evaluations_student']:
            existing=old.execute(f'SELECT * FROM {table} ORDER BY id').fetchall()
            current={row[0]:row for row in new.execute(f'SELECT * FROM {table} ORDER BY id')}
            assert all(current.get(row[0])==row for row in existing),table
        goals=old.execute('SELECT id,code,title,archived,owner_id,year_id,subject_id,grade FROM evaluations_goal').fetchall()
        for pk,code,title,archived,owner,year,subject,grade in goals:
            actual=new.execute('SELECT code,title,archived,owner_id,stage,study_direction_id,legacy_context FROM evaluations_goal WHERE id=?',(pk,)).fetchone()
            assert actual[:4]==(code,title,archived,owner)
            assert actual[4]==min(3,(grade+1)//2)
            assert actual[5] is not None
            legacy=json.loads(actual[6]);assert (legacy['school_year_id'],legacy['subject_id'],legacy['grade'])==(year,subject,grade)
            classes=[row[0] for row in old.execute('SELECT classroom_id FROM evaluations_goal_classrooms WHERE goal_id=? ORDER BY classroom_id',(pk,))]
            assert sorted(legacy['classroom_ids'])==classes
        print(f'{len(goals)} doelen omgezet; historische lessen, punten, scores, feedback en leerlingen uit de back-up identiek. Latere toevoegingen blijven behouden.')

if '--live' in sys.argv:
    verify(ROOT/'data/schoolportal.sqlite3')
else:
    with tempfile.TemporaryDirectory(prefix='portal-migration-') as directory:
        target=Path(directory)/'schoolportal.sqlite3';shutil.copy2(backup,target)
        subprocess.run([sys.executable,'manage.py','migrate','--noinput'],cwd=ROOT,
            env={**os.environ,'DATA_DIR':directory},check=True)
        verify(target)
