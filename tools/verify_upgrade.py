"""Snapshot selected existing fields before migrations; compare after migration."""
import json
import sqlite3
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
db = sqlite3.connect(root / 'data' / 'schoolportal.sqlite3')
queries = {
    'lessons': 'SELECT id, owner_id, classroom_id, title, date, feedback, revision FROM evaluations_lesson ORDER BY id',
    'scores': 'SELECT id, point_id, learner_id, value FROM evaluations_score ORDER BY id',
    'learners': 'SELECT id, lesson_id, student_id, name, feedback FROM evaluations_lessonstudent ORDER BY id',
    'goals': 'SELECT id, lesson_id, source_id, code, title, position FROM evaluations_lessongoal ORDER BY id',
    'points': 'SELECT id, goal_id, title, position FROM evaluations_lessonpoint ORDER BY id',
}
state = {name: [list(row) for row in db.execute(query)] for name, query in queries.items()}
db.close()
path = root / 'data' / 'pre-upgrade-check.json'
if sys.argv[1] == 'before':
    path.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
    print('Voor migratie:', {key:len(value) for key,value in state.items()})
elif sys.argv[1] == 'after':
    expected = json.loads(path.read_text(encoding='utf-8'))
    assert state == expected, 'Data changed: inspect before proceeding.'
    print('Gegevensbehoud bevestigd:', {key:len(value) for key,value in state.items()})
