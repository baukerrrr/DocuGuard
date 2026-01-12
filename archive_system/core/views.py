from django.shortcuts import render
from .models import Document


def document_list(request):
    # Если пользователь вошел (Admin или сотрудник) -> Показываем ВСЁ
    if request.user.is_authenticated:
        docs = Document.objects.all()
    # Если гость -> Показываем только ОБЩИЕ документы
    else:
        docs = Document.objects.filter(security_level='public')

    return render(request, 'core/document_list.html', {'docs': docs})