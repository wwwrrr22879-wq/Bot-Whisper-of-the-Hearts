import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode

# 🔐 ТВОЇ ДАНІ
BOT_TOKEN = "8436221087:AAHfUdq28uv40eVWtuDuAYRVTyCXF6iZ6M0"
ADMIN_ID = 1470389051
ADMIN_GROUP_ID = -1003120877184

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Список заблокованих користувачів
banned_users = set()

# Стартове привітання
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Привет, я твой бот <b>Шепот Сердец</b>, тень твоих думок 🌙\n\n"
        "Рад, что ты сюда написал. Напиши своё сообщение, и тебе скоро ответит администратор 💌"
    )

# Обробка всіх повідомлень
@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    # Перевірка на бан
    if user_id in banned_users:
        await message.answer("🚫 Ты заблокирован и не можешь отправлять сообщения.")
        return

    # Формуємо повідомлення для адмін-групи
    user_info = f"👤 <b>{message.from_user.full_name}</b>\n"
    if message.from_user.username:
        user_info += f"@{message.from_user.username}\n"
    user_info += f"ID: <code>{user_id}</code>\n\n"
    user_info += f"💬 <b>Сообщение:</b>\n{message.text}"

    # Пересилаємо адміну
    await bot.send_message(ADMIN_GROUP_ID, user_info)

# Обробка відповідей адміна в групі
@dp.message(lambda msg: msg.chat.id == ADMIN_GROUP_ID and msg.reply_to_message)
async def admin_reply(message: types.Message):
    # Шукаємо ID користувача в оригінальному тексті
    reply_text = message.reply_to_message.text
    try:
        user_id_line = [line for line in reply_text.splitlines() if "ID:" in line][0]
        user_id = int(user_id_line.split(":")[1].strip().strip("<code>").strip("</code>"))
    except:
        await message.reply("⚠️ Не удалось определить ID пользователя.")
        return

    # Надсилаємо відповідь користувачу (анонімно)
    await bot.send_message(user_id, f"💌 Сообщение от администратора:\n{message.text}")
    await message.reply("✅ Ответ отправлен пользователю.")

# Команди для бану/разбану
@dp.message(lambda msg: msg.chat.id == ADMIN_GROUP_ID and msg.text.startswith("/ban"))
async def ban_user(message: types.Message):
    try:
        user_id = int(message.text.split()[1])
        banned_users.add(user_id)
        await message.reply(f"🚫 Пользователь {user_id} заблокирован.")
    except:
        await message.reply("❌ Укажи ID после /ban")

@dp.message(lambda msg: msg.chat.id == ADMIN_GROUP_ID and msg.text.startswith("/unban"))
async def unban_user(message: types.Message):
    try:
        user_id = int(message.text.split()[1])
        banned_users.discard(user_id)
        await message.reply(f"✅ Пользователь {user_id} разблокирован.")
    except:
        await message.reply("❌ Укажи ID после /unban")

@dp.message(lambda msg: msg.chat.id == ADMIN_GROUP_ID and msg.text == "/banned")
async def show_banned(message: types.Message):
    if not banned_users:
        await message.reply("📭 Нет заблокированных пользователей.")
    else:
        banned_list = "\n".join(str(u) for u in banned_users)
        await message.reply(f"🚫 <b>Заблокированные пользователи:</b>\n{banned_list}")

# 🔁 Запуск
async def main():
    print("✨ Бот Шепіт Сердець запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
