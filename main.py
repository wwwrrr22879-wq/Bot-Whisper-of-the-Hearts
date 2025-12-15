# main.py
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask
import threading

# 🔐 ДАНІ
TOKEN = "8556657168:AAFwnvcgwL-RjJ_tHcMe_D_qrUnsT-XH2a0"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 message_id бота в адмін-чаті → user_id
reply_map = {}
user_admin = {}        # user_id → admin_id (хто взяв ПЗ)
taken_users = set()    # всі користувачі, яких вже взяли
user_messages = {}     # user_id → кількість повідомлень
secret_achievements = {}  # user_id → set(secret_achievement_keys)

# --- ДОСТИЖЕННЯ ---
ACHIEVEMENTS = {
    1: ("🥇 Первый шаг", "Ты написал своё первое сообщение"),
    5: ("💬 Разговор пошёл", "Ты написал 5 сообщений"),
    50: ("🔥 Активный участник", "Ты написал 50 сообщений"),
    100: ("⭐ Постоянный пользователь", "100 сообщений в боте"),
    250: ("🚀 На волне", "250 сообщений"),
    500: ("💎 Преданный", "500 сообщений"),
    1000: ("🏆 Легенда", "1000 сообщений"),
    2500: ("👑 Элита", "2500 сообщений"),
    5000: ("🌌 Абсолют", "5000 сообщений")
}

SECRET_ACHIEVEMENTS = {
    "night": ("🌙 Ночная тень", "Ты написал сообщение ночью"),
    "exact_time": ("⏰ Точное время", "Ты написал сообщение ровно в 10:35")
}

# 🚫 Заблоковані
banned_users = set()

# --- КОМАНДА START ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    if message.from_user.id in banned_users:
        return
    await message.answer(
        "🌸 Привет, солнышко!\n\n"
        "Я — бот *Шепот сердец 💌*\n"
        "Выбери одну из кнопок ниже и начни общение с администрацией.",
        parse_mode="Markdown",
    )

# --- ДОСТИЖЕНИЯ ---
@dp.message(lambda message: message.text == "🏆 Мои достижения")
async def achievements(message: types.Message):
    uid = message.from_user.id
    count = user_messages.get(uid, 0)
    secrets = secret_achievements.get(uid, set())

    text = ["🏆 *Твои достижения:*", ""]
    has_any = False

    for need, (title, desc) in ACHIEVEMENTS.items():
        if count >= need:
            has_any = True
            text.append(f"{title}\n📌 {desc}\n")

    if secrets:
        has_any = True
        text.append("🔒 *Секретные достижения:*")
        for s in secrets:
            title, desc = SECRET_ACHIEVEMENTS[s]
            text.append(f"{title}\n📌 {desc}\n")

    if not has_any:
        text.append("❌ У тебя пока нет достижений.\nНапиши сообщение — и первое сразу появится 😉")

    await message.answer("\n".join(text), parse_mode="Markdown")

# --- ОБРАБОТКА ПОВІДОМЛЕНЬ ---
@dp.message()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    # підрахунок повідомлень
    user_messages[user_id] = user_messages.get(user_id, 0) + 1
    now = datetime.now()
    secrets = secret_achievements.setdefault(user_id, set())
    if 22 <= now.hour or now.hour < 8:
        secrets.add("night")
    if now.hour == 10 and now.minute == 35:
        secrets.add("exact_time")

    # 👤 Користувач → адміни
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        header = f"💬 От {username}\nID: {user_id}\n\n"
        keyboard = None

        # Якщо користувач не взятий → додаємо кнопку "Взять ПЗ"
        if user_id not in taken_users:
            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[[types.InlineKeyboardButton(text="Взять ПЗ", callback_data="take_pz")]]
            )

        # Відправка повідомлення в адмін-чат
        if message.text:
            sent = await bot.send_message(ADMIN_CHAT_ID, header + message.text, reply_markup=keyboard)
        elif message.photo:
            sent = await bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=header, reply_markup=keyboard)
        elif message.video:
            sent = await bot.send_video(ADMIN_CHAT_ID, message.video.file_id, caption=header, reply_markup=keyboard)
        elif message.voice:
            sent = await bot.send_voice(ADMIN_CHAT_ID, message.voice.file_id, caption=header, reply_markup=keyboard)
        elif message.document:
            sent = await bot.send_document(ADMIN_CHAT_ID, message.document.file_id, caption=header, reply_markup=keyboard)
        elif message.sticker:
            sent = await bot.send_sticker(ADMIN_CHAT_ID, message.sticker.file_id, reply_markup=keyboard)
        else:
            sent = await bot.send_message(ADMIN_CHAT_ID, header + "[неподдерживаемый тип]", reply_markup=keyboard)

        reply_map[sent.message_id] = user_id

    # 🛠 Адмін → користувачу (тільки той, хто взяв)
    else:
        if not message.reply_to_message:
            return
        original_user_id = reply_map.get(message.reply_to_message.message_id)
        if not original_user_id:
            return

        # тільки адмін, який взяв ПЗ
        if user_admin.get(original_user_id) != message.from_user.id:
            return

        try:
            if message.text:
                await bot.send_message(original_user_id, message.text)
            elif message.photo:
                await bot.send_photo(original_user_id, message.photo[-1].file_id)
            elif message.video:
                await bot.send_video(original_user_id, message.video.file_id)
            elif message.voice:
                await bot.send_voice(original_user_id, message.voice.file_id)
            elif message.document:
                await bot.send_document(original_user_id, message.document.file_id)
            elif message.sticker:
                await bot.send_sticker(original_user_id, message.sticker.file_id)
        except:
            await bot.send_message(ADMIN_CHAT_ID, f"⚠️ Пользователь {original_user_id} заблокировал бота.")

# --- КНОПКА ВЗЯТЬ ПЗ ---
@dp.callback_query(lambda call: call.data == "take_pz")
async def take_pz(call: types.CallbackQuery):
    admin_id = call.from_user.id
    msg = call.message
    try:
        user_id = int(msg.text.split("ID:")[1].split("\n")[0])
    except:
        await call.answer("Ошибка", show_alert=True)
        return
    if user_id in user_admin:
        await call.answer("Пользователь уже взят другим администратором", show_alert=True)
        return

    user_admin[user_id] = admin_id
    taken_users.add(user_id)
    await msg.edit_reply_markup(reply_markup=None)
    await call.answer("Вы взяли ПЗ")

# --- Flask keep-alive ---
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is alive!"
def run():
    app.run(host="0.0.0.0", port=8080)
threading.Thread(target=run).start()

# --- RUN ---
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
