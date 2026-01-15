import time
import os
import subprocess
from datetime import datetime

print("⏳ Запуск планировщика очистки логов (каждые 20 минут)...")

while True:
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Запускаю очистку...")

    # Запускаем нашу команду Django
    # Используем subprocess для надежности
    subprocess.run(["python", "manage.py", "cleanup_logs"], shell=True)

    print("✅ Готово. Следующая очистка через 20 минут.")

    # Ждем 20 минут (1 час * 20 минут * 20 секунд)
    time.sleep(1 * 20 * 60)