from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

# 🔐 Твої дані
TOKEN = "8436221087:AAHfUdq28uv40eVWtuDuAYRVTyCXF6iZ6M0"
ADMIN_CHAT_ID = -1003120877184  # ID групи адміністрації

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 словник для зв’язку повідомлень користувач ↔ бот
reply_map = {}       # ключ: message_id в групі адміністраторів, значення: user_id
banned_users = set() # заблоковані користувачі

# 🌸 Привітання після /start
@dp.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.answer("❌ Ви заблоковані і не можете писати боту.")
        return

    await message.answer(
        "🌸 Привет, солнышко!\n\n"
        "Я — бот *Шепот сердец 💌*\n"
        "Можешь написать своё сообщение — и я передам его администраторам.\n"
        "Они обязательно тебе ответят с лучиком тепла ☀️",
        parse_mode="Markdown"
    )

# 🕊️ Обробка повідомлень
@dp.message()
async def handle_messages(message: Message):
    user_id = message.from_user.id

    # ❌ Перевірка на бан
    if user_id in banned_users:
        await message.answer("❌ Ви заблоковані і не можете писати боту.")
        return

    # 💌 Повідомлення від користувача → адміністрація
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        text = f"💬 Сообщение от {username} (ID: {user_id}):\n\n{message.text or '[не текстовое сообщение]'}"
        sent = await bot.send_message(ADMIN_CHAT_ID, text)
        reply_map[sent.message_id] = user_id

    # 🩷 Повідомлення у групі адміністраторів → користувачеві
    elif message.chat.id == ADMIN_CHAT_ID:
        # Пересилаємо тільки, якщо це reply на повідомлення бота
        if message.reply_to_message and message.reply_to_message.message_id in reply_map:
            user_id = reply_map[message.reply_to_message.message_id]
            await bot.send_message(user_id, f"💌 Ответ администратора:\n\n{message.text}")

        # ⚠️ Бан/розбан через reply (може робити будь-хто)
        if message.text and message.text.startswith("/ban"):
            if message.reply_to_message and message.reply_to_message.message_id in reply_map:
                banned_user = reply_map[message.reply_to_message.message_id]
                banned_users.add(banned_user)
                await message.answer(f"✅ Користувач {banned_user} заблокований.")
        
        if message.text and message.text.startswith("/unban"):
            if message.reply_to_message and message.reply_to_message.message_id in reply_map:
                unbanned_user = reply_map[message.reply_to_message.message_id]
                banned_users.discard(unbanned_user)
                await message.answer(f"✅ Користувач {unbanned_user} розблокований.")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
