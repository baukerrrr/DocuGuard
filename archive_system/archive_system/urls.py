from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Вот в этой строке не хватало 'profile_view' в конце
from core.views import document_list, login_view, logout_view, upload_document, delete_document, profile_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', document_list, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('upload/', upload_document, name='upload'),
    path('delete/<int:doc_id>/', delete_document, name='delete_document'),
    path('profile/', profile_view, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)