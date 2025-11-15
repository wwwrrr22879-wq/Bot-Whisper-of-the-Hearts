# main.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 🔐 Дані твої
TOKEN = "8436221087:AAHfUdq28uv40eVWtuDuAYRVTyCXF6iZ6M0"  # твій токен
ADMIN_CHAT_ID = -1003120877184  # ID групи адміністрації
OWNER_ID = 1470389051  # твій особистий ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 Збереження зв'язку повідомлення адміна ↔ користувач
reply_map = {}  # key: message_id адміна, value: user_id

# 🚫 Список заблокованих користувачів
banned_users = set()

# --- Команди ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    if message.from_user.id in banned_users:
        return
    await message.answer(
        "🌸 Привет, солнышко!\n\n"
        "Я — бот *Шепот сердец 💌*\n"
        "Напиши своё сообщение — и я передам его администраторам.\n"
        "Они обязательно ответят тебе с лучиком тепла ☀️",
        parse_mode="Markdown"
    )

@dp.message(Command("ban"))
async def ban_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может банить.")
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответь на сообщение пользователя, которого хочешь забанить.")
        return
    user_id = reply_map.get(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("⚠️ Не удалось определить пользователя.")
        return
    banned_users.add(user_id)
    await message.reply(f"✅ Пользователь {user_id} заблокирован.")

@dp.message(Command("unban"))
async def unban_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может разбанить.")
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответь на сообщение пользователя, которого хочешь разбанить.")
        return
    user_id = reply_map.get(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("⚠️ Не удалось определить пользователя.")
        return
    banned_users.discard(user_id)
    await message.reply(f"✅ Пользователь {user_id} разблокирован.")

@dp.message(Command("banned"))
async def banned_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может смотреть заблокированных.")
        return
    if banned_users:
        await message.reply("🚫 Заблокированные пользователи:\n" + "\n".join(map(str, banned_users)))
    else:
        await message.reply("✅ Нет заблокированных пользователей.")

# --- Обработка сообщений ---
@dp.message()
async def handle_messages(message: types.Message):
    # Користувач пише → пересилаємо адмінам
    if message.chat.id != ADMIN_CHAT_ID:
        user_id = message.from_user.id
        if user_id in banned_users:
            return
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        text = f"💬 Сообщение от {username} (ID: {user_id}):\n\n{message.text or '[не текстовое сообщение]'}"
        sent = await bot.send_message(ADMIN_CHAT_ID, text)
        reply_map[sent.message_id] = user_id

    # Адмін відповідає у reply → пересилаємо назад користувачу
    elif message.chat.id == ADMIN_CHAT_ID:
        if message.reply_to_message and message.reply_to_message.message_id in reply_map:
            user_id = reply_map[message.reply_to_message.message_id]
            await bot.send_message(user_id, f"💌 Ответ администратора:\n\n{message.text}")

# --- Запуск ---
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
