# core/config.py

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токены и ID администратора. Выбрасываем ошибку, если переменные отсутствуют.
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле.")

PAYMENT_BOT_TOKEN = os.getenv("PAYMENT_BOT_TOKEN")
if not PAYMENT_BOT_TOKEN:
    raise ValueError("PAYMENT_BOT_TOKEN не найден в .env файле.")

ADMIN_ID_STR = os.getenv("ADMIN_ID")
if not ADMIN_ID_STR:
    raise ValueError("ADMIN_ID не найден в .env файле.")

try:
    ADMIN_ID = int(ADMIN_ID_STR)
except (ValueError, TypeError):
    raise ValueError("ADMIN_ID должен быть корректным целым числом.")
