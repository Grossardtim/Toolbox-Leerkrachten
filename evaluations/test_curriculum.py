from datetime import date
from django.test import TestCase
from . import tests as fixtures
from .models import Goal, Point, Lesson, LessonStudent, Score, Student
from .services import snapshot_goal
from .coverage import build_coverage
from .templatetags.evaluation_metrics import out_of_100


class CurriculumTests(TestCase):
    def setUp(self):
        fixtures.PortalTests.setUp(self)

    def test_partial_selection_appends_without_erasing_scores(self):
        g=Goal.objects.create(owner=self.teacher,study_direction=self.direction,stage=3,code='BK04',title='Manicure')
        points=[Point.objects.create(goal=g,title=t,position=i) for i,t in enumerate(['Reiniging','Massage','Werk','Afsluiting'])]
        url=f'/lessen/{self.lesson.pk}/doelen/'
        self.client.post(url,{'action':'add_selection','revision':0,'points':[points[0].pk,points[2].pk]})
        target=self.lesson.goals.get(source=g)
        self.assertEqual(target.points.count(),2)
        first=target.points.first()
        score=Score.objects.create(point=first,learner=self.learner,value=0)
        self.client.post(url,{'action':'add_selection','revision':1,'goals':[g.pk]})
        self.assertEqual(target.points.count(),4)
        self.assertTrue(Score.objects.filter(pk=score.pk,value=0).exists())
        self.client.post(url,{'action':'add_selection','revision':2,'goals':[g.pk]})
        self.assertEqual(target.points.count(),4)

    def test_wrong_scope_rolls_back_entire_selection(self):
        wrong=Goal.objects.create(owner=self.teacher,study_direction=self.direction,stage=1,code='WRONG',title='Andere graad')
        self.client.post(f'/lessen/{self.lesson.pk}/doelen/',{'action':'add_selection','revision':0,'goals':[self.goal.pk,wrong.pk]})
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.revision,0)
        self.assertEqual(self.lesson.goals.count(),1)

    def test_direct_goal_and_completion_across_lessons(self):
        direct=Goal.objects.create(owner=self.teacher,study_direction=self.direction,stage=3,code='DIRECT',title='Zelfstandig werken')
        snap=snapshot_goal(self.lesson,direct)
        self.assertTrue(snap.points.get().is_direct)
        Score.objects.create(point=snap.points.get(),learner=self.learner,value=0)
        points=list(self.snap.points.all())
        Score.objects.create(point=points[0],learner=self.learner,value=0)
        _,rows=build_coverage(self.teacher,{'classroom':self.room})
        summary=next(r for r in rows if r['goal_id']==self.goal.pk and r['kind']=='bk')
        self.assertFalse(summary['cells'][0]['seen'])
        lesson=Lesson.objects.create(owner=self.teacher,classroom=self.room,subject=self.subject,grade=6,title='Vervolg',date=date(2026,10,7))
        learner=LessonStudent.objects.create(lesson=lesson,student=self.student,name=self.student.name)
        target=snapshot_goal(lesson,self.goal,[self.goal.points.last()])
        Score.objects.create(point=target.points.get(),learner=learner,value=80)
        _,rows=build_coverage(self.teacher,{'classroom':self.room})
        summary=next(r for r in rows if r['goal_id']==self.goal.pk and r['kind']=='bk')
        self.assertTrue(summary['cells'][0]['seen'])
        self.assertEqual(summary['cells'][0]['covered'],2)
        self.assertTrue(next(r for r in rows if r['kind']=='direct')['cells'][0]['seen'])

    def test_normalization_excludes_empty_and_absent(self):
        from .services import metric
        self.assertEqual(out_of_100(metric([0,80,None,'absent'],4)),50)
        self.assertEqual(out_of_100(metric([60],1)),75)
        self.assertIsNone(out_of_100(metric([None,'absent'],2)))

    def test_save_large_lesson_19_students(self):
        roster=[self.learner]
        for i in range(18):
            student=Student.objects.create(classroom=self.room,name=f'Fictief {i:02d}')
            roster.append(LessonStudent.objects.create(lesson=self.lesson,student=student,name=student.name))
        goal=Goal.objects.create(owner=self.teacher,study_direction=self.direction,stage=3,code='LARGE',title='Uitgebreid')
        for i in range(60):Point.objects.create(goal=goal,title=f'Subdoel {i}',position=i)
        snapshot_goal(self.lesson,goal)
        data={'revision':0,'title':'19 leerlingen','date':'2026-10-05','feedback':'Demo'}
        for learner in roster:
            data[f'feedback_{learner.pk}']='Test'
            for group in self.lesson.goals.all():
                for point in group.points.all():data[f'score_{point.pk}_{learner.pk}']='60'
        self.assertGreater(len(data),1000)
        self.assertEqual(self.client.post(f'/lessen/{self.lesson.pk}/',data).status_code,302)
        self.assertEqual(Score.objects.count(),19*62)

    def test_subgoal_identity_survives_reorder(self):
        original=list(self.goal.points.all())
        self.client.post(f'/beheer/doelen/{self.goal.pk}/',{'study_direction':self.direction.pk,'stage':3,
            'code':self.goal.code,'title':self.goal.title,'evaluation_points':'Punt 2\nPunt 1'})
        self.assertEqual(list(self.goal.points.values_list('pk',flat=True)),[original[1].pk,original[0].pk])
