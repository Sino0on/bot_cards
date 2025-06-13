from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from decouple import config

from keyboards import get_keyboard_buttons
from services.json_writer import save_manager, edit_card_number, load_data, get_all_chats, toggle_chat_status, \
    delete_chat, get_chat_status, update_request_status, get_request_by_id, credit_operator_bonus, set_operator_active, \
    update_procent, update_procent_bonus, update_address_set, save_data
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.json_writer import get_cards_for_manager
from services.validators import check_admin

router = Router()



class AdminCreateChatFSM(StatesGroup):
    waiting_for_chat_id = State()
    waiting_for_chat_title = State()

class AddOperatorFSM(StatesGroup):
    choosing_chat = State()
    selecting_operator = State()





@router.message(F.text == "💬 Чаты")
async def admin_chats_menu(message: Message):
    if not check_admin(message.from_user.id):
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить чат")],
            [KeyboardButton(text="➕ Добавить оператора в чат")],
            [KeyboardButton(text="➖ Удалить оператора из чата")],
            [KeyboardButton(text="📋 Список чатов")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer("Управление чатами:", reply_markup=kb)


@router.message(F.text == "➕ Добавить чат")
async def add_chat_start(message: Message, state: FSMContext):
    await message.answer("Введи ID группы (без -100 в начале):", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await state.set_state(AdminCreateChatFSM.waiting_for_chat_id)


@router.message(AdminCreateChatFSM.waiting_for_chat_id)
async def add_chat_id(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление нового чата отменена.",
                             reply_markup=get_keyboard_buttons(message.from_user.id))
        return
    if not message.text.strip().isdigit():
        await message.answer("❗ Введи только числа.")
        return
    await state.update_data(chat_id=int(message.text.strip()))
    await message.answer("Теперь введи название чата:")
    await state.set_state(AdminCreateChatFSM.waiting_for_chat_title)


from services.json_writer import add_chat  # мы его уже писали выше

@router.message(AdminCreateChatFSM.waiting_for_chat_title)
async def add_chat_title(message: Message, state: FSMContext):
    data = await state.get_data()
    success = add_chat(data["chat_id"], message.text.strip())
    if success:
        await message.answer("✅ Чат добавлен.", reply_markup=get_keyboard_buttons(message.from_user.id))
    else:
        await message.answer("⚠️ Такой чат уже существует.", reply_markup=get_keyboard_buttons(message.from_user.id))
    await state.clear()


@router.message(F.text == "➕ Добавить оператора в чат")
async def start_add_operator(message: Message, state: FSMContext):
    from services.json_writer import get_chats_with_names

    buttons = [
        [KeyboardButton(text=chat["name"])] for chat in get_chats_with_names()

    ]
    buttons.append([KeyboardButton(text="❌ Отмена")])

    markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await message.answer("Выберите чат, в который хотите добавить оператора:", reply_markup=markup)
    await state.set_state(AddOperatorFSM.choosing_chat)



@router.message(AddOperatorFSM.choosing_chat)
async def choose_chat(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменена.",
                             reply_markup=get_keyboard_buttons(message.from_user.id))
        return

    from services.json_writer import get_chat_by_name, get_all_managers
    chat = get_chat_by_name(message.text.strip())

    if not chat:
        await message.answer("❌ Чат не найден. Попробуйте снова.")
        return

    await state.update_data(chat_id=chat["id"], chat_name=chat["name"])

    # Показываем список операторов
    buttons = []
    for m in get_all_managers():
        name = m.get("name", f"ID {m['id']}")
        buttons.append([KeyboardButton(text=f"{name} ({m['id']})")])

    buttons.append([KeyboardButton(text="✅ Готово"), KeyboardButton(text="❌ Отмена")])
    markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await message.answer("Выберите операторов, которых хотите добавить в чат:", reply_markup=markup)
    await state.set_state(AddOperatorFSM.selecting_operator)




from services.json_writer import assign_operators_to_chat  # создадим

@router.message(AddOperatorFSM.selecting_operator)
async def select_operator_to_add(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменена.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return

    if message.text == "✅ Готово":
        await state.clear()
        await message.answer("✅ Добавление завершено.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return

    try:
        operator_id = int(message.text.strip().split("(")[-1].replace(")", ""))
    except:
        await message.answer("❗ Неверный формат. Выберите из списка.")
        return

    data = await state.get_data()
    from services.json_writer import add_operator_to_chat

    success = add_operator_to_chat(chat_id=data["chat_id"], operator_id=operator_id)
    if success:
        await message.answer(f"✅ Оператор {operator_id} добавлен в чат.")
    else:
        await message.answer("⚠️ Уже добавлен.")




# @router.message(F.text == "📋 Список чатов")
# async def show_chats(message: Message):
#     data = load_data()
#     if not data.get("chats"):
#         await message.answer("Нет чатов.")
#         return
#
#     text = "📋 Чаты:\n\n"
#     for chat in data["chats"]:
#         text += f"💬 {chat['name']} (ID: {chat['id']})\n"
#         text += "👥 Операторы: " + ", ".join(str(m) for m in chat.get("managers", [])) + "\n\n"
#
#     await message.answer(text)

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@router.message(F.text == "📋 Список чатов")
async def show_chats_buttons(message: Message):
    chats = get_all_chats()
    if not chats:
        await message.answer("📭 Нет добавленных чатов.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{c['name']} ({'✅' if c.get('status', True) else '❌'})",
                callback_data=f"chat_{c['id']}"
            )]
            for c in chats
        ]
    )

    await message.answer("Выбери чат для управления:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("chat_"))
async def manage_single_chat(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[1])
    status = get_chat_status(chat_id)

    from services.json_writer import load_data
    from collections import defaultdict

    data = load_data()
    chat = next((c for c in data["chats"] if c["id"] == chat_id), None)

    text = f"💬 Управление чатом ID: {chat_id}\n\n"

    txs = chat.get("transactions", []) if chat else []
    if not txs:
        text += "📭 В этом чате нет активных транзакций."
    else:
        by_operator = defaultdict(lambda: defaultdict(list))
        for tx in txs:
            by_operator[tx["operator"]][tx.get("card", "****")].append(tx)

        total_kgs = 0
        for op_id, cards in by_operator.items():
            manager = next((m for m in data["managers"] if m["id"] == op_id), {})
            op_name = manager.get("name", f"ID {op_id}")
            text += f"🧾 Международные переводы {op_name}\n"
            for card, tx_list in cards.items():
                text += f"💳 {card}\n"
                for tx in tx_list:
                    dt = tx.get("timestamp", "—")
                    amt = tx["money"]
                    total_kgs += amt
                    text += f"🔹 ({dt}) {amt} KGS ✅\n"
            text += "\n"

        rate = data.get("settings", {}).get("usdt_rate", 89)
        procent = data.get("settings", {}).get("procent", 12)
        usd = round(total_kgs / rate, 2)
        after_fee = round(usd * (1 - procent / 100), 2)

        text += f"📑 Общая сумма KGS: {total_kgs} KGS\n"
        text += f"🧾 ({len(txs)} инвойсов)\n\n"
        text += f"{total_kgs} / {rate} = {usd}\n"
        text += f"{usd} - {procent}% = {after_fee}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить операторов", callback_data=f"editop_{chat_id}")],
        [InlineKeyboardButton(
            text="🔴 Выключить" if status else "🟢 Включить",
            callback_data=f"toggle_{chat_id}"
        )],
        [InlineKeyboardButton(text="🗑 Удалить чат", callback_data=f"delchat_{chat_id}")]
    ])

    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()



@router.callback_query(F.data.startswith("toggle_"))
async def toggle_status(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[1])
    new_status = toggle_chat_status(chat_id)
    if new_status is not None:
        status_text = "🟢 включен" if new_status else "🔴 выключен"
        await callback.message.answer(f"Чат теперь {status_text}.")
    else:
        await callback.message.answer("❌ Чат не найден.")
    await callback.answer()


@router.callback_query(F.data.startswith("delchat_"))
async def delete_chat_handler(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[1])
    success = delete_chat(chat_id)
    if success:
        await callback.message.answer("🗑 Чат удалён.")
    else:
        await callback.message.answer("❌ Не удалось удалить чат.")
    await callback.answer()


@router.message(F.text == "📊 Балансы")
async def admin_balance_menu(message: Message):
    if not check_admin(message.from_user.id):
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Баланс по операторам")],
            [KeyboardButton(text="💬 Баланс по чатам")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выбери тип баланса:", reply_markup=kb)


@router.message(F.text == "👥 Баланс по операторам")
async def balance_operators(message: Message):
    from services.json_writer import get_operators_balances
    results = get_operators_balances()

    if not results:
        await message.answer("Нет операторов.")
        return

    text = "👥 Балансы операторов:\n\n"
    for op in results:
        text += f"{op['name']} ({op['id']}): {op['balance']} сом\n"

    await message.answer(text)


@router.message(F.text == "💬 Баланс по чатам")
async def balance_chats(message: Message):
    from services.json_writer import get_chats_balances
    results = get_chats_balances()

    if not results:
        await message.answer("Нет чатов.")
        return

    text = "💬 Балансы чатов:\n\n"
    for ch in results:
        text += f"{ch['name']} ({ch['id']}): {ch['balance']} сом\n"

    await message.answer(text)

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@router.message(F.text == "🧾 История по операторам")
async def select_operator_for_history(message: Message):
    from services.json_writer import load_data
    data = load_data()

    if not data.get("managers"):
        await message.answer("Нет операторов.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{m['name']} ({m['id']})", callback_data=f"txhistory_{m['id']}")]
            for m in data["managers"]
        ]
    )

    await message.answer("Выбери оператора для просмотра истории:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("txhistory_"))
async def show_operator_report_options(callback: CallbackQuery):
    operator_id = callback.data.split("_")[1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📆 Сегодня", callback_data=f"txrange_{operator_id}_1")],
        [InlineKeyboardButton(text="📅 Последние 7 дней", callback_data=f"txrange_{operator_id}_7")],
        [InlineKeyboardButton(text="🗓️ Последние 30 дней", callback_data=f"txrange_{operator_id}_30")]
    ])
    await callback.message.answer(f"Выбери период для отчёта по оператору {operator_id}:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("txrange_"))
async def report_by_date(callback: CallbackQuery):
    parts = callback.data.split("_")
    operator_id = int(parts[1])
    days = int(parts[2])

    from services.json_writer import get_transactions_by_operator
    txs = get_transactions_by_operator(operator_id, days=days)

    if not txs:
        await callback.message.answer("❌ За выбранный период нет транзакций.")
        await callback.answer()
        return

    text = f"🧾 Транзакции за {days} дн. по оператору {operator_id}:\n\n"
    total = 0

    for tx in txs:
        total += tx["amount"]
        time = datetime.fromisoformat(tx["timestamp"]).strftime("%d.%m %H:%M")
        text += f"🕒 {time}\n💬 {tx['chat_name']}\n💳 {tx['card']}\n💰 {tx['amount']} сом\n\n"

    text += f"🧮 Итого: {total} сом"
    await callback.message.answer(text)
    await callback.answer()


from aiogram.fsm.state import State, StatesGroup

class SettingsFSM(StatesGroup):
    waiting_for_address = State()
    waiting_for_address_set = State()
    waiting_for_limit = State()
    waiting_for_bonus = State()
    waiting_for_bonus_procent = State()
    waiting_for_usdt_rate = State()


from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from services.json_writer import get_settings

@router.message(F.text == "⚙️ Настройки системы")
async def settings_menu(message: types.Message):
    settings = get_settings()
    address = settings.get("address", "—")
    address_set = settings.get("address_set", "—")
    limit = settings.get("limit", "—")
    usdt_rate = settings.get("usdt_rate", "—")
    procent = settings.get("procent", "—")
    bonus = settings.get("procent_bonus", "—")

    text = (
        f"⚙️ <b>Текущие настройки</b>:\n"
        f"🏦 Адрес: <code>{address}</code>\n"
        f"🏦 Сеть: <code>{address_set}</code>\n"
        f"💰 Лимит: {limit} USD\n"
        f"💰 Курс: {usdt_rate} \n"
        f"💱 Процент: {procent}%\n"
        f"💰 Процент бонуса: {bonus}%\n\n"
        f"Выберите, что хотите изменить:"
    )

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Изменить адрес")],
            [KeyboardButton(text="✏️ Изменить лимит")],
            [KeyboardButton(text="✏️ Изменить процент")],
            [KeyboardButton(text="✏️ Изменить процент бонуса")],
            [KeyboardButton(text="💱 Изменить курс USDT")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

    await message.answer(text, reply_markup=kb, parse_mode="HTML")



from services.json_writer import update_address

@router.message(F.text == "✏️ Изменить адрес")
async def change_address(message: types.Message, state: FSMContext):
    await message.answer("Введите новый адрес:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await state.set_state(SettingsFSM.waiting_for_address)

@router.message(SettingsFSM.waiting_for_address)
async def save_address(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return

    update_address(message.text.strip())
    # await state.clear()
    await state.set_state(SettingsFSM.waiting_for_address_set)
    await message.answer("Введите сеть крипты:", reply_markup=get_keyboard_buttons(message.from_user.id))


@router.message(SettingsFSM.waiting_for_address_set)
async def save_address(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return

    update_address_set(message.text.strip())
    await state.clear()
    await message.answer("✅ Адрес обновлён.", reply_markup=get_keyboard_buttons(message.from_user.id))



from services.json_writer import update_limit

@router.message(F.text == "✏️ Изменить лимит")
async def change_limit(message: types.Message, state: FSMContext):
    await message.answer("Введите новый лимит (число):", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await state.set_state(SettingsFSM.waiting_for_limit)

@router.message(SettingsFSM.waiting_for_limit)
async def save_limit(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return

    try:
        new_limit = float(message.text.strip())
    except ValueError:
        await message.answer("❗ Введите корректное число.")
        return

    update_limit(new_limit)
    await state.clear()
    await message.answer(f"✅ Лимит обновлён до {new_limit} USDT.", reply_markup=get_keyboard_buttons(message.from_user.id))


@router.message(F.text == "✏️ Изменить процент")
async def change_limit(message: types.Message, state: FSMContext):
    await message.answer("Введите новый процент (число):", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await state.set_state(SettingsFSM.waiting_for_bonus)

@router.message(SettingsFSM.waiting_for_bonus)
async def save_limit(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return

    try:
        new_limit = float(message.text.strip())
    except ValueError:
        await message.answer("❗ Введите корректное число.")
        return

    update_procent(new_limit)
    await state.clear()
    await message.answer(f"✅ Процент обновлён до {new_limit}%.", reply_markup=get_keyboard_buttons(message.from_user.id))



@router.message(F.text == "✏️ Изменить процент бонуса")
async def change_limit(message: types.Message, state: FSMContext):
    await message.answer("Введите новый процент бонуса (число):", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await state.set_state(SettingsFSM.waiting_for_bonus_procent)

@router.message(SettingsFSM.waiting_for_bonus_procent)
async def save_limit(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return

    try:
        new_limit = float(message.text.strip())
    except ValueError:
        await message.answer("❗ Введите корректное число.")
        return

    update_procent_bonus(new_limit)
    await state.clear()
    await message.answer(f"✅ Процент бонуса обновлён до {new_limit}%.", reply_markup=get_keyboard_buttons(message.from_user.id))


@router.message(F.text == "💱 Изменить курс USDT")
async def change_usdt_rate(message: Message, state: FSMContext):
    await message.answer("Введите новый курс USDT:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await state.set_state(SettingsFSM.waiting_for_usdt_rate)

@router.message(SettingsFSM.waiting_for_usdt_rate)
async def save_usdt_rate(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return

    try:
        rate = float(message.text.strip())
    except ValueError:
        await message.answer("❗ Введите корректное число.")
        return

    from services.json_writer import update_usdt_rate
    update_usdt_rate(rate)

    await state.clear()
    await message.answer(f"✅ Курс USDT обновлён: {rate}", reply_markup=get_keyboard_buttons(message.from_user.id))


@router.callback_query(F.data.startswith("approve_request:"))
async def approve_request(callback: CallbackQuery):
    request_id = int(callback.data.split(":")[1])
    req = get_request_by_id(request_id)

    if not req or req["status"] != "pending":
        await callback.answer("❌ Заявка не найдена или уже обработана", show_alert=True)
        return

    # Обновим статус
    update_request_status(request_id, "approved")

    # Рассчитываем бонус
    settings = get_settings()
    procent_bonus = settings.get("procent_bonus", 6)

    bonus = round(req["usd"] * (procent_bonus / 100), 8)

    # Начисляем бонус и активируем
    credit_operator_bonus(req["operator_id"], bonus)
    set_operator_active(req["operator_id"], True)

    # Отправка сообщения оператору
    try:
        await callback.bot.send_message(
            chat_id=req["operator_id"],
            text=f"💸 Баланс пополнен на ${bonus}"
        )
    except Exception as e:
        print(f"[ERROR] Не удалось отправить сообщение оператору {req['operator_id']}: {e}")

    # Обновляем сообщение в админ-чате
    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ <b>Заявка подтверждена</b>\n💸 Бонус: {bonus} $",
        parse_mode="HTML"
    )
    await callback.answer("✅ Заявка принята")



@router.callback_query(F.data.startswith("decline_request:"))
async def decline_request(callback: CallbackQuery):
    request_id = int(callback.data.split(":")[1])
    req = get_request_by_id(request_id)

    if not req or req["status"] != "pending":
        await callback.answer("❌ Заявка не найдена или уже обработана", show_alert=True)
        return

    update_request_status(request_id, "declined")

    await callback.message.edit_text(
        callback.message.text + f"\n\n❌ <b>Заявка отклонена</b>",
        parse_mode="HTML"
    )
    await callback.answer("❌ Заявка отклонена")


class RemoveOperatorFSM(StatesGroup):
    choosing_chat = State()
    choosing_operator = State()


@router.message(F.text == "➖ Удалить оператора из чата")
async def start_remove_operator(message: Message, state: FSMContext):
    from services.json_writer import get_chats_with_names

    buttons = [[KeyboardButton(text=chat["name"])] for chat in get_chats_with_names()]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await message.answer("Выберите чат, из которого хотите удалить оператора:", reply_markup=markup)
    await state.set_state(RemoveOperatorFSM.choosing_chat)


@router.message(RemoveOperatorFSM.choosing_chat)
async def choose_chat_to_remove(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return
    from services.json_writer import get_chat_by_name, get_manager_name_by_id
    chat = get_chat_by_name(message.text.strip())

    if not chat:
        await message.answer("❌ Чат не найден.")
        return

    if not chat["managers"]:
        await message.answer("❗ В этом чате нет операторов.")
        await state.clear()
        return

    await state.update_data(chat_id=chat["id"], chat_name=chat["name"])

    buttons = [
        [KeyboardButton(text=f"{manager_id} — {get_manager_name_by_id(manager_id) or 'Без имени'}")]
        for manager_id in chat["managers"]
    ]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await message.answer("Выберите оператора для удаления:", reply_markup=markup)
    await state.set_state(RemoveOperatorFSM.choosing_operator)


@router.message(RemoveOperatorFSM.choosing_operator)
async def remove_operator(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено.", reply_markup=get_keyboard_buttons(message.from_user.id))
        return
    operator_line = message.text.strip()
    operator_id = operator_line.split("—")[0].strip()

    if not operator_id.isdigit():
        await message.answer("❗ Неверный формат. Попробуйте снова.")
        return

    data = await state.get_data()
    from services.json_writer import remove_operator_from_chat

    success = remove_operator_from_chat(chat_id=data["chat_id"], operator_id=int(operator_id))
    if success:
        await message.answer(f"🗑 Оператор `{operator_id}` удалён из чата *{data['chat_name']}*", parse_mode="Markdown")
    else:
        await message.answer("❌ Не удалось удалить. Возможно, такого оператора нет.")

    await state.clear()


from aiogram.fsm.state import StatesGroup, State

class TransferToShop(StatesGroup):
    choosing_chat = State()
    waiting_for_amount = State()


@router.message(F.text == "💸 Отправка денег в шоп")
async def start_transfer_to_shop(message: Message, state: FSMContext):
    from services.json_writer import get_all_chats

    chats = get_all_chats()
    if not chats:
        await message.answer("❗ Нет доступных групп.")
        return

    buttons = [
        [InlineKeyboardButton(text=chat["name"], callback_data=f"transfer:{chat['id']}")]
        for chat in chats
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите группу:", reply_markup=markup)
    await state.set_state(TransferToShop.choosing_chat)



@router.callback_query(F.data.startswith("transfer:"))
async def ask_transfer_amount(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    from services.json_writer import get_chat_by_id

    chat = get_chat_by_id(chat_id)
    if not chat:
        await callback.answer("Чат не найден", show_alert=True)
        return

    await state.update_data(chat_id=chat_id, chat_name=chat["name"])
    await callback.message.answer(f"Введите сумму в *USDT*, которую хотите перевести из баланса группы *{chat['name']}* \nБаланс: {chat['balance']}", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))
    await state.set_state(TransferToShop.waiting_for_amount)
    await callback.answer()


@router.message(TransferToShop.waiting_for_amount)
async def process_transfer_amount(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление нового чата отменена.",
                             reply_markup=get_keyboard_buttons(message.from_user.id))
        return
    amount_text = message.text.strip()
    if not amount_text.replace('.', '', 1).isdigit():
        await message.answer("❗ Введите корректную сумму в USDT.")
        return

    amount = float(amount_text)
    data = await state.get_data()
    chat_id = data["chat_id"]
    from services.json_writer import get_chat_by_id, update_chat

    chat = get_chat_by_id(chat_id)
    if not chat:
        await message.answer("❗ Группа не найдена.")
        await state.clear()
        return

    balance = chat.get("balance", 0)
    all_balance = chat.get("all_balance", 0)

    if amount > balance:
        await message.answer(f"❌ Недостаточно средств. На балансе: {balance} USD")
        return

    # списываем
    chat["balance"] = round(balance - amount, 2)
    update_chat(chat_id, chat)

    await message.answer(f"✅ Успешно отправлено {amount} USD из группы *{chat['name']}*.\n💰 Остаток: {chat['balance']} USD", parse_mode="Markdown")

    # уведомляем группу
    try:
        await message.bot.send_message(
            chat_id=-chat["id"],
            text=(
                f"📤 *Деньги отправлены в шоп!*\n"
                f"💸 Переведено: *{amount} USD*\n"
                f"💰 Остаток баланса: *{chat['balance']} USD*\n"
                f"📊 Всего заработано: *{all_balance} USD*"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"[ERROR] Не удалось уведомить группу: {e}")

    await state.clear()


from aiogram.fsm.state import StatesGroup, State

class ChatSettingsFSM(StatesGroup):
    choosing_chat = State()
    choosing_parameter = State()
    entering_value = State()


@router.message(F.text == "⚙️ Настройки чата")
async def start_chat_settings(message: Message, state: FSMContext):
    from services.json_writer import get_all_chats

    chats = get_all_chats()
    if not chats:
        await message.answer("Нет доступных чатов.")
        return

    buttons = [
        [InlineKeyboardButton(text=chat["name"], callback_data=f"chatsettings:{chat['id']}")]
        for chat in chats
    ]

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите чат для изменения настроек:", reply_markup=markup)
    await state.set_state(ChatSettingsFSM.choosing_chat)



@router.callback_query(F.data.startswith("chatsettings:"))
async def show_chat_settings(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    await state.update_data(chat_id=chat_id)

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔢 Курс (USDT)", callback_data="set_rate")],
        [InlineKeyboardButton(text="💰 Процент комиссии", callback_data="set_procent")],
        [InlineKeyboardButton(text="🎯 Процент бонуса", callback_data="set_bonus")],
        [InlineKeyboardButton(text="🏦 Адрес перевода", callback_data="set_address")],
    ])

    await callback.message.answer("Выберите параметр для изменения:", reply_markup=buttons)
    await state.set_state(ChatSettingsFSM.choosing_parameter)
    await callback.answer()


@router.callback_query(ChatSettingsFSM.choosing_parameter)
async def ask_new_value(callback: CallbackQuery, state: FSMContext):
    param = callback.data
    await state.update_data(parameter=param)

    text_map = {
        "set_rate": "Введите новый курс USDT:",
        "set_procent": "Введите новый процент комиссии:",
        "set_bonus": "Введите новый процент бонуса:",
        "set_address": "Введите новый адрес LTC:",
        "set_address_set": "Введите новый сеть LTC:"
    }

    await callback.message.answer(text_map[param])
    await state.set_state(ChatSettingsFSM.entering_value)
    await callback.answer()


@router.message(ChatSettingsFSM.entering_value)
async def save_new_setting(message: Message, state: FSMContext):
    from services.json_writer import update_chat_settings

    data = await state.get_data()
    chat_id = data["chat_id"]
    param = data["parameter"]
    value = message.text.strip()

    if param in ["set_rate", "set_procent", "set_bonus"]:
        try:
            value = float(value)
        except:
            await message.answer("❗ Введите корректное число.")
            return

    update_chat_settings(chat_id, param, value)
    await message.answer("✅ Значение успешно обновлено.")
    await state.clear()


class ManualTransactionFSM(StatesGroup):
    waiting_for_card = State()
    waiting_for_amount = State()


@router.message(F.text == "➕ Добавить чек вручную")
async def manual_transaction_start(message: Message, state: FSMContext):
    await message.answer("Введите последние 4 цифры карты:")
    await state.set_state(ManualTransactionFSM.waiting_for_card)




@router.message(ManualTransactionFSM.waiting_for_card)
async def handle_card_input(message: Message, state: FSMContext):
    input_card = message.text.strip()

    if not input_card.isdigit() or len(input_card) != 4:
        await message.answer("❗ Введите 4 цифры.")
        return

    data = load_data()

    matched = None
    for chat in data.get("chats", []):
        for operator_id in chat.get("managers", []):
            manager = next((m for m in data.get("managers", []) if m["id"] == operator_id), None)
            if not manager:
                continue
            for card in manager.get("cards", []):
                if card["card"][-4:] == input_card and card.get("active", True):
                    matched = {
                        "chat_id": chat["id"],
                        "operator_id": operator_id,
                        "card_number": card["card"]
                    }
                    break
            if matched:
                break
        if matched:
            break

    if not matched:
        await message.answer("❌ Карта не найдена ни в одном чате.")
        await state.clear()
        return

    await state.update_data(**matched)
    await message.answer("✅ Карта найдена. Введите сумму в KGS:")
    await state.set_state(ManualTransactionFSM.waiting_for_amount)



@router.message(ManualTransactionFSM.waiting_for_amount)
async def handle_amount_input(message: Message, state: FSMContext):
    amount_text = message.text.strip()
    if not amount_text.isdigit():
        await message.answer("❗ Введите сумму числом.")
        return

    amount = int(amount_text)
    data = await state.get_data()

    # Добавляем транзакцию в чат
    from datetime import datetime
    chats = load_data()
    for chat in chats.get("chats", []):
        if chat["id"] == data["chat_id"]:
            chat.setdefault("transactions", []).append({
                "msg_id": 0,
                "operator": data["operator_id"],
                "card": data["card_number"],
                "money": amount,
                "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")
            })
            break

    save_data(chats)

    await message.answer("✅ Транзакция успешно добавлена.")
    await state.clear()
