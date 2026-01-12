from django.shortcuts import render
from .models import Document


def document_list(request):
    # 1. Сначала получаем список документов по правам доступа (как раньше)
    if request.user.is_superuser:
        docs = Document.objects.all()
    elif request.user.is_authenticated:
        docs = Document.objects.filter(security_level__in=['public', 'internal'])
    else:
        docs = Document.objects.filter(security_level='public')

    # 2. ПОИСК (Исправленный для русского языка)
    search_query = request.GET.get('q', '')

    if search_query:
        # Превращаем запрос в маленькие буквы (Тест -> тест)
        query_lower = search_query.lower()

        # Проходимся по списку и ищем совпадения вручную через Python
        # Это решает проблему с регистром (Заглавные/Строчные)
        docs = [doc for doc in docs if doc.title.lower().startswith(query_lower)]

    return render(request, 'core/document_list.html', {
        'docs': docs,
        'search_query': search_query
    })