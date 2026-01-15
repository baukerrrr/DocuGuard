from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from .models import Document, Category, AuditLog, ShareLink, Profile
from .forms import DocumentForm, ProfileForm
from django.http import FileResponse


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
    sort_param = request.GET.get('sort', 'date_desc')

    # Базовый запрос
    docs = Document.objects.all()

    # Фильтрация
    if category_id:
        docs = docs.filter(category_id=category_id)

    if search_query:
        docs = docs.filter(title__icontains=search_query)

    # СОРТИРОВКА
    if sort_param == 'name_asc':
        docs = docs.order_by('title')
    elif sort_param == 'name_desc':
        docs = docs.order_by('-title')
    elif sort_param == 'date_asc':
        docs = docs.order_by('uploaded_at')
    else:
        docs = docs.order_by('-uploaded_at')

    categories = Category.objects.all()

    return render(request, 'core/document_list.html', {
        'docs': docs,
        'categories': categories,
        'current_category': int(category_id) if category_id else None,
        'search_query': search_query,
        'current_sort': sort_param
    })


# 4. ЗАГРУЗКА ДОКУМЕНТА (с записью в журнал)
@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()

            # 🕵️‍♂️ ЗАПИСЬ В ЖУРНАЛ
            AuditLog.objects.create(
                user=request.user,
                action="Загрузка файла",
                document_title=doc.title
            )

            messages.success(request, 'Документ успешно загружен!')
            return redirect('home')
    else:
        form = DocumentForm()

    return render(request, 'core/upload_document.html', {'form': form})


# 5. УДАЛЕНИЕ ДОКУМЕНТА (с проверкой прав и журналом)
@login_required
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)

    # Проверка прав: Автор или Суперюзер
    if request.user == doc.uploaded_by or request.user.is_superuser:

        # 🕵️‍♂️ ЗАПИСЬ В ЖУРНАЛ (До удаления, чтобы сохранить название)
        AuditLog.objects.create(
            user=request.user,
            action="Удаление файла",
            document_title=doc.title
        )

        doc.delete()
        messages.success(request, 'Документ удален.')
    else:
        messages.error(request, 'У вас нет прав на удаление этого документа.')

    return redirect('home')


# 6. ЛИЧНЫЙ КАБИНЕТ (С аватаркой)
@login_required
def profile_view(request):
    docs_count = Document.objects.filter(uploaded_by=request.user).count()

    # Убеждаемся, что у пользователя есть профиль (защита от старых ошибок)
    Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Проверяем, какую кнопку нажал пользователь

        # Если нажали "Сохранить аватар" (в форме будет скрытое поле action="update_avatar")
        if 'update_avatar' in request.POST:
            avatar_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
            if avatar_form.is_valid():
                avatar_form.save()
                messages.success(request, 'Аватар обновлен!')
                return redirect('profile')
            password_form = PasswordChangeForm(request.user)  # Вторую форму оставляем пустой

        # Если нажали "Сменить пароль"
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль изменен!')
                return redirect('profile')
            avatar_form = ProfileForm(instance=request.user.profile)  # Первую форму оставляем старой

        else:
            avatar_form = ProfileForm(instance=request.user.profile)
            password_form = PasswordChangeForm(request.user)

    else:
        # GET-запрос: просто показываем формы
        avatar_form = ProfileForm(instance=request.user.profile)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'core/profile.html', {
        'avatar_form': avatar_form,
        'password_form': password_form,
        'docs_count': docs_count
    })


# 7. УПРАВЛЕНИЕ КАТЕГОРИЯМИ (Только для админа)
@user_passes_test(lambda u: u.is_superuser)
def manage_categories(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Category.objects.create(name=name)
            messages.success(request, f'Категория "{name}" создана!')
            return redirect('manage_categories')

    categories = Category.objects.all()
    return render(request, 'core/category_manager.html', {'categories': categories})


@user_passes_test(lambda u: u.is_superuser)
def delete_category(request, cat_id):
    category = get_object_or_404(Category, id=cat_id)
    category.delete()
    messages.success(request, 'Категория удалена!')
    return redirect('manage_categories')


# 8. РЕДАКТИРОВАНИЕ ДОКУМЕНТА (с журналом)
@login_required
def edit_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)

    if request.user != doc.uploaded_by and not request.user.is_superuser:
        messages.error(request, "У вас нет прав на редактирование этого документа.")
        return redirect('home')

    if request.method == 'POST':
        doc.title = request.POST.get('title')

        cat_id = request.POST.get('category')
        if cat_id:
            doc.category = Category.objects.get(id=cat_id)
        else:
            doc.category = None

        doc.security_level = request.POST.get('security_level')

        doc.save()

        # 🕵️‍♂️ ЗАПИСЬ В ЖУРНАЛ
        AuditLog.objects.create(
            user=request.user,
            action="Редактирование",
            document_title=doc.title
        )

        messages.success(request, 'Документ успешно изменен!')
        return redirect('home')

    categories = Category.objects.all()
    return render(request, 'core/edit_document.html', {
        'doc': doc,
        'categories': categories
    })


# 9. ПРОСМОТР ЖУРНАЛА (Новая функция)
@user_passes_test(lambda u: u.is_superuser)
def audit_log_view(request):
    logs = AuditLog.objects.all()
    return render(request, 'core/audit_log.html', {'logs': logs})


# 10. СОЗДАНИЕ ПУБЛИЧНОЙ ССЫЛКИ
@login_required
def create_share_link(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)

    # Проверка прав: только автор или админ могут делиться
    if request.user != doc.uploaded_by and not request.user.is_superuser:
        messages.error(request, "У вас нет прав делиться этим файлом.")
        return redirect('home')

    # Создаем или получаем уже существующую ссылку
    share_link, created = ShareLink.objects.get_or_create(document=doc)

    # Формируем полный URL (например: http://127.0.0.1:8000/s/uuid/)
    full_link = request.build_absolute_uri(f"/s/{share_link.token}/")

    return render(request, 'core/share_result.html', {'full_link': full_link, 'doc': doc})


# 11. ПУБЛИЧНОЕ СКАЧИВАНИЕ (БЕЗ @login_required !!!)
def public_download(request, token):
    # Ищем ссылку по токену
    share_link = get_object_or_404(ShareLink, token=token)
    doc = share_link.document

    # Проверяем, существует ли файл физически
    try:
        # Открываем файл как поток байтов
        response = FileResponse(open(doc.file.path, 'rb'))
        # Заставляем браузер скачивать, а не открывать
        response['Content-Disposition'] = f'attachment; filename="{doc.file.name.split("/")[-1]}"'
        return response
    except FileNotFoundError:
        raise Http404("Файл не найден на сервере")