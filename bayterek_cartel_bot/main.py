# main.py

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from database.db import init_db
from handlers import user as user_handlers
from handlers import admin as admin_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Основная функция для запуска бота.
    """
    # Загружаем переменные окружения из .env файла
    load_dotenv()
    
    # Получаем токен бота из .env
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не найден в переменных окружения.")
        return
        
    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        logger.error("ADMIN_ID не найден в переменных окружения.")
        return

    # Инициализация базы данных
    await init_db()
    
    # Инициализация ботов с новым синтаксисом
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_routers(user_handlers.router, admin_handlers.router)
    
    logger.info("Запуск бота...")
    
    # Запускаем поллинг, передавая бот администратора в обработчики
    await dp.start_polling(bot, payment_bot=bot)


if __name__ == "__main__":
    asyncio.run(main())

