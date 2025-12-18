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
NORM_PER_WEEK = 50

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================== ПАМЯТЬ ==================
user_admin = {}
user_messages = {}
secret_achievements = {}
all_users = set()
blocked_users = set()
taken_users = set()
user_topic = {}
reply_map = {}
admin_week = None
admin_stats = {}

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

# ================== ЧЕРГА ПОВІДОМЛЕНЬ ==================
send_queue = asyncio.Queue()

async def worker_send():
    while True:
        user_id, content, media = await send_queue.get()
        try:
            if media is None:
                await bot.send_message(user_id, content)
            else:
                # media = (type, file_id)
                typ, file_id = media
                if typ == "photo":
                    await bot.send_photo(user_id, file_id, caption=content)
                elif typ == "video":
                    await bot.send_video(user_id, file_id, caption=content)
                elif typ == "voice":
                    await bot.send_voice(user_id, file_id, caption=content)
                elif typ == "video_note":
                    await bot.send_video_note(user_id, file_id)
                elif typ == "document":
                    await bot.send_document(user_id, file_id, caption=content)
                elif typ == "sticker":
                    await bot.send_sticker(user_id, file_id)
        except:
            blocked_users.add(user_id)
        await asyncio.sleep(0.05)  # невелика пауза щоб не спамити API

# ================== ВСПОМОГАТЕЛЬНОЕ ==================
def check_week_reset():
    global admin_week, admin_stats
    current_week = datetime.now().isocalendar().week
    if admin_week != current_week:
        admin_week = current_week
        admin_stats = {}

# ================== START ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    all_users.add(message.from_user.id)
    await message.answer(
        "🌸 Привет!\nТы в боте поддержки 💌\nВыбери действие в меню ниже.",
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
        "6️⃣ Политика запрещена.\n"
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
        1: ("Новичок 🐣", "Ты только начал свой путь"),
        3: ("Любопытный 👀", "Уже 3 сообщения"),
        5: ("Упорный 💪", "Отправил 5 сообщений"),
        10: ("Разговорчивый 💬", "10 сообщений"),
        25: ("Активный 🔥", "25 сообщений"),
        50: ("Очень активный ⚡", "50 сообщений"),
        100: ("Опытный 🧠", "100 сообщений"),
        250: ("Проверенный временем ⏳", "250 сообщений"),
        500: ("Ветеран 🏅", "500 сообщений"),
        1000: ("Легенда 🌟", "1000 сообщений"),
        2500: ("Мифический 🐉", "2500 сообщений"),
        5000: ("Мастер поддержки 👑", "5000 сообщений"),
        10000: ("Живая легенда 💎", "10000 сообщений")
    }

    for n, (title, desc) in milestones.items():
        if count >= n:
            achieved.append(f"🏆 {title} — {desc}")

    secrets = secret_achievements.get(uid, set())
    if secrets:
        achieved.append("\n🔒 Секретные достижения:")
        for s in secrets:
            achieved.append(f"✨ {s}")

    if not achieved:
        achieved.append("❌ Пока нет достижений")

    await message.answer("🎖 *Твои достижения:*\n\n" + "\n".join(achieved), parse_mode="Markdown")

# ================== CALLBACK ==================
@dp.callback_query(F.data == "take_pz")
async def take_pz(call: types.CallbackQuery):
    admin_id = call.from_user.id
    msg = call.message
    try:
        user_id = int(msg.text.split("ID:")[1].split("\n")[0])
    except:
        await call.answer("Ошибка")
        return

    user_admin[user_id] = admin_id
    taken_users.add(user_id)
    await msg.edit_reply_markup(reply_markup=None)
    await call.answer("Пользователь взят")
    reply_map[msg.message_id] = user_id

# ================== СООБЩЕНИЯ ==================
@dp.message()
async def messages(message: types.Message):
    uid = message.from_user.id
    all_users.add(uid)
    check_week_reset()
    user_messages[uid] = user_messages.get(uid, 0) + 1

    # ===== АДМИН ЧАТ =====
    if message.chat.id == ADMIN_CHAT_ID:
        admin_stats[uid] = admin_stats.get(uid, 0) + 1
        # OWNER може писати будь-кому
        if message.reply_to_message:
            user_id = reply_map.get(message.reply_to_message.message_id)
            if user_id and (uid == OWNER_ID or user_admin.get(user_id) == uid):
                media = None
                content = message.text or ""
                if message.photo:
                    media = ("photo", message.photo[-1].file_id)
                elif message.video:
                    media = ("video", message.video.file_id)
                elif message.voice:
                    media = ("voice", message.voice.file_id)
                elif message.video_note:
                    media = ("video_note", message.video_note.file_id)
                elif message.document:
                    media = ("document", message.document.file_id)
                elif message.sticker:
                    media = ("sticker", message.sticker.file_id)
                await send_queue.put((user_id, "💌\n\n" + content, media))
        return

    # ===== ПОЛЬЗОВАТЕЛЬ =====
    if message.text in ("📩 Новые обращения", "🆘 Нужна поддержка"):
        user_topic[uid] = message.text
        await message.answer("✉️ Напиши своё сообщение, и администрация ответит!")
        return

    if message.text and message.text.lower() == "поменять админа":
        user_admin.pop(uid, None)
        taken_users.discard(uid)
        text = f"ID: {uid}\n\nПоменять админа"
        sent = await bot.send_message(ADMIN_CHAT_ID, text, reply_markup=take_pz_kb)
        reply_map[sent.message_id] = uid
        return

    topic = user_topic.get(uid, "Без темы")
    username = f"@{message.from_user.username}" if message.from_user.username else "Пользователь без юзернейма"
    text = f"{username}\nID: {uid}\nТема: {topic}\n\n{message.text or '[медиа]'}"
    kb = take_pz_kb if uid not in taken_users else None
    sent = await bot.send_message(ADMIN_CHAT_ID, text, reply_markup=kb)
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
async def main():
    asyncio.create_task(worker_send())  # запускаємо worker черги
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
