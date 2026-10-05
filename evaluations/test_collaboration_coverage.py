from datetime import date
from io import BytesIO
from zipfile import ZipFile
from django.test import TestCase
from accounts.models import User
from evaluations.models import Year, StudyDirection, Subject, Classroom, Student, Goal, Point, Lesson, LessonStudent, Score
from evaluations.services import snapshot_goal
from evaluations.coverage import build_coverage, coverage_workbook

class CollaborationAndCoverageTests(TestCase):
    def setUp(self):
        self.a=User.objects.create_user('owner',can_evaluate=True)
        self.b=User.objects.create_user('viewer',can_evaluate=True)
        self.admin=User.objects.create_superuser('admin',password='Admin-Password-789')
        self.year=Year.objects.create(owner=self.a,name='2026')
        self.direction=StudyDirection.objects.create(owner=self.a,name='Haarzorg')
        subject=Subject.objects.create(owner=self.a,year=self.year,name='Praktijk')
        self.room=Classroom.objects.create(owner=self.a,year=self.year,name='6A',study_direction=self.direction,grade=6)
        self.room.subjects.add(subject)
        pupil=Student.objects.create(classroom=self.room,name='Voorbeeld')
        goal=Goal.objects.create(owner=self.a,study_direction=self.direction,stage=3,code='BK1',title='Doel')
        for i in range(3): Point.objects.create(goal=goal,title=f'Punt {i}',position=i)
        self.lessons=[]
        for number,value in enumerate([40,60]):
            lesson=Lesson.objects.create(owner=self.a,classroom=self.room,subject=subject,grade=6,title='Les',date=date(2026,10,4))
            learner=LessonStudent.objects.create(lesson=lesson,student=pupil,name=pupil.name)
            snap=snapshot_goal(lesson,goal)
            points=list(snap.points.all())
            Score.objects.create(point=points[0],learner=learner,value=value)
            Score.objects.create(point=points[1],learner=learner,value=0)
            Score.objects.create(point=points[2],learner=learner,status='absent')
            self.lessons.append(lesson)
        self.client.force_login(self.b)

    def test_shared_read_is_not_write_permission(self):
        lesson=self.lessons[0]
        response=self.client.get(f'/lessen/{lesson.pk}/')
        self.assertContains(response,'Alleen bekijken')
        self.assertContains(response,'disabled')
        self.assertNotContains(response,'form="evaluation-form">Scores')
        self.assertEqual(self.client.post(f'/lessen/{lesson.pk}/',{}).status_code,403)
        self.assertEqual(self.client.post(f'/lessen/{lesson.pk}/doelen/',{'action':'remove','goal':lesson.goals.first().pk,'confirm':'yes','revision':0}).status_code,404)
        self.assertEqual(self.client.get(f'/wissen/lessen/{lesson.pk}/').status_code,404)
        self.assertEqual(self.client.get(f'/beheer/klassen/{self.room.pk}/').status_code,200)

    def test_admin_controls_visibility_and_always_sees_everyone(self):
        self.b.view_all_teachers=False;self.b.save()
        self.assertEqual(self.client.get(f'/lessen/{self.lessons[0].pk}/').status_code,404)
        self.b.visible_teachers.add(self.a)
        self.assertEqual(self.client.get(f'/lessen/{self.lessons[0].pk}/').status_code,200)
        self.b.visible_teachers.clear()
        self.assertFalse(any(cell['seen'] for row in self.client.get('/doelenoverzicht/').context['rows'] for cell in row['cells']))
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(f'/lessen/{self.lessons[0].pk}/').status_code,200)
        self.assertEqual(self.client.get('/beheerder/logboek/').status_code,200)

    def test_coverage_means_zero_absent_and_excel(self):
        learners,rows=build_coverage(self.b,{'classroom':self.room})
        self.assertEqual(len(learners),1)
        self.assertEqual(len(rows),4)
        summary=next(row for row in rows if row['kind']=='bk')
        self.assertFalse(summary['cells'][0]['seen'])
        self.assertEqual(summary['cells'][0]['covered'],2)
        rows=[row for row in rows if row['kind']!='bk']
        self.assertEqual(rows[0]['cells'][0]['average'],50)
        self.assertEqual(rows[0]['cells'][0]['category'],40)
        self.assertTrue(rows[1]['cells'][0]['seen'])
        self.assertEqual(rows[1]['cells'][0]['category'],0)
        self.assertFalse(rows[2]['cells'][0]['seen'])
        output=coverage_workbook(learners,rows)
        with ZipFile(BytesIO(output)) as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn(b'freeze',archive.read('xl/worksheets/sheet1.xml').replace(b'frozen',b'freeze'))
        self.assertEqual(self.client.get('/doelenoverzicht/',{'classroom':self.room.pk,'download':'excel'}).status_code,200)
        self.b.view_all_teachers=False;self.b.save()
        self.assertFalse(any(cell['seen'] for row in self.client.get('/doelenoverzicht/',{'classroom':self.room.pk}).context['rows'] for cell in row['cells']))

    def test_colors_are_personal_validated_and_not_score_colors(self):
        from accounts.preferences import COLORS
        values={key:'#123456' for key in COLORS}
        self.assertEqual(self.client.post('/instellingen/',values).status_code,302)
        self.b.refresh_from_db();self.a.refresh_from_db()
        self.assertEqual(self.b.ui_colors['menu'],'#123456')
        self.assertEqual(self.a.ui_colors,{})
        values['menu']='red;display:none'
        self.assertEqual(self.client.post('/instellingen/',values).status_code,200)
        self.b.refresh_from_db()
        self.assertEqual(self.b.ui_colors['menu'],'#123456')
        self.assertEqual(self.client.get('/beheerder/backups/').status_code,403)

