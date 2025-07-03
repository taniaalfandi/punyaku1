from pymongo import MongoClient
from datetime import datetime, timedelta
from config import MONGO_URI, DB_NAME, CHANNEL_ID

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users = db.users
files = db.files
premium = db.premium
admins = db.admins

# User Management
def add_user(user_id: int, username: str):
    users.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "joined_at": datetime.now()}},
        upsert=True
    )

# Premium Features
def add_premium(user_id: int, days: int):
    expiry = datetime.now() + timedelta(days=days)
    premium.update_one(
        {"user_id": user_id},
        {"$set": {"expiry": expiry}},
        upsert=True
    )

def is_premium(user_id: int) -> bool:
    user = premium.find_one({"user_id": user_id})
    return user and user["expiry"] > datetime.now()

# Admin Control
def add_admin(user_id: int):
    admins.update_one(
        {"user_id": user_id},
        {"$set": {"is_admin": True}},
        upsert=True
    )

def is_admin(user_id: int) -> bool:
    return admins.find_one({"user_id": user_id}) or user_id in ADMINS

# File Storage
def save_file(file_id: str, file_name: str, uploader_id: int):
    files.insert_one({
        "file_id": file_id,
        "file_name": file_name,
        "uploader_id": uploader_id,
        "channel_msg_id": None,
        "timestamp": datetime.now()
    })

def get_file_links(limit=10):
    return list(files.find().sort("timestamp", -1).limit(limit))
