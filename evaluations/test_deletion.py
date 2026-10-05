from datetime import date
from django.test import TestCase, Client
from accounts.models import User
from .models import Year, Subject, Classroom, Student, Goal, Point, Lesson, LessonStudent, Score, AuditEvent
from .services import snapshot_goal


class RecordDeletionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user('owner', can_evaluate=True)
        cls.other = User.objects.create_user('other', can_evaluate=True)
        cls.admin = User.objects.create_superuser('admin', password='A-long-test-password')
        cls.year = Year.objects.create(owner=cls.teacher, name='2026')
        cls.subject = Subject.objects.create(owner=cls.teacher, year=cls.year, name='Praktijk')
        cls.room = Classroom.objects.create(owner=cls.teacher, year=cls.year, name='6HV', grade=6, direction='Haarzorg')
        cls.room.subjects.add(cls.subject)
        cls.student = Student.objects.create(classroom=cls.room, name='Leerling A')
        cls.goal = Goal.objects.create(owner=cls.teacher, stage=3, code='D1', title='Doel')

        Point.objects.create(goal=cls.goal, title='Punt')
        cls.lesson = Lesson.objects.create(owner=cls.teacher, classroom=cls.room, subject=cls.subject, grade=6, title='Les', date=date(2026,10,4))
        cls.roster = LessonStudent.objects.create(lesson=cls.lesson, student=cls.student, name=cls.student.name)
        cls.snapshot = snapshot_goal(cls.lesson, cls.goal)
        Score.objects.create(point=cls.snapshot.points.first(), learner=cls.roster, value=60)

    def setUp(self):
        self.client.force_login(self.teacher)

    def url(self, kind, obj):
        return f'/wissen/{kind}/{obj.pk}/'

    def confirmed(self, kind, obj):
        url = self.url(kind, obj)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return self.client.post(url, {'confirm': 'yes', 'token': response.context['token']})

    def test_empty_management_records_can_be_deleted(self):
        objects = [
            ('schooljaren', Year.objects.create(owner=self.teacher, name='Leeg jaar')),
            ('vakken', Subject.objects.create(owner=self.teacher, year=self.year, name='Leeg vak')),
            ('klassen', Classroom.objects.create(owner=self.teacher, year=self.year, name='Lege klas', grade=6)),
            ('leerlingen', Student.objects.create(classroom=self.room, name='Ongebruikte leerling')),
        ]
        for kind, obj in objects:
            with self.subTest(kind=kind):
                self.assertEqual(self.confirmed(kind, obj).status_code, 302)
                self.assertFalse(type(obj).objects.filter(pk=obj.pk).exists())
                self.assertTrue(AuditEvent.objects.filter(object_type=obj._meta.model_name, object_id=obj.pk).exists())

    def test_used_parents_and_roster_students_are_protected(self):
        for kind, obj in [('schooljaren', self.year), ('vakken', self.subject), ('klassen', self.room), ('leerlingen', self.student)]:
            with self.subTest(kind=kind):
                self.assertContains(self.client.get(self.url(kind, obj)), 'wordt nog gebruikt')
                self.assertEqual(self.confirmed(kind, obj).status_code, 409)
                self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())
        self.assertEqual(Score.objects.count(), 1)

    def test_goal_deletion_keeps_historical_scores_and_snapshots(self):
        self.assertEqual(self.confirmed('doelen', self.goal).status_code, 302)
        self.assertFalse(Goal.objects.filter(pk=self.goal.pk).exists())
        self.snapshot.refresh_from_db()
        self.assertIsNone(self.snapshot.source_id)
        self.assertEqual(self.snapshot.title, 'Doel')
        self.assertEqual(self.snapshot.points.first().title, 'Punt')
        self.assertEqual(Score.objects.get().value, 60)

    def test_lesson_deletion_is_explicit_and_cascades_only_lesson(self):
        response = self.client.get(self.url('lessen', self.lesson))
        self.assertTrue(Lesson.objects.filter(pk=self.lesson.pk).exists())
        self.assertContains(response, 'beoordelingen worden mee verwijderd')
        self.assertEqual(self.confirmed('lessen', self.lesson).status_code, 302)
        self.assertFalse(Lesson.objects.filter(pk=self.lesson.pk).exists())
        self.assertFalse(Score.objects.exists())
        self.assertTrue(Student.objects.filter(pk=self.student.pk).exists())
        self.assertTrue(Goal.objects.filter(pk=self.goal.pk).exists())
        self.assertTrue(Classroom.objects.filter(pk=self.room.pk).exists())

    def test_confirmation_and_fresh_token_required(self):
        url = self.url('lessen', self.lesson)
        token = self.client.get(url).context['token']
        self.assertEqual(self.client.post(url, {'token': token}).status_code, 400)
        self.assertEqual(self.client.post(url, {'confirm': 'yes', 'token': 'forged'}).status_code, 409)
        Lesson.objects.filter(pk=self.lesson.pk).update(title='Intussen gewijzigd')
        self.assertEqual(self.client.post(url, {'confirm': 'yes', 'token': token}).status_code, 409)
        self.assertTrue(Lesson.objects.filter(pk=self.lesson.pk).exists())

    def test_shared_management_and_admin_lesson_deletion(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url('lessen', self.lesson)).status_code,404)
        self.assertEqual(self.client.get(self.url('doelen', self.goal)).status_code,200)
        self.assertEqual(self.client.post(self.url('doelen', self.goal), {'confirm':'yes'}).status_code,409)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url('lessen', self.lesson)).status_code,200)
        self.assertEqual(self.confirmed('lessen', self.lesson).status_code,302)
        self.assertTrue(Goal.objects.filter(pk=self.goal.pk).exists())

    def test_admin_can_delete_empty_teacher_but_not_self_or_used_teacher(self):
        self.assertEqual(self.client.get(self.url('leerkrachten', self.other)).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url('leerkrachten', self.admin)).status_code, 404)
        self.assertEqual(self.confirmed('leerkrachten', self.teacher).status_code, 409)
        self.assertEqual(self.confirmed('leerkrachten', self.other).status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.other.pk).exists())

    def test_csrf_blocks_delete(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.teacher)
        self.assertEqual(client.post(self.url('lessen', self.lesson), {'confirm':'yes'}).status_code, 403)
        self.assertTrue(Lesson.objects.filter(pk=self.lesson.pk).exists())

    def test_class_selection_shows_only_its_students_and_keeps_all_class_rows(self):
        other_room = Classroom.objects.create(owner=self.teacher, year=self.year, name='5HV', grade=5)
        Student.objects.create(classroom=other_room, name='Leerling B')
        response = self.client.get(f'/beheer/klassen/?classroom={self.room.pk}')
        self.assertContains(response, 'Klas 6HV selecteren')
        self.assertContains(response, 'Klas 5HV selecteren')
        self.assertContains(response, 'Leerling A')
        self.assertNotContains(response, 'Leerling B')
        self.assertContains(response, 'selected-row')
        self.assertContains(self.client.get('/beheer/klassen/'), 'Leerling B')
