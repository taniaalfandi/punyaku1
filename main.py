import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import MessageToDeleteNotFound
from config import BOT_TOKEN, CHANNEL_ID
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ===== BASIC COMMANDS =====
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.reply("📁 Welcome to File Store Bot!")

# ===== ADMIN TOOLS =====
@dp.message_handler(commands=['addadmin'])
async def add_admin_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ Admin only!")
    try:
        user_id = int(message.get_args())
        add_admin(user_id)
        await message.reply(f"✅ Added admin: {user_id}")
    except:
        await message.reply("Usage: /addadmin <user_id>")

# ===== PREMIUM SYSTEM =====
@dp.message_handler(commands=['addpremium'])
async def add_premium_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ Admin only!")
    try:
        args = message.get_args().split()
        user_id, days = int(args[0]), int(args[1])
        add_premium(user_id, days)
        await message.reply(f"⭐ User {user_id} is now premium for {days} days!")
    except:
        await message.reply("Usage: /addpremium <user_id> <days>")

# ===== FILE HANDLING =====
@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_file(message: types.Message):
    file_id = message.document.file_id
    file_name = message.document.file_name
    
    # Forward to channel
    channel_msg = await bot.send_document(
        chat_id=CHANNEL_ID,
        document=file_id,
        caption=f"Uploaded by: @{message.from_user.username}"
    )
    
    # Save to DB
    save_file(file_id, file_name, message.from_user.id)
    
    # Generate link
    file_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{channel_msg.message_id}"
    await message.reply(f"🔗 Your file link:\n{file_link}")

# ===== BATCH LINK GENERATOR =====
@dp.message_handler(commands=['batchlinks'])
async def batch_links(message: types.Message):
    if not is_premium(message.from_user.id):
        return await message.reply("❌ Premium feature!")
    
    recent_files = get_file_links(10)
    if not recent_files:
        return await message.reply("No files found!")
    
    links = [
        f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{f['channel_msg_id']}"
        for f in recent_files
    ]
    
    await message.reply("🔗 Recent files:\n" + "\n".join(links))

# ===== AUTO DELETE =====
@dp.message_handler(commands=['autodel'])
async def auto_delete(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ Admin only!")
    
    try:
        sec = int(message.get_args())
        msg = await message.reply(f"🗑 This message will self-destruct in {sec}s...")
        await asyncio.sleep(sec)
        await msg.delete()
    except:
        await message.reply("Usage: /autodel <seconds>")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp)
