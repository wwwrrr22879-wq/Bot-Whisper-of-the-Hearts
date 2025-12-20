# main.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask
import threading

# 🔐 Дані
TOKEN = "8291867377:AAGqd4UAVY4gU3zVR5YevZSb1Nly6j6-UDY"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 message_id бота в адмін-чаті → user_id
reply_map = {}

# 👤 user_id → адмін який взяв
active_admins = {}

# 🚫 Заблоковані
banned_users = set()

# --- START ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    if message.from_user.id in banned_users:
        return
    await message.answer(
        "🌸 Привет, солнышко!\n\n"
        "Я — бот *Шепот сердец 💌*\n"
        "Напиши своё сообщение — и я передам его администраторам.\n"
        "Они обязательно ответят тебе ☀️",
        parse_mode="Markdown"
    )

# --- БАН ---
@dp.message(Command("ban"))
async def ban_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return
    user_id = reply_map.get(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("Не удалось определить пользователя.")
        return
    banned_users.add(user_id)
    await message.reply(f"🚫 Пользователь {user_id} забанен.")

# --- РАЗБАН ---
@dp.message(Command("unban"))
async def unban_command(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return
    user_id = reply_map.get(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("Не удалось определить пользователя.")
        return
    banned_users.discard(user_id)
    await message.reply(f"✅ Пользователь {user_id} разбанен.")

# --- Inline кнопка «Взять ПЗ» ---
def take_user_button(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Взять ПЗ", callback_data=f"take_user:{user_id}")]
        ]
    )
    return kb

# --- Обробка callback від кнопки ---
@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    data = call.data
    if data.startswith("take_user:"):
        user_id = int(data.split(":")[1])
        admin_id = call.from_user.id
        active_admins[user_id] = admin_id
        await call.message.edit_reply_markup(reply_markup=None)
        await call.answer(f"Вы взяли ПЗ {user_id}")

# --- СООБЩЕНИЯ ---
@dp.message()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    # Користувач → адмін
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        header = f"💬 {username}\nID: {user_id}\n\n"

        # Перевіряємо чи новий користувач або зміна адміна
        new_user = user_id not in active_admins
        change_admin = message.text and message.text.lower() == "поменять админа"

        kb = take_user_button(user_id) if new_user or change_admin else None

        if message.text:
            sent = await bot.send_message(ADMIN_CHAT_ID, header + message.text, reply_markup=kb)
        elif message.photo:
            sent = await bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=header, reply_markup=kb)
        elif message.video:
            sent = await bot.send_video(ADMIN_CHAT_ID, message.video.file_id, caption=header, reply_markup=kb)
        elif message.voice:
            sent = await bot.send_voice(ADMIN_CHAT_ID, message.voice.file_id, caption=header, reply_markup=kb)
        elif message.document:
            sent = await bot.send_document(ADMIN_CHAT_ID, message.document.file_id, caption=header, reply_markup=kb)
        elif message.sticker:
            sent = await bot.send_sticker(ADMIN_CHAT_ID, message.sticker.file_id)
        else:
            sent = await bot.send_message(ADMIN_CHAT_ID, header + "[неподдерживаемый тип]", reply_markup=kb)

        reply_map[sent.message_id] = user_id

    # Адмін → користувачу
    else:
        if not message.reply_to_message:
            return
        original_user_id = reply_map.get(message.reply_to_message.message_id)
        if not original_user_id:
            return

        # Перевіряємо чи адмін взяв цього користувача
        if active_admins.get(original_user_id) != message.from_user.id:
            return

        try:
            if message.text:
                await bot.send_message(original_user_id, f"{message.text}")
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
