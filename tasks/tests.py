from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Task


class TaskViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='pass12345!')
        self.other = User.objects.create_user('bob', password='pass12345!')
        self.task = Task.objects.create(user=self.user, title='Buy milk')
        self.client.login(username='alice', password='pass12345!')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('task_list'))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_list_shows_only_own_tasks(self):
        Task.objects.create(user=self.other, title='Bob secret')
        response = self.client.get(reverse('task_list'))
        self.assertContains(response, 'Buy milk')
        self.assertNotContains(response, 'Bob secret')

    def test_cannot_open_someone_elses_task(self):
        bob_task = Task.objects.create(user=self.other, title='Bob secret')
        for name in ('task_detail', 'task_update', 'task_delete'):
            response = self.client.get(reverse(name, args=[bob_task.pk]))
            self.assertEqual(response.status_code, 404, name)

    def test_create_assigns_current_user(self):
        response = self.client.post(reverse('task_create'), {'title': 'New one', 'priority': 'high'})
        self.assertRedirects(response, reverse('task_list'))
        task = Task.objects.get(title='New one')
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.priority, 'high')

    def test_update(self):
        response = self.client.post(
            reverse('task_update', args=[self.task.pk]),
            {'title': 'Buy oat milk', 'priority': 'low'},
        )
        self.assertRedirects(response, reverse('task_detail', args=[self.task.pk]))
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Buy oat milk')

    def test_delete(self):
        response = self.client.post(reverse('task_delete', args=[self.task.pk]))
        self.assertRedirects(response, reverse('task_list'))
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_toggle(self):
        self.client.post(reverse('task_toggle', args=[self.task.pk]))
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)

    def test_toggle_rejects_get(self):
        response = self.client.get(reverse('task_toggle', args=[self.task.pk]))
        self.assertEqual(response.status_code, 405)

    def test_toggle_ignores_external_next(self):
        response = self.client.post(
            reverse('task_toggle', args=[self.task.pk]),
            {'next': 'https://evil.example.com/'},
        )
        self.assertRedirects(response, reverse('task_list'))

    def test_filter_and_search(self):
        Task.objects.create(user=self.user, title='Read book', completed=True)
        response = self.client.get(reverse('task_list'), {'status': 'completed'})
        self.assertContains(response, 'Read book')
        self.assertNotContains(response, 'Buy milk')

        response = self.client.get(reverse('task_list'), {'q': 'milk'})
        self.assertContains(response, 'Buy milk')
        self.assertNotContains(response, 'Read book')

    def test_is_overdue(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        self.task.due_date = yesterday
        self.assertTrue(self.task.is_overdue)
        self.task.completed = True
        self.assertFalse(self.task.is_overdue)
