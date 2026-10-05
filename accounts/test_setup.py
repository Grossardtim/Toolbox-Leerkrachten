from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import TestCase, override_settings, Client
from .models import User


class FirstSetupTests(TestCase):
    def test_setup_is_not_available_on_normal_web_app(self):
        self.assertEqual(self.client.get('/eerste-start/').status_code,404)

    @override_settings(STANDALONE=True)
    def test_only_empty_local_installation_can_create_first_admin(self):
        with TemporaryDirectory() as directory, override_settings(DATA_DIR=Path(directory)):
            self.assertRedirects(self.client.get('/aanmelden/'),'/eerste-start/')
            self.assertEqual(self.client.get('/eerste-start/',REMOTE_ADDR='192.168.1.2').status_code,404)
            response=self.client.post('/eerste-start/',{'username':'beheerder','password1':'Testing-Strong-8642','password2':'Testing-Strong-8642'})
            self.assertRedirects(response,'/aanmelden/')
            admin=User.objects.get(username='beheerder')
            self.assertTrue(admin.is_superuser)
            self.assertTrue(admin.check_password('Testing-Strong-8642'))
            self.assertEqual(self.client.get('/eerste-start/').status_code,404)
            self.assertEqual(self.client.post('/eerste-start/',{'username':'extra'}).status_code,404)
            self.assertFalse(admin.can_evaluate)

    @override_settings(STANDALONE=True)
    def test_setup_requires_csrf(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/eerste-start/',{'username':'admin'}).status_code,403)
