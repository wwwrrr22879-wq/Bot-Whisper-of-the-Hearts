import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask
import threading
from datetime import datetime

# ================== ДАННЫЕ ==================
TOKEN = "8291867377:AAGqd4UAVY4gU3zVR5YevZSb1Nly6j6-UDY"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================== ПАМЯТЬ ==================
user_admin = {}          # user_id -> admin_id
user_messages = {}       # user_id -> count
secret_achievements = {} # user_id -> set
taken_users = set()
user_topic = {}
reply_map = {}           # admin_message_id -> user_id

# ================== КНОПКИ ==================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏆 Мои достижения")],
        [KeyboardButton(text="📩 Новые обращения"), KeyboardButton(text="🆘 Нужна поддержка")],
        [KeyboardButton(text="📜 Правила"), KeyboardButton(text="⏰ График работы")]
    ],
    resize_keyboard=True
)

take_pz_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Взять ПЗ", callback_data="take_pz")]]
)

# ================== START ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🌸 Привет!\n\n"
        "Ты в боте поддержки 💌\n"
        "Выбери действие в меню ниже.",
        reply_markup=main_menu
    )

# ================== ПРАВИЛА ==================
@dp.message(F.text == "📜 Правила")
async def rules(message: types.Message):
    await message.answer(
        "📜 Правила\n\n"
        "1️⃣ Не спамить\n"
        "2️⃣ Не оскорблять администрацию\n"
        "3️⃣ Не просить личные данные админов\n"
        "4️⃣ Запрещён 18+, кровь, самоповреждения\n"
        "5️⃣ Политика и религия запрещены\n"
        "6️⃣ Запрещён пиар\n"
        "7️⃣ Неадекват → предупреждение → бан",
        parse_mode="Markdown"
    )

# ================== ГРАФИК ==================
@dp.message(F.text == "⏰ График работы")
async def schedule(message: types.Message):
    await message.answer(
        "⏰ График работы\n\n"
        "🌞 08:00 – 22:00\n"
        "🌙 22:00 – 08:00\n\n"
        "По МСК",
        parse_mode="Markdown"
    )

# ================== ДОСТИЖЕНИЯ ==================
@dp.message(F.text == "🏆 Мои достижения")
async def achievements(message: types.Message):
    uid = message.from_user.id
    count = user_messages.get(uid, 0)

    milestones = {
        1: "Новичок",
        5: "Упорный",
        50: "Активный",
        100: "Опытный",
        250: "Серьёзный",
        500: "Ветеран",
        1000: "Легенда"
    }

    text = []
    for n, name in milestones.items():
        if count >= n:
            text.append(f"🏆 {name}")

    if not text:
        text.append("❌ Пока нет достижений")

    await message.answer("🎖 Твои достижения:\n\n" + "\n".join(text))

# ================== CALLBACK ==================
@dp.callback_query(F.data == "take_pz")
async def take_pz(call: types.CallbackQuery):
    msg = call.message
    try:
        user_id = int(msg.text.split("ID:")[1].split("\n")[0])
    except:
        await call.answer("Ошибка")
        return

    user_admin[user_id] = call.from_user.id
    taken_users.add(user_id)
    reply_map[msg.message_id] = user_id

    await msg.edit_reply_markup(None)
    await call.answer("Пользователь взят")

# ================== ПОИСК USER_ID ПО REPLY ==================
def find_user_id(message):
    m = message
    while m:
        if m.message_id in reply_map:
            return reply_map[m.message_id]
        m = m.reply_to_message
    return None

# ================== СООБЩЕНИЯ ==================
@dp.message()
async def messages(message: types.Message):
    uid = message.from_user.id
    now = datetime.now()

    # ===== АДМИНЫ =====
    if message.chat.id == ADMIN_CHAT_ID:
        if not message.reply_to_message:
            return

        user_id = find_user_id(message.reply_to_message)
        if not user_id:
            return

        if message.from_user.id != OWNER_ID:
            if user_admin.get(user_id) != message.from_user.id:
                return

        heart = "💌\n\n"
        try:
            if message.text:
                await bot.send_message(user_id, heart + message.text)
            elif message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id)
            elif message.video:
                await bot.send_video(user_id, message.video.file_id)
            elif message.voice:
                await bot.send_voice(user_id, message.voice.file_id)
            elif message.document:
                await bot.send_document(user_id, message.document.file_id)
            elif message.sticker:
                await bot.send_sticker(user_id, message.sticker.file_id)
        except:
            await bot.send_message(ADMIN_CHAT_ID, f"⚠️ Пользователь {user_id} заблокировал бота.")
        return

    # ===== ЮЗЕРЫ =====
    user_messages[uid] = user_messages.get(uid, 0) + 1

    if message.text in ("📩 Новые обращения", "🆘 Нужна поддержка"):
        user_topic[uid] = message.text
        await message.answer("✉️ Напиши своё сообщение")
        return

    topic = user_topic.get(uid, "Без темы")
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    header = f"Тема: {topic}\n{username}\nID: {uid}\n\n"

    kb = take_pz_kb if uid not in taken_users else None

    sent = await bot.send_message(ADMIN_CHAT_ID, header + (message.text or ""), reply_markup=kb)
    reply_map[sent.message_id] = uid

# ================== KEEP ALIVE ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run():
    app.run("0.0.0.0", 8080)

threading.Thread(target=run).start()

# ================== RUN ==================
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
