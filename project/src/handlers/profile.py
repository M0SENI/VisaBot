# src/handlers/profile.py
from telebot import TeleBot
from telebot.types import CallbackQuery
from src.utils.keyboards import main_menu_keyboard

def profile_handler(bot: TeleBot, call: CallbackQuery):
    user = call.from_user
    text = f"""
👤 Profile

Name: {user.first_name} {user.last_name or ''}
Username: @{user.username or 'None'}
ID: {user.id}

🚧 Other information will be added soon.
    """.strip()

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu_keyboard()  # یا یه دکمه Back
    )