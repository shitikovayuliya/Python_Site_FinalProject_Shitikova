from django.contrib import admin
from .models import Category, Listing, RentalRequest, ListingImage, Review

# Регистрация моделей в админ-панели Django
# Позволяет модераторам и администраторам управлять контентом сайта

admin.site.register(Category)       # Категории объявлений
admin.site.register(Listing)        # Объявления об аренде
admin.site.register(RentalRequest)  # Заявки на аренду
admin.site.register(ListingImage)   # Дополнительные фото объявлений
admin.site.register(Review)         # Отзывы пользователей
