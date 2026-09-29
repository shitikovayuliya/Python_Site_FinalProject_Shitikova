from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Listing, Category


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
        """Новый пользователь успешно регистрируется"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)  # редирект после регистрации
        self.assertTrue(User.objects.filter(username='newuser').exists())

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
            'categories': [self.category.id],
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
            'categories': [self.category.id],
        })
        ad = Listing.objects.get(title='Тестовое объявление')
        self.assertFalse(ad.is_approved)


# ───────────────────────────────────────────
# 3. Тесты модерации
# ───────────────────────────────────────────
class ModerationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.moderator = User.objects.create_user(
            username='moderator',
            email='mod@test.com',
            password='ModPass123!'
        )
        self.moderator.is_staff = True
        self.moderator.save()

        self.regular_user = User.objects.create_user(
            username='regular',
            email='reg@test.com',
            password='RegPass123!'
        )

        self.category = Category.objects.create(name='Костюмы')

        # Создаём два неободренных объявления
        self.ad1 = Listing.objects.create(
            owner=self.regular_user,
            title='Костюм на свадьбу',
            description='Размер 48',
            price_per_day='2000.00',
            location='Иркутск',
            is_approved=False,
        )
        self.ad1.categories.add(self.category)

        self.ad2 = Listing.objects.create(
            owner=self.regular_user,
            title='Вечернее платье',
            description='Размер 42',
            price_per_day='1000.00',
            location='Ангарск',
            is_approved=False,
        )
        self.ad2.categories.add(self.category)

    def test_approve_page_requires_staff(self):
        """Обычный пользователь не может открыть страницу модерации"""
        self.client.login(username='regular', password='RegPass123!')
        response = self.client.get(reverse('core:approve_ad'))
        self.assertEqual(response.status_code, 302)  # редирект на login

    def test_moderator_can_open_approve_page(self):
        """Модератор видит страницу модерации"""
        self.client.login(username='moderator', password='ModPass123!')
        response = self.client.get(reverse('core:approve_ad'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Костюм на свадьбу')
        self.assertContains(response, 'Вечернее платье')

    def test_moderator_can_approve_ad(self):
        """Модератор может одобрить объявление"""
        self.client.login(username='moderator', password='ModPass123!')
        response = self.client.post(reverse('core:approve_ad'), {
            str(self.ad1.id): 'approve',
        })
        self.assertEqual(response.status_code, 302)  # редирект на главную
        self.ad1.refresh_from_db()
        self.assertTrue(self.ad1.is_approved)

    def test_unapproved_ads_not_on_home(self):
        """Неодобренные объявления не видны на главной"""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Костюм на свадьбу')
        self.assertNotContains(response, 'Вечернее платье')

    def test_approved_ad_appears_on_home(self):
        """Одобренное объявление появляется на главной"""
        self.ad1.is_approved = True
        self.ad1.save()
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Костюм на свадьбу')


# ───────────────────────────────────────────
# 4. Тесты моделей
# ───────────────────────────────────────────
class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        self.category = Category.objects.create(name='Пальто')

    def test_category_str(self):
        """Метод __str__ у Category возвращает название"""
        self.assertEqual(str(self.category), 'Пальто')

    def test_listing_str(self):
        """Метод __str__ у Listing возвращает заголовок и username"""
        listing = Listing.objects.create(
            owner=self.user,
            title='Зимнее пальто',
            description='Тёплое, размер 46',
            price_per_day='800.00',
            location='Иркутск',
        )
        self.assertEqual(str(listing), 'Зимнее пальто (testuser)')

    def test_listing_default_is_approved_false(self):
        """По умолчанию is_approved = False"""
        listing = Listing.objects.create(
            owner=self.user,
            title='Тест',
            description='Тест',
            price_per_day='100.00',
        )
        self.assertFalse(listing.is_approved)

    def test_listing_default_is_active_true(self):
        """По умолчанию is_active = True"""
        listing = Listing.objects.create(
            owner=self.user,
            title='Тест',
            description='Тест',
            price_per_day='100.00',
        )
        self.assertTrue(listing.is_active)


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
