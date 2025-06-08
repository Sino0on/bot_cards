from aiogram import types
from aiogram.types import KeyboardButton

from services.validators import check_admin, check_manager


def get_keyboard_buttons(user_id: int = None):
    buttons = []

    if check_manager(user_id):
        buttons.append([
            KeyboardButton(text="💳 Добавить карту"),
            KeyboardButton(text="💳 Мои карты"),
            KeyboardButton(text="📄 Мои транзакции")


        ])
        buttons.append([
            KeyboardButton(text="💼 Баланс карт"),
            KeyboardButton(text="💰 Мой баланс")
        ])

    if check_admin(user_id):
        buttons.append([
            KeyboardButton(text="🧠 Добавить менеджера"),
            KeyboardButton(text="👨‍💼 Операторы"),
            KeyboardButton(text="⚙️ Настройки системы")
        ])
        buttons.append([
            KeyboardButton(text="💬 Чаты"),  # управление чатами
            KeyboardButton(text="📊 Балансы"),  # управление чатами
            KeyboardButton(text="💸 Отправка денег в шоп")
        ])

    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard