# main.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask
import threading

TOKEN = "8291867377:AAGqd4UAVY4gU3zVR5YevZSb1Nly6j6-UDY"
ADMIN_CHAT_ID = -1003120877184
OWNER_ID = 1470389051

bot = Bot(token=TOKEN)
dp = Dispatcher()

reply_map = {}        # message_id бота -> user_id
active_admins = {}   # user_id -> admin_id
banned_users = set()

# ---------- START ----------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🌸 Привет!\n\n"
        "Напиши сообщение — и администратор скоро ответит 💌"
    )

# ---------- INLINE ----------
def take_user_button(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Взять ПЗ", callback_data=f"take:{user_id}")]
        ]
    )

@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    if call.data.startswith("take:"):
        user_id = int(call.data.split(":")[1])
        active_admins[user_id] = call.from_user.id
        await call.message.edit_reply_markup()
        await call.answer("ПЗ взят")

# ---------- MESSAGES ----------
@dp.message()
async def messages(message: types.Message):
    uid = message.from_user.id

    if uid in banned_users:
        return

    # ===== USER → ADMINS =====
    if message.chat.id != ADMIN_CHAT_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "Пользователь без юзернейма"
        header = f"{username}\nID: {uid}\n\n"

        change_admin = message.text and message.text.lower() == "поменять админа"
        if change_admin:
            active_admins.pop(uid, None)

        kb = take_user_button(uid) if uid not in active_admins else None

        if message.text:
            sent = await bot.send_message(ADMIN_CHAT_ID, header + message.text, reply_markup=kb)
        elif message.photo:
            sent = await bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=header, reply_markup=kb)
        elif message.video:
            sent = await bot.send_video(ADMIN_CHAT_ID, message.video.file_id, caption=header, reply_markup=kb)
        elif message.voice:
            sent = await bot.send_voice(ADMIN_CHAT_ID, message.voice.file_id, caption=header)
        elif message.video_note:
            sent = await bot.send_video_note(ADMIN_CHAT_ID, message.video_note.file_id)
        elif message.document:
            sent = await bot.send_document(ADMIN_CHAT_ID, message.document.file_id, caption=header)
        elif message.sticker:
            sent = await bot.send_sticker(ADMIN_CHAT_ID, message.sticker.file_id)
        else:
            return

        reply_map[sent.message_id] = uid

    # ===== ADMIN → USER =====
    else:
        if not message.reply_to_message:
            return

        # 🔥 ГЛАВНЕ ВИПРАВЛЕННЯ
        user_id = reply_map.get(message.reply_to_message.message_id)

        if not user_id and message.reply_to_message.reply_to_message:
            user_id = reply_map.get(message.reply_to_message.reply_to_message.message_id)

        if not user_id:
            return

        if active_admins.get(user_id) != message.from_user.id:
            return

        try:
            if message.text:
                await bot.send_message(user_id, message.text)
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
        except:
            await bot.send_message(ADMIN_CHAT_ID, f"⚠️ Пользователь {user_id} заблокировал бота")

# ---------- KEEP ALIVE ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "alive"

def run():
    app.run("0.0.0.0", 8080)

threading.Thread(target=run).start()

# ---------- RUN ----------
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
