from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def premium_keyboard():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("💎 Get Premium", callback_data="buy_premium")
    )
