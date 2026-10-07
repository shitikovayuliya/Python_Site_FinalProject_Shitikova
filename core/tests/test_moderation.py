from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from ..models import Listing, Category


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
        self.ad1.category = self.category
        self.ad1.save()

        self.ad2 = Listing.objects.create(
            owner=self.regular_user,
            title='Вечернее платье',
            description='Размер 42',
            price_per_day='1000.00',
            location='Ангарск',
            is_approved=False,
        )
        self.ad2.category = self.category
        self.ad2.save()

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

        # Отправляем данные ровно так, как их ждёт view: ad_id и action
        response = self.client.post(reverse('core:approve_ad'), {
            'ad_id': str(self.ad1.id),
            'action': 'approve'
        })

        self.assertEqual(response.status_code, 302)  # редирект после действия

        self.ad1.refresh_from_db()  # обновляем объект из базы
        self.assertTrue(self.ad1.is_approved, "Объявление должно быть одобрено")
        self.assertTrue(self.ad1.is_active, "Объявление должно стать активным")

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
