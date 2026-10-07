from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
    ]

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='rental_requests',
        verbose_name='Объявление'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rental_requests',
        verbose_name='Пользователь'
    )
    start_date = models.DateField('Дата начала аренды')
    end_date = models.DateField('Дата окончания аренды')
    quantity = models.PositiveIntegerField('Количество предметов', default=1)
    comments = models.TextField('Комментарии', blank=True)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    requested_at = models.DateTimeField('Дата запроса', auto_now_add=True)

    class Meta:
        verbose_name = 'Запрос на аренду'
        verbose_name_plural = 'Запросы на аренду'
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.listing.title}: {self.user.username} ({self.start_date}–{self.end_date})"


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
# Booking — Бронирование (альтернативная модель заявок)
# Дублирует логику RentalRequest, но с дополнительным
# статусом 'completed'.
# ============================================================
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
        ('completed', 'Завершено'),
    ]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заявка {self.id} на {self.listing.title}"


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

    def __str__(self):
        return f"Отзыв {self.rating}⭐ на {self.listing.title}"
