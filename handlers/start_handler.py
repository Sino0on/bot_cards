from aiogram import Router, F, types
from decouple import config

from aiogram import Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

# from clients import find_client_by_user_id, get_user_id_by_phone, register, check_manager, get_user_info_by_id

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from keyboards import get_keyboard_buttons
from services.validators import check_manager, check_admin
from services.json_writer import find_manager_by_user_id

router = Router()




@router.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    if message.chat.id != message.from_user.id:
        await message.answer(
            f'Пиши в личку',
            reply_markup=ReplyKeyboardRemove()
        )
        return
    user = find_manager_by_user_id(message.from_user.id)
    print(user)
    if user:
        await message.answer(
            f'Здравствуйте, {user["name"]}', reply_markup=get_keyboard_buttons(message.from_user.id)
        )
        return
    await message.answer(
        'Давай',
        # reply_markup=get_contact_button(),
    )
    # await state.set_state(Registration.waiting_for_contact)
