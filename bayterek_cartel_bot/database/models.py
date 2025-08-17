# database/models.py

import sqlite3
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class User:
    """Модель пользователя."""
    telegram_id: int
    username: str
    city: str
    is_verified: bool = False
    referral_code: Optional[str] = None
    invited_by_user_id: Optional[int] = None
    referrals_count: int = 0

@dataclass
class Order:
    """Модель заказа."""
    user_id: int
    product_name: str
    weight: float
    price: float
    payment_screenshot: str
    discount_applied: bool
    status: str = field(default="pending")

async def create_tables():
    """
    Создает таблицы в базе данных, если они не существуют.
    """
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            city TEXT,
            is_verified BOOLEAN,
            referral_code TEXT UNIQUE,
            invited_by_user_id INTEGER,
            referrals_count INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT,
            weight REAL,
            price REAL,
            payment_screenshot TEXT,
            discount_applied BOOLEAN,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id)
        )
    """)
    
    conn.commit()
    conn.close()

