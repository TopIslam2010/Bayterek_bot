# handlers/user.py

import json
import logging
import os
from aiogram import F, Router, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.keyboards import (
    generate_captcha_keyboard,
    CAPTCHA_EMOJI,
    generate_city_keyboard,
    generate_main_menu_keyboard,
    generate_products_keyboard,
    generate_weight_keyboard
)
from core.states import UserState
from database.db import get_user, create_user, create_order, generate_referral_code, update_referral_count, get_referral_count
from database.models import User, Order

router = Router()
logger = logging.getLogger(__name__)

# Загрузка данных о товарах и приветственного сообщения
try:
    with open('data/products.json', 'r', encoding='utf-8') as f:
        PRODUCTS = json.load(f)
    with open('data/welcome_message.txt', 'r', encoding='utf-8') as f:
        WELCOME_MESSAGE = f.read()
except FileNotFoundError as e:
    logger.error(f"Файл данных не найден: {e}")
    PRODUCTS = {}
    WELCOME_MESSAGE = "Добро пожаловать в наш магазин!"


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /start. В зависимости от состояния пользователя,
    начинает процесс верификации или показывает главное меню.
    """
    user_id = message.from_user.id
    args = message.text.split()
    referral_code = None
    if len(args) > 1:
        referral_code = args[1]
    
    logger.info(f"Получена команда /start от {user_id}. Реферальный код: {referral_code}")
    
    # Попытка получить пользователя из базы данных
    user = await get_user(user_id)
    
    if user and user.is_verified:
        # Если пользователь уже зарегистрирован и верифицирован, показываем главное меню
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=generate_main_menu_keyboard(),
            reply_to_message_id=message.message_id
        )
        await state.set_state(UserState.main_menu)
        if referral_code:
            await message.answer("Вы уже являетесь пользователем, приглашение не будет засчитано.")
    else:
        # Если новый пользователь, начинаем процесс верификации
        if referral_code:
            await state.update_data(invited_by_referral_code=referral_code)
            
        await message.answer(
            "Привет! Прежде чем мы начнем, давай убедимся, что ты не бот. "
            "Найди и нажми на эмодзи часов " + CAPTCHA_EMOJI,
            reply_markup=generate_captcha_keyboard()
        )
        await state.set_state(UserState.captcha)


@router.callback_query(UserState.captcha, F.data.startswith("captcha_"))
async def process_captcha(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает коллбэки капчи. После успешного прохождения засчитывает реферала
    и переводит в состояние выбора города.
    """
    selected_emoji = callback_query.data.split("_")[1]
    user_data = await state.get_data()
    referral_code = user_data.get("invited_by_referral_code")

    if selected_emoji == CAPTCHA_EMOJI:
        # Успешное прохождение капчи
        if referral_code:
            referrer = await get_user(None, referral_code=referral_code)
            if referrer:
                await update_referral_count(referrer.telegram_id)
                await state.update_data(invited_by_user_id=referrer.telegram_id)
                logger.info(f"Капча пройдена. Реферал засчитан для пользователя {referrer.telegram_id}.")
            else:
                logger.warning(f"Реферальный код {referral_code} не найден.")
        
        await callback_query.message.edit_text(
            "Отлично, верификация пройдена! Теперь выбери свой город:",
            reply_markup=generate_city_keyboard()
        )
        await state.set_state(UserState.city_selection)
    else:
        await callback_query.message.answer("Неверно, попробуй еще раз.", reply_markup=generate_captcha_keyboard())
    await callback_query.answer()


@router.callback_query(UserState.city_selection, F.data.startswith("city_"))
async def process_city_selection(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает выбор города. Сохраняет пользователя в БД.
    """
    city = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "anonymous"
    
    user_data = await state.get_data()
    invited_by_user_id = user_data.get("invited_by_user_id")
    
    new_user = User(
        telegram_id=user_id,
        username=username,
        city=city,
        is_verified=True,
        referral_code=await generate_referral_code(),
        invited_by_user_id=invited_by_user_id
    )
    await create_user(new_user)
    
    # Редактируем старое сообщение, чтобы оно не мешало
    await callback_query.message.edit_text(f"Твой город — {city}!")
    
    # Отправляем новое сообщение с основным меню
    await callback_query.message.answer(
        WELCOME_MESSAGE,
        reply_markup=generate_main_menu_keyboard()
    )
    
    await state.set_state(UserState.main_menu)
    await callback_query.answer()


@router.message(F.text == "🛒 Каталог товаров", UserState.main_menu)
async def show_catalog(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает кнопку 'Каталог товаров' и показывает список товаров.
    """
    # Проверяем, что каталог не пуст
    if not PRODUCTS:
        await message.answer("Каталог товаров временно пуст. Пожалуйста, зайдите позже.")
        return

    await message.answer(
        "Наш каталог:",
        reply_markup=generate_products_keyboard(PRODUCTS)
    )
    await state.set_state(UserState.choosing_product)


@router.callback_query(UserState.choosing_product, F.data.startswith("product_"))
async def show_product_details(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает выбор товара из каталога и показывает его детали.
    """
    product_id = callback_query.data.split("_")[1]
    product = PRODUCTS.get(product_id)
    
    if product:
        await state.update_data(current_product_id=product_id)
        
        await callback_query.message.answer_photo(
            photo=product["photo"],
            caption=f"<b>{product['name']}</b>\n\n{product['description']}\n\n"
                    f"Выберите желаемый вес:",
            reply_markup=generate_weight_keyboard(product_id, product["weights"])
        )
        await state.set_state(UserState.choosing_weight)
    else:
        # Если товар не найден, сообщаем об этом и возвращаем в главное меню
        await callback_query.message.answer("Такого товара не существует. Возвращаю в главное меню.",
                                            reply_markup=generate_main_menu_keyboard())
        await state.set_state(UserState.main_menu)
        
    await callback_query.answer()


@router.callback_query(F.data == "back_to_catalog", UserState.choosing_weight)
async def back_to_catalog(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатывает кнопку "Назад" в каталоге.
    """
    await callback_query.message.edit_text(
        "Наш каталог:",
        reply_markup=generate_products_keyboard(PRODUCTS)
    )
    await state.set_state(UserState.choosing_product)
    await callback_query.answer()


@router.callback_query(UserState.choosing_weight, F.data.startswith("buy_"))
async def process_purchase(callback_query: CallbackQuery, state: FSMContext, payment_bot: Bot) -> None:
    """
    Обрабатывает выбор веса и начинает процесс покупки.
    Автоматически применяет скидку, если пользователь её заработал.
    """
    data = callback_query.data.split("_")
    product_id = data[1]
    weight = float(data[2])
    
    product = PRODUCTS.get(product_id)
    if not product:
        await callback_query.message.answer("Ошибка: товар не найден.")
        await callback_query.answer()
        return

    price = float(product["weights"].get(str(int(weight))))
    
    if not price:
        await callback_query.message.answer("Ошибка: неверный вес товара.")
        await callback_query.answer()
        return

    user_id = callback_query.from_user.id
    referrals_count = await get_referral_count(user_id)
    discount_applied = False
    
    if referrals_count >= 5:
        # Применяем скидку 5%
        price *= 0.95
        price = round(price, 2)
        discount_applied = True
        await callback_query.message.answer("🎉 Поздравляем! Ваша скидка 5% активирована!")

    await state.update_data(
        order_details={
            "product_name": product["name"],
            "weight": weight,
            "price": price,
            "user_id": user_id,
            "discount_applied": discount_applied
        }
    )

    await callback_query.message.answer(
        f"Отлично! Ваш заказ на **{weight} грамм** товара **{product['name']}** на сумму **{price} руб** принят.\n"
        f"Пожалуйста, переведите указанную сумму на нашу карту. После перевода, отправьте скриншот чека в этот чат."
    )
    
    await state.set_state(UserState.waiting_for_payment)
    await callback_query.answer()


@router.message(F.photo, UserState.waiting_for_payment)
async def process_payment_photo(message: Message, state: FSMContext, payment_bot: Bot) -> None:
    """
    Обрабатывает получение скриншота оплаты.
    """
    user_data = await state.get_data()
    order_details = user_data.get("order_details")

    if not order_details:
        await message.answer("Ошибка. Пожалуйста, начните заказ заново, нажав на /start.")
        await state.clear()
        return
        
    order = Order(
        user_id=order_details["user_id"],
        product_name=order_details["product_name"],
        weight=order_details["weight"],
        price=order_details["price"],
        payment_screenshot=message.photo[-1].file_id,
        discount_applied=order_details.get("discount_applied", False)
    )

    await create_order(order)

    await message.answer(
        "Спасибо, ваш скриншот получен! Ожидайте подтверждения от оператора. "
        "Как только оплата будет подтверждена, я вас уведомлю. \n\n"
        "Если у вас есть вопросы, вы можете обратиться в поддержку: @suppor_bayterek"
    )

    # Отправляем уведомление администратору через второй бот
    admin_id = int(os.getenv("ADMIN_ID"))
    discount_text = "Скидка 5% применена!" if order.discount_applied else "Скидка не применялась."
    await payment_bot.send_message(
        chat_id=admin_id,
        text=f"‼️ НОВЫЙ ЗАКАЗ ‼️\n"
             f"От пользователя: @{message.from_user.username} (ID: {message.from_user.id})\n"
             f"Товар: {order.product_name} ({order.weight}г)\n"
             f"Сумма: {order.price} руб\n"
             f"Состояние: {discount_text}\n\n"
             f"Для подтверждения, ответьте на это сообщение командой /confirm."
    )
    
    await payment_bot.send_photo(
        chat_id=admin_id,
        photo=order.payment_screenshot,
        caption="Скриншот оплаты:"
    )

    await state.clear()


@router.message(F.text == "🛠 Поддержка", UserState.main_menu)
async def show_support(message: Message) -> None:
    """
    Обрабатывает кнопку 'Поддержка'.
    """
    await message.answer("По всем вопросам обращайтесь к оператору: @suppor_bayterek")


@router.message(F.text == "🔗 Реферальная ссылка", UserState.main_menu)
async def show_referral_link(message: Message) -> None:
    """
    Обрабатывает кнопку 'Реферальная ссылка' и показывает счётчик.
    """
    user_id = message.from_user.id
    user = await get_user(user_id)
    if user and user.referral_code:
        referral_link = f"https://t.me/BayterekCartelbot?start={user.referral_code}"
        
        referrals_count = await get_referral_count(user_id)
        
        status_text = ""
        if referrals_count >= 5:
            status_text = "🎉 Вы заработали скидку 5% на следующую покупку!"
        else:
            status_text = f"Вы пригласили {referrals_count}/5 человек. Пригласите ещё {5 - referrals_count} и получите скидку 5%!"
            
        await message.answer(
            f"Ваша уникальная реферальная ссылка:\n{referral_link}\n\n"
            f"{status_text}"
        )
    else:
        await message.answer("Ваш реферальный код не найден. Пожалуйста, обратитесь в поддержку.")


@router.message(UserState.main_menu)
async def handle_invalid_text_in_main_menu(message: Message) -> None:
    """
    Обрабатывает любые текстовые сообщения, которые не являются командами,
    когда пользователь находится в главном меню. Это предотвращает баг с "ошибкой".
    """
    await message.answer("Пожалуйста, выберите действие из меню.")

@router.callback_query(UserState.main_menu)
async def handle_invalid_callback_in_main_menu(callback_query: CallbackQuery) -> None:
    """
    Перехватывает некорректные нажатия на кнопки, когда бот находится в главном меню.
    Это предотвращает старые коллбэки от ломания бота.
    """
    await callback_query.answer("Это действие больше неактуально. Пожалуйста, выберите действие из меню.", show_alert=True)

