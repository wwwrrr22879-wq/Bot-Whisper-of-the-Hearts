from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

TOKEN = "8445444619:AAFdR4jF1IQJzEFlL_DsJ-JTxT9nwkwwC58"
ADMIN_CHAT_ID = -1003120877184  # твій основний чат адміністраторів

bot = Bot(token=TOKEN)
dp = Dispatcher()

# словник для збереження зв'язку повідомлення адміна ↔ користувач
reply_map = {}  # ключ: message_id адміна, значення: user_id

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "👋 Привет!\n"
        "Рад тебя видеть! 💫\n"
        "Я — бот *Шепот сердец 💌*\n\n"
        "Можешь написать своё сообщение — администратор скоро тебе ответит.",
        parse_mode="Markdown"
    )

@dp.message()
async def handle_messages(message: Message):
    # Повідомлення від користувача
    if message.chat.id != ADMIN_CHAT_ID:
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        text = f"📩 Сообщение от {username} (ID: {user_id}):\n\n{message.text or '[не текстовое сообщение]'}"
        sent = await bot.send_message(ADMIN_CHAT_ID, text)
        reply_map[sent.message_id] = user_id

    # Повідомлення від адміна у reply на користувача
    elif message.chat.id == ADMIN_CHAT_ID:
        if message.reply_to_message and message.reply_to_message.message_id in reply_map:
            user_id = reply_map[message.reply_to_message.message_id]
            await bot.send_message(user_id, f"💌 Ответ админа:\n\n{message.text}")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
