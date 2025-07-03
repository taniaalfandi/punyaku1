from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users = db.users
files = db.files
premium_users = db.premium_users
admins = db.admins

def add_user(user_id: int, username: str):
    users.update_one(
        {"user_id": user_id},
        {"$set": {"username": username}},
        upsert=True
    )

def add_premium(user_id: int, expiry_date: str):
    premium_users.update_one(
        {"user_id": user_id},
        {"$set": {"expiry": expiry_date}},
        upsert=True
    )

def delete_premium(user_id: int):
    premium_users.delete_one({"user_id": user_id})

def add_admin(user_id: int):
    admins.insert_one({"user_id": user_id})

def delete_admin(user_id: int):
    admins.delete_one({"user_id": user_id})

def is_premium(user_id: int) -> bool:
    return premium_users.find_one({"user_id": user_id}) is not None

def is_admin(user_id: int) -> bool:
    return admins.find_one({"user_id": user_id}) is not None

def save_file(file_id: str, file_name: str, file_type: str, uploader_id: int):
    files.insert_one({
        "file_id": file_id,
        "file_name": file_name,
        "file_type": file_type,
        "uploader_id": uploader_id,
        "timestamp": datetime.now()
    })

def delete_files(file_ids: list):
    files.delete_many({"file_id": {"$in": file_ids}})
