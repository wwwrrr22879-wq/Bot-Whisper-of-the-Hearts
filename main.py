# main.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask
import threading

# 🔐 Твої дані
TOKEN = "8556657168:AAFwnvcgwL-RjJ_tHcMe_D_qrUnsT-XH2a0"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 Зв'язок повідомлення адміна ↔ користувач
reply_map = {}  # key: message_id користувача, value: user_id

# 🚫 Заблоковані користувачі
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
    user_id = reply_map.get(message.reply_to_message.reply_to_message.message_id)
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
    user_id = reply_map.get(message.reply_to_message.reply_to_message.message_id)
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

# --- Обработка сообщений (текст + медиа) ---
@dp.message()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    # --- Користувач пише → пересилаємо адміну ---
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        text = f"💬 Сообщение от {username} (ID: {user_id}):\n\n"

        if message.text:
            text += message.text
            sent = await bot.send_message(ADMIN_CHAT_ID, text)
        elif message.photo:
            sent = await bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=text)
        elif message.video:
            sent = await bot.send_video(ADMIN_CHAT_ID, message.video.file_id, caption=text)
        elif message.voice:
            sent = await bot.send_voice(ADMIN_CHAT_ID, message.voice.file_id, caption=text)
        elif message.document:
            sent = await bot.send_document(ADMIN_CHAT_ID, message.document.file_id, caption=text)
        else:
            sent = await bot.send_message(ADMIN_CHAT_ID, text + "[неподдерживаемый тип]")

        # Зберігаємо під message_id оригінального повідомлення користувача
        reply_map[message.message_id] = user_id

    # --- Адмін відповідає у reply → пересилаємо назад користувачу ---
    elif message.chat.id == ADMIN_CHAT_ID:
        if message.reply_to_message:
            original_user_id = reply_map.get(message.reply_to_message.reply_to_message.message_id)
            if not original_user_id:
                return
            try:
                if message.text:
                    await bot.send_message(original_user_id, f"💌 Ответ администратора:\n\n{message.text}")
                elif message.photo:
                    await bot.send_photo(original_user_id, message.photo[-1].file_id, caption="💌 Ответ администратора")
                elif message.video:
                    await bot.send_video(original_user_id, message.video.file_id, caption="💌 Ответ администратора")
                elif message.voice:
                    await bot.send_voice(original_user_id, message.voice.file_id, caption="💌 Ответ администратора")
                elif message.document:
                    await bot.send_document(original_user_id, message.document.file_id, caption="💌 Ответ администратора")
                else:
                    await bot.send_message(original_user_id, "💌 Ответ администратора [неподдерживаемый тип]")
            except:
                await bot.send_message(ADMIN_CHAT_ID, f"⚠️ Пользователь {original_user_id} заблокировал бота.")

# --- Flask для Keep Alive ---
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()

# --- Запуск бота ---
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
