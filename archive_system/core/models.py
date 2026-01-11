from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    retention_days = models.IntegerField(default=365, verbose_name="Срок хранения (дней)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Document(models.Model):
    SECURITY_CHOICES = [
        ('public', '🟢 Общий (Видят все)'),
        ('internal', '🟡 Для служебного пользования'),
        ('secret', '🔴 Секретно (Только топ-менеджмент)'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Краткое описание")

    # ВОТ ИЗМЕНЕНИЕ: Просто кидаем все файлы в папку "docs" без сложностей
    file = models.FileField(upload_to='docs/', verbose_name="Файл")

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="Категория")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Кто загрузил")

    security_level = models.CharField(
        max_length=20,
        choices=SECURITY_CHOICES,
        default='internal',
        verbose_name="Гриф секретности"
    )

    is_archived = models.BooleanField(default=False, verbose_name="В архиве?")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Последнее изменение")

    def __str__(self):
        return f"{self.title} [{self.security_level}]"

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"