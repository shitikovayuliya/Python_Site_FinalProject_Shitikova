from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from core.views import user_login, register

urlpatterns = [
    path('admin/', admin.site.urls),

    # Наши кастомные страницы входа/регистрации
    path('accounts/login/', user_login, name='login'),
    path('accounts/register/', register, name='register'),

    # Стандартный logout
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Приложение core
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
