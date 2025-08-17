# handlers/admin.py

import logging
from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import Message

from core.config import ADMIN_ID
from database.db import update_order_status

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("confirm"), F.from_user.id == ADMIN_ID)
async def confirm_order_from_admin(message: Message, bot: Bot) -> None:
    """
    Обрабатывает команду /confirm для администратора.
    Подтверждает оплату заказа и уведомляет пользователя.
    """
    if not message.reply_to_message or not message.reply_to_message.caption:
        await message.answer("Пожалуйста, ответьте этой командой на сообщение с информацией о заказе.")
        return

    try:
        # Извлекаем ID пользователя из текста уведомления
        text = message.reply_to_message.caption
        user_id_str_start = text.find("ID: ") + 4
        user_id_str_end = text.find(")", user_id_str_start)
        user_id = int(text[user_id_str_start:user_id_str_end])
        
        # Обновляем статус заказа в базе данных
        await update_order_status(user_id, "confirmed")
        
        await message.answer(f"✅ Заказ от пользователя с ID {user_id} подтвержден.")
        
        # Уведомляем пользователя о подтверждении
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 **Ваш заказ подтвержден!**\n\n"
                 f"Оператор уже занимается вашим заказом. "
                 f"Для получения товара обратитесь в поддержку: @suppor_bayterek"
        )
        
    except (ValueError, IndexError, Exception) as e:
        logger.error(f"Ошибка при обработке подтверждения заказа: {e}")
        await message.answer("Произошла ошибка при подтверждении заказа. Пожалуйста, попробуйте еще раз.")
