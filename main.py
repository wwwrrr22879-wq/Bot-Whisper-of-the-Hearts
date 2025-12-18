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

# ================== ЧЕРГА ==================
message_queue = asyncio.Queue()

async def queue_worker():
    while True:
        user_id, content, content_type = await message_queue.get()
        try:
            if content_type == "text":
                await bot.send_message(user_id, content)
            elif content_type == "photo":
                await bot.send_photo(user_id, content)
            elif content_type == "video":
                await bot.send_video(user_id, content)
            elif content_type == "voice":
                await bot.send_voice(user_id, content)
            elif content_type == "video_note":
                await bot.send_video_note(user_id, content)
            elif content_type == "document":
                await bot.send_document(user_id, content)
            elif content_type == "sticker":
                await bot.send_sticker(user_id, content)
        except:
            blocked_users.add(user_id)
        await asyncio.sleep(2)  # пауза 2 секунди між повідомленнями
        message_queue.task_done()

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

        if not message.reply_to_message:
            return
        user_id = reply_map.get(message.reply_to_message.message_id)
        # Тільки власник або адмін, який взяв ПЗ, може писати
        if uid != OWNER_ID and (not user_id or user_admin.get(user_id) != uid):
            await message.reply("❌ Вы не можете писать этому пользователю")
            return

        content_type = "text"
        content = message.text or ""
        if message.photo:
            content_type = "photo"
            content = message.photo[-1].file_id
        elif message.video:
            content_type = "video"
            content = message.video.file_id
        elif message.voice:
            content_type = "voice"
            content = message.voice.file_id
        elif message.video_note:
            content_type = "video_note"
            content = message.video_note.file_id
        elif message.document:
            content_type = "document"
            content = message.document.file_id
        elif message.sticker:
            content_type = "sticker"
            content = message.sticker.file_id

        await message_queue.put((user_id, "💌\n\n" + content if content_type=="text" else content, content_type))
        return

    # ===== ПОЛЬЗОВАТЕЛЬ =====
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
    asyncio.create_task(queue_worker())  # запускаємо чергу
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
