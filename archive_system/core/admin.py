# Файл: core/admin.py
from django.contrib import admin
from .models import Category, Document


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'retention_days')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    # Колонки в таблице
    list_display = ('title', 'category', 'security_level', 'uploaded_by', 'is_archived', 'created_at')

    # Фильтры справа (очень удобно для курсовой показать "поиск")
    list_filter = ('security_level', 'is_archived', 'category', 'created_at')

    # Поиск по словам
    search_fields = ('title', 'description')

    # Автоматически подставлять текущего юзера при создании
    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)