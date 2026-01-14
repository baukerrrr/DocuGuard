from django.contrib import admin
from .models import Category, Document

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    # Исправили поля на те, что реально есть в модели
    list_display = ['title', 'category', 'security_level', 'uploaded_at', 'uploaded_by']
    list_filter = ['category', 'security_level', 'uploaded_at']
    search_fields = ['title']