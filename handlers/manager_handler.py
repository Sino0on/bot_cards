from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from keyboards import get_keyboard_buttons
from services.json_writer import save_manager, edit_card_number, get_usdt_rate, add_group_withdraw_request, \
    deduct_from_card, get_user_by_id
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.json_writer import get_cards_for_manager
from services.send_application import notify_admin_about_request
from services.validators import check_admin

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
    await message.answer("Введите ID нового менеджера:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await state.set_state(AddManager.waiting_for_id)


@router.message(AddManager.waiting_for_id)
async def ask_for_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление менеджера отменено.",
                             reply_markup=get_keyboard_buttons(message.from_user.id))
        return
    text = message.text.strip()

    if not text.isdigit():
        await message.answer("❌ Пожалуйста, введите только числовой ID (только цифры).")
        return

    await state.update_data(manager_id=int(text))
    await message.answer("Теперь введите имя менеджера:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await state.set_state(AddManager.waiting_for_name)


@router.message(AddManager.waiting_for_name)
async def save_new_manager(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление менеджера отменено.",
                             reply_markup=get_keyboard_buttons(message.from_user.id))
        return
    user_data = await state.get_data()
    manager_id = user_data["manager_id"]
    name = message.text.strip()

    success = save_manager(manager_id, name)
    if success:
        await message.answer(f"✅ Менеджер {name} с ID {manager_id} добавлен!",reply_markup=get_keyboard_buttons(message.from_user.id))
    else:
        await message.answer("⚠️ Менеджер с таким ID уже существует.", reply_markup=get_keyboard_buttons(message.from_user.id))
    await state.clear()


from services.json_writer import find_manager_by_user_id, add_card_to_manager


@router.message(F.text == "💳 Добавить карту")
async def start_add_card(message: Message, state: FSMContext):
    manager = find_manager_by_user_id(message.from_user.id)
    if manager:
        await message.answer("Введите номер карты:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
        await state.set_state(AddCard.waiting_for_card_number)
    else:
        await message.answer("❌ Ты не зарегистрирован как менеджер.")


@router.message(AddCard.waiting_for_card_number)
async def save_card(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление карты отменена.",
                             reply_markup=get_keyboard_buttons(message.from_user.id))
        return
    card_number = message.text.strip()
    result = add_card_to_manager(message.from_user.id, card_number)

    if result is True:
        await message.answer(f"✅ Карта {card_number} добавлена.", reply_markup=get_keyboard_buttons(message.from_user.id))
    elif result is False:
        await message.answer("⚠️ Такая карта уже добавлена.", reply_markup=get_keyboard_buttons(message.from_user.id))
    else:
        await message.answer("❌ Ты не зарегистрирован как менеджер.", reply_markup=get_keyboard_buttons(message.from_user.id))
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
                    [
                        InlineKeyboardButton(text="🗑 Удалить карту", callback_data=f"delete_{card['card']}"),
                        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{card['card']}")
                    ]
                ])

                card_number = card['card']
                fiat_balance = card['money']
                settings = get_settings()
                usdt_balance = round(fiat_balance / settings['usdt_rate'], 2)  # пример курса 1 USDT = 89 сом

                # masked = f"{card_number[-4:]}"  # берём последние 4 цифры карты
                card_display = f"ZHE {card_number}"  # можно заменить ZHE на нужное название

                text = (
                    f"💳 <b>{card_display} KGS</b>\n"
                    f"🌐 ФИАТ: <b>{fiat_balance:.2f}</b>\n"
                    f"💵 USDT: <b>{usdt_balance:.2f}</b>"
                )

                await callback.message.answer(
                    text,
                    reply_markup=buttons,
                    parse_mode="HTML"
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


@router.message(F.text == "👨‍💼 Операторы")
async def operator_menu(message: Message):
    if not check_admin(message.from_user.id):
        await message.answer("⛔ У тебя нет доступа.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить оператора")],
            [KeyboardButton(text="❌ Удалить оператора")],
            [KeyboardButton(text="📋 Все операторы")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выбери действие с операторами:", reply_markup=kb)


from services.json_writer import load_data

@router.message(F.text == "📋 Все операторы")
async def list_operators_inline(message: Message):
    if not check_admin(message.from_user.id):
        return

    data = load_data()
    if not data["managers"]:
        await message.answer("Список операторов пуст.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{m['name']} ({m['id']})", callback_data=f"opmenu_{m['id']}")]
        for m in data["managers"]
    ])
    await message.answer("Выбери оператора для управления реквизитами:", reply_markup=kb)



from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from services.json_writer import delete_manager_by_id

@router.message(F.text == "❌ Удалить оператора")
async def choose_operator_to_delete(message: Message):
    data = load_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{m['name']} ({m['id']})", callback_data=f"delmgr_{m['id']}")]
        for m in data["managers"]
    ])
    await message.answer("Выбери оператора для удаления:", reply_markup=kb)


@router.callback_query(F.data.startswith("delmgr_"))
async def delete_operator(callback: CallbackQuery):
    operator_id = callback.data.split("_")[1]
    success = delete_manager_by_id(operator_id)

    if success:
        await callback.message.answer(f"✅ Оператор {operator_id} удалён.")
    else:
        await callback.message.answer("❌ Ошибка удаления.")
    await callback.answer()


@router.callback_query(F.data.startswith("opmenu_"))
async def operator_menu_rekvizit(callback: CallbackQuery, state: FSMContext):
    operator_id = callback.data.split("_")[1]
    await state.set_data({"selected_operator_id": operator_id})

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Карты (реквизиты)", callback_data=f"op_cards:{operator_id}")],
        [InlineKeyboardButton(text="➕ Добавить карту", callback_data=f"op_add_card:{operator_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_home")]
    ])
    await callback.message.answer(f"Оператор ID: {operator_id}", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("op_cards:"))
async def show_operator_cards(callback: CallbackQuery, state: FSMContext):
    operator_id = callback.data.split(':')[-1]

    manager = find_manager_by_user_id(int(operator_id))
    if not manager:
        await callback.message.answer("❌ Оператор не найден.")
        return

    if not manager["cards"]:
        await callback.message.answer("У этого оператора нет карт.")
        return

    text = f"💳 Реквизиты оператора {manager['name']}:\n\n"
    for idx, card in enumerate(manager["cards"], 1):
        text += f"{idx}. {card['card']} — {card['money']} сом\n"

    await callback.message.answer(text)
    await callback.answer()


class EditCardFSM(StatesGroup):
    waiting_for_new_number = State()


@router.callback_query(F.data.startswith("edit_"))
async def edit_card(callback: CallbackQuery, state: FSMContext):
    card_number = callback.data.split("_")[1]
    await state.set_data({"old_card_number": card_number})
    await state.set_state(EditCardFSM.waiting_for_new_number)

    await callback.message.answer(f"Введите новый номер для карты `{card_number}`:", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await callback.answer()



@router.message(EditCardFSM.waiting_for_new_number)
async def save_new_card_number(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление новой карты отменена.",
                             reply_markup=get_keyboard_buttons(message.from_user.id))
        return
    new_card = message.text.strip()
    data = await state.get_data()
    old_card = data["old_card_number"]
    user_id = message.from_user.id

    if not new_card.isdigit():
        await message.answer("❗ Введите только цифры.")
        return

    success = edit_card_number(user_id, old_card, new_card)
    if success:
        await message.answer(f"✅ Карта обновлена: {old_card} → {new_card}", reply_markup=get_keyboard_buttons(message.from_user.id))
    else:
        await message.answer("❌ Не удалось обновить карту.", reply_markup=get_keyboard_buttons(message.from_user.id))
    await state.clear()



@router.callback_query(F.data == 'back_to_home')
async def back_to_home(callback: CallbackQuery, state: FSMContext):
    print(callback.from_user.id)
    user = find_manager_by_user_id(callback.from_user.id)
    print(user)
    if user:
        await callback.message.answer(
            f'Здравствуй {user["name"]}', reply_markup=get_keyboard_buttons(callback.message.from_user.id)
        )
        return
    await callback.message.answer(
        'Давай',
        # reply_markup=get_contact_button(),
    )
    # await state.set_state(Registration.waiting_for_contact)


@router.message(F.text == "🔙 Назад")
async def back_to_home_m(message: Message):
    print(message.from_user.id)
    user = find_manager_by_user_id(message.from_user.id)
    print(user)
    if user:
        await message.answer(
            f'Здравствуй, {user["name"]}', reply_markup=get_keyboard_buttons(message.from_user.id)
        )
        return
    await message.answer(
        'Давай',
        # reply_markup=get_contact_button(),
    )
    # await state.set_state(Registration.waiting_for_contact)


from datetime import datetime, timedelta


@router.message(F.text == "📄 Мои транзакции")
async def my_transactions(message: Message):
    from services.json_writer import get_transactions_by_operator
    transactions = get_transactions_by_operator(message.from_user.id)

    if not transactions:
        await message.answer("У тебя пока нет транзакций.")
        return

    text = "📄 Твои транзакции:\n\n"
    total = 0

    for tx in transactions:
        total += tx["amount"]
        time = datetime.fromisoformat(tx["timestamp"]).strftime("%d.%m %H:%M")
        text += (
            f"🕒 {time}\n"
            f"💬 {tx['chat_name']}\n"
            f"💳 {tx['card']}\n"
            f"💰 {tx['amount']} сом\n\n"
        )

    text += f"🧮 Итого: {total} сом"
    await message.answer(text)


from services.json_writer import get_settings, get_cards_for_manager
from aiogram import types
from aiogram.types import Message

@router.message(F.text == "💼 Баланс карт")
async def show_balance_summary(message: Message):
    settings = get_settings()
    limit = settings.get("limit", 800.0)
    usdt_rate = get_usdt_rate()

    cards = get_cards_for_manager(message.from_user.id)
    if not cards:
        await message.answer("У тебя пока нет ни одной карты.")
        return

    total_usdt = 0
    card_lines = []

    for card in cards:
        card_number = card["card"]
        fiat = card["money"]
        usdt = round(fiat / usdt_rate, 2)
        total_usdt += usdt

        # masked = f"{card_number[-4:]}"
        card_display = f"ZHE *{card_number}"

        card_lines.append(
            f"💳 {card_display} KGS\n"
            f"   🌐 ФИАТ: {fiat:.2f}\n"
            f"   💵 USDT: {usdt:.2f}"
        )

    remaining = round(limit - total_usdt, 2)

    text = (
        f"🔰 <b>Лимит:</b> {limit:.2f} USDT\n\n"
        f"🧩 <b>Фиатные счета:</b>\n"
        + "\n\n".join(card_lines) +
        "\n\n📊 <b>Итого:</b>\n"
        f"   💵 USDT: {total_usdt:.2f}\n"
        f"   🔰 Лимит: {remaining:.2f}"
    )
    reply_markup = InlineKeyboardMarkup(
        # inline_keyboard=[
        #     [InlineKeyboardButton(text="🔁 Закончить круг", callback_data="finish_round")]
        # ]
    )
    await message.answer(text, parse_mode="HTML", reply_markup=reply_markup)


@router.callback_query(F.data == "finish_round")
async def handle_finish_round(callback: CallbackQuery):
    from services.json_writer import (
        get_manager_cards,
        get_settings,
        create_round_request,
        clear_cards_balance
    )

    operator_id = callback.from_user.id
    cards = get_manager_cards(operator_id)
    total_fiat = sum(c["money"] for c in cards)

    if total_fiat <= 0:
        await callback.message.answer("❗ Невозможно создать заявку — баланс всех карт равен 0.")
        await callback.answer()
        return

    # Курс
    settings = get_settings()
    usdt_rate = settings.get("usdt_rate", 89)
    ltc_rate = settings.get("ltc_rate", 86.05)
    address = settings.get("address", "—")
    deadline = datetime.now() + timedelta(hours=2)

    total_usd = round(total_fiat / usdt_rate, 2)
    total_ltc = round(total_usd / ltc_rate, 8)

    # Списываем с карт
    clear_cards_balance(operator_id)

    # Создаём заявку
    request_id = create_round_request(
        operator_id=operator_id,
        usd=total_usd,
        ltc=total_ltc,
        address=address,
        deadline=deadline
    )
    request_data = {
        "operator_id": operator_id,
        "usd": total_usd,
        "ltc": total_ltc,
        "address": address,
        "deadline": deadline
    }
    await notify_admin_about_request(callback.bot, request_data, request_id)
    await callback.message.answer(
        f"🧾 Заявка №{request_id}\n\n"
        f"💵 Сумма в USD: {total_usd} $\n"
        f"🪙 Сумма в LTC: {total_ltc} LTC\n\n"
        f"📬 Адрес для перевода:\n`{address}`\n\n"
        f"⏳ Действителен до: {deadline.strftime('%d %B %Y, %H:%M')}",
        parse_mode="Markdown"
    )

    await callback.answer()


@router.message(F.text == "💰 Мой баланс")
async def show_operator_balance(message: Message):
    from services.json_writer import get_operator_bonus_balance

    balance = get_operator_bonus_balance(message.from_user.id)

    await message.answer(f"💰 Баланс: ${balance:.2f}")


@router.message(Command("b"))
async def group_balance_report(message: Message):
    print(message.chat.id)
    print(message.chat.type)
    if not message.chat or message.chat.type not in ["group", "supergroup"]:
        await message.answer("❗ Эта команда работает только в группе.")
        return

    from services.json_writer import get_chat_by_id, get_settings
    chat_id = message.chat.id
    if '100' in str(chat_id):
        chat_id = abs(int(str(abs(chat_id))[3:]))
    print(chat_id)
    group = get_chat_by_id(abs(chat_id))

    if not group:
        await message.answer("❗ Эта группа не зарегистрирована в системе.")
        return

    transactions = group.get("transactions", [])
    if not transactions:
        await message.answer("📭 Пока нет активных транзакций.")
        return

    settings = get_settings()
    rate = settings.get("usdt_rate", 89)

    # 1. Формируем список
    total_kgs = 0
    operator_map = {}  # {op_id: [list of tx]}

    for tx in transactions:
        op_id = tx["operator"]
        operator_map.setdefault(op_id, []).append(tx)
        total_kgs += tx["money"]

    lines = []
    for op_id, txs in operator_map.items():
        # user_tag = f"<a href='tg://user?id={op_id}'>оператор {op_id}</a>"
        lines.append(f"🔺 Отчёт:")
        for tx in txs:
            ts = tx["timestamp"]

            # преобразование
            dt = datetime.fromisoformat(ts)
            formatted = dt.strftime("%d.%m.%Y %H:%M")
            ts = formatted
            amount = tx["money"]
            card = tx.get("card", "****")
            lines.append(f"🔷 ({ts}) {amount} KGS ✅ (💳 {card})")
        lines.append("")

    # 2. Итоги
    data = load_data()
    procent = data.get("settings", {}).get("procent", 12)
    usd = round(total_kgs / rate, 2)
    company_cut = round(usd * procent / 100, 2)

    final_usd = round(usd - company_cut, 2)

    lines.append(f"📊 <b>Общая сумма: {total_kgs} KGS</b>")
    lines.append(f"🧾 ({len(transactions)} инвойсов)")
    lines.append("")
    lines.append(f"{total_kgs} / {rate} = <b>{usd} USD</b>")
    lines.append(f"{usd} - {procent}% = <b>{final_usd} USD</b>")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Вывод готов", callback_data=f"group_withdraw:{chat_id}")]
    ])

    await message.answer("\n".join(lines), reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("group_withdraw:"))
async def handle_group_withdraw(callback: CallbackQuery):
    from services.json_writer import (
        get_chat_by_id,
        update_chat,
        get_settings,
        credit_operator_bonus
    )


    chat_id = int(callback.data.split(":")[1])
    print(chat_id)
    chat = get_chat_by_id(chat_id)

    if not chat:
        await callback.answer("❗ Группа не найдена", show_alert=True)
        return

    transactions = chat.get("transactions", [])
    if not transactions:
        await callback.answer("❗ Нет активных транзакций", show_alert=True)
        return

    settings = get_settings()
    rate = settings.get("usdt_rate", 89)

    # Считаем общую сумму
    total_kgs = sum(tx["money"] for tx in transactions)
    procent = settings.get("procent", 12)  # комиссия компании
    procent_bonus = settings.get("procent_bonus", 6)  # бонус оператору
    rate = settings.get("usdt_rate", 89)

    # Переводим в USD
    usd = round(total_kgs / rate, 2)

    # Считаем, сколько забирает компания
    company_cut = round(usd * (procent / 100), 2)

    # Сумма после комиссии
    final_usd = round(usd - company_cut, 2)

    # Считаем бонус оператору
    operator_bonus_total = round(usd * (procent_bonus / 100), 8)

    # Начислим 6% операторам
    operator_map = {}
    for tx in transactions:
        op_id = tx["operator"]
        operator_map.setdefault(op_id, 0)
        operator_map[op_id] += tx["money"]

    operator_map2 = {}  # {op_id: [list of tx]}

    for tx in transactions:
        op_id = tx["operator"]
        operator_map2.setdefault(op_id, []).append(tx)
        total_kgs += tx["money"]
    lines = []
    for op_id, txs in operator_map2.items():
        print(txs)
        user = get_user_by_id(op_id)
        user_tag = f"<a href='tg://user?username={user['name']}'>оператор {user['name']}</a>"
        lines.append(f"🔺 Отчёт: {user_tag}")
        for tx in txs:
            ts = tx["timestamp"]

            # преобразование
            dt = datetime.fromisoformat(ts)
            formatted = dt.strftime("%d.%m.%Y %H:%M")
            ts = formatted
            amount = tx["money"]
            card = tx.get("card", "****")
            lines.append(f"🔷 ({ts}) {amount} KGS ✅ (💳 {card})")
        lines.append("")

    # 2. Итоги
    data = load_data()
    procent = data.get("settings", {}).get("procent", 12)
    usd = round(total_kgs / rate, 2)
    company_cut = round(usd * procent / 100, 2)

    final_usd = round(usd - company_cut, 2)

    lines.append(f"📊 <b>Общая сумма: {total_kgs} KGS</b>")
    lines.append(f"🧾 ({len(transactions)} инвойсов)")
    lines.append("")
    lines.append(f"{total_kgs} / {rate} = <b>{usd} USD</b>")
    lines.append(f"{usd} - {procent}% = <b>{final_usd} USD</b>")
    lines.append(f"\n\nИз чата - {chat['name']}")
    await callback.bot.send_message(chat_id=-4899834369, text=lines)
    total_operator_kgs = sum(operator_map.values())

    for op_id, kgs in operator_map.items():
        share = kgs / total_operator_kgs
        bonus = round(operator_bonus_total * share, 8)
        credit_operator_bonus(op_id, bonus)

        try:
            await callback.bot.send_message(
                chat_id=op_id,
                text=f"💸 Баланс пополнен на ${bonus}"
            )
        except Exception:
            pass
    # Отправим каждому оператору инструкции по переводу средств
    address = settings.get("address", "LTC_ADDRESS_NOT_SET")

    operator_transactions = {}
    for tx in transactions:
        op_id = tx["operator"]
        operator_transactions.setdefault(op_id, []).append(tx)

    for op_id, txs in operator_transactions.items():
        lines = ["📬 *Переведите средства по следующим картам:*"]

        for tx in txs:
            dt = datetime.fromisoformat(tx["timestamp"]).strftime("%d.%m.%Y %H:%M")
            card = tx.get("card", "****")
            amount = tx["money"]
            lines.append(f"💳 Карта *...{card[-4:]}* — {amount} KGS ({dt})")

        usd_total = round(sum(tx["money"] for tx in txs) / rate, 2)

        lines.append("")
        lines.append(f"💵 *Итого к отправке:* {usd_total} USD")
        lines.append(f"📥 *Адрес для перевода:*\n`{address}`")

        try:
            await callback.bot.send_message(
                chat_id=op_id,
                text="\n".join(lines),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❌ Ошибка при отправке сообщения оператору {op_id}: {e}")

    # Перемещаем в old_transactions
    chat.setdefault("old_transactions", []).extend(transactions)
    chat["transactions"] = []

    for tx in transactions:
        print(tx)
        deduct_from_card(user_id=tx["operator"], card_number=tx["card"], amount=tx["money"])
    update_chat(chat_id, chat)

    # Готовим данные для записи заявки
    operator_bonuses = {}
    for op_id, kgs in operator_map.items():
        share = kgs / total_operator_kgs
        bonus = round(operator_bonus_total * share, 8)
        operator_bonuses[op_id] = (kgs, bonus)

    # Записываем заявку
    add_group_withdraw_request(
        chat_id=chat["id"],
        chat_name=chat.get("name", "Unknown"),
        transactions=transactions,
        rate=rate,
        company_cut=company_cut,
        operator_bonuses=operator_bonuses,
        final_usd=final_usd
    )

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Вывод завершён.</b>\n📦 Баланс очищен.",
        parse_mode="HTML"
    )

    await callback.answer("✅ Вывод готов. Заявка зафиксирована.")


@router.message(Command("r"))
async def show_registered_cards(message: Message):
    from services.json_writer import get_chat_by_id, get_formatted_cards

    chat_id = message.chat.id
    chat = get_chat_by_id(chat_id)

    if not chat:
        await message.answer("❌ Этот чат не зарегистрирован.")
        return

    operators = chat.get("managers", [])
    if not operators:
        await message.answer("ℹ️ В этом чате нет зарегистрированных операторов.")
        return

    text = f"📋 Зарегистрированные карты в чате *{chat.get('name', '—')}*:\n\n"

    for op_id in operators:
        cards = get_formatted_cards(op_id)
        if cards:
            text += f"👤 {op_id}\n"
            for c in cards:
                text += f"  • 💳 {c}*\n"
            text += "\n"
        # else:
            # text += f"👤 <code>{op_id}</code>\n  • 🚫 Нет карт\n\n"

    await message.answer(text, parse_mode="Markdown")

