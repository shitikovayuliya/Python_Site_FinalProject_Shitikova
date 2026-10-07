from django.test import TestCase
from django.contrib.auth.models import User
from ..models import Listing, Category


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
