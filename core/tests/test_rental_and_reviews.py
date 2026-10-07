from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import Listing, Category, RentalRequest, Review


class RentalAndReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Пользователи
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.renter = User.objects.create_user(username='renter', password='pass')
        self.moderator = User.objects.create_user(username='mod', password='pass')
        self.moderator.is_staff = True
        self.moderator.save()

        # Категория
        self.category = Category.objects.create(name='Одежда')

        # Объявление (одобренное)
        self.listing = Listing.objects.create(
            owner=self.owner,
            title='Куртка зимняя',
            description='Тёплая куртка',
            price_per_day=1500,
            location='Иркутск',
            is_approved=True,
            is_active=True,
        )
        self.listing.category = self.category
        self.listing.save()

        self.today = timezone.now().date()

    def test_create_rental_request_pending_by_default(self):
        """При создании заявки статус должен быть pending."""
        req = RentalRequest.objects.create(
            listing=self.listing,
            renter=self.renter,
            start_date=self.today,
            end_date=self.today + timedelta(days=3),
        )
        self.assertEqual(req.status, 'pending')
        self.assertEqual(req.renter, self.renter)

    def test_prevent_double_booking_on_same_dates(self):
        """Нельзя создать вторую заявку на пересекающиеся даты для той же вещи."""
        # Первая заявка (одобрена)
        RentalRequest.objects.create(
            listing=self.listing,
            renter=self.renter,
            start_date=self.today,
            end_date=self.today + timedelta(days=5),
            status='approved',
        )

        # Вторая заявка на те же даты — должна не сохраниться или вызвать ошибку
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            req2 = RentalRequest(
                listing=self.listing,
                renter=User.objects.create_user(username='renter2', password='pass'),
                start_date=self.today + timedelta(days=2),  # пересечение
                end_date=self.today + timedelta(days=4),
            )
            req2.full_clean()  # проверка валидации
            req2.save()        # если full_clean не выбросил ошибку, save тоже не должен пройти

    def test_review_only_for_approved_rental(self):
        """Отзыв можно оставить только для заявки со статусом approved."""
        from django.core.exceptions import ValidationError

        rental = RentalRequest.objects.create(
            listing=self.listing,
            renter=self.renter,
            start_date=self.today + timedelta(days=10),
            end_date=self.today + timedelta(days=12),
            status='approved',
        )

        review = Review.objects.create(
            listing=self.listing,  # <-- не rental, а listing
            author=self.renter,  # <-- автор отзыва
            rating=5,
            comment='Всё отлично!',
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.author, self.renter)

    def test_no_review_for_pending_or_rejected(self):
        """Нельзя оставить отзыв, если аренда не завершена (статус не approved)."""
        from django.core.exceptions import ValidationError

        rental_pending = RentalRequest.objects.create(
            listing=self.listing,
            renter=self.renter,
            start_date=self.today,
            end_date=self.today + timedelta(days=2),
            status='pending',
        )


        with self.assertRaises(ValidationError):
            Review.objects.create(
                listing=self.listing,  # <-- вместо rental=...
                author=self.renter,  # <-- автор отзыва
                rating=5,
                comment='Не должно пройти',
            )

        rental_rejected = RentalRequest.objects.create(
            listing=self.listing,
            renter=self.renter,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=7),
            status='rejected',
        )

        with self.assertRaises(ValidationError):
            Review.objects.create(
                listing=self.listing,
                author=self.renter,
                rating=5,
                comment='Тоже не должно пройти',
            )

        rental_approved = RentalRequest.objects.create(
            listing=self.listing,
            renter=self.renter,
            start_date=self.today + timedelta(days=10),
            end_date=self.today + timedelta(days=12),
            status='approved',
        )

        review = Review.objects.create(
            listing=self.listing,
            author=self.renter,
            rating=5,
            comment='Всё ок, аренда одобрена',
        )
        self.assertIsNotNone(review.id)

