import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.http import FileResponse, Http404
from django.db.models import Q  # Для сложных фильтров (ИЛИ)
from django.utils.encoding import escape_uri_path
import os

# Импортируем все наши модели и формы
from .models import Document, Category, AuditLog, ShareLink, Profile
from .forms import DocumentForm, ProfileForm


# ==========================================
# 1. АВТОРИЗАЦИЯ
# ==========================================

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


def logout_view(request):
    logout(request)
    return redirect('home')


# ==========================================
# 2. ГЛАВНАЯ СТРАНИЦА (СПИСОК + ФИЛЬТРЫ)
# ==========================================

@login_required
def document_list(request):
    # Получаем параметры из URL
    category_id = request.GET.get('category')
    search_query = request.GET.get('q', '')
    sort_param = request.GET.get('sort', 'date_desc')
    file_type = request.GET.get('type')  # Тип файла (pdf, word, etc.)

    # Базовый запрос: берем все документы
    docs = Document.objects.all()

    # --- ФИЛЬТРАЦИЯ ---

    # 1. По Категории
    if category_id:
        docs = docs.filter(category_id=category_id)

    # 2. По Поиску (Название)
    if search_query:
        docs = docs.filter(title__icontains=search_query)

    # 3. По Типу файла (Используем Q для логики ИЛИ)
    if file_type == 'pdf':
        docs = docs.filter(file__iendswith='.pdf')
    elif file_type == 'word':
        docs = docs.filter(Q(file__iendswith='.doc') | Q(file__iendswith='.docx'))
    elif file_type == 'excel':
        docs = docs.filter(Q(file__iendswith='.xls') | Q(file__iendswith='.xlsx') | Q(file__iendswith='.csv'))
    elif file_type == 'image':
        docs = docs.filter(Q(file__iendswith='.jpg') | Q(file__iendswith='.jpeg') | Q(file__iendswith='.png'))
    elif file_type == 'archive':
        docs = docs.filter(Q(file__iendswith='.zip') | Q(file__iendswith='.rar'))

    # --- СОРТИРОВКА ---
    if sort_param == 'name_asc':
        docs = docs.order_by('title')
    elif sort_param == 'name_desc':
        docs = docs.order_by('-title')
    elif sort_param == 'date_asc':
        docs = docs.order_by('uploaded_at')
    else:
        docs = docs.order_by('-uploaded_at')  # По умолчанию новые сверху

    categories = Category.objects.all()

    # Пустая форма нужна для Модального окна загрузки на главной странице
    form = DocumentForm()

    return render(request, 'core/document_list.html', {
        'docs': docs,
        'categories': categories,
        'form': form,  # <-- Передаем форму для модалки
        'current_category': int(category_id) if category_id else None,
        'search_query': search_query,
        'current_sort': sort_param,
        'current_type': file_type
    })


# ==========================================
# 3. ДЕЙСТВИЯ С ДОКУМЕНТАМИ
# ==========================================

@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()

            # 🕵️‍♂️ Лог
            AuditLog.objects.create(
                user=request.user,
                action="Загрузка файла",
                document_title=doc.title
            )

            messages.success(request, 'Документ успешно загружен!')
            return redirect('home')

    # Если это GET запрос (отдельная страница), показываем форму
    else:
        form = DocumentForm()

    return render(request, 'core/upload_document.html', {'form': form})


@login_required
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)

    # Проверка прав
    if request.user == doc.uploaded_by or request.user.is_superuser:

        # 🕵️‍♂️ Лог (до удаления)
        AuditLog.objects.create(
            user=request.user,
            action="Удаление файла",
            document_title=doc.title
        )

        doc.delete()
        messages.success(request, 'Документ удален.')
    else:
        messages.error(request, 'У вас нет прав на удаление.')

    return redirect('home')


@login_required
def edit_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)

    if request.user != doc.uploaded_by and not request.user.is_superuser:
        messages.error(request, "Нет прав на редактирование.")
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

        # 🕵️‍♂️ Лог
        AuditLog.objects.create(
            user=request.user,
            action="Редактирование",
            document_title=doc.title
        )

        messages.success(request, 'Документ изменен!')
        return redirect('home')

    categories = Category.objects.all()
    return render(request, 'core/edit_document.html', {'doc': doc, 'categories': categories})


# ==========================================
# 4. ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# ==========================================

@login_required
def profile_view(request):
    # Гарантируем, что профиль существует
    Profile.objects.get_or_create(user=request.user)

    docs_count = Document.objects.filter(uploaded_by=request.user).count()

    if request.method == 'POST':
        # 1. Смена Аватарки
        if 'update_avatar' in request.POST:
            avatar_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
            if avatar_form.is_valid():
                avatar_form.save()
                messages.success(request, 'Аватар обновлен!')
                return redirect('profile')
            password_form = PasswordChangeForm(request.user)

        # 2. Смена Пароля
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Чтобы не выкинуло
                messages.success(request, 'Пароль изменен!')
                return redirect('profile')
            avatar_form = ProfileForm(instance=request.user.profile)

        else:
            avatar_form = ProfileForm(instance=request.user.profile)
            password_form = PasswordChangeForm(request.user)

    else:
        avatar_form = ProfileForm(instance=request.user.profile)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'core/profile.html', {
        'avatar_form': avatar_form,
        'password_form': password_form,
        'docs_count': docs_count
    })


# ==========================================
# 5. АДМИН-ПАНЕЛЬ (Категории + Логи)
# ==========================================

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


@user_passes_test(lambda u: u.is_superuser)
def audit_log_view(request):
    logs = AuditLog.objects.all()
    return render(request, 'core/audit_log.html', {'logs': logs})


# ==========================================
# 6. ПУБЛИЧНЫЕ ССЫЛКИ
# ==========================================

@login_required
def create_share_link(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)

    if request.user != doc.uploaded_by and not request.user.is_superuser:
        messages.error(request, "Нет прав делиться этим файлом.")
        return redirect('home')

    share_link, created = ShareLink.objects.get_or_create(document=doc)

    # Формируем полный URL
    full_link = request.build_absolute_uri(f"/s/{share_link.token}/")

    return render(request, 'core/share_result.html', {'full_link': full_link, 'doc': doc})


def public_download(request, token):
    # Открытый доступ без авторизации
    share_link = get_object_or_404(ShareLink, token=token)
    doc = share_link.document

    try:
        response = FileResponse(open(doc.file.path, 'rb'))
        # Принудительное скачивание
        response['Content-Disposition'] = f'attachment; filename="{doc.file.name.split("/")[-1]}"'
        return response
    except FileNotFoundError:
        raise Http404("Файл не найден на сервере")


# ==========================================
# 7. УМНОЕ ОТКРЫТИЕ ФАЙЛА
# ==========================================
import mimetypes
from django.utils.encoding import escape_uri_path

@login_required
def open_file(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)

    if not os.path.exists(doc.file.path):
        raise Http404("Файл не найден")

    # 1. Определяем: скачивать или показывать
    disposition_type = 'attachment' if request.GET.get('download') else 'inline'

    # 2. Открываем файл
    response = FileResponse(open(doc.file.path, 'rb'))

    # 3. Определяем MIME-тип (PDF, JPG и т.д.)
    content_type, _ = mimetypes.guess_type(doc.file.path)
    if not content_type:
        content_type = 'application/octet-stream'
    response['Content-Type'] = content_type

    # 4. Формируем имя файла
    # Берем расширение (например .pdf)
    ext = os.path.splitext(doc.file.name)[1]
    # Собираем новое имя: "Красивое Имя" + ".pdf"
    new_filename = f"{doc.title}{ext}"

    # 5. МАГИЯ КОДИРОВКИ (RFC 5987)
    # Это заставляет браузер понять русские буквы и пробелы
    encoded_name = escape_uri_path(new_filename)

    # Заголовок выглядит так: inline; filename*=UTF-8''%D0%9E%D1%82%D1%87%D0%B5%D1%82.pdf
    response['Content-Disposition'] = f"{disposition_type}; filename*=UTF-8''{encoded_name}"

    return response