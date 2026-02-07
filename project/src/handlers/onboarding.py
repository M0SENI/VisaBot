# Handler for onboarding module
# handlers/onboarding.py
from telebot import TeleBot, types
from src.database.db_manager import get_user, create_user
from src.utils.keyboards import main_menu_keyboard
import random
import string

def start_handler(bot: TeleBot, message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        # Create new user
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        referred_by = None
        args = message.text.split()
        if len(args) > 1:
            ref_code = args[1]
            referrer = Session().query(User).filter_by(referral_code=ref_code).first()
            if referrer:
                referred_by = referrer.id
                # Create referral entry (mock for now)
        
        user_data = {
            'user_id': user_id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'referral_code': referral_code,
            'referred_by': referred_by
        }
        create_user(user_data)
        bot.send_message(message.chat.id, "Welcome! You've been registered.", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "Welcome back!", reply_markup=main_menu_keyboard())