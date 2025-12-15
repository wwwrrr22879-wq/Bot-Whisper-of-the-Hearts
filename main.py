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
user_topic = {}          # user_id -> "Нужна поддержка" / "Новые обращения" / None

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
def get_achievement_text(count, uid):
    achievements_list = []
    if count >= 1:
        achievements_list.append(("🥇 Новичок", "Отправил первое сообщение"))
    if count >= 5:
        achievements_list.append(("🎖️ Малый активист", "Отправил 5 сообщений"))
    if count >= 50:
        achievements_list.append(("🏅 Активист", "Отправил 50 сообщений"))
    if count >= 100:
        achievements_list.append(("🏆 Большой активист", "Отправил 100 сообщений"))
    if count >= 250:
        achievements_list.append(("🌟 Мега активист", "Отправил 250 сообщений"))
    if count >= 500:
        achievements_list.append(("💎 Супер активист", "Отправил 500 сообщений"))
    if count >= 1000:
        achievements_list.append(("🔥 Легенда", "Отправил 1000 сообщений"))
    if count >= 2500:
        achievements_list.append(("💫 Сверхзвезда", "Отправил 2500 сообщений"))
    if count >= 5000:
        achievements_list.append(("🌌 Бессмертный", "Отправил 5000 сообщений"))

    secrets = secret_achievements.get(uid, set())
    for s in secrets:
        achievements_list.append(("🔒 Секретное", s))
    return achievements_list

@dp.message(F.text == "🏆 Мои достижения")
async def achievements(message: types.Message):
    uid = message.from_user.id
    count = user_messages.get(uid, 0)
    achieved = get_achievement_text(count, uid)
    if not achieved:
        await message.answer("❌ Пока нет достижений")
        return
    text = "🏆 *Твои достижения:*\n\n"
    for name, desc in achieved:
        text += f"🎯 {name} — {desc}\n"
    await message.answer(text, parse_mode="Markdown")

# ================== ВЫБОР ТЕМЫ ==================
@dp.message(F.text == "📩 Новые обращения")
async def new_request(message: types.Message):
    uid = message.from_user.id
    user_topic[uid] = "Новые обращения"
    await message.answer("Напиши своё сообщение и администрации с радостью ответят.")

@dp.message(F.text == "🆘 Нужна поддержка")
async def need_support(message: types.Message):
    uid = message.from_user.id
    user_topic[uid] = "Нужна поддержка"
    await message.answer("Напиши своё сообщение и администрации с радостью ответят.")

# ================== CALLBACK ==================
@dp.callback_query(F.data == "take_pz")
async def take_pz(call: types.CallbackQuery):
    admin_id = call.from_user.id
    msg = call.message
    user_id = int(msg.text.split("ID:")[1].split("\n")[0])
    user_admin[user_id] = admin_id
    taken_users.add(user_id)
    # Убираем кнопку после взятия
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("Пользователь взят")

# ================== СООБЩЕНИЯ ==================
@dp.message()
async def messages(message: types.Message):
    uid = message.from_user.id
    now = datetime.now()
    topic = user_topic.get(uid, None)

    # ===== УЧЁТ СООБЩЕНИЙ =====
    if topic is None:  # только если не выбрана тема кнопки
        user_messages[uid] = user_messages.get(uid, 0) + 1
        secrets = secret_achievements.setdefault(uid, set())
        if 22 <= now.hour or now.hour < 8:
            secrets.add("Ночная активность")
        if now.hour == 10 and now.minute == 35:
            secrets.add("Точное время 10:35")
    else:
        # если выбрана тема, не начисляем достижения
        pass

    # ===== СМЕНА АДМИНА =====
    if message.text and message.text.lower() == "поменять админа":
        user_admin.pop(uid, None)
        taken_users.discard(uid)
        topic = None
        user_topic[uid] = None

    # ===== ПОЛЬЗОВАТЕЛЬ → АДМИНЫ =====
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "Пользователь без юзернейма"
        text = f"{username}\nID: {uid}\n\n"
        kb = take_pz_kb if uid not in taken_users else None

        if topic:  # пользователь выбрал тему кнопки
            await message.answer(f"Напиши своё сообщение и администрации с радостью ответят.")
            return

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
