# core/keyboards.py

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)

CAPTCHA_EMOJI = "⏰"

def generate_captcha_keyboard() -> InlineKeyboardMarkup:
    """Генерирует инлайн-клавиатуру для капчи с одним верным вариантом."""
    buttons = [
        InlineKeyboardButton(text="🍎", callback_data="captcha_🍎"),
        InlineKeyboardButton(text="⏰", callback_data="captcha_⏰"),
        InlineKeyboardButton(text="🍏", callback_data="captcha_🍏"),
        InlineKeyboardButton(text="🍊", callback_data="captcha_🍊"),
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    return keyboard

def generate_city_keyboard() -> InlineKeyboardMarkup:
    """Генерирует инлайн-клавиатуру для выбора города."""
    buttons = [
        [InlineKeyboardButton(text="Алматы", callback_data="city_Алматы")],
        [InlineKeyboardButton(text="Астана", callback_data="city_Астана")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def generate_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Генерирует основную Reply-клавиатуру с меню."""
    buttons = [
        [KeyboardButton(text="🛒 Каталог товаров")],
        [KeyboardButton(text="🔗 Реферальная ссылка"), KeyboardButton(text="🛠 Поддержка")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard

def generate_products_keyboard(products: dict) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру с товарами из каталога.
    Если каталог пуст, возвращает пустую клавиатуру.
    """
    if not products:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Каталог пуст", callback_data="catalog_empty")
        ]])
        
    buttons = []
    for product_id, product_data in products.items():
        button = InlineKeyboardButton(text=product_data.get("name", "Неизвестный товар"), callback_data=f"product_{product_id}")
        buttons.append([button])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def generate_weight_keyboard(product_id: str, weights: dict) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру для выбора веса товара.
    """
    buttons = []
    for weight, price in weights.items():
        button_text = f"{weight} гр. - {price} руб."
        callback_data = f"buy_{product_id}_{weight}"
        buttons.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    
    # Добавляем кнопку "Назад" для удобной навигации
    buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_catalog"))
    
    # Оборачиваем кнопки в список списков, чтобы они располагались по одной в строке
    inline_keyboard = [[button] for button in buttons]
    
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
