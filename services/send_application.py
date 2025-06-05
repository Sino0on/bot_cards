from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ADMIN_GROUP_ID = -4899834369

async def notify_admin_about_request(bot: Bot, request: dict, request_id: int):
    operator_id = request["operator_id"]
    usd = request["usd"]
    ltc = request["ltc"]
    address = request["address"]
    deadline = request["deadline"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"approve_request:{request_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"decline_request:{request_id}"
            )
        ]
    ])

    text = (
        f"🆕 <b>Новая заявка №{request_id}</b>\n\n"
        f"👤 Оператор: <a href='tg://user?id={operator_id}'>{operator_id}</a>\n"
        f"💵 USD: <b>{usd}</b>\n"
        f"🪙 LTC: <b>{ltc}</b>\n"
        f"📬 Адрес:\n<code>{address}</code>\n"
        f"⏳ Действительна до: <b>{deadline}</b>"
    )

    await bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=text,
        reply_markup=kb,
        parse_mode="HTML"
    )


