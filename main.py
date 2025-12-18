# main.py
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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
user_admin = {}            # user_id -> admin_id
user_messages = {}         # user_id -> count сообщений
secret_achievements = {}   # user_id -> set секретных достижений
all_users = set()          # все пользователи
blocked_users = set()      # заблокировавшие бота
taken_users = set()        # пользователи, которых взяли админы
user_topic = {}            # user_id -> тема
reply_map = {}             # message_id админ → user_id

# учёт недели и нормы админов
admin_week = None
admin_stats = {}           # admin_id -> количество сообщений за неделю

# ================== КНОПКИ ==================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏆 Мои достижения")],
        [KeyboardButton(text="📩 Новые обращения"), KeyboardButton(text="🆘 Нужна поддержка")],
        [KeyboardButton(text="📜 Правила"), KeyboardButton(text="⏰ График работы")]
    ], resize_keyboard=True
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

# ================== СТАТИСТИКА БОТА ==================
@dp.message(Command("stats"))
async def bot_stats(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer(
        f"📊 Статистика бота\n\n"
        f"👥 Всего пользователей: {len(all_users)}\n"
        f"🚫 Заблокировали бота: {len(blocked_users)}\n"
        f"💬 Активных: {len(user_messages)}"
    )

# ================== РАССЫЛКА ==================
@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Используй: /broadcast текст")
        return
    text = parts[1]
    sent = 0
    for uid in list(all_users):
        try:
            await bot.send_message(uid, text)
            sent += 1
        except:
            blocked_users.add(uid)
    await message.answer(f"✅ Рассылка завершена. Отправлено: {sent}")

# ================== ПРАВИЛА ==================
@dp.message(F.text == "📜 Правила")
async def rules(message: types.Message):
    await message.answer(
        "📜 Правила\n"
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
        "⏰ График работы\n"
        "🌞 08:00 – 22:00 — дневная смена\n"
        "🌙 22:00 – 08:00 — ночная смена\nПо МСК"
    )

# ================== ДОСТИЖЕНИЯ ==================
@dp.message(F.text == "🏆 Мои достижения")
async def achievements(message: types.Message):
    uid = message.from_user.id
    count = user_messages.get(uid, 0)
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
    achieved = [f"🏆 {title} — {desc}" for n,(title,desc) in milestones.items() if count>=n]
    secrets = secret_achievements.get(uid,set())
    if secrets:
        achieved.append("🔒 Секретные достижения:")
        achieved.extend(f"✨ {s}" for s in secrets)
    if not achieved:
        achieved.append("❌ Пока нет достижений")
    await message.answer("🎖 *Твои достижения:*\n" + "\n".join(achieved), parse_mode="Markdown")

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
    user_messages[uid] = user_messages.get(uid,0)+1

    # ===== АДМИН ЧАТ =====
    if message.chat.id == ADMIN_CHAT_ID:
        admin_stats[uid] = admin_stats.get(uid,0)+1
        if message.text:
            text = message.text.lower()
            if text=="норма":
                count = admin_stats.get(uid,0)
                status = "✅ Норма выполнена" if count>=NORM_PER_WEEK else "❌ Норма не выполнена"
                await message.reply(f"📈 Твоя норма: {count}/{NORM_PER_WEEK}\n{status}")
                return
            if text=="норма вся":
                lines=["📊 *Норма администраторов:*"]
                for aid,cnt in admin_stats.items():
                    status = "✅" if cnt>=NORM_PER_WEEK else "❌"
                    lines.append(f"• {aid}: {cnt}/{NORM_PER_WEEK} {status}")
                await message.reply("\n".join(lines),parse_mode="Markdown")
                return
        if not message.reply_to_message:
            return
        user_id = reply_map.get(message.reply_to_message.message_id)
        if not user_id or user_admin.get(user_id)!=uid:
            return
        try:
            if message.text:
                await bot.send_message(user_id,"💌\n\n"+message.text)
        except:
            blocked_users.add(user_id)
        return

    # ===== ПОЛЬЗОВАТЕЛЬ =====
    if message.text in ("📩 Новые обращения","🆘 Нужна поддержка"):
        user_topic[uid] = message.text
        await message.answer("✉️ Напиши своё сообщение, и администрация ответит!")
        return

    if message.text and message.text.lower()=="поменять админа":
        user_admin.pop(uid,None)
        taken_users.discard(uid)
        text = f"ID: {uid}\n\nПоменять админа"
        sent = await bot.send_message(ADMIN_CHAT_ID,text,reply_markup=take_pz_kb)
        reply_map[sent.message_id]=uid
        return

    topic = user_topic.get(uid,"Без темы")
    text = f"Тема: {topic}\nID: {uid}\n\n"
    kb = take_pz_kb if uid not in taken_users else None
    sent = await bot.send_message(ADMIN_CHAT_ID,text+(message.text or "[медиа]"),reply_markup=kb)
    reply_map[sent.message_id]=uid

# ================== KEEP ALIVE ==================
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is alive"

def run():
    app.run("0.0.0.0",8080)
threading.Thread(target=run).start()

# ================== RUN ==================
if __name__=="__main__":
    asyncio.run(dp.start_polling(bot))
