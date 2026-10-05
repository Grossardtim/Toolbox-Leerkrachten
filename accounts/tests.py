from django.test import TestCase
from .models import User

class AccountManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin=User.objects.create_superuser('admin.test',password='Test-admin-password-42')
        cls.teacher=User.objects.create_user('teacher.test',password='Test-teacher-password-42',first_name='Voorbeeld',can_evaluate=True)
        cls.inactive=User.objects.create_user('inactive.test',is_active=False)

    def test_login_dropdown_has_only_active_accounts(self):
        response=self.client.get('/aanmelden/')
        self.assertContains(response,'<select')
        self.assertContains(response,'teacher.test')
        self.assertContains(response,'admin.test')
        self.assertNotContains(response,'inactive.test')
        self.assertNotContains(response,'Test-admin-password-42')

    def test_login_still_requires_password(self):
        self.assertEqual(self.client.post('/aanmelden/',{'username':'teacher.test','password':'wrong'}).status_code,200)
        response=self.client.post('/aanmelden/',{'username':'teacher.test','password':'Test-teacher-password-42'})
        self.assertEqual(response.status_code,302)

    def test_teacher_cannot_manage_users(self):
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get('/leerkrachten/').status_code,403)
        self.assertEqual(self.client.post(f'/leerkrachten/{self.teacher.pk}/',{}).status_code,403)

    def test_admin_can_create_and_deactivate_without_deleting(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get('/'),'Leerkrachten & toegang')
        response=self.client.post('/leerkrachten/?nieuw=1',{'username':'nieuw','first_name':'Nieuw','last_name':'Test',
            'is_active':'on','can_evaluate':'on','can_export':'on','password1':'Nieuw-test-password-42','password2':'Nieuw-test-password-42'})
        self.assertEqual(response.status_code,302)
        person=User.objects.get(username='nieuw')
        self.assertTrue(person.check_password('Nieuw-test-password-42'))
        self.assertFalse(person.is_staff)
        self.assertFalse(person.is_superuser)
        response=self.client.post(f'/leerkrachten/{person.pk}/',{'username':'nieuw','first_name':'Nieuw','last_name':'Test','can_evaluate':'on'})
        self.assertEqual(response.status_code,302)
        person.refresh_from_db()
        self.assertFalse(person.is_active)
        self.assertFalse(person.can_export)
        self.assertTrue(person.check_password('Nieuw-test-password-42'))

    def test_admin_profile_not_editable_as_teacher(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(f'/leerkrachten/{self.admin.pk}/').status_code,404)

    def test_invalid_password_not_saved(self):
        self.client.force_login(self.admin)
        self.client.post('/leerkrachten/?nieuw=1',{'username':'bad','password1':'123','password2':'456'})
        self.assertFalse(User.objects.filter(username='bad').exists())
