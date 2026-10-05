from unittest.mock import patch
from django.test import TestCase, Client
from accounts.models import User
from accounts.local_app import register_shutdown
from .models import Year, StudyDirection, Subject, Classroom, Student, Goal, AuditEvent
from . import tests as portal_tests


class SharedAdministrationTests(TestCase):
    def test_edit_preserves_creator_and_logs_actual_editor(self):
        creator = User.objects.create_user('creator')
        editor = User.objects.create_user('editor', can_evaluate=False)
        direction = StudyDirection.objects.create(owner=creator, name='Haarzorg')
        self.client.force_login(editor)
        response = self.client.post(f'/beheer/studierichtingen/{direction.pk}/', {'name':'Haarverzorging'})
        self.assertEqual(response.status_code,302)
        direction.refresh_from_db()
        self.assertEqual(direction.owner_id,creator.pk)
        self.assertEqual(direction.name,'Haarverzorging')
        self.assertTrue(AuditEvent.objects.filter(actor=editor,object_id=direction.pk,action='gewijzigd').exists())
        self.assertContains(self.client.post('/beheer/studierichtingen/?nieuw=1',{'name':'Haarverzorging'}),'Deze naam bestaat al')

    def test_software_log_is_admin_only_and_version_is_visible(self):
        from schoolportal.releases import VERSION, RELEASES
        self.assertRegex(VERSION,r'^\d+\.\d+\.\d{3}$')
        self.assertEqual(VERSION,RELEASES[0]['version'])
        user=User.objects.create_user('version-viewer')
        self.client.force_login(user)
        self.assertContains(self.client.get('/'),VERSION)
        self.assertEqual(self.client.get('/beheerder/versies/').status_code,403)
        admin=User.objects.create_superuser('version-admin',password='Only-for-testing-234')
        self.client.force_login(admin)
        self.assertContains(self.client.get('/beheerder/versies/'),VERSION)

    def test_shutdown_requires_local_launcher_login_and_csrf(self):
        user=User.objects.create_user('local')
        self.client.force_login(user)
        register_shutdown(None)
        self.assertEqual(self.client.post('/afsluiten/').status_code,403)
        register_shutdown(lambda:None)
        try:
            self.assertEqual(self.client.get('/afsluiten/',REMOTE_ADDR='192.0.2.1').status_code,403)
            with patch('accounts.local_app.threading.Timer') as timer:
                self.assertEqual(self.client.get('/afsluiten/').status_code,200)
                timer.assert_not_called()
                self.assertEqual(self.client.post('/afsluiten/').status_code,200)
                timer.return_value.start.assert_called_once()
            client=Client(enforce_csrf_checks=True);client.force_login(user)
            self.assertEqual(client.post('/afsluiten/').status_code,403)
        finally:
            register_shutdown(None)


class AdminLessonTests(TestCase):
    setUp = portal_tests.PortalTests.setUp
    payload = portal_tests.PortalTests.payload
    # Run only these additional scenarios, reusing the realistic lesson fixture.
    def test_admin_edits_other_lesson_without_taking_ownership(self):
        admin=User.objects.create_superuser('full-admin',password='Test-admin-56789')
        self.client.force_login(admin)
        self.assertEqual(self.client.post(f'/lessen/{self.lesson.pk}/',self.payload()).status_code,302)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.owner_id,self.teacher.pk)
        self.assertEqual(self.lesson.feedback,'Klasfeedback')
        self.assertTrue(AuditEvent.objects.filter(actor=admin,object_id=self.lesson.pk).exists())
