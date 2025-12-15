# main.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading

# 🔐 Дані
TOKEN = "8556657168:AAFwnvcgwL-RjJ_tHcMe_D_qrUnsT-XH2a0"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 💬 Зв'язок повідомлення бота → user_id
reply_map = {}

# 🚫 Заблоковані
banned_users = set()

# 👨‍💼 Користувач → призначений адмін
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

# --- СООБЩЕНИЯ ---
@dp.message()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    # 👤 Користувач пише
    if message.chat.id != ADMIN_CHAT_ID:
        # Якщо користувач ще не має адміна або хоче змінити адміна
        if user_id not in user_admin or (message.text and message.text.lower() == "поменять админа"):
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Взять ПЗ", callback_data=f"take_admin_{user_id}")]]
            )
            await bot.send_message(ADMIN_CHAT_ID,
                                   f"💬 Новое сообщение от @{message.from_user.username or 'без_юзернейма'} (ID: {user_id})\n"
                                   f"Пользователь хочет назначить админа.",
                                   reply_markup=keyboard)
            # зберігаємо ID повідомлення бота
            sent = await bot.send_message(ADMIN_CHAT_ID, message.text or "[медиа]", reply_markup=keyboard)
            reply_map[sent.message_id] = user_id
            return

        # Є призначений адмін → пересилаємо тільки йому
        admin_id = user_admin[user_id]
        header = f"💬 От @{message.from_user.username or 'без_юзернейма'} (ID: {user_id}):\n\n"

        if message.text:
            sent = await bot.send_message(admin_id, header + message.text)
        elif message.photo:
            sent = await bot.send_photo(admin_id, message.photo[-1].file_id, caption=header)
        elif message.video:
            sent = await bot.send_video(admin_id, message.video.file_id, caption=header)
        elif message.voice:
            sent = await bot.send_voice(admin_id, message.voice.file_id, caption=header)
        elif message.document:
            sent = await bot.send_document(admin_id, message.document.file_id, caption=header)
        else:
            sent = await bot.send_message(admin_id, header + "[неподдерживаемый тип]")

        reply_map[sent.message_id] = user_id

    # 🛠 Адмін пише
    else:
        if not message.reply_to_message:
            return

        original_user_id = reply_map.get(message.reply_to_message.message_id)
        if not original_user_id:
            return

        # Перевіряємо, чи адмін є призначеним для цього користувача
        if user_admin.get(original_user_id) != message.from_user.id:
            return  # інші адміні не можуть відповісти

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

# --- Обробка кнопок ---
@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    data = callback.data
    admin_id = callback.from_user.id

    if data.startswith("take_admin_"):
        user_id = int(data.split("_")[-1])
        user_admin[user_id] = admin_id
        await callback.message.edit_reply_markup(None)
        await bot.send_message(admin_id, f"✅ Ты взял ПЗ пользователя {user_id}")

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
