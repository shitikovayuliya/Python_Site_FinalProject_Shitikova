from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from ..models import Listing, Category


# ───────────────────────────────────────────
# 2. Тесты создания объявлений
# ───────────────────────────────────────────
class CreateAdTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='TestPass123!'
        )
        self.category = Category.objects.create(name='Платья')

    def test_create_ad_requires_login(self):
        """Страница создания объявления недоступна без входа"""
        response = self.client.get(reverse('core:create_ad'))
        self.assertEqual(response.status_code, 302)  # редирект на login

    def test_logged_user_can_open_create_page(self):
        """Авторизованный пользователь видит форму"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('core:create_ad'))
        self.assertEqual(response.status_code, 200)

    def test_logged_user_can_create_ad(self):
        """Авторизованный пользователь может создать объявление"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.post(reverse('core:create_ad'), {
            'title': 'Свадебное платье',
            'description': 'Красивое белое платье, размер 44',
            'price_per_day': '1500.00',
            'location': 'Иркутск',
            'category': self.category.id,
        })
        self.assertEqual(response.status_code, 302)  # редирект на submitted
        self.assertTrue(Listing.objects.filter(title='Свадебное платье').exists())

    def test_new_ad_is_not_approved(self):
        """Новое объявление ждёт модерации (is_approved=False)"""
        self.client.login(username='testuser', password='TestPass123!')
        self.client.post(reverse('core:create_ad'), {
            'title': 'Тестовое объявление',
            'description': 'Описание',
            'price_per_day': '500.00',
            'location': 'Иркутск',
            'category': self.category.id,

        })
        ad = Listing.objects.get(title='Тестовое объявление')
        self.assertFalse(ad.is_approved)


# ───────────────────────────────────────────
# 5. Тесты базовых страниц
# ───────────────────────────────────────────
class PageAccessTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        """Главная страница доступна"""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        """Страница 'О проекте' доступна"""
        response = self.client.get(reverse('core:about'))
        self.assertEqual(response.status_code, 200)

    def test_contact_page(self):
        """Страница 'Контакты' доступна"""
        response = self.client.get(reverse('core:contact'))
        self.assertEqual(response.status_code, 200)