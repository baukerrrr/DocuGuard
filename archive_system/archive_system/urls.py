from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import document_list

urlpatterns = [
    path('admin/', admin.site.urls),

    # Включаем готовые адреса для входа/выхода
    path('accounts/', include('django.contrib.auth.urls')),

    path('', document_list, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)