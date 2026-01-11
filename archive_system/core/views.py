from django.shortcuts import render
from .models import Document


def document_list(request):
    # Получаем все документы из базы
    docs = Document.objects.all()

    # Отправляем их на страницу (в шаблон)
    return render(request, 'core/document_list.html', {'docs': docs})