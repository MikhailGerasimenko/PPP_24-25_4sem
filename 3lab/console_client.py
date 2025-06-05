import argparse
import requests
import websockets
import asyncio
import json
import sys
import uuid
from datetime import datetime

# Тестовый MD5 хеш для слова "test" = 098f6bcd4621d373cade4e832627b4f6
TEST_HASH = "098f6bcd4621d373cade4e832627b4f6"
HTTP_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

def print_message(message, message_type=None):
    """
    Форматированный вывод сообщений
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

async def connect_websocket(client_id):
    """
    Подключение к WebSocket серверу и получение обновлений
    """
    uri = f"{WS_URL}/ws/{client_id}"
    try:
        async with websockets.connect(
            uri,
            ping_interval=20,  # Отправлять пинг каждые 20 секунд
            ping_timeout=60,   # Ждать понг 60 секунд
            close_timeout=60   # Ждать закрытия соединения 60 секунд
        ) as websocket:
            print_message("🔌 WebSocket подключение установлено")
            
            # Запускаем отдельную задачу для пинга
            ping_task = asyncio.create_task(keep_alive(websocket))
            
            try:
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        print_message(data.get("message", "Неизвестное сообщение"))
                        
                        # Если получено сообщение о завершении, прерываем цикл
                        msg_type = data.get("type", "")
                        if msg_type in ["success", "not_found", "error"]:
                            break
                    except json.JSONDecodeError as e:
                        print_message(f"⚠️ Ошибка при разборе JSON: {e}")
                    except websockets.exceptions.ConnectionClosed:
                        print_message("⚠️ Соединение закрыто сервером")
                        break
                    except Exception as e:
                        print_message(f"⚠️ Ошибка при получении сообщения: {e}")
                        break
            finally:
                # Отменяем задачу пинга при выходе
                ping_task.cancel()
                try:
                    await ping_task
                except asyncio.CancelledError:
                    pass
    except Exception as e:
        print_message(f"⚠️ Ошибка подключения к WebSocket: {e}")

async def keep_alive(websocket):
    """
    Поддерживает соединение активным с помощью пингов
    """
    try:
        while True:
            await asyncio.sleep(20)  # Пинг каждые 20 секунд
            try:
                pong = await websocket.ping()
                await pong
            except:
                return
    except asyncio.CancelledError:
        pass

def start_bruteforce(hash_to_crack, client_id):
    """
    Отправка запроса на начало брутфорса
    """
    url = f"{HTTP_URL}/start"
    data = {
        "hash_to_crack": hash_to_crack,
        "client_id": client_id
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print_message(f"⚠️ Ошибка при отправке запроса: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Клиент для брутфорс API")
    parser.add_argument("hash", help="MD5 хеш для взлома")
    parser.add_argument("--client-id", default=str(uuid.uuid4()), help="ID клиента")
    
    args = parser.parse_args()
    
    try:
        print_message(f"🎯 Начинаем взлом хеша: {args.hash}")
        
        # Запускаем брутфорс
        result = start_bruteforce(args.hash, args.client_id)
        if result is None:
            print_message("❌ Не удалось запустить брутфорс")
            return
        
        print_message(f"✅ Задача запущена: {result.get('task_id')}")
        
        # Запускаем WebSocket клиент
        asyncio.run(connect_websocket(args.client_id))
    except KeyboardInterrupt:
        print_message("\n⛔️ Прерывание работы...")
    except Exception as e:
        print_message(f"⚠️ Ошибка: {e}")
    finally:
        print_message("👋 Завершение работы клиента")

if __name__ == "__main__":
    main() 