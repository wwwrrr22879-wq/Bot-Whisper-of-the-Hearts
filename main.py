# main.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from flask import Flask
import threading

# 🔐 Дані
TOKEN = "8556657168:AAFwnvcgwL-RjJ_tHcMe_D_qrUnsT-XH2a0"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 message_id бота в адмін-чаті → user_id
reply_map = {}

# 🚫 Заблоковані
banned_users = set()

# 👤 Користувач → Адмін
user_admin = {}  # user_id: admin_id

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

# --- ОБРОБКА ПОВІДОМЛЕНЬ ---
@dp.message()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    # Користувач пише в бот → адмін-чат
    if message.chat.id != ADMIN_CHAT_ID:
        # Перевірка чи користувач вже має адміна
        assigned_admin = user_admin.get(user_id)
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        header = f"💬 От {username}\nID: {user_id}\n\n"

        if message.text and message.text.lower() == "поменять админа":
            # користувач хоче змінити адміна
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Взять ПЗ", callback_data=f"take_{user_id}")]
                ]
            )
            await bot.send_message(ADMIN_CHAT_ID, f"Пользователь {username} хочет поменять админа", reply_markup=keyboard)
            return

        # Відправка повідомлення з кнопкою, якщо адмін не призначений
        if not assigned_admin:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Взять ПЗ", callback_data=f"take_{user_id}")]
                ]
            )
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
            else:
                sent = await bot.send_message(ADMIN_CHAT_ID, header + "[неподдерживаемый тип]", reply_markup=keyboard)
        else:
            # Відправка тільки призначеному адміну
            if message.text:
                sent = await bot.send_message(assigned_admin, header + message.text)
            elif message.photo:
                sent = await bot.send_photo(assigned_admin, message.photo[-1].file_id, caption=header)
            elif message.video:
                sent = await bot.send_video(assigned_admin, message.video.file_id, caption=header)
            elif message.voice:
                sent = await bot.send_voice(assigned_admin, message.voice.file_id, caption=header)
            elif message.document:
                sent = await bot.send_document(assigned_admin, message.document.file_id, caption=header)
            else:
                sent = await bot.send_message(assigned_admin, header + "[неподдерживаемый тип]")

        # зберігаємо ID повідомлення БОТА
        reply_map[sent.message_id] = user_id

    # Адмін відповідає користувачу
    else:
        if not message.reply_to_message:
            return

        original_user_id = reply_map.get(message.reply_to_message.message_id)
        if not original_user_id:
            return

        # Перевірка, чи цей адмін призначений користувачу
        if user_admin.get(original_user_id) and user_admin[original_user_id] != message.from_user.id:
            return  # повідомлення йде тільки від призначеного адміна

        try:
            if message.text:
                await bot.send_message(original_user_id, f"💌 Ответ администратора:\n\n{message.text}")
            elif message.photo:
                await bot.send_photo(original_user_id, message.photo[-1].file_id)
            elif message.video:
                await bot.send_video(original_user_id, message.video.file_id)
            elif message.voice:
                await bot.send_voice(original_user_id, message.voice.file_id)
            elif message.document:
                await bot.send_document(original_user_id, message.document.file_id)
        except:
            await bot.send_message(ADMIN_CHAT_ID, f"⚠️ Пользователь {original_user_id} заблокировал бота.")

# --- Обробка callback кнопок ---
@dp.callback_query()
async def callbacks(query: CallbackQuery):
    data = query.data
    if data.startswith("take_"):
        user_id = int(data.split("_")[1])
        user_admin[user_id] = query.from_user.id
        await query.message.edit_reply_markup()  # прибираємо кнопку
        await query.answer(f"✅ Вы взяли ПЗ пользователя {user_id}")

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
