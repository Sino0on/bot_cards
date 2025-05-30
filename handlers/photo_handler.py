from aiogram import Dispatcher, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from decouple import config
from services.ocr_service import text_contains_number
from handlers.manager_handler import AcceptMoney


router = Router()
from services.ocr_service import extract_text
from services.json_writer import find_manager_by_card_number

GROUP_ID = -1002571182477  # твоя группа

@router.message(F.photo & F.chat.id == GROUP_ID)
async def handle_group_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = file.file_path
    file_bytes = await message.bot.download_file(file_path)

    text = await extract_text(file_bytes)
    if not text:
        return

    # Поиск менеджера по тексту (в котором могла быть карта)
    manager = find_manager_by_card_number(text)

    if manager:
        # Сохраняем номер карты, чтобы потом понять куда деньги
        found_card = None
        for card in manager["cards"]:
            if card["card"] in text:
                found_card = card["card"]
                break

        if found_card:
            # Сохраняем в FSM
            await state.set_data({
                "card_number": found_card,
                "photo_id": photo.file_id,
                "text": text
            })

            # Отправляем с кнопками
            buttons = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Принять", callback_data=f"accept:{found_card}"),
                    InlineKeyboardButton(text="❌ Отказать", callback_data="decline_card"),
                ]
            ])

            await message.bot.send_photo(
                chat_id=int(manager["id"]),
                photo=photo.file_id,
                caption=f"📸 Найдена карта `{found_card}` в фото",
                reply_markup=buttons,
                parse_mode="Markdown"
            )


from services.json_writer import add_money_to_card

@router.callback_query(F.data.startswith("accept:"))
async def accept_card_callback(callback: CallbackQuery, state: FSMContext):
    card_number = callback.data.split(":")[1]
    await callback.message.answer("Введите сумму, которую нужно зачислить:")
    await state.set_state(AcceptMoney.waiting_for_sum)
    await state.update_data(card_number=card_number)
    await callback.answer()

@router.callback_query(F.data == "decline_card")
async def decline_card_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Операция отменена.")
    await state.clear()
    await callback.answer()

@router.message(AcceptMoney.waiting_for_sum)
async def add_money(message: Message, state: FSMContext):
    amount_text = message.text.strip()
    if not amount_text.isdigit():
        await message.answer("❗ Введите только число.")
        return

    amount = int(amount_text)
    data = await state.get_data()
    card_number = data["card_number"]

    success = add_money_to_card(card_number, amount)
    if success:
        await message.answer(f"✅ На карту {card_number} зачислено {amount} сом.")
    else:
        await message.answer("❌ Не удалось найти карту.")
    await state.clear()

