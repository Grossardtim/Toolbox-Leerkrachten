"""Reproducible large fictitious curriculum, restricted to the QA directory."""
from datetime import date
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import User
from evaluations.models import Year, StudyDirection, Subject, Classroom, Student, Goal, Point, Lesson, LessonStudent, Score
from evaluations.services import snapshot_goal


class Command(BaseCommand):
    help = 'Vul een geïsoleerde QA-database met fictieve klassen van 19 leerlingen.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DATA_DIR.resolve().is_relative_to((settings.BASE_DIR / 'outputs').resolve()):
            raise CommandError('Alleen toegestaan in een afzonderlijke outputs/demo-map.')
        teacher = User.objects.get(username='demo.leerkracht')
        year, _ = Year.objects.get_or_create(owner=teacher, name='2026–2027')
        names = ['Amber Voorbeeld', 'Bram Voorbeeld', 'Cato De Voorbeeld', 'Daan Voorbeeld',
                 'Elise Voorbeeld', 'Finn Voorbeeld', 'Gitte Voorbeeld', 'Hugo Voorbeeld',
                 'Imane Voorbeeld', 'Jules Voorbeeld', 'Kato Van Voorbeeld', 'Liam Voorbeeld',
                 'Mila Voorbeeld', 'Noah Voorbeeld', 'Olivia Voorbeeld', 'Pieter Voorbeeld',
                 'Quinten Voorbeeld', 'Rania Voorbeeld', 'Senne Voorbeeld']
        for direction_name, suffix in [('DEMO Schoonheidsverzorging','SV'), ('DEMO Haarzorg','HZ'), ('DEMO Zorg','Z')]:
            direction, _ = StudyDirection.objects.get_or_create(owner=teacher, name=direction_name)
            subjects=[]
            for title in ['Praktijk', 'Professionele vaardigheden']:
                subject, _ = Subject.objects.get_or_create(owner=teacher, year=year, name=f'{title} · {suffix}')
                subject.study_directions.add(direction)
                subjects.append(subject)
            goals=[]
            for number in range(1,13):
                title = 'Manicure' if number==1 else f'Praktijkvaardigheid {number:02d}'
                goal, _ = Goal.objects.get_or_create(owner=teacher, study_direction=direction, stage=3,
                    code=f'DEMO.BK{number:02d}', defaults={'title':title})
                texts = ['Reiniging handen', 'Voorbereidende massage', 'Eigenlijk werk', 'Afsluitende massage'] if number==1 else [
                    f'Stap {n}: de leerling voert de voorbereiding en de handeling zorgvuldig uit en licht de gemaakte keuzes toe.' for n in range(1,7)]
                if number==12: texts=[]
                for i,text in enumerate(texts): Point.objects.get_or_create(goal=goal, title=text, defaults={'position':i})
                goals.append(goal)
            for grade in (5,6):
                room,_=Classroom.objects.get_or_create(owner=teacher,year=year,name=f'DEMO {grade}{suffix}',
                    defaults={'study_direction':direction,'direction':direction.name,'grade':grade})
                room.subjects.set(subjects)
                students=[Student.objects.get_or_create(classroom=room,name=name)[0] for name in names]
                for index in range(4):
                    lesson,created=Lesson.objects.get_or_create(owner=teacher,classroom=room,
                        title=f'DEMO Praktijkles {index+1} · {direction_name}',
                        defaults={'subject':subjects[index%2],'grade':grade,'date':date(2026,10,index+1),
                                  'feedback':'Fictieve voorbeeldgegevens om layout en opvolging te beoordelen.'})
                    if not created: continue
                    roster=[LessonStudent.objects.create(lesson=lesson,student=s,name=s.name,feedback='Fictieve feedback: werk de voorbereiding verder uit.') for s in students]
                    for g_index,goal in enumerate(goals[:10]):
                        selected=list(goal.points.all())
                        if g_index==0: selected=selected[index:index+1]
                        snap=snapshot_goal(lesson,goal,selected)
                        for p_index,point in enumerate(snap.points.all()):
                            for n,learner in enumerate(roster):
                                if (n+p_index+index)%11==0: continue
                                absent=(n+p_index+index)%17==0
                                Score.objects.create(point=point,learner=learner,status='absent' if absent else 'scored',
                                    value=None if absent else [0,20,40,60,80][(n+p_index+index)%5])
                    snapshot_goal(lesson,goals[-1])
        self.stdout.write('Fictieve demo uitgebreid: 6 klassen van 19 leerlingen, 36 BK’s, 24 lessen, meerdere vakken en deel-BK’s.')
