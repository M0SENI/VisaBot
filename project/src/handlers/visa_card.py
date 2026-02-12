# src/handlers/visa_card.py
from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.database.db_manager import Session
from src.database.models import Product, ProductContent
from src.utils.keyboards import visa_menu_keyboard, products_list_keyboard, product_detail_keyboard , get_main_menu_markup
from src.utils.states import set_state, get_state, get_state_data, clear_state
from config.settings import ADMIN_ID, WALLET_ADDRESS


def visa_card_handler(bot: TeleBot, call: CallbackQuery):
    """Entry point to Visa Card section"""
    bot.edit_message_text(
        "Please select an option:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=visa_menu_keyboard()
    )

def visa_callback_handler(bot: TeleBot, call: CallbackQuery, action: str):
    print(f"[VISA CALLBACK] Action received: {action}")
    bot.answer_callback_query(call.id, "Processing...")

    data_parts = action.split(':')
    if not data_parts:
        return

    cmd = data_parts[0]

    if cmd == 'menu':
        bot.edit_message_text(
            "Please select an option:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=visa_menu_keyboard()
        )

    elif cmd == 'order':
        show_products_list(bot, call)

    elif cmd == 'products':
        page = int(data_parts[1]) if len(data_parts) > 1 else 1
        show_products_list(bot, call, page)

    elif cmd == 'product':
        product_id = int(data_parts[1])
        show_product_detail(bot, call, product_id)

    elif cmd == 'guide':
        product_id = int(data_parts[1])
        show_product_guide(bot, call, product_id)

    elif cmd == 'order_product':
        product_id = int(data_parts[1])
        start_order_flow(bot, call, product_id)

    elif cmd == 'order_continue':
        product_id = int(data_parts[1])
        start_order_name(bot, call, product_id)

    elif cmd == 'verification_guide':
        bot.send_message(
            call.message.chat.id,
            "Verification guide is not set yet. Please contact support."
        )

    elif cmd == 'cancel':
        clear_state(call.from_user.id)
        bot.edit_message_text(
            "Operation cancelled.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_main_menu_markup(call.from_user.id)
        )

    else:
        bot.send_message(call.message.chat.id, "Invalid command.")

def show_products_list(bot: TeleBot, call: CallbackQuery, page: int = 1):
    session = Session()
    try:
        products = session.query(Product).order_by(Product.id.desc()).all()
        if not products:
            text = "No products available at the moment.\nComing soon."
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Back", callback_data="visa:menu")
            )
        else:
            text = "Select a product to order:"
            markup = products_list_keyboard(products, page)

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    finally:
        session.close()

def show_product_detail(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            bot.answer_callback_query(call.id, "Product not found!", show_alert=True)
            return

        text = (
            f"Product ID: {product.id}\n"
            f"Code: {product.code}\n"
            f"Name: {product.name}\n"
            f"Price: {product.price:,} IRR\n\n"
            f"Description:\n{product.description_text or 'None'}"
        )

        markup = product_detail_keyboard(product_id)

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    finally:
        session.close()

def show_product_guide(bot: TeleBot, call: CallbackQuery, product_id: int):
    text = (
        "Product Guide:\n"
        "• Step 1 ...\n"
        "• Step 2 ...\n"
        "(This text will be editable from admin panel in the future)"
    )
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Back to Product", callback_data=f"visa:product:{product_id}")
    )
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

def start_order_flow(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            bot.answer_callback_query(call.id, "Product not found!", show_alert=True)
            return

        set_state(call.from_user.id, 'order_full_name', {
            'product_id': product_id,
            'product_name': product.name,
            'product_price': product.price
        })

        text = (
            f"For ordering '{product.name}' at {product.price:,.0f} IRR,\n"
            "Please enter your full name in English:"
        )
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Cancel", callback_data="order:cancel")
        )

        # پیام قبلی رو حذف کن (عکس جزئیات محصول)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=markup
        )
    finally:
        session.close()