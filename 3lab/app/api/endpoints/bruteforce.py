from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from app.celery.tasks import bruteforce_task, NOTIFICATION_CHANNEL
from app.core.redislite_init import redis_instance
import json
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class BruteforceRequest(BaseModel):
    hash_to_crack: str
    client_id: str
    max_length: int = 5

@router.post("/start")
async def start_bruteforce(request: BruteforceRequest):
    """
    Запускает задачу брутфорса
    """
    try:
        task = bruteforce_task.delay(request.hash_to_crack, request.client_id)
        return {"task_id": task.id, "status": "started"}
    except Exception as e:
        return {"error": str(e)}, 500

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket эндпоинт для получения обновлений о процессе брутфорса
    """
    await websocket.accept()
    logger.info(f"WebSocket подключение установлено для клиента {client_id}")
    
    # Подписываемся на канал Redis для этого клиента
    pubsub = redis_instance.pubsub()
    pubsub.subscribe(NOTIFICATION_CHANNEL)
    logger.info(f"Подписались на канал {NOTIFICATION_CHANNEL}")
    
    try:
        # Слушаем сообщения
        while True:
            try:
                # Проверяем сообщения Redis
                message = pubsub.get_message(timeout=1)
                if message and message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    try:
                        json_data = json.loads(data)
                        if json_data.get("client_id") == client_id:
                            await websocket.send_json(json_data)
                            logger.info(f"Отправлено сообщение клиенту {client_id}: {json_data}")
                            
                            # Если это финальное сообщение, закрываем соединение
                            if json_data.get("type") in ["success", "not_found", "error"]:
                                logger.info(f"Получено финальное сообщение для клиента {client_id}")
                                break
                    except json.JSONDecodeError:
                        logger.error(f"Ошибка декодирования JSON: {data}")
                    except Exception as e:
                        logger.error(f"Ошибка при обработке сообщения: {e}")
                
                # Небольшая пауза чтобы не нагружать процессор
                await asyncio.sleep(0.1)
                
            except WebSocketDisconnect:
                logger.info(f"Клиент {client_id} отключился")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле обработки сообщений: {e}")
                break
    finally:
        # Отписываемся от канала Redis при любом исходе
        pubsub.unsubscribe(NOTIFICATION_CHANNEL)
        logger.info(f"Отписались от канала {NOTIFICATION_CHANNEL} для клиента {client_id}")
        await websocket.close()


# python -m uvicorn app.api.endpoints.bruteforce:router --reload 
# python -m celery -A app.celery.celery_app worker --loglevel=info
# python console_client.py 202cb962ac59075b964b07152d234b70 (123)
# 