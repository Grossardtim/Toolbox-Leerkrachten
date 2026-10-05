from datetime import date
from django.test import TestCase
from accounts.models import User
from .models import Year, StudyDirection, Subject, Classroom, Goal, Point, Lesson, stage_for_grade
from .services import goals_for_lesson


class GoalScopeTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('scope',can_evaluate=True)
        self.direction=StudyDirection.objects.create(owner=self.user,name='Haarzorg')
        self.goal=Goal.objects.create(owner=self.user,study_direction=self.direction,stage=3,code='G3',title='Graadbreed doel')
        Point.objects.create(goal=self.goal,title='Punt')
        self.client.force_login(self.user)

    def lesson(self, year, grade, subject, direction=None):
        y,_=Year.objects.get_or_create(owner=self.user,name=year)
        s,_=Subject.objects.get_or_create(owner=self.user,year=y,name=subject)
        c=Classroom.objects.create(owner=self.user,year=y,name=f'{grade}-{subject}',grade=grade,study_direction=direction or self.direction)
        return Lesson.objects.create(owner=self.user,classroom=c,subject=s,grade=grade,date=date(2026,10,4),title='Les')

    def test_reuse_across_years_subjects_and_years_five_six_seven(self):
        for year,grade,subject in [('2026',5,'Praktijk'),('2027',6,'Theorie'),('2028',7,'Stage')]:
            lesson=self.lesson(year,grade,subject)
            self.assertIn(self.goal,goals_for_lesson(lesson))
            response=self.client.post(f'/lessen/{lesson.pk}/doelen/',{'action':'add','goal':self.goal.pk,'revision':0})
            self.assertEqual(response.status_code,302)
            self.assertEqual(lesson.goals.get().source_id,self.goal.pk)

    def test_other_stage_direction_and_archived_goals_are_rejected(self):
        other=StudyDirection.objects.create(owner=self.user,name='Ander')
        for lesson in [self.lesson('2026',4,'Vak'),self.lesson('2026',6,'Ander vak',other)]:
            self.assertNotIn(self.goal,goals_for_lesson(lesson))
            self.assertEqual(self.client.post(f'/lessen/{lesson.pk}/doelen/',{'action':'add','goal':self.goal.pk,'revision':0}).status_code,404)
        self.goal.archived=True;self.goal.save()
        self.assertFalse(goals_for_lesson(self.lesson('2026',6,'Derde vak')).exists())

    def test_manage_goal_needs_no_schoolyear_or_subject(self):
        response=self.client.post('/beheer/doelen/?nieuw=1',{'study_direction':self.direction.pk,'stage':2,
            'code':'G2','title':'Nieuw doel','evaluation_points':'Een\nTwee'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(Year.objects.count(),0)
        goal=Goal.objects.get(code='G2')
        self.assertEqual(goal.points.count(),2)
        response=self.client.get(f'/beheer/doelen/{goal.pk}/?year=99999')
        self.assertEqual(response.status_code,200)
        self.assertNotIn('subject',response.context['form'].fields)
        self.assertNotIn('classrooms',response.context['form'].fields)
        self.assertNotContains(response,'name="year"')

    def test_foreign_direction_cannot_be_used_and_stages_are_explicit(self):
        other=User.objects.create_user('other')
        direction=StudyDirection.objects.create(owner=other,name='Privé')
        response=self.client.post('/beheer/doelen/?nieuw=1',{'study_direction':direction.pk,'stage':3,'code':'F',
            'title':'Niet toegestaan','evaluation_points':'Punt'})
        self.assertEqual(response.status_code,302)
        self.assertTrue(Goal.objects.filter(code='F',study_direction=direction).exists())
        self.assertEqual([stage_for_grade(g) for g in range(1,8)],[1,1,2,2,3,3,3])
        self.assertIsNone(stage_for_grade(None))

    def test_source_deletion_link_only_in_management(self):
        lesson=self.lesson('2026',6,'Praktijk')
        response=self.client.get(f'/lessen/{lesson.pk}/')
        self.assertContains(response,'G3')
        self.assertNotContains(response,f'/wissen/doelen/{self.goal.pk}/')
        self.assertContains(self.client.get('/beheer/doelen/'),f'/wissen/doelen/{self.goal.pk}/')
        self.client.post(f'/lessen/{lesson.pk}/doelen/',{'action':'add','goal':self.goal.pk,'revision':0})
        response=self.client.get(f'/lessen/{lesson.pk}/')
        self.assertContains(response,'uit deze les verwijderen')
