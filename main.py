# main.py
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask
import threading
from datetime import datetime

# ================== ДАННЫЕ ==================
TOKEN = "8556657168:AAFwnvcgwL-RjJ_tHcMe_D_qrUnsT-XH2a0"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================== ПАМЯТЬ ==================
user_admin = {}          # user_id -> admin_id
user_messages = {}       # user_id -> count
secret_achievements = {} # user_id -> set
taken_users = set()      # users already taken

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
        "📜 *Правила*\n\n"
        "1️⃣ Не спамить.\n"
        "2️⃣ Не оскорблять администрацию.\n"
        "3️⃣ Не просить личную информацию админов.\n"
        "4️⃣ Запрещён 18+, самоповреждения, кровь.\n"
        "5️⃣ Перетаскивание админов — бан.\n"
        "6️⃣ Политика и религия запрещены.\n"
        "7️⃣ Запрещён пиар.\n"
        "8️⃣ Не брать более 3 админов.\n"
        "9️⃣ Неадекват — предупреждение → бан.\n"
        "🔟 Запрещены оскорбительные слова.",
        parse_mode="Markdown"
    )

# ================== ГРАФИК ==================
@dp.message(F.text == "⏰ График работы")
async def schedule(message: types.Message):
    await message.answer(
        "⏰ *График работы*\n\n"
        "🌞 08:00 – 22:00 — дневная смена\n"
        "🌙 22:00 – 08:00 — ночная смена\n\n"
        "По МСК",
        parse_mode="Markdown"
    )

# ================== ДОСТИЖЕНИЯ ==================
@dp.message(F.text == "🏆 Мои достижения")
async def achievements(message: types.Message):
    uid = message.from_user.id
    count = user_messages.get(uid, 0)

    achieved = []
    for n in [1, 5, 50, 100, 250, 500, 1000, 2500, 5000]:
        if count >= n:
            achieved.append(f"✅ {n} сообщений")

    secrets = secret_achievements.get(uid, set())
    if secrets:
        achieved.append("\n🔒 Секретные:")
        for s in secrets:
            achieved.append(f"✨ {s}")

    if not achieved:
        achieved.append("❌ Пока нет достижений")

    await message.answer("🏆 *Твои достижения:*\n\n" + "\n".join(achieved), parse_mode="Markdown")

# ================== CALLBACK ==================
@dp.callback_query(F.data == "take_pz")
async def take_pz(call: types.CallbackQuery):
    admin_id = call.from_user.id
    msg = call.message

    user_id = int(msg.text.split("ID:")[1].split("\n")[0])
    user_admin[user_id] = admin_id
    taken_users.add(user_id)

    await call.answer("Пользователь взят")

# ================== СООБЩЕНИЯ ==================
@dp.message()
async def messages(message: types.Message):
    uid = message.from_user.id
    now = datetime.now()

    # ===== УЧЁТ СООБЩЕНИЙ =====
    user_messages[uid] = user_messages.get(uid, 0) + 1

    # ===== СЕКРЕТНЫЕ ДОСТИЖЕНИЯ =====
    secrets = secret_achievements.setdefault(uid, set())

    if 22 <= now.hour or now.hour < 8:
        secrets.add("Ночная активность")
    if now.hour == 10 and now.minute == 35:
        secrets.add("Точное время 10:35")

    # ===== СМЕНА АДМИНА =====
    if message.text and message.text.lower() == "поменять админа":
        user_admin.pop(uid, None)
        taken_users.discard(uid)

    # ===== ПОЛЬЗОВАТЕЛЬ → АДМИНЫ =====
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "Пользователь без юзернейма"

        text = f"{username}\nID: {uid}\n\n"
        kb = None

        if uid not in taken_users:
            kb = take_pz_kb

        if message.text:
            await bot.send_message(ADMIN_CHAT_ID, text + message.text, reply_markup=kb)
        elif message.photo:
            await bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=text, reply_markup=kb)
        elif message.video:
            await bot.send_video(ADMIN_CHAT_ID, message.video.file_id, caption=text, reply_markup=kb)
        elif message.voice:
            await bot.send_voice(ADMIN_CHAT_ID, message.voice.file_id, caption=text)
        elif message.video_note:
            await bot.send_video_note(ADMIN_CHAT_ID, message.video_note.file_id)
        elif message.document:
            await bot.send_document(ADMIN_CHAT_ID, message.document.file_id, caption=text)
        elif message.sticker:
            await bot.send_sticker(ADMIN_CHAT_ID, message.sticker.file_id)

    # ===== АДМИН → ПОЛЬЗОВАТЕЛЬ =====
    else:
        if not message.reply_to_message:
            return

        try:
            user_id = int(message.reply_to_message.text.split("ID:")[1].split("\n")[0])
        except:
            return

        if user_admin.get(user_id) != message.from_user.id:
            return

        heart = "💌\n\n"

        if message.text:
            await bot.send_message(user_id, heart + message.text)
        elif message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id)
        elif message.video:
            await bot.send_video(user_id, message.video.file_id)
        elif message.voice:
            await bot.send_voice(user_id, message.voice.file_id)
        elif message.video_note:
            await bot.send_video_note(user_id, message.video_note.file_id)
        elif message.document:
            await bot.send_document(user_id, message.document.file_id)
        elif message.sticker:
            await bot.send_sticker(user_id, message.sticker.file_id)

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
