import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from database import *
from config import BOT_TOKEN, ADMINS

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ===== HANDLER UTAMA =====
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    add_user(user_id, username)
    await message.reply("🎉 Selamat datang di File Store Bot!")

# ===== FITUR PREMIUM =====
@dp.message_handler(commands=['addpremium'])
async def add_premium_cmd(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("❌ Hanya Admin!")
    args = message.get_args().split()
    if len(args) != 2:
        return await message.reply("Format: /addpremium <user_id> <expiry_date>")
    user_id, expiry = int(args[0]), args[1]
    add_premium(user_id, expiry)
    await message.reply(f"✅ User {user_id} sekarang Premium hingga {expiry}!")

@dp.message_handler(commands=['delpremium'])
async def del_premium_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ Hanya Admin!")
    user_id = int(message.get_args())
    delete_premium(user_id)
    await message.reply(f"✅ User {user_id} dihapus dari Premium!")

# ===== FITUR ADMIN =====
@dp.message_handler(commands=['addadmin'])
async def add_admin_cmd(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("❌ Hanya Owner!")
    user_id = int(message.get_args())
    add_admin(user_id)
    await message.reply(f"✅ User {user_id} sekarang Admin!")

@dp.message_handler(commands=['deladmin'])
async def del_admin_cmd(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("❌ Hanya Owner!")
    user_id = int(message.get_args())
    delete_admin(user_id)
    await message.reply(f"✅ User {user_id} dihapus dari Admin!")

# ===== FITUR FILE STORE =====
@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_file(message: types.Message):
    user_id = message.from_user.id
    file_id = message.document.file_id
    file_name = message.document.file_name
    save_file(file_id, file_name, "document", user_id)
    await message.reply("📁 File berhasil disimpan!")

@dp.message_handler(commands=['batch_delete'])
async def batch_delete(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ Hanya Admin!")
    file_ids = message.get_args().split()
    delete_files(file_ids)
    await message.reply(f"🗑️ {len(file_ids)} file dihapus!")

# ===== AUTO DELETE MESSAGE =====
@dp.message_handler(commands=['autodelete'])
async def auto_delete(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ Hanya Admin!")
    seconds = int(message.get_args())
    await message.delete()
    reply = await message.reply(f"⚠ Pesan ini akan dihapus dalam {seconds} detik!")
    await asyncio.sleep(seconds)
    await reply.delete()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
