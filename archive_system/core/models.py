import os  # <-- НЕ ЗАБУДЬ ЭТУ СТРОКУ
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
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    # 👇 НОВАЯ ФУНКЦИЯ: возвращает расширение файла (например: .docx)
    def get_extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()

    # 👇 НОВАЯ ФУНКЦИЯ: проверяет, картинка это или нет (для превью)
    def is_image(self):
        return self.get_extension() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# Модель для журнала действий
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Пользователь")
    action = models.CharField(max_length=50, verbose_name="Действие")  # Например: "Загрузка", "Удаление"
    document_title = models.CharField(max_length=255, verbose_name="Документ")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']  # Сначала новые записи