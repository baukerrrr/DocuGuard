from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import AuditLog


class Command(BaseCommand):
    help = 'Удаляет записи журнала старше 2 часов'

    def handle(self, *args, **kwargs):
        # Вычисляем время: "сейчас минус 2 часа"
        time_threshold = timezone.now() - timedelta(hours=2)

        # Удаляем все записи, которые были созданы РАНЬШЕ этого времени
        deleted_count, _ = AuditLog.objects.filter(timestamp__lt=time_threshold).delete()

        self.stdout.write(self.style.SUCCESS(f'Очистка завершена. Удалено записей: {deleted_count}'))