from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Document, Category
from .forms import DocumentForm


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
def document_list(request):
    # А. БЕЗОПАСНОСТЬ: Определяем базовый список доступных документов
    if request.user.is_superuser:
        docs = Document.objects.all()
    elif request.user.is_authenticated:
        docs = Document.objects.filter(security_level__in=['public', 'internal'])
    else:
        docs = Document.objects.filter(security_level='public')

    # Б. ФИЛЬТР ПО КАТЕГОРИЯМ
    categories = Category.objects.all()
    category_id = request.GET.get('category')

    if category_id:
        docs = docs.filter(category_id=category_id)

    # В. ПОИСК (Строгий, через Python)
    search_query = request.GET.get('q', '')
    if search_query:
        query_lower = search_query.lower()
        # Ищем только те, что начинаются с запроса
        docs = [doc for doc in docs if doc.title.lower().startswith(query_lower)]

    # Г. ОТПРАВКА ДАННЫХ
    context = {
        'docs': docs,
        'categories': categories,
        'current_category': int(category_id) if category_id else None,
        'search_query': search_query
    }
    return render(request, 'core/document_list.html', context)


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