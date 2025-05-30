from aiogram import Router, F, types
from decouple import config

from aiogram import Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

# from clients import find_client_by_user_id, get_user_id_by_phone, register, check_manager, get_user_info_by_id

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from services.validators import check_manager, check_admin
from services.json_writer import find_manager_by_user_id

router = Router()

def get_keyboard_buttons(user_id: int = None):
    buttons = []
    print(user_id)
    if check_manager(user_id):
        buttons.append([
            KeyboardButton(text="💳 Добавить карту"),
            KeyboardButton(text="💳 Мои карты")
        ])
    if check_admin(user_id):
        buttons.append([
            KeyboardButton(text="🧠 Добавить менеджера"),
            KeyboardButton(text="🧠 В разработке ..."),
        ])
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons)
    return keyboard


@router.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    print(message.from_user.id)
    user = find_manager_by_user_id(message.from_user.id)
    print(user)
    if user:
        await message.answer(
            f'Здравствуйте, {user["name"]} 💙', reply_markup=get_keyboard_buttons(message.from_user.id)
        )
        return
    await message.answer(
        'Для продолжения работы необходим ваш контакт. Нажмите на кнопку "📞 Поделиться контактом".',
        # reply_markup=get_contact_button(),
    )
    # await state.set_state(Registration.waiting_for_contact)
