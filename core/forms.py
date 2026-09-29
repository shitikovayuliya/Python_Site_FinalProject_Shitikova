from django import forms
from .models import Listing, Review, RentalRequest


# ============================================================
# CreateAdForm — Форма создания и редактирования объявления
# Используется в views create_ad и edit_ad.
# Содержит основные поля модели Listing + русские подписи (labels).
# ============================================================
class CreateAdForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'title',
            'description',
            'is_active',
            'price_per_day',
            'location',
            'category',
            'image',
            'contact_info',
        ]
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'price_per_day': 'Цена за день (₽)',
            'location': 'Локация',
            'category': 'Категория',
            'image': 'Фото',
            'contact_info': 'Контактная информация',
            'is_active': 'Объявление активно',
        }
        widgets = {
            'categories': forms.Select(),
        }


# ============================================================
# RegistrationForm — Форма регистрации нового пользователя
# Обычная Form (не ModelForm), т.к. User создаётся вручную в view.
# Проверяет совпадение паролей в методе clean().
# ============================================================
class RegistrationForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=150)
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned


# ============================================================
# RentalRequestForm — Форма запроса на аренду
# Пользователь выбирает даты начала и окончания аренды.
# Поля с type="date" для удобного календарика в браузере.
# Проверяет, что дата окончания не раньше даты начала.
# ============================================================
class RentalRequestForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Дата начала аренды',
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Дата окончания аренды',
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError('Дата окончания не может быть раньше даты начала.')
        return cleaned


# ============================================================
# ReviewForm — Форма отзыва на объявление
# ModelForm на основе модели Review: рейтинг (1–5) и комментарий.
# Текстовое поле компактное (3 строки) с плейсхолдером-подсказкой.
# ============================================================
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Напишите, что понравилось или что можно улучшить…',
                'style': 'width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 6px;'
            }),
        }
