from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Listing, RentalRequest
from .forms import CreateAdForm, RegistrationForm, RentalRequestForm, ReviewForm
from django.utils import timezone



# ── Главная ──────────────────────────────────
def home(request):
    listings = Listing.objects.filter(is_approved=True, is_active=True)

    # Поиск по ключевым словам (в заголовке и описании)
    query = request.GET.get('q')
    if query and query.strip():
        listings = listings.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Фильтр по местоположению
    location = request.GET.get('location')
    if location and location.strip():
        listings = listings.filter(location__icontains=location)

    # Фильтр по стоимости аренды
    max_price = request.GET.get('max_price')
    if max_price and max_price.strip():
        try:
            price = float(max_price)
            listings = listings.filter(price_per_day__lte=price)
        except ValueError:
            pass

    paginator = Paginator(listings, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'location': location,
        'max_price': max_price,
    }
    return render(request, 'core/home.html', context)



# ── О проекте / Контакты ──────────────────────
def about(request):
    return render(request, 'core/about.html')


def contact(request):
    return render(request, 'core/contact.html')


# ── Детальная карточка объявления ────────────
def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    # 1. Сначала проверяем «Приостановлено владельцем»
    if not listing.is_active:
        display_status = 'Недоступно'
        status_class = 'unavailable'
    else:
        # 2. Проверяем активные брони (пересечение с сегодня)
        now = timezone.now().date()
        active_booking = RentalRequest.objects.filter(
            listing=listing,
            status='approved',          # <-- замени на своё значение, если у тебя другое
            start_date__lte=now,
            end_date__gte=now,
        ).exists()

        if active_booking:
            display_status = 'Забронировано'
            status_class = 'booked'
        else:
            display_status = 'Доступно'
            status_class = 'available'

    reviews = listing.reviews.all() if hasattr(listing, 'reviews') else []

    # Передаём форму только если пользователь авторизован (так как в шаблоне она показывается только для них)
    form = ReviewForm() if request.user.is_authenticated else None

    return render(request, 'core/listing_detail.html', {
        'listing': listing,
        'display_status': display_status,
        'status_class': status_class,
        'reviews': reviews,
        'form': form,
    })
# ── Подать заявку на аренду ──────────────────

@login_required
def rental_request(request, pk):
    listing = get_object_or_404(Listing, pk=pk, is_approved=True, is_active=True)

    if request.method == 'POST':
        form = RentalRequestForm(request.POST)
        if form.is_valid():
            rental = form.save(commit=False)      # создаём объект без сохранения
            rental.user = request.user           # привязываем пользователя
            rental.listing = listing             # привязываем объявление
            rental.status = 'pending'            # статус ставим на сервере
            rental.save()                        # сохраняем в БД (в RentalRequest!)

            messages.success(request, 'Заявка отправлена владельцу!')
            return redirect('core:listing_detail', pk=listing.pk)
    else:
        form = RentalRequestForm()

    return render(request, 'core/rental_request.html', {
        'form': form,
        'listing': listing,
    })

# ── Мои заявки (для обычного пользователя) ───
@login_required
def my_requests(request):
    requests = RentalRequest.objects.filter(user=request.user).select_related('listing')
    return render(request, 'core/my_requests.html', {'requests': requests})


# ── Создание объявления ──────────────────────
@login_required
def create_ad(request):
    if request.method == 'POST':
        form = CreateAdForm(request.POST, request.FILES)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.owner = request.user
            ad.save()              # сначала сохраняем сам объект
            form.save_m2m()        # потом сохраняем связи (категории, картинки и т.п.)
            return redirect('core:ad_submitted')
    else:
        form = CreateAdForm()
    return render(request, 'core/create_ad.html', {'form': form})


# ── Страница «Отправлено» ────────────────────
def ad_submitted(request):
    return render(request, 'core/ad_submitted.html')


# ── Модерация (для staff) ────────────────────
@login_required
def approve_ad(request):
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав на модерацию объявлений.')
        return redirect('core:home')

    if request.method == 'POST':
        ad_id = request.POST.get('ad_id')
        action = request.POST.get('action')

        if not ad_id or action not in ['approve', 'reject']:
            messages.error(request, 'Некорректные данные формы.')
            return redirect('core:approve_ad')

        try:
            ad = Listing.objects.get(id=ad_id)
        except Listing.DoesNotExist:
            messages.error(request, 'Объявление не найдено.')
            return redirect('core:approve_ad')

        if action == 'approve':
            ad.is_approved = True
            ad.is_active = True
            ad.save()
            messages.success(request, f'Объявление «{ad.title}» одобрено.')
        elif action == 'reject':
            ad.is_approved = False
            ad.is_active = False  # <-- вот ключ: объявление уходит из очереди
            ad.save()
            messages.warning(request, f'Объявление «{ad.title}» отклонено.')

        return redirect('core:approve_ad')

    # Показываем только ожидающие: не одобрены И ещё активны
    ads = Listing.objects.filter(is_approved=False, is_active=True)
    return render(request, 'core/approve_ad.html', {'ads': ads})

# ── Регистрация ──────────────────────────────
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            User.objects.create_user(username=username, email=email, password=password)
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'core/register.html', {'form': form})


# ── Вход ─────────────────────────────────────
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('core:home')
        else:
            return render(request, 'core/login.html', {'error': 'Неверный логин или пароль'})
    return render(request, 'core/login.html')

from django.contrib.auth import logout

@login_required
def logout_view(request):
    logout(request)
    return redirect('core:home')

# ── Мои объявления ─────────────────────────────────────
@login_required
def my_ads(request):
    # Все объявления владельца
    ads = Listing.objects.filter(owner=request.user).order_by('-created_at')

    # Формируем понятный статус для шаблона
    for ad in ads:
        if not ad.is_approved and ad.is_active:
            ad.status_text = 'На модерации'
            ad.status_class = 'text-warning'
        elif ad.is_approved and ad.is_active:
            ad.status_text = 'Опубликовано'
            ad.status_class = 'text-success'
        else:
            # Сюда попадают отклонённые (is_approved=False, is_active=False)
            ad.status_text = 'Отклонено'
            ad.status_class = 'text-danger'

    context = {
        'ads': ads,
    }
    return render(request, 'core/my_ads.html', context)
# ── Редактирование объявления ─────────────────────────────────────
@login_required
def edit_ad(request, ad_id):
    try:
        ad = Listing.objects.get(id=ad_id)
    except Listing.DoesNotExist:
        messages.error(request, 'Объявление не найдено.')
        return redirect('core:my_ads')

    if ad.owner != request.user:
        messages.error(request, 'Вы не можете редактировать чужое объявление.')
        return redirect('core:my_ads')

    if request.method == 'POST':
        form = CreateAdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, f'Объявление «{ad.title}» успешно обновлено.')
            return redirect('core:my_ads')
        else:
            # Отладка: выводим ошибки в консоль серверЫа
            print("=== ОШИБКИ ФОРМЫ ПРИ РЕДАКТИРОВАНИИ ===")
            print(form.errors)
            print("=======================================")
    else:
        form = CreateAdForm(instance=ad)

    return render(request, 'core/edit_ad.html', {
        'form': form,
        'ad': ad,
    })


# ── Мои заявки ─────────────────────────────────────
@login_required
def my_bookings(request):
    requests = RentalRequest.objects.filter(user=request.user) \
        .exclude(listing__owner=request.user) \
        .select_related('listing') \
        .order_by('-requested_at')

    for r in requests:
        if r.status == 'pending':
            r.status_text = 'На рассмотрении'
            r.status_class = 'text-warning'
        elif r.status == 'approved':
            r.status_text = 'Одобрено'
            r.status_class = 'text-success'
        elif r.status == 'rejected':
            r.status_text = 'Отклонено'
            r.status_class = 'text-danger'
        else:
            r.status_text = 'Отменено'
            r.status_class = 'text-muted'

    context = {'requests': requests}
    return render(request, 'core/my_bookings.html', context)


# ── Одобрение заявки ─────────────────────────────────────
@login_required
def approve_booking(request, booking_id):
    rental = get_object_or_404(RentalRequest, id=booking_id)

    if rental.listing.owner != request.user:
        messages.error(request, 'Вы не можете модерировать чужие заявки.')
        return redirect('core:owner_requests')

    rental.status = 'approved'
    rental.save()
    messages.success(request, f'Заявка №{rental.id} на "{rental.listing.title}" одобрена.')
    return redirect('core:owner_requests')


# ── Отклонение заявки ─────────────────────────────────────
@login_required
def reject_booking(request, booking_id):
    rental = get_object_or_404(RentalRequest, id=booking_id)

    if rental.listing.owner != request.user:
        messages.error(request, 'Вы не можете модерировать чужие заявки.')
        return redirect('core:owner_requests')

    rental.status = 'rejected'
    rental.save()
    messages.warning(request, f'Заявка №{rental.id} на "{rental.listing.title}" отклонена.')
    return redirect('core:owner_requests')


# ── Заявки на объявления владельца ───────────────────────
@login_required
def owner_requests(request):
    requests = RentalRequest.objects.filter(listing__owner=request.user) \
        .select_related('listing', 'user') \
        .order_by('-requested_at')

    for r in requests:
        if r.status == 'pending':
            r.status_text = 'На рассмотрении'
            r.status_class = 'text-warning'
        elif r.status == 'approved':
            r.status_text = 'Одобрено'
            r.status_class = 'text-success'
        elif r.status == 'rejected':
            r.status_text = 'Отклонено'
            r.status_class = 'text-danger'
        else:
            r.status_text = 'Отменено'
            r.status_class = 'text-muted'

    context = {'requests': requests}
    return render(request, 'core/owner_requests.html', context)


# ── Создание отзыва  ─────────────────────────────────────
@login_required
def create_review(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.listing = listing
            review.author = request.user
            review.save()
            messages.success(request, 'Спасибо за отзыв!')
            return redirect('core:listing_detail', pk=listing.pk)
    else:
        form = ReviewForm()

    reviews = listing.reviews.all()

    return render(request, 'core/listing_detail.html', {
        'listing': listing,
        'form': form,
        'reviews': reviews,
    })

# ── Удаление объявления  ─────────────────────────────────────
@login_required
def delete_ad(request, ad_id):
    ad = get_object_or_404(Listing, id=ad_id)

    # Проверка: удалять может только владелец
    if ad.owner != request.user:
        messages.error(request, 'Вы не можете удалять чужие объявления.')
        return redirect('core:my_ads')

    if request.method == 'POST':
        ad.delete()
        messages.success(request, 'Объявление успешно удалено.')
        return redirect('core:my_ads')

    # Если GET — показываем страницу подтверждения (или можно сделать через JS-подтверждение)
    return render(request, 'core/delete_ad_confirm.html', {'ad': ad})

# ── Активация объявления  ─────────────────────────────────────
@login_required
def toggle_active(request, ad_id):
    ad = get_object_or_404(Listing, id=ad_id, owner=request.user)
    ad.is_active = not ad.is_active
    ad.save()
    return redirect('core:my_ads')
