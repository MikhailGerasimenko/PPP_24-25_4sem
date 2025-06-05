from pydantic_settings import BaseSettings
from app.core.redislite_init import redis_instance, redis_socket

class Settings(BaseSettings):
    # Настройки Celery с использованием Unix-сокета redislite
    CELERY_BROKER_URL: str = f"redis+socket://{redis_socket}"
    CELERY_RESULT_BACKEND: str = f"redis+socket://{redis_socket}"

# Создаем экземпляр настроек
settings = Settings() 