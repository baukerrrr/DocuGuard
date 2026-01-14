from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Document(models.Model):
    SECURITY_CHOICES = [
        ('public', 'Общий доступ'),
        ('internal', 'Служебное пользование'),
        ('secret', 'Секретно'),
    ]

    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    security_level = models.CharField(max_length=20, choices=SECURITY_CHOICES, default='public')
    file = models.FileField(upload_to='documents/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # ВОТ ЭТО МЫ ДОБАВЛЯЕМ:
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title