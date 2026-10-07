import uuid
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


# ───────────────────────────────────────────
# 1. Тесты аутентификации
# ───────────────────────────────────────────
class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='TestPass123!'
        )

    def test_register_page_loads(self):
        """Страница регистрации доступна и возвращает 200"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_register(self):
        unique_username = f'newuser_{uuid.uuid4().hex[:8]}'
        unique_email = f'{unique_username}@test.com'
        pwd = 'StrongPass123!'

        response = self.client.post(reverse('register'), {
            'username': unique_username,
            'email': unique_email,
            'password1': pwd,
            'password2': pwd,
            'password': pwd
        })

        if response.status_code != 302:
            print("Ошибки формы:", response.context['form'].errors)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/')
        self.assertTrue(User.objects.filter(username=unique_username).exists())

    def test_login_page_loads(self):
        """Страница входа доступна"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_login(self):
        """Пользователь может войти с правильными данными"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)  # редирект на главную

    def test_user_cannot_login_wrong_password(self):
        """Вход с неверным паролем не проходит"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)  # остаётся на странице входа
