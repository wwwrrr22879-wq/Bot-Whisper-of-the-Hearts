# main.py
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
import json
import os

# ====== ТВОЇ НАЛАШТУВАННЯ (вставлені як ти просив) ======
TOKEN = "8445444619:AAFdR4jF1IQJzEFlL_DsJ-JTxT9nwkwwC58"
ADMIN_CHAT_ID = -1003120877184   # група адміністраторів (починається з -100...)
OWNER_ID = 1470389051            # твій особистий ID
# =========================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словник для зв'язку: message_id (в адмін-чати) -> user_id
reply_map = {}

# Файл для збереження забанених користувачів
BANNED_FILE = "banned.json"
if os.path.exists(BANNED_FILE):
    try:
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            banned_users = set(json.load(f))
    except Exception:
        banned_users = set()
else:
    banned_users = set()

def save_bans():
    try:
        with open(BANNED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(banned_users), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving bans:", e)

# ====== /start ======
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "🌸 Привет, солнышко!\n\n"
        "Я — бот *Шепот сердец 💌*\n"
        "Напиши любое сообщение — оно будет переслано в администрацию.\n"
        "Администраторы ответят тебе лично 💌",
        parse_mode="Markdown"
    )

# ====== Бан-команди для власника (тільки в адмін-чаті) ======
@dp.message(Command("ban"))
async def ban_command(message: Message):
    # Використовувати /ban тільки ти (OWNER_ID) і в адмін-чати (ADMIN_CHAT_ID)
    if message.from_user.id != OWNER_ID:
        await message.reply("⛔ У вас нет прав на выполнение этой команды.")
        return
    if message.chat.id != ADMIN_CHAT_ID:
        await message.reply("⛔ Команду нужно выполнять в админ-чате.")
        return
    if not message.reply_to_message:
        await message.reply("❗ Используй /ban в ответ (reply) на пересланное сообщение бота.")
        return

    replied_msg = message.reply_to_message
    # Ми зберігаємо mapping: ключ - message_id, значення - user_id
    if replied_msg.message_id not in reply_map:
        await message.reply("⚠️ Не найден user по этому reply (возможно старое сообщение).")
        return

    user_to_ban = reply_map[replied_msg.message_id]
    banned_users.add(user_to_ban)
    save_bans()
    await message.reply(f"✅ Пользователь {user_to_ban} заблокирован.")
    # опційне повідомлення користувачу:
    try:
        await bot.send_message(user_to_ban, "⛔ Ты заблокирован администрацией и не можешь отправлять сообщения этому боту.")
    except Exception:
        pass

@dp.message(Command("unban"))
async def unban_command(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("⛔ У вас нет прав на выполнение этой команды.")
        return
    if message.chat.id != ADMIN_CHAT_ID:
        await message.reply("⛔ Команду нужно выполнять в админ-чате.")
        return
    if not message.reply_to_message:
        await message.reply("❗ Используй /unban в ответ (reply) на пересланное сообщение бота.")
        return

    replied_msg = message.reply_to_message
    if replied_msg.message_id not in reply_map:
        await message.reply("⚠️ Не найден user по этому reply.")
        return

    user_to_unban = reply_map[replied_msg.message_id]
    if user_to_unban in banned_users:
        banned_users.remove(user_to_unban)
        save_bans()
        await message.reply(f"✅ Пользователь {user_to_unban} разбанен.")
        try:
            await bot.send_message(user_to_unban, "✅ Тебя разблокировали — теперь можно писать боту.")
        except Exception:
            pass
    else:
        await message.reply("ℹ️ Этот пользователь не был в списке забаненных.")

@dp.message(Command("bannedlist"))
async def banned_list(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("⛔ У вас нет прав на выполнение этой команды.")
        return
    if not banned_users:
        await message.reply("Список забаненных пуст.")
        return
    txt = "Забаненные пользователи (ID):\n" + "\n".join(str(x) for x in banned_users)
    await message.reply(txt)

# ====== Основна логіка пересилки ======
@dp.message()
async def handle_messages(message: Message):
    # Якщо користувач забанений — ігноруємо або шлемо короткий текст
    if message.chat.id != ADMIN_CHAT_ID:
        user_id = message.from_user.id
        if user_id in banned_users:
            try:
                await message.answer("⛔ Ты заблокирован и не можешь писать этому боту.")
            except Exception:
                pass
            return

    # Якщо повідомлення від звичайного користувача — переслати в адмін-чат
    if message.chat.id != ADMIN_CHAT_ID:
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else "без_юзернейма"
        # Якщо це не текст — виводимо підказку
        body = message.text if message.text else "[не текстовое сообщение]"
        text = f"💬 Сообщение от {username} (ID: {user_id}):\n\n{body}"
        try:
            sent = await bot.send_message(ADMIN_CHAT_ID, text)
            # Зберігаємо зв'язок: id повідомлення, що відправили в адмін чат -> user_id
            reply_map[sent.message_id] = user_id
        except Exception as e:
            print("Ошибка при отправке в админ-чат:", e)

    # Якщо повідомлення в адмін-чаті — і це reply на переслане нами повідомлення — переслати юзеру
    elif message.chat.id == ADMIN_CHAT_ID:
        if message.reply_to_message and message.reply_to_message.message_id in reply_map:
            target_user = reply_map[message.reply_to_message.message_id]
            # Якщо ціль в бані — не відправляємо
            if target_user in banned_users:
                await message.reply("⚠️ Этот пользователь заблокирован — сообщение не отправлено.")
                return
            try:
                await bot.send_message(target_user, f"💌 Ответ администратора:\n\n{message.text}")
            except Exception as e:
                await message.reply(f"❗ Не удалось отправить сообщение пользователю (ID {target_user}).")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
