import os
import redislite

# Создаем экземпляр Redislite с явным указанием пути к файлу
redis_instance = redislite.Redis(
    os.path.join(os.getcwd(), "redis.db"),
    serverconfig={'port': '6379'}
)

# Получаем путь к сокету для использования в других модулях
redis_socket = redis_instance.socket_file 