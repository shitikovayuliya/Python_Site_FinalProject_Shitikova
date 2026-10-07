from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# ============================================================
# Category — Категория объявлений (например: «Одежда», «Инструменты»)
# Справочник, на который ссылается каждое объявление.
# ============================================================
class Category(models.Model):
    name = models.CharField('Название категории', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


# ============================================================
# Listing — Объявление об аренде вещи
# Главная модель: название, описание, цена, фото, владелец,
# флаги одобрения модератором и активности.
# Статус («Доступно / Забронировано / Недоступно») вычисляется
# в view на основе is_active и активных заявок RentalRequest.
# ============================================================
class Listing(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Категория'
    )
    is_approved = models.BooleanField(default=False)   # одобрено модератором
    is_active = models.BooleanField(default=True)       # владелец может приостановить
    image = models.ImageField(upload_to='ads_images/', blank=True, null=True)
    contact_info = models.TextField(
        blank=True,
        null=True,
        verbose_name="Контактная информация для арендаторов"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.owner.username})"


# ============================================================
# RentalRequest — Запрос на аренду от пользователя к владельцу
# Пользователь выбирает даты и отправляет заявку; владелец
# одобряет (status='approved') или отклоняет её.
# Именно по одобренным заявкам с пересекающимися датами
# определяется статус «Забронировано» в карточке объявления.
# ============================================================
class RentalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    renter = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def clean(self):
        # Проверка на пересечение с другими активными заявками
        overlapping = RentalRequest.objects.filter(
            listing=self.listing,
            status__in=['pending', 'approved'],
        ).exclude(pk=self.pk).filter(
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
        )
        if overlapping.exists():
            raise ValidationError("Эта вещь уже забронирована на выбранные даты.")

    def save(self, *args, **kwargs):
        self.full_clean()  # вызовет clean()
        super().save(*args, **kwargs)

# ============================================================
# ListingImage — Дополнительные фото для объявления
# К одному объявлению можно привязать несколько изображений
# (главное фото хранится в поле image модели Listing,
# а дополнительные — здесь, с сортировкой по полю order).
# ============================================================
class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Объявление',
    )
    image = models.ImageField('Фото', upload_to='listings/')
    alt_text = models.CharField('Альтернативный текст', max_length=255, blank=True)
    order = models.PositiveIntegerField('Порядок отображения', default=0)

    class Meta:
        verbose_name = 'Фото объявления'
        verbose_name_plural = 'Фото объявлений'
        ordering = ['order']

    def __str__(self):
        return f"Фото для {self.listing.title}"


# ============================================================
# Review — Отзыв на объявление и его владельца
# Оставлять может любой авторизованный пользователь;
# рейтинг — от 1 до 5 звёзд, комментарий необязателен.
# Отзывы выводятся в карточке объявления.
# ============================================================
class Review(models.Model):
    listing = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[
        (1, '1 ⭐'),
        (2, '2 ⭐'),
        (3, '3 ⭐'),
        (4, '4 ⭐'),
        (5, '5 ⭐'),
    ])
    comment = models.TextField(blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Проверяем, что у автора есть хотя бы одна завершённая аренда этого объявления
        from core.models import RentalRequest
        has_completed_rental = RentalRequest.objects.filter(
            listing=self.listing,
            renter=self.author,
            status='approved',

        ).exists()

        if not has_completed_rental:
            raise ValidationError(
                "Отзыв можно оставить только после завершённой аренды этой вещи."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Отзыв {self.rating}⭐ на {self.listing.title}"
