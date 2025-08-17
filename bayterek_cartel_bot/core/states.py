# core/states.py

from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    """Состояния пользователя в боте."""
    captcha = State()  # Ожидание прохождения капчи
    city_selection = State()  # Ожидание выбора города
    main_menu = State()  # Главное меню
    choosing_product = State()  # Ожидание выбора товара
    choosing_weight = State()  # Ожидание выбора веса
    waiting_for_payment = State()  # Ожидание скриншота оплаты

class AdminState(StatesGroup):
    """Состояния администратора в боте."""
    main_menu = State()  # Главное меню администратора
    waiting_for_confirm = State()  # Ожидание подтверждения заказа

