# main.py
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ================== НАЛАШТУВАННЯ ==================
TOKEN = "8556657168:AAFwnvcgwL-RjJ_tHcMe_D_qrUnsT-XH2a0"
OWNER_ID = 1470389051  # твій Telegram ID

# ==================================================
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🏛 Усі адмін-групи, де є бот
admin_chats = set()

# 🔗 звʼязок повідомлення адміна ↔ користувач
reply_map = {}

# 🚫 заблоковані користувачі
banned_users = set()

# ================== ВІДСТЕЖЕННЯ ГРУП ==================
@dp.my_chat_member()
async def track_groups(event: types.ChatMemberUpdated):
    me = await bot.get_me()
    if event.new_chat_member.user.id == me.id:
        if event.new_chat_member.status in ("member", "administrator"):
            admin_chats.add(event.chat.id)
            print(f"➕ Бот додан у чат: {event.chat.id}")

# ================== /start ==================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    if message.from_user.id in banned_users:
        return

    await message.answer(
        "🌸 Привет, солнышко!\n\n"
        "Я — бот *Шепот сердец 💌*\n"
        "Напиши своё сообщение — и я передам его администраторам.\n"
        "Они обязательно ответят тебе с теплом 🤍",
        parse_mode="Markdown"
    )

# ================== БАН ==================
@dp.message(Command("ban"))
async def ban_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может банить.")
        return

    if not message.reply_to_message:
        await message.reply("⚠️ Ответь на сообщение пользователя.")
        return

    user_id = reply_map.get(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("⚠️ Пользователь не найден.")
        return

    banned_users.add(user_id)
    await message.reply(f"🚫 Пользователь {user_id} забанен.")

# ================== РАЗБАН ==================
@dp.message(Command("unban"))
async def unban_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Только владелец может разбанить.")
        return

    if not message.reply_to_message:
        await message.reply("⚠️ Ответь на сообщение пользователя.")
        return

    user_id = reply_map.get(message.reply_to_message.message_id)
    if not user_id:
        await message.reply("⚠️ Пользователь не найден.")
        return

    banned_users.discard(user_id)
    await message.reply(f"✅ Пользователь {user_id} разбанен.")

# ================== СПИСОК БАНОВ ==================
@dp.message(Command("banned"))
async def banned_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ Нет доступа.")
        return

    if not banned_users:
        await message.reply("✅ Забаненных нет.")
    else:
        await message.reply("🚫 Забаненные:\n" + "\n".join(map(str, banned_users)))

# ================== ОСНОВНА ЛОГІКА ==================
@dp.message()
async def handle_all(message: types.Message):
    user_id = message.from_user.id

    if user_id in banned_users:
        return

    # -------- КОРИСТУВАЧ → АДМІНИ --------
    if message.chat.type == "private":
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        header = (
            "📩 ПОДДЕРЖКА\n"
            f"👤 {username}\n"
            f"🆔 {user_id}\n\n"
        )

        for chat_id in admin_chats:
            try:
                if message.text:
                    sent = await bot.send_message(chat_id, header + message.text)
                elif message.photo:
                    sent = await bot.send_photo(chat_id, message.photo[-1].file_id, caption=header)
                elif message.video:
                    sent = await bot.send_video(chat_id, message.video.file_id, caption=header)
                elif message.voice:
                    sent = await bot.send_voice(chat_id, message.voice.file_id, caption=header)
                elif message.document:
                    sent = await bot.send_document(chat_id, message.document.file_id, caption=header)
                else:
                    sent = await bot.send_message(chat_id, header + "[неподдерживаемый тип]")

                reply_map[sent.message_id] = user_id
            except:
                pass

    # -------- АДМІН → КОРИСТУВАЧ --------
    elif message.chat.id in admin_chats:
        if message.reply_to_message and message.reply_to_message.message_id in reply_map:
            user_id = reply_map[message.reply_to_message.message_id]

            try:
                if message.text:
                    await bot.send_message(user_id, "💌 Ответ администратора:\n\n" + message.text)
                elif message.photo:
                    await bot.send_photo(user_id, message.photo[-1].file_id, caption="💌 Ответ администратора")
                elif message.video:
                    await bot.send_video(user_id, message.video.file_id, caption="💌 Ответ администратора")
                elif message.voice:
                    await bot.send_voice(user_id, message.voice.file_id, caption="💌 Ответ администратора")
                elif message.document:
                    await bot.send_document(user_id, message.document.file_id, caption="💌 Ответ администратора")
            except:
                await bot.send_message(
                    message.chat.id,
                    f"⚠️ Пользователь {user_id} заблокировал бота."
                )

# ================== FLASK ДЛЯ RENDER ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(dp.start_polling(bot))
