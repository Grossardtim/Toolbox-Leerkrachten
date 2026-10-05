from importlib import import_module
from types import SimpleNamespace
from django.apps import apps
from django.db import connection
from django.test import TestCase
from accounts.models import User
from .models import Year, Subject, StudyDirection, Classroom, Student


class StructureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('structure', can_evaluate=True, view_all_teachers=False)
        cls.other = User.objects.create_user('foreign', can_evaluate=True, view_all_teachers=False)
        cls.year = Year.objects.create(owner=cls.user, name='2026–2027')
        cls.direction = StudyDirection.objects.create(owner=cls.user, name='Haarzorg')
        cls.subject = Subject.objects.create(owner=cls.user, year=cls.year, name='Praktijk')
        cls.subject.study_directions.add(cls.direction)

    def setUp(self):
        self.client.force_login(self.user)

    def test_directions_are_unique_across_years_and_private(self):
        response = self.client.post('/beheer/studierichtingen/?nieuw=1', {'name':'Haarzorg'})
        self.assertContains(response, 'Deze naam bestaat al')
        Year.objects.create(owner=self.user, name='2027–2028')
        hidden = StudyDirection.objects.create(owner=self.other, name='Niet zichtbaar')
        self.assertContains(self.client.get('/beheer/studierichtingen/'), hidden.name)
        self.assertEqual(self.client.get(f'/beheer/studierichtingen/{hidden.pk}/').status_code, 200)
        self.assertEqual(self.client.post('/beheer/studierichtingen/?nieuw=1', {'name':'Schoonheidszorg'}).status_code,302)

    def test_class_direction_and_subject_must_match_and_belong_to_teacher(self):
        data={'name':'6HA','grade':6,'study_direction':self.direction.pk,'subjects':[self.subject.pk]}
        url=f'/beheer/klassen/?year={self.year.pk}'
        self.assertEqual(self.client.post(url,data).status_code,302)
        room=Classroom.objects.get(name='6HA')
        self.assertEqual(room.study_direction,self.direction)
        self.assertEqual(self.client.post(url,{**data,'name':'6HB'}).status_code,302)
        alternative=StudyDirection.objects.create(owner=self.user,name='Ander')
        self.assertContains(self.client.post(url,{**data,'name':'6HC','study_direction':alternative.pk}), 'Kies alleen vakken')
        foreign=StudyDirection.objects.create(owner=self.other,name='Extern')
        self.assertContains(self.client.post(url,{**data,'study_direction':foreign.pk}), 'Kies alleen vakken')
        self.assertContains(self.client.post(f'/beheer/vakken/{self.subject.pk}/?year={self.year.pk}', {'name':'Praktijk','study_directions':[alternative.pk]}), 'Pas eerst de klaskoppeling aan')

    def test_backfill_is_idempotent_and_keeps_existing_students(self):
        room=Classroom.objects.create(owner=self.user,year=self.year,name='Oud',direction=' Haarzorg ',grade=6)
        room.subjects.add(self.subject)
        pupil=Student.objects.create(classroom=room,name='Blijft bestaan')
        migrate=import_module('evaluations.migrations.0005_backfill_directions').forwards
        editor=SimpleNamespace(connection=connection)
        migrate(apps,editor)
        migrate(apps,editor)
        room.refresh_from_db();pupil.refresh_from_db()
        self.assertEqual(room.study_direction,self.direction)
        self.assertEqual(pupil.classroom_id,room.pk)
        self.assertEqual(StudyDirection.objects.filter(owner=self.user,name='Haarzorg').count(),1)
        self.assertTrue(self.subject.study_directions.filter(pk=self.direction.pk).exists())

    def test_directions_used_by_classes_cannot_be_deleted(self):
        response=self.client.get(f'/wissen/studierichtingen/{self.direction.pk}/')
        self.assertEqual(response.status_code,200)
        response=self.client.post(f'/wissen/studierichtingen/{self.direction.pk}/', {'confirm':'yes','token':response.context['token']})
        self.assertEqual(response.status_code,409)
        self.assertTrue(StudyDirection.objects.filter(pk=self.direction.pk).exists())
