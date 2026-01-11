from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.views import document_list  # <-- Импортируем нашу функцию

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', document_list, name='home'),  # <-- Главная страница (пустые кавычки)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)