from django.shortcuts import render
from .models import Document, Category  # <-- Не забудь добавить Category сюда!


def document_list(request):
    # 1. БЕЗОПАСНОСТЬ: Определяем базовый список доступных документов
    if request.user.is_superuser:
        docs = Document.objects.all()
    elif request.user.is_authenticated:
        docs = Document.objects.filter(security_level__in=['public', 'internal'])
    else:
        docs = Document.objects.filter(security_level='public')

    # 2. ФИЛЬТР ПО КАТЕГОРИЯМ (Работает с базой данных)
    # Получаем все категории для меню
    categories = Category.objects.all()
    # Смотрим, выбрал ли пользователь категорию (пришел ли id в ссылке)
    category_id = request.GET.get('category')

    if category_id:
        # Оставляем только документы этой категории
        docs = docs.filter(category_id=category_id)

    # 3. ПОИСК (Работает через Python для строгого соответствия)
    search_query = request.GET.get('q', '')
    if search_query:
        query_lower = search_query.lower()
        docs = [doc for doc in docs if doc.title.lower().startswith(query_lower)]

    # 4. ОТПРАВКА ДАННЫХ
    context = {
        'docs': docs,
        'categories': categories,  # Список кнопок для меню
        'current_category': int(category_id) if category_id else None,  # Чтобы подсветить активную кнопку
        'search_query': search_query
    }
    return render(request, 'core/document_list.html', context)