from celery import Celery
from app.core.redislite_init import redis_socket

# Создаем Celery приложение
celery_app = Celery(
    'app',
    broker=f"redis+socket://{redis_socket}",
    backend=f"redis+socket://{redis_socket}",
    include=['app.celery.tasks']  # Важно: включаем модуль с задачами
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 час максимум на задачу
    worker_prefetch_multiplier=1,  # Брать по одной задаче
    worker_max_tasks_per_child=1  # Перезапускать воркер после каждой задачи
)

# Экспортируем для использования в других модулях
__all__ = ['celery_app'] 