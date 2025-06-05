import time
import itertools
import string
import hashlib
import json
from typing import Optional
from celery import shared_task
from app.core.redislite_init import redis_instance
from app.celery.celery_app import celery_app
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NOTIFICATION_CHANNEL = "ws_notifications"

@shared_task(name='app.celery.tasks.bruteforce_task')
def bruteforce_task(hash_to_crack: str, client_id: str):
    """
    Задача для брутфорса MD5 хеша
    """
    try:
        logger.info(f"Начало брутфорса для хеша {hash_to_crack} (клиент: {client_id})")
        
        # Используем и строчные и прописные буквы
        characters = string.ascii_letters + string.digits
        max_length = 5  # Максимальная длина пароля
        
        # Публикуем начало работы
        start_message = {
            "client_id": client_id,
            "message": "🔍 Начинаю брутфорс...",
            "type": "start"
        }
        logger.info(f"Отправка сообщения в Redis: {start_message}")
        redis_instance.publish(NOTIFICATION_CHANNEL, json.dumps(start_message))

        total_attempts = 0
        for length in range(1, max_length + 1):
            logger.info(f"Перебор паролей длины {length}")
            for guess in itertools.product(characters, repeat=length):
                password = ''.join(guess)
                guess_hash = hashlib.md5(password.encode()).hexdigest()
                
                total_attempts += 1
                if total_attempts % 1000 == 0:  # Отправляем статус каждые 1000 попыток
                    progress_message = {
                        "client_id": client_id,
                        "message": f"⚡️ Проверено {total_attempts} паролей. Текущий: {password}",
                        "type": "progress"
                    }
                    logger.info(f"Отправка прогресса в Redis: {progress_message}")
                    redis_instance.publish(NOTIFICATION_CHANNEL, json.dumps(progress_message))
                
                if guess_hash == hash_to_crack:
                    # Найден правильный пароль
                    result = f"✅ Пароль найден: {password} (после {total_attempts} попыток)"
                    success_message = {
                        "client_id": client_id,
                        "message": result,
                        "type": "success"
                    }
                    logger.info(f"Отправка результата в Redis: {success_message}")
                    redis_instance.publish(NOTIFICATION_CHANNEL, json.dumps(success_message))
                    return password
        
        # Пароль не найден
        not_found_message = {
            "client_id": client_id,
            "message": f"❌ Пароль не найден после {total_attempts} попыток",
            "type": "not_found"
        }
        logger.info(f"Отправка сообщения о неудаче в Redis: {not_found_message}")
        redis_instance.publish(NOTIFICATION_CHANNEL, json.dumps(not_found_message))
        return None
        
    except Exception as e:
        logger.error(f"Ошибка в процессе брутфорса: {e}")
        # В случае ошибки отправляем сообщение об ошибке
        error_message = {
            "client_id": client_id,
            "message": f"⚠️ Произошла ошибка: {str(e)}",
            "type": "error"
        }
        redis_instance.publish(NOTIFICATION_CHANNEL, json.dumps(error_message))
        raise

# ... (остальной код файла без изменений) ... 