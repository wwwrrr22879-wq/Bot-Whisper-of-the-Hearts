# main.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask
import threading
import datetime

# 🔐 Дані
TOKEN = "8556657168:AAFwnvcgwL-RjJ_tHcMe_D_qrUnsT-XH2a0"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 Зв'язки
reply_map = {}  # message_id бота в адмін-чаті → user_id
admin_map = {}  # user_id → admin_id (хто взяв ПЗ)
user_message_count = {}  # user_id → кількість повідомлень
banned_users = set()
new_user_messages = set()  # щоб кнопка "Взять ПЗ" з'являлась тільки для нових

# --- Основні кнопки ---
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Мои достижения")
    kb.add("Список администраторов")
    kb.add("Новые обращения")
    kb.add("Нужна поддержка")
    kb.add("Правила")
    kb.add("График работы бота")
    return kb

# --- Достижения ---
def check_achievements(user_id):
    count = user_message_count.get(user_id, 0)
    achievements = []

    if count == 1:
        achievements.append("🥇 Первое сообщение")
    if count == 5:
        achievements.append("🎖 Пятое сообщение")
    if count == 50:
        achievements.append("🏅 50 сообщений")
    if count == 100:
        achievements.append("🏆 100 сообщений")
    if count == 250:
        achievements.append("💎 250 сообщений")
    if count == 500:
        achievements.append("💠 500 сообщений")
    if count == 1000:
        achievements.append("💫 1000 сообщений")
    if count == 2500:
        achievements.append("🌟 2500 сообщений")
    if count == 5000:
        achievements.append("🌌 5000 сообщений")
    
    # Секретные
    now = datetime.datetime.now()
    if now.hour == 0 and count % 13 == 0:
        achievements.append("🌙 Секрет: Сообщение ночью")
    if now.minute == 35:
        achievements.append("⏱ Секрет: Написал в 35 минут")
    
    return achievements

# --- START ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    if message.from_user.id in banned_users:
        return
    await message.answer(
        "🌸 Привет! Я — бот Шепот сердец 💌",
        reply_markup=main_keyboard()
    )

# --- Обработка сообщений ---
@dp.message()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    # --- Достижения ---
    user_message_count[user_id] = user_message_count.get(user_id, 0) + 1
    achievements = check_achievements(user_id)

    if message.text == "Мои достижения":
        if achievements:
            text = "\n".join(f"{a}" for a in achievements)
        else:
            text = "🎯 У вас пока нет достижений."
        await message.answer(text)
        return

    # --- Новые обращения ---
    if message.text in ["Новые обращения", "Поменять админа", "Нужна поддержка"]:
        # Інлайн кнопка для взяття ПЗ
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Взять ПЗ", callback_data=f"take_user_{user_id}"))
        text_header = f"💬 Новое сообщение от @{message.from_user.username if message.from_user.username else 'без_юзернейма'}\nID: {user_id}\n\n{message.text}"
        sent = await bot.send_message(ADMIN_CHAT_ID, text_header, reply_markup=kb)
        reply_map[sent.message_id] = user_id
        new_user_messages.add(user_id)
        return

    # --- Сообщения от пользователя ---
    if user_id not in admin_map:
        # Пересылаем в основную админку только новые обращения
        if user_id in new_user_messages:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Взять ПЗ", callback_data=f"take_user_{user_id}"))
            text_header = f"💬 От @{message.from_user.username if message.from_user.username else 'без_юзернейма'}\nID: {user_id}\n\n{message.text}"
            sent = await bot.send_message(ADMIN_CHAT_ID, text_header, reply_markup=kb)
            reply_map[sent.message_id] = user_id
            new_user_messages.discard(user_id)
        else:
            # просто пересылаем без кнопки
            text_header = f"💬 От @{message.from_user.username if message.from_user.username else 'без_юзернейма'}\nID: {user_id}\n\n{message.text}"
            sent = await bot.send_message(ADMIN_CHAT_ID, text_header)
            reply_map[sent.message_id] = user_id
        return

    # --- Админ отвечает пользователю ---
    if user_id in admin_map.values():
        return  # админ не пишет сюда

# --- Обработка callback кнопок ---
@dp.callback_query()
async def callback_take_user(query: types.CallbackQuery):
    data = query.data
    if data.startswith("take_user_"):
        user_id = int(data.split("_")[-1])
        admin_id = query.from_user.id

        # Запоминаем кто взял ПЗ
        admin_map[user_id] = admin_id

        # Убираем кнопку
        await query.message.edit_reply_markup(None)
        await query.answer("Вы взяли ПЗ!")

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
