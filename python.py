import os
import uuid
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = "8198025806:AAFlgK3acg0UYo7HdJdO0cULAokYTgS0Rt0"
API_ID = 27342258
API_HASH = "df1d220364ecb7ac56d29152d194e14f"
ADMIN_IDS = [1580687565]  # Replace with your admin ID
AUTO_DELETE_TIME = 60  # Seconds before auto-deleting messages
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://upinputra30:RoOsNOLn8kDv8Vv8@upinputra.lzwpkfr.mongodb.net/?retryWrites=true&w=majority&appName=upinputra")

# Initialize MongoDB
client = MongoClient(MONGODB_URI)
db = client.telegram_file_bot
files_collection = db.files
users_collection = db.users
auto_delete_collection = db.auto_delete

# Initialize Flask app
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Database Functions
def save_file(file_id, file_name, file_type, uploader_id, batch_id=None):
    files_collection.insert_one({
        "file_id": file_id,
        "file_name": file_name,
        "file_type": file_type,
        "uploader_id": uploader_id,
        "upload_time": datetime.now(),
        "batch_id": batch_id
    })

def get_file(file_id):
    return files_collection.find_one({"file_id": file_id})

def get_batch_files(batch_id):
    return list(files_collection.find({"batch_id": batch_id}))

def is_vip(user_id):
    user = users_collection.find_one({"user_id": user_id})
    return user.get("is_vip", False) if user else False

def add_vip_user(user_id, username):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "username": username,
            "is_vip": True,
            "join_time": datetime.now()
        }},
        upsert=True
    )

def schedule_auto_delete(message_id, chat_id):
    auto_delete_collection.insert_one({
        "message_id": message_id,
        "chat_id": chat_id,
        "delete_time": datetime.now() + timedelta(seconds=AUTO_DELETE_TIME)
    })

def check_pending_deletes():
    while True:
        now = datetime.now()
        pending = list(auto_delete_collection.find({"delete_time": {"$lte": now}}))
        
        for doc in pending:
            try:
                bot.delete_message(chat_id=doc["chat_id"], message_id=doc["message_id"])
            except Exception as e:
                print(f"Failed to delete message: {e}")
            
            auto_delete_collection.delete_one({"_id": doc["_id"]})
        
        time.sleep(10)

# Command Handlers
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        "🔹 /upload - Upload a file (VIP only)\n"
        "🔹 /batch - Start batch upload (VIP only)\n"
        "🔹 /vip - Become a VIP member"
    )

def upload(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_vip(user.id) and user.id not in ADMIN_IDS:
        update.message.reply_text("❌ VIP members only!")
        return
    update.message.reply_text("📤 Please upload a file (document/photo).")

def batch_start(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_vip(user.id) and user.id not in ADMIN_IDS:
        update.message.reply_text("❌ VIP members only!")
        return
    
    batch_id = str(uuid.uuid4())
    context.user_data['batch_id'] = batch_id
    update.message.reply_text("📦 Batch mode activated! Send multiple files, then type /batch_done when finished.")

def batch_done(update: Update, context: CallbackContext):
    if 'batch_id' not in context.user_data:
        update.message.reply_text("❌ No active batch!")
        return
    
    batch_id = context.user_data.pop('batch_id')
    files = get_batch_files(batch_id)
    
    if not files:
        update.message.reply_text("❌ No files in this batch!")
        return
    
    update.message.reply_text(f"✅ {len(files)} files uploaded in batch!")

def handle_file(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_vip(user.id) and user.id not in ADMIN_IDS:
        update.message.reply_text("❌ Access denied!")
        return

    file = update.message.document or update.message.photo[-1] if update.message.photo else None
    if not file:
        update.message.reply_text("⚠️ Invalid file!")
        return

    file_id = file.file_id
    file_name = file.file_name if hasattr(file, 'file_name') else "photo.jpg"
    file_type = "document" if update.message.document else "photo"
    batch_id = context.user_data.get('batch_id')

    save_file(file_id, file_name, file_type, user.id, batch_id)
    msg = update.message.reply_text(f"✅ {file_name} uploaded successfully!" + (" (Batch)" if batch_id else ""))
    schedule_auto_delete(msg.message_id, msg.chat_id)

def vip(update: Update, context: CallbackContext):
    user = update.effective_user
    add_vip_user(user.id, user.username)
    update.message.reply_text("🎉 You're now a VIP member!")

# Setup Dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("upload", upload))
dispatcher.add_handler(CommandHandler("batch", batch_start))
dispatcher.add_handler(CommandHandler("batch_done", batch_done))
dispatcher.add_handler(CommandHandler("vip", vip))
dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo, handle_file))

# Webhook
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'OK'

# Initialize
if __name__ == '__main__':
    # Create indexes
    files_collection.create_index("file_id")
    users_collection.create_index("user_id")
    auto_delete_collection.create_index("delete_time")
    
    # Start auto-delete thread
    threading.Thread(target=check_pending_deletes, daemon=True).start()
    
    # Set webhook and run Flask app
    bot.set_webhook(f"https://your-heroku-app.herokuapp.com/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
