from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def premium_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💎 Upgrade Premium", callback_data="upgrade_premium"))
    return markup
