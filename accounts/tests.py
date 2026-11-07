from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AuthTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('signup'), {
            'username': 'carol',
            'email': 'carol@example.com',
            'password1': 'S3cure-pass-123',
            'password2': 'S3cure-pass-123',
        })
        self.assertRedirects(response, reverse('task_list'))
        user = User.objects.get(username='carol')
        self.assertEqual(user.email, 'carol@example.com')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user('dave', email='dave@example.com', password='x')
        response = self.client.post(reverse('signup'), {
            'username': 'dave2',
            'email': 'DAVE@example.com',
            'password1': 'S3cure-pass-123',
            'password2': 'S3cure-pass-123',
        })
        self.assertContains(response, 'already exists')

    def test_login_and_logout(self):
        User.objects.create_user('erin', password='S3cure-pass-123')
        response = self.client.post(reverse('login'), {'username': 'erin', 'password': 'S3cure-pass-123'})
        self.assertRedirects(response, reverse('task_list'))

        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_wrong_password_shows_error(self):
        User.objects.create_user('frank', password='S3cure-pass-123')
        response = self.client.post(reverse('login'), {'username': 'frank', 'password': 'nope'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alert-error')
