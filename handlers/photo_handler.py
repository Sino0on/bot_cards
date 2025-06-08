from aiogram import Dispatcher, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from decouple import config
from services.ocr_service import text_contains_number
from services.json_writer import load_data, find_manager_by_user_id, get_all_chats
from services.ocr_service import extract_text

from handlers.manager_handler import AcceptMoney


router = Router()
from services.ocr_service import extract_text
from services.json_writer import find_manager_by_card_number

from aiogram.filters.callback_data import CallbackData

class AcceptCardCallback(CallbackData, prefix="accept"):
    card: str          # например: "4566"
    chat_id: int          # например: "4566"
    msg_id: int        # ID сообщения с фото


GROUP_ID = -4851516748

@router.message(F.photo)
async def handle_group_photo(message: Message):
    if message.chat.id != GROUP_ID:
        return  # игнорируем сообщения из других чатов
    chat_id = message.chat.id
    chat_id = int(message.caption.split('\n')[0])
    msg_id = message.caption.split('\n')[1]
    print(f"[DEBUG] Chat ID: {chat_id}, Msg ID: {msg_id}")

    # Шаг 1: Найти чат
    chats = get_all_chats()
    current_chat = next((c for c in chats if c["id"] == abs(chat_id)), None)
    print(message.chat.id)
    if not message.chat.id == GROUP_ID:
        return  # чат не зарегистрирован или выключен

    # Шаг 2: Скачиваем фото
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)

    # Шаг 3: Распознаём текст
    text = await extract_text(file_bytes)
    print(text)
    if not text:
        return

    # Шаг 4: Проверка по картам всех менеджеров, привязанных к чату
    data = load_data()
    potential_managers = [m for m in data["managers"] if int(m["id"]) in current_chat["managers"] and m["status"]]
    print(text)
    for manager in potential_managers:
        for card in manager.get("cards", []):
            if card["card"] in text:
                # Карта найдена — шлём оператору фото
                print(f'[DEBUG] Check come to {card["card"]}')
                buttons = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Принять",
                            callback_data=AcceptCardCallback(
                                card=card["card"],
                                chat_id=chat_id,
                                msg_id=msg_id
                            ).pack()
                        ),

                        InlineKeyboardButton(text="❌ Отказать", callback_data="decline_card")
                    ]
                ])

                await message.bot.send_photo(
                    chat_id=int(manager["id"]),
                    photo=photo.file_id,
                    caption=f"📸 Найден чек с картой `{card['card']}`\n",
                    reply_markup=buttons,
                    parse_mode="Markdown"
                )
                return  # остановимся на первом найденном



from services.json_writer import add_money_to_card

from aiogram.fsm.context import FSMContext
from services.json_writer import add_money_to_card


@router.callback_query(AcceptCardCallback.filter())
async def accept_card_callback(callback: CallbackQuery, callback_data: AcceptCardCallback, state: FSMContext):
    await state.set_state(AcceptMoney.waiting_for_sum)
    await state.update_data({
        "msg_id": callback_data.msg_id,
        "card_number": callback_data.card,
        "chat_id": callback_data.chat_id,  # можно брать отсюда
        "operator_id": callback.from_user.id
    })
    confirmed_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Статус: Оплачено", callback_data="noop")]
    ])
    await callback.message.edit_reply_markup(reply_markup=confirmed_markup)
    await callback.message.answer("Введите сумму для этой транзакции (в сомах):")
    await callback.answer()





@router.callback_query(F.data == "decline_card")
async def decline_card_callback(callback: CallbackQuery, state: FSMContext):
    confirmed_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Статус: Отказано", callback_data="noop")]
    ])
    await callback.message.edit_reply_markup(reply_markup=confirmed_markup)
    await callback.message.answer("❌ Операция отменена.")
    await state.clear()
    await callback.answer()

from services.json_writer import add_transaction, add_money_to_card


@router.message(AcceptMoney.waiting_for_sum)
async def finalize_transaction(message: Message, state: FSMContext):
    amount_text = message.text.strip()
    if not amount_text.isdigit():
        await message.answer("❗ Введите только число.")
        return

    amount = int(amount_text)
    data = await state.get_data()
    operator_id = data["operator_id"]
    card_number = data["card_number"]

    # Пополняем баланс карты
    print(add_money_to_card(operator_id, card_number, amount))

    # Добавляем транзакцию
    add_transaction(
        chat_id=abs(data["chat_id"]),
        msg_id=data["msg_id"],
        operator_id=operator_id,
        card_number=card_number,
        money=amount
    )

    # 🔍 Проверка лимита после пополнения
    from services.json_writer import (
        get_manager_cards,
        get_usdt_rate,
        get_settings,
        set_manager_status
    )

    cards = get_manager_cards(operator_id)
    total_fiat = sum(c["money"] for c in cards)
    rate = get_usdt_rate()
    total_usdt = round(total_fiat / rate, 2)
    limit = get_settings().get("limit", 800)

    if total_usdt >= limit:
        set_manager_status(operator_id, True)

        await message.bot.send_message(
            chat_id=operator_id,
            text=(
                f"🚫 <b>Ты превысил лимит</b>\n"
                f"💰 На картах: <b>{total_usdt:.2f} USDT</b>\n"
                f"🔰 Лимит: <b>{limit} USDT</b>\n"
            ),
            parse_mode="HTML"
        )

    await message.answer(f"✅ Зачислено {amount} сом на карту {card_number}")

    # Отправим сообщение в группу (опционально)
    await message.bot.send_message(
        chat_id=GROUP_ID,
        text=(
            f"✅ Транзакция подтверждена\n"
            f"📤 От: @{message.from_user.username or 'оператор'}\n"
            f"💳 Карта: {card_number}\n"
            f"💰 Сумма: {amount} сом\n"
            f"🧾 Чек: msg_id = {data['msg_id']}\n"
            f"🧾 Чат: chat_id = {data['chat_id']}"
        )
    )

    await state.clear()

