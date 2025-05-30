from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from services.json_writer import save_manager
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.json_writer import get_cards_for_manager


router = Router()

# Шаги состояния
class AddManager(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()


class AddCard(StatesGroup):
    waiting_for_card_number = State()


class AcceptMoney(StatesGroup):
    waiting_for_sum = State()


# Клавиатура
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧠 Добавить менеджера")]
    ],
    resize_keyboard=True
)

@router.message(F.text == "🧠 Добавить менеджера")
async def ask_for_id(message: Message, state: FSMContext):
    await message.answer("Введите ID нового менеджера:")
    await state.set_state(AddManager.waiting_for_id)


@router.message(AddManager.waiting_for_id)
async def ask_for_name(message: Message, state: FSMContext):
    text = message.text.strip()

    if not text.isdigit():
        await message.answer("❌ Пожалуйста, введите только числовой ID (только цифры).")
        return

    await state.update_data(manager_id=int(text))
    await message.answer("Теперь введите имя менеджера:")
    await state.set_state(AddManager.waiting_for_name)


@router.message(AddManager.waiting_for_name)
async def save_new_manager(message: Message, state: FSMContext):
    user_data = await state.get_data()
    manager_id = user_data["manager_id"]
    name = message.text.strip()

    success = save_manager(manager_id, name)
    if success:
        await message.answer(f"✅ Менеджер {name} с ID {manager_id} добавлен!")
    else:
        await message.answer("⚠️ Менеджер с таким ID уже существует.")
    await state.clear()


from services.json_writer import find_manager_by_user_id, add_card_to_manager


@router.message(F.text == "💳 Добавить карту")
async def start_add_card(message: Message, state: FSMContext):
    manager = find_manager_by_user_id(message.from_user.id)
    if manager:
        await message.answer("Введите номер карты:")
        await state.set_state(AddCard.waiting_for_card_number)
    else:
        await message.answer("❌ Ты не зарегистрирован как менеджер.")


@router.message(AddCard.waiting_for_card_number)
async def save_card(message: Message, state: FSMContext):
    card_number = message.text.strip()
    result = add_card_to_manager(message.from_user.id, card_number)

    if result is True:
        await message.answer(f"✅ Карта {card_number} добавлена.")
    elif result is False:
        await message.answer("⚠️ Такая карта уже добавлена.")
    else:
        await message.answer("❌ Ты не зарегистрирован как менеджер.")
    await state.clear()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.message(F.text == "💳 Мои карты")
async def show_my_cards(message: Message):
    cards = get_cards_for_manager(message.from_user.id)
    if cards is None:
        await message.answer("❌ Ты не зарегистрирован как менеджер.")
        return

    if not cards:
        await message.answer("У тебя пока нет карт.")
        return

    # Ручная сборка разметки по 2 кнопки в ряд
    keyboard = []
    row = []

    for idx, card in enumerate(cards):
        button = InlineKeyboardButton(
            text=f"💳 {card['card']}",
            callback_data=f"card_{card['card']}"
        )
        row.append(button)

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:  # если осталась последняя кнопка
        keyboard.append(row)

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer("Твои карты:", reply_markup=markup)



@router.callback_query(F.data.startswith("card_"))
async def show_card_info(callback: CallbackQuery):
    card_number = callback.data.split("_")[1]
    cards = get_cards_for_manager(callback.from_user.id)

    if cards:
        for card in cards:
            if card["card"] == card_number:
                buttons = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🗑 Удалить карту",
                        callback_data=f"delete_{card_number}"
                    )]
                ])
                await callback.message.answer(
                    f"💳 Карта: ...{card['card']}\n💰 Баланс: {card['money']} сом",
                    reply_markup = buttons
                )
                await callback.answer()
                return

    await callback.answer("Карта не найдена", show_alert=True)


from services.json_writer import delete_card_for_manager

@router.callback_query(F.data.startswith("delete_"))
async def delete_card(callback: CallbackQuery):
    card_number = callback.data.split("_")[1]
    success = delete_card_for_manager(callback.from_user.id, card_number)

    if success:
        await callback.message.answer(f"🗑 Карта {card_number} удалена.")
    else:
        await callback.message.answer("❌ Не удалось удалить карту.")
    await callback.answer()
