from datetime import date
from django.test import TestCase, Client
from django.db import IntegrityError, transaction
from accounts.models import User
from .models import Year, Subject, Classroom, Student, Goal, Point, Lesson, LessonStudent, Score, StudyDirection
from .services import snapshot_goal, lesson_report, metric

class PortalTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user('teacher', view_all_teachers=False, password='A-test-password-42', can_evaluate=True)
        self.other = User.objects.create_user('other', view_all_teachers=False, password='Other-test-password-42', can_evaluate=True)
        self.year = Year.objects.create(owner=self.teacher, name='2026–2027')
        self.subject = Subject.objects.create(owner=self.teacher, year=self.year, name='Praktijk')
        self.direction = StudyDirection.objects.create(owner=self.teacher, name='Haarzorg')
        self.subject.study_directions.add(self.direction)
        self.room = Classroom.objects.create(owner=self.teacher, year=self.year, name='6HV', direction='Haarzorg', study_direction=self.direction, grade=6)
        self.room.subjects.add(self.subject)
        self.student = Student.objects.create(classroom=self.room, name='Leerling Een')
        self.goal = Goal.objects.create(owner=self.teacher, study_direction=self.direction, code='A', title='Doel A', stage=3)

        Point.objects.create(goal=self.goal, title='Punt 1')
        Point.objects.create(goal=self.goal, title='Punt 2', position=1)
        self.lesson = Lesson.objects.create(owner=self.teacher, classroom=self.room, subject=self.subject, title='Les', date=date(2026,10,5), grade=6)
        self.learner = LessonStudent.objects.create(lesson=self.lesson, student=self.student, name=self.student.name)
        self.snap = snapshot_goal(self.lesson, self.goal)
        self.client.force_login(self.teacher)

    def payload(self, revision=0, values=('20', '80')):
        data = {'revision': revision, 'title': 'Les bijgewerkt', 'date': '2026-10-06', 'feedback': 'Klasfeedback',
                f'feedback_{self.learner.pk}': 'Goed gewerkt'}
        for point, value in zip(self.snap.points.all(), values):
            data[f'score_{point.pk}_{self.learner.pk}'] = value
        return data

    def test_pages_render(self):
        paths = ['/', '/evaluaties/', '/lessen/nieuw/', f'/lessen/{self.lesson.pk}/', '/wachtwoord/']
        paths += [f'/beheer/{kind}/?year={self.year.pk}' for kind in ['schooljaren','vakken','klassen','leerlingen','doelen']]
        paths += [f'/beheer/{kind}/?year={self.year.pk}&nieuw=1' for kind in ['vakken','klassen','leerlingen','doelen']]
        for path in paths:
            with self.subTest(path=path): self.assertEqual(self.client.get(path).status_code, 200)

    def test_save_scores_feedback_and_reopen(self):
        response = self.client.post(f'/lessen/{self.lesson.pk}/', self.payload())
        self.assertEqual(response.status_code, 302)
        self.lesson.refresh_from_db(); self.learner.refresh_from_db()
        self.assertEqual(self.lesson.feedback, 'Klasfeedback')
        self.assertEqual(self.learner.feedback, 'Goed gewerkt')
        self.assertEqual(self.lesson.revision, 1)
        self.assertEqual(lesson_report(self.lesson)['class_metric']['average'], 50)
        self.assertContains(self.client.get(f'/lessen/{self.lesson.pk}/'), 'Goed gewerkt')

    def test_invalid_score_rejected_without_partial_changes(self):
        response = self.client.post(f'/lessen/{self.lesson.pk}/', self.payload(values=('21','80')))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Score.objects.exists())
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.revision, 0)

    def test_database_rejects_invalid_score(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Score.objects.create(point=self.snap.points.first(), learner=self.learner, value=1)

    def test_blank_excluded_and_clear_supported(self):
        self.client.post(f'/lessen/{self.lesson.pk}/', self.payload(values=('', '80')))
        self.assertEqual(lesson_report(self.lesson)['class_metric'], {'average': 80, 'total': 80, 'count': 1, 'possible': 2, 'absent': 0, 'maximum': 80})
        self.client.post(f'/lessen/{self.lesson.pk}/', self.payload(revision=1, values=('', '')))
        self.assertIsNone(lesson_report(self.lesson)['class_metric']['average'])

    def test_stale_revision_cannot_overwrite(self):
        self.client.post(f'/lessen/{self.lesson.pk}/', self.payload())
        response = self.client.post(f'/lessen/{self.lesson.pk}/', self.payload(values=('40', '40')))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(lesson_report(self.lesson)['class_metric']['average'], 50)

    def test_incomplete_payload_cannot_erase_scores(self):
        self.client.post(f'/lessen/{self.lesson.pk}/', self.payload())
        self.assertEqual(self.client.post(f'/lessen/{self.lesson.pk}/', {'revision': 1}).status_code, 400)
        self.assertEqual(Score.objects.count(), 2)

    def test_teacher_isolation_all_endpoints(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/beheer/klassen/{self.room.pk}/?year={self.year.pk}').status_code,200)
        self.assertEqual(self.client.get(f'/evaluaties/?year={self.year.pk}').status_code,200)
        paths = [f'/lessen/{self.lesson.pk}/']
        for path in paths:
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.post(f'/lessen/{self.lesson.pk}/', self.payload()).status_code, 404)
        self.assertEqual(self.client.post(f'/lessen/{self.lesson.pk}/doelen/', {'action':'remove','goal':self.snap.pk,'revision':0,'confirm':'yes'}).status_code, 404)

    def test_revocation_applies_to_existing_session(self):
        self.teacher.can_evaluate = False; self.teacher.save()
        self.assertEqual(self.client.get('/evaluaties/').status_code, 403)
        self.assertEqual(self.client.post(f'/lessen/{self.lesson.pk}/', self.payload()).status_code, 403)

    def test_deactivated_account_blocked(self):
        self.teacher.is_active = False; self.teacher.save()
        self.assertEqual(self.client.get('/evaluaties/').status_code, 302)

    def test_goal_edits_preserve_previous_lesson(self):
        self.goal.title = 'Nieuwe betekenis'; self.goal.save()
        self.goal.points.all().delete()
        self.snap.refresh_from_db()
        self.assertEqual(self.snap.title, 'Doel A')
        self.assertEqual(self.snap.points.count(), 2)

    def test_point_weighting_not_average_of_goal_averages(self):
        second = Goal.objects.create(owner=self.teacher, study_direction=self.direction, code='B', title='Doel B')
        Point.objects.create(goal=second, title='Punt 3')
        snap = snapshot_goal(self.lesson, second)
        for p in self.snap.points.all(): Score.objects.create(point=p, learner=self.learner, value=20)
        Score.objects.create(point=snap.points.first(), learner=self.learner, value=80)
        report = lesson_report(self.lesson)
        self.assertEqual(report['class_metric']['average'], 40)
        self.assertEqual(report['student_metrics'][0]['metric']['average'], 40)

    def test_removal_needs_confirmation_and_revision(self):
        url = f'/lessen/{self.lesson.pk}/doelen/'
        self.client.post(url, {'action':'remove','goal':self.snap.pk,'revision':0})
        self.assertEqual(self.lesson.goals.count(), 1)
        self.client.post(url, {'action':'remove','goal':self.snap.pk,'revision':0,'confirm':'yes'})
        self.assertEqual(self.lesson.goals.count(), 0)

    def test_foreign_goal_cannot_be_added(self):
        y = Year.objects.create(owner=self.other, name='2026')
        s = Subject.objects.create(owner=self.other, year=y, name='Vak')
        g = Goal.objects.create(owner=self.other, code='X', title='Privé')
        response = self.client.post(f'/lessen/{self.lesson.pk}/doelen/', {'action':'add','goal':g.pk,'revision':0})
        self.assertEqual(response.status_code, 404)
        self.lesson.refresh_from_db(); self.assertEqual(self.lesson.revision, 0)

    def test_management_creation_and_goal_edit(self):
        self.assertEqual(self.client.post(f'/beheer/vakken/?year={self.year.pk}', {'name':'Theorie', 'study_directions':[self.direction.pk]}).status_code, 302)
        self.assertEqual(self.client.post(f'/beheer/klassen/?year={self.year.pk}', {'name':'5HV','study_direction':self.direction.pk,'grade':5,'subjects':[self.subject.pk]}).status_code, 302)
        room = Classroom.objects.get(name='5HV')
        self.assertEqual(self.client.post(f'/beheer/leerlingen/?year={self.year.pk}', {'classroom':room.pk,'name':'Nieuw','active':'on'}).status_code, 302)
        response = self.client.post(f'/beheer/doelen/{self.goal.pk}/?year={self.year.pk}',
            {'study_direction':self.direction.pk,'stage':3,'code':'A','title':'Aangepast', 'evaluation_points':'Nieuw punt\nTweede punt'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.goal.points.first().title, 'Nieuw punt')
        self.assertEqual(self.snap.points.first().title, 'Punt 1')

    def test_lesson_creation_copies_roster(self):
        response = self.client.post(f'/lessen/nieuw/?year={self.year.pk}', {'classroom':self.room.pk,'subject':self.subject.pk,'title':'Nieuwe les','date':'2026-10-07'})
        self.assertEqual(response.status_code, 302)
        lesson = Lesson.objects.get(title='Nieuwe les')
        self.assertEqual(lesson.roster.get().name, self.student.name)

    def test_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.teacher)
        self.assertEqual(client.post(f'/lessen/{self.lesson.pk}/', self.payload()).status_code, 403)

    def test_admin_can_view_all_evaluations(self):
        admin = User.objects.create_superuser('admin', password='Admin-test-password-42')
        self.client.force_login(admin)
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        self.assertEqual(self.client.get('/evaluaties/').status_code, 200)
        self.assertEqual(self.client.get('/admin/accounts/user/').status_code, 200)
        self.assertEqual(self.client.get('/admin/accounts/user/add/').status_code, 200)

    def test_login_rate_limit_including_admin(self):
        self.client.logout()
        for _ in range(5):
            self.client.post('/aanmelden/', {'username':'teacher','password':'wrong'})
        self.assertEqual(self.client.post('/aanmelden/', {'username':'teacher','password':'wrong'}).status_code, 429)
        self.assertEqual(self.client.post('/admin/login/', {'username':'teacher','password':'wrong'}).status_code, 429)

    def test_no_data_is_not_zero(self):
        self.assertEqual(metric([], 3), {'total':None,'average':None,'count':0,'possible':3,'absent':0,'maximum':0})

    def test_zero_and_absence_are_distinct_and_persist(self):
        response = self.client.post(f'/lessen/{self.lesson.pk}/', self.payload(values=('0','absent')))
        self.assertEqual(response.status_code, 302)
        report = lesson_report(self.lesson)
        self.assertEqual(report['class_metric'], {'total':0,'average':0,'count':1,'possible':2,'absent':1,'maximum':80})
        self.assertEqual(Score.objects.get(status='absent').value, None)
        response = self.client.get(f'/lessen/{self.lesson.pk}/')
        self.assertContains(response, 'value="absent" selected')
        self.assertContains(response, 'value="0" selected')
        self.client.post(f'/lessen/{self.lesson.pk}/', self.payload(revision=1, values=('absent','absent')))
        report = lesson_report(self.lesson)
        self.assertIsNone(report['class_metric']['average'])
        self.assertEqual(report['class_metric']['absent'], 2)

    def test_database_rejects_absent_with_number(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Score.objects.create(point=self.snap.points.first(), learner=self.learner, value=0, status='absent')

    def test_wrong_grade_goal_hidden_and_cannot_be_added(self):
        wrong = Goal.objects.create(owner=self.teacher, study_direction=self.direction, stage=2, code='FIFTH', title='Vijfde leerjaar')

        Point.objects.create(goal=wrong, title='Punt')
        response = self.client.get(f'/lessen/{self.lesson.pk}/')
        self.assertNotContains(response, 'FIFTH')
        self.assertEqual(self.client.post(f'/lessen/{self.lesson.pk}/doelen/', {'action':'add','goal':wrong.pk,'revision':0}).status_code, 404)

    def test_goal_rejects_invalid_stage(self):
        response = self.client.post(f'/beheer/doelen/?year={self.year.pk}',
            {'study_direction':self.direction.pk,'stage':4,'code':'NEW','title':'Ongeldig', 'evaluation_points':'Punt'})
        self.assertContains(response, 'Selecteer een geldige keuze')
        self.assertFalse(Goal.objects.filter(code='NEW').exists())

    def test_correct_grade_goal_add_and_duplicate_prevention(self):
        new = Goal.objects.create(owner=self.teacher, study_direction=self.direction, stage=3, code='NEW', title='Zesde')

        Point.objects.create(goal=new, title='Nieuw punt')
        url = f'/lessen/{self.lesson.pk}/doelen/'
        self.assertEqual(self.client.post(url, {'action':'add','goal':new.pk,'revision':0}).status_code, 302)
        self.assertEqual(self.client.post(url, {'action':'add','goal':new.pk,'revision':1}).status_code, 302)
        self.assertEqual(self.lesson.goals.filter(source=new).count(), 1)

    def second_snapshot(self):
        goal = Goal.objects.create(owner=self.teacher, study_direction=self.direction,
                                   stage=3, code='B', title='Doel B')

        Point.objects.create(goal=goal, title='Derde punt')
        return snapshot_goal(self.lesson, goal)

    def test_reordering_saves_with_scores_and_feedback(self):
        second = self.second_snapshot()
        data = self.payload()
        data['goal_order'] = f'{second.pk},{self.snap.pk}'
        data[f'score_{second.points.first().pk}_{self.learner.pk}'] = '0'
        response = self.client.post(f'/lessen/{self.lesson.pk}/', data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(self.lesson.goals.values_list('pk', flat=True)), [second.pk, self.snap.pk])
        report = lesson_report(self.lesson)
        self.assertEqual(report['class_metric']['total'], 100)
        self.assertEqual(report['class_metric']['count'], 3)
        self.assertEqual(report['learners'][0].display_feedback, 'Goed gewerkt')

    def test_invalid_order_cannot_partially_save(self):
        self.client.post(f'/lessen/{self.lesson.pk}/', self.payload())
        for invalid in ['', '999999', f'{self.snap.pk},{self.snap.pk}', 'abc']:
            data = self.payload(revision=1, values=('0','0'))
            data['goal_order'] = invalid
            self.assertEqual(self.client.post(f'/lessen/{self.lesson.pk}/', data).status_code, 400)
            self.assertEqual(lesson_report(self.lesson)['class_metric']['total'], 100)
            self.lesson.refresh_from_db()
            self.assertEqual(self.lesson.revision, 1)

    def test_stale_reorder_preserves_order_and_scores(self):
        second = self.second_snapshot()
        data = self.payload()
        data[f'score_{second.points.first().pk}_{self.learner.pk}'] = '80'
        self.client.post(f'/lessen/{self.lesson.pk}/', data)
        data['goal_order'] = f'{second.pk},{self.snap.pk}'
        self.assertEqual(self.client.post(f'/lessen/{self.lesson.pk}/', data).status_code, 409)
        self.assertEqual(list(self.lesson.goals.values_list('pk', flat=True)), [self.snap.pk, second.pk])
        self.assertEqual(lesson_report(self.lesson)['class_metric']['total'], 180)

    def test_combined_management_and_import_scope(self):
        response = self.client.get(f'/beheer/klassen/?year={self.year.pk}&classroom={self.room.pk}')
        self.assertContains(response, self.student.name)
        self.assertContains(response, 'Klassen &amp; leerlingen')
        self.assertContains(response, 'Filter op Studierichting')
        form = self.client.get(f'/beheer/leerlingen/?year={self.year.pk}&classroom={self.room.pk}&nieuw=1').context['form']
        self.assertEqual(form['classroom'].value(), self.room.pk)
        before = Goal.objects.count()
        self.assertContains(self.client.get(f'/beheer/doelen/import/?year={self.year.pk}'), 'Wacht op voorbeeldbestand')
        self.assertEqual(Goal.objects.count(), before)
        self.client.force_login(self.other)
        # Import preparation no longer reads or selects a schoolyear.
        self.assertEqual(self.client.get(f'/beheer/doelen/import/?year={self.year.pk}').status_code, 200)
        self.assertEqual(self.client.get(f'/beheer/klassen/?classroom={self.room.pk}').status_code, 200)

    def test_no_filters_shows_all_own_years_including_inactive_records(self):
        old_year = Year.objects.create(owner=self.teacher, name='2025–2026')
        old_subject = Subject.objects.create(owner=self.teacher, year=old_year, name='Oud vak')
        old_class = Classroom.objects.create(owner=self.teacher, year=old_year, name='5HV', direction='Haarzorg', grade=5, archived=True)
        Student.objects.create(classroom=old_class, name='Oude leerling', active=False)
        Lesson.objects.create(owner=self.teacher, classroom=old_class, subject=old_subject,
                              grade=5, title='Oude les', date=date(2025,10,5))
        foreign_year = Year.objects.create(owner=self.other, name='2024–2025')
        Classroom.objects.create(owner=self.other, year=foreign_year, name='PRIVEKLAS', direction='Privé', grade=4)
        for query in ['', '?year=']:
            response = self.client.get('/beheer/klassen/' + query)
            for text in ['5HV', '6HV', 'Oude leerling', 'Leerling Een']:
                self.assertContains(response, text)
            self.assertContains(response, 'PRIVEKLAS')
            self.assertContains(self.client.get('/evaluaties/' + query), 'Oude les')
        response = self.client.get(f'/beheer/klassen/?year={self.year.pk}')
        self.assertNotContains(response, 'Oude leerling')
        self.assertNotContains(self.client.get(f'/evaluaties/?year={self.year.pk}'), 'Oude les')
        response = self.client.get('/beheer/vakken/')
        self.assertContains(response, 'Oud vak')
        self.assertContains(response, 'Praktijk')
