# database/db.py

import logging
import sqlite3
from typing import Optional

from .models import User, Order, create_tables

logger = logging.getLogger(__name__)

async def init_db():
    """
    Инициализирует базу данных и создает таблицы, если они не существуют.
    """
    try:
        await create_tables()
        logger.info("База данных успешно инициализирована.")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")

async def get_user(telegram_id: Optional[int] = None, referral_code: Optional[str] = None) -> Optional[User]:
    """
    Получает пользователя по Telegram ID или реферальному коду.
    """
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        if telegram_id:
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        elif referral_code:
            cursor.execute("SELECT * FROM users WHERE referral_code = ?", (referral_code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user = User(
                telegram_id=row[0],
                username=row[1],
                city=row[2],
                is_verified=bool(row[3]),
                referral_code=row[4],
                invited_by_user_id=row[5],
                referrals_count=row[6]
            )
            return user
        return None
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД при получении пользователя: {e}")
        return None

async def create_user(user: User):
    """
    Создает нового пользователя или обновляет существующего.
    """
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO users (
                telegram_id,
                username,
                city,
                is_verified,
                referral_code,
                invited_by_user_id,
                referrals_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user.telegram_id,
            user.username,
            user.city,
            user.is_verified,
            user.referral_code,
            user.invited_by_user_id,
            user.referrals_count
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Пользователь {user.telegram_id} успешно создан/обновлен.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД при создании/обновлении пользователя: {e}")

async def create_order(order: Order):
    """
    Создает новый заказ.
    """
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (
                user_id,
                product_name,
                weight,
                price,
                payment_screenshot,
                discount_applied,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order.user_id,
            order.product_name,
            order.weight,
            order.price,
            order.payment_screenshot,
            order.discount_applied,
            order.status
        ))
        conn.commit()
        conn.close()
        logger.info(f"Новый заказ от пользователя {order.user_id} успешно создан.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД при создании заказа: {e}")

async def update_order_status(user_id: int, status: str):
    """
    Обновляет статус последнего заказа пользователя.
    """
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
        last_order_id = cursor.fetchone()
        
        if last_order_id:
            cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, last_order_id[0]))
            conn.commit()
            logger.info(f"Статус заказа {last_order_id[0]} для пользователя {user_id} обновлен на '{status}'.")
        else:
            logger.warning(f"Заказ для пользователя {user_id} не найден.")
            
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД при обновлении статуса заказа: {e}")

async def generate_referral_code() -> str:
    """
    Генерирует уникальный реферальный код.
    """
    import string
    import random
    
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return code

async def update_referral_count(user_id: int):
    """
    Увеличивает счетчик рефералов для пользователя.
    """
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET referrals_count = referrals_count + 1 WHERE telegram_id = ?", (user_id,))
        conn.commit()
        conn.close()
        logger.info(f"Счетчик рефералов для пользователя {user_id} обновлен.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД при обновлении счетчика рефералов: {e}")

async def get_referral_count(user_id: int) -> int:
    """
    Получает количество рефералов пользователя.
    """
    try:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT referrals_count FROM users WHERE telegram_id = ?", (user_id,))
        count = cursor.fetchone()
        conn.close()
        return count[0] if count else 0
    except sqlite3.Error as e:
        logger.error(f"Ошибка БД при получении количества рефералов: {e}")
        return 0
