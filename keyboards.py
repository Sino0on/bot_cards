from aiogram import types
from aiogram.types import KeyboardButton


def get_keyboard_buttons(user_id: int = None):
    buttons = [
        [
            KeyboardButton(text="📊 Информация по счету"),
            KeyboardButton(text="📇 Баланс счёта"),
        ],
        [
            KeyboardButton(text="💳 Виртуальная карта"),
            KeyboardButton(text="📝 Оставить отзыв"),
        ],
    ]

    if user_id == 795677145:
        buttons.append([
            KeyboardButton(text="✍️ Отправить рассылку"),
            KeyboardButton(text="🧠 Добавить менеджера"),
        ])

    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons)
    return keyboard