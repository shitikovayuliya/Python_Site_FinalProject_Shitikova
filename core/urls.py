from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ============================================================
    # Главная и информационные страницы
    # ============================================================
    path('', views.home, name='home'),                        # Главная страница — список объявлений
    path('about/', views.about, name='about'),                 # Страница «О сервисе»
    path('contact/', views.contact, name='contact'),          # Страница «Контакты»

    # ============================================================
    # Управление объявлениями (для владельцев)
    # ============================================================
    path('create/', views.create_ad, name='create_ad'),        # Создание нового объявления
    path('submitted/', views.ad_submitted, name='ad_submitted'),  # Страница «Заявка отправлена» после создания
    path('approve/', views.approve_ad, name='approve_ad'),     # Одобрение объявления (модерация)
    path('my-ads/', views.my_ads, name='my_ads'),              # Список своих объявлений
    path('my-ads/edit/<int:ad_id>/', views.edit_ad, name='edit_ad'),  # Редактирование объявления
    path('ad/<int:ad_id>/delete/', views.delete_ad, name='delete_ad'),  # Удаление объявления
    path('my-ads/toggle/<int:ad_id>/', views.toggle_active, name='toggle_active'), # Активация объявления


    # ============================================================
    # Бронирования и запросы на аренду
    # ============================================================
    path('my-bookings/', views.my_bookings, name='my_bookings'),  # Мои бронирования (как арендатор)
    path('bookings/approve/<int:booking_id>/', views.approve_booking, name='approve_booking'),  # Одобрить бронь (как владелец)
    path('bookings/reject/<int:booking_id>/', views.reject_booking, name='reject_booking'),  # Отклонить бронь (как владелец)

    path('my-requests/', views.my_requests, name='my_requests'),          # Мои запросы на аренду
    path('owner-requests/', views.owner_requests, name='owner_requests'),  # Запросы к моим объявлениям (как владелец)

    # ============================================================
    # Отзывы
    # ============================================================
    path('listing/<int:pk>/review/', views.create_review, name='create_review'),  # Оставить отзыв на объявление

    # ============================================================
    # Карточка объявления и аренда
    # ============================================================
    path('listing/<int:pk>/', views.listing_detail, name='listing_detail'),  # Детальная страница объявления
    path('listing/<int:pk>/rent/', views.rental_request, name='rental_request'),  # Форма запроса аренды

    # ============================================================
    # Аутентификация и регистрация
    # ============================================================
    path('login/', views.user_login, name='user_login'),    # Вход в аккаунт
    path('register/', views.register, name='register'),    # Регистрация
    path('logout/', views.logout_view, name='logout'),      # Выход из аккаунта
]
