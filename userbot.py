import re
from asyncio import Event

from telethon import TelegramClient, events
from telethon.events import NewMessage
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import PeerChannel, PeerChat, MessageMediaPhoto
from decouple import config
# from telethon.tl.functions.messages import SendReaction
from telethon.tl.types import ReactionEmoji

from services.json_writer import get_active_chat_ids

# Получи эти данные на https://my.telegram.org
api_id = config('API_ID')
api_hash = config('API_HASH')
session_name = 'userbot'  # создаст .session файл

# Укажи ID своей группы
GROUP_ID = -4851516748

client = TelegramClient(session_name, api_id, api_hash)


@client.on(events.NewMessage)
async def react_to_transaction(event: events.NewMessage.Event):
    chat_id = event.chat_id

    # Проверяем чаты
    allowed_chats = get_active_chat_ids()
    if abs(chat_id) not in allowed_chats:
        print(chat_id, allowed_chats)
        return

    # Проверяем наличие фото
    if isinstance(event.message.media, MessageMediaPhoto):
        caption = f"{chat_id}\n{event.message.id}"
        peer = await client.get_input_entity(GROUP_ID)
        await client.send_file(
            entity=peer,
            file=event.message.media.photo,
            caption=caption,
            force_document=False
        )


@client.on(events.NewMessage(chats=GROUP_ID))
async def react_to_transaction(event):
    text = event.raw_text

    # Ищем msg_id в тексте
    msg_match = re.search(r"msg_id\s*=\s*(\d+)", text)
    chat_match = re.search(r"chat_id\s*=\s*(-?\d+)", text)
    text = text.split('💰')[1]
    text = text.split('🧾')[0]
    if msg_match and chat_match:
        msg_id = int(msg_match.group(1))
        chat_id = chat_match.group(1)
        print('[DEBUG] CHAT_ID', -(int(chat_id)))
        peer = await client.get_entity(int(chat_id))
        print(f"[DEBUG] Chat ID: {chat_id}, Msg ID: {msg_id}")
        try:

            await client(SendReactionRequest(
                peer=peer,
                msg_id=msg_id,
                reaction=[ReactionEmoji(emoticon="👍")]
            ))
            print(f"✅ Реакция на сообщение {msg_id} поставлена")
            await client.send_message(entity=peer,
                reply_to=msg_id, message=text
            )
        except Exception as e:
            print(f"❌ Ошибка реакции: {e}")

client.start()
print("🤖 Юзербот запущен и ждёт подтверждений...")
client.run_until_disconnected()
