import os
import sys
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','schoolportal.settings')
import django
django.setup()
from evaluations.models import Classroom, Lesson
from exports.services import export_payload
room = Classroom.objects.get(owner__username='demo.leerkracht',name='6HV')
lessons = list(Lesson.objects.filter(classroom=room).select_related('subject').order_by('date','pk'))
root=Path('outputs/export-qa')
root.mkdir(parents=True,exist_ok=True)
for mode,student in [('class',None),('student',room.students.order_by('pk').first())]:
    payload=export_payload(lessons,room,student)
    (root/f'{mode}.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
print('Fictieve demo-exportgegevens voorbereid')
