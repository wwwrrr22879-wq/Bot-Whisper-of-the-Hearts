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
user_admin = {}
user_messages = {}
secret_achievements = {}
taken_users = set()
user_topic = {}
reply_map = {}

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
        "🌸 Привет!\n\nТы в боте поддержки 💌\nВыбери действие в меню ниже.",
        reply_markup=main_menu
    )

# ================== ПРАВИЛА ==================
@dp.message(F.text == "📜 Правила")
async def rules(message: types.Message):
    await message.answer(
        "📜 Правила\n\n"
        "1️⃣ Не спамить.\n"
        "2️⃣ Не оскорблять администрацию.\n"
        "3️⃣ Не просить личную информацию админов.\n"
        "4️⃣ Запрещён 18+, самоповреждения, кровь.\n"
        "5️⃣ Перетаскивание админов — бан.\n"
        "6️⃣ Политика и религия запрещены.\n"
        "7️⃣ Запрещён пиар.\n"
        "8️⃣ Не брать более 3 админов.\n"
        "9️⃣ Неадекват — предупреждение → бан.\n"
        "🔟 Запрещены оскорбительные слова."
    )

# ================== ГРАФИК ==================
@dp.message(F.text == "⏰ График работы")
async def schedule(message: types.Message):
    await message.answer(
        "⏰ График работы\n\n"
        "🌞 08:00 – 22:00 — дневная смена\n"
        "🌙 22:00 – 08:00 — ночная смена\n\n"
        "По МСК"
    )

# ================== ДОСТИЖЕНИЯ ==================
@dp.message(F.text == "🏆 Мои достижения")
async def achievements(message: types.Message):
    uid = message.from_user.id
    count = user_messages.get(uid, 0)

    achieved = []
    milestones = {
        1: "Новичок",
        5: "Упорный",
        50: "Активный пользователь",
        100: "Опытный пользователь",
        250: "Серьезный",
        500: "Ветеран",
        1000: "Легенда"
    }

    for n, title in milestones.items():
        if count >= n:
            achieved.append(f"🏆 {title}")

    if not achieved:
        achieved.append("❌ Пока нет достижений")

    await message.answer("🎖 Твои достижения:\n\n" + "\n".join(achieved))

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

    await msg.edit_reply_markup()
    await call.answer("Пользователь взят")

# ================== СООБЩЕНИЯ ==================
@dp.message()
async def messages(message: types.Message):
    uid = message.from_user.id

    # ===== АДМИН =====
    if message.chat.id == ADMIN_CHAT_ID:
        if not message.reply_to_message:
            return

        user_id = reply_map.get(message.reply_to_message.message_id)
        if not user_id:
            return

        if message.from_user.id != OWNER_ID:
            if user_admin.get(user_id) != message.from_user.id:
                return

        heart = "💌\n\n"
        if message.text:
            await bot.send_message(user_id, heart + message.text)
        return

    # ===== ПОЛЬЗОВАТЕЛЬ =====
    user_messages[uid] = user_messages.get(uid, 0) + 1

    if message.text in ("📩 Новые обращения", "🆘 Нужна поддержка"):
        user_topic[uid] = message.text
        await message.answer("✉️ Напиши сообщение для администрации")
        return

    topic = user_topic.get(uid, "Без темы")
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    text = f"Тема: {topic}\n{username}\nID: {uid}\n\n"

    kb = take_pz_kb if uid not in taken_users else None
    sent = await bot.send_message(ADMIN_CHAT_ID, text + (message.text or ""), reply_markup=kb)
    reply_map[sent.message_id] = uid

# ================== KEEP ALIVE ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot alive"

threading.Thread(target=lambda: app.run("0.0.0.0", 8080)).start()

# ================== RUN ==================
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
