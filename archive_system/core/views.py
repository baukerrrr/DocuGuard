from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Document, Category
from .forms import DocumentForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

# 1. ФУНКЦИЯ ВХОДА (Login)
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


# 2. ФУНКЦИЯ ВЫХОДА (Logout)
def logout_view(request):
    logout(request)
    return redirect('home')


# 3. ГЛАВНАЯ СТРАНИЦА (Список + Поиск + Категории)
@login_required
def document_list(request):
    # Получаем параметры из URL
    category_id = request.GET.get('category')
    search_query = request.GET.get('q', '')
    sort_param = request.GET.get('sort', 'date_desc')  # По умолчанию: сначала новые

    # Базовый запрос
    docs = Document.objects.all()

    # Фильтрация
    if category_id:
        docs = docs.filter(category_id=category_id)

    if search_query:
        docs = docs.filter(title__icontains=search_query)

    # СОРТИРОВКА (Логика)
    if sort_param == 'name_asc':
        docs = docs.order_by('title')  # А -> Я
    elif sort_param == 'name_desc':
        docs = docs.order_by('-title')  # Я -> А
    elif sort_param == 'date_asc':
        docs = docs.order_by('uploaded_at')  # Старые -> Новые
    else:
        docs = docs.order_by('-uploaded_at')  # Новые -> Старые (Default)

    categories = Category.objects.all()

    # ВАЖНО: Эта строка должна быть с отступом в 4 пробела (как переменные в начале функции)
    return render(request, 'core/document_list.html', {
        'docs': docs,
        'categories': categories,
        'current_category': int(category_id) if category_id else None,
        'search_query': search_query,
        'current_sort': sort_param
    })

# 4. ЗАГРУЗКА ДОКУМЕНТА (Upload)
@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # 🛑 СТОП! Не сохраняем в базу сразу.
            doc = form.save(commit=False)

            # ✍️ Вписываем автора вручную (это текущий пользователь)
            doc.uploaded_by = request.user

            # ✅ Теперь сохраняем окончательно
            doc.save()
            return redirect('home')
    else:
        form = DocumentForm()

    return render(request, 'core/upload_document.html', {'form': form})


# 5. УДАЛЕНИЕ ДОКУМЕНТА
@login_required
def delete_document(request, doc_id):
    # Ищем документ по ID или выдаем ошибку 404
    doc = get_object_or_404(Document, pk=doc_id)

    # ПРОВЕРКА ПРАВ: Удалить может только Автор или Суперюзер
    if request.user == doc.uploaded_by or request.user.is_superuser:
        doc.delete()  # Удаляем из базы и с диска

    # Возвращаемся на главную
    return redirect('home')

# 6. ЛИЧНЫЙ КАБИНЕТ
@login_required
def profile_view(request):
    # Считаем, сколько файлов загрузил этот пользователь
    docs_count = Document.objects.filter(uploaded_by=request.user).count()

    # Логика смены пароля
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Важно! Обновляем сессию, иначе пользователя выкинет после смены пароля
            update_session_auth_hash(request, user)
            messages.success(request, 'Ваш пароль был успешно изменен!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'core/profile.html', {
        'form': form,
        'docs_count': docs_count
    })