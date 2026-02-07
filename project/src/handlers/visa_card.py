# src/handlers/visa_card.py
from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.database.db_manager import Session
from src.database.models import Product, ProductContent
from src.utils.keyboards import visa_menu_keyboard, products_list_keyboard, product_detail_keyboard
import telebot
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


def start_order_name(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            bot.answer_callback_query(call.id, "Product not found!", show_alert=True)
            return

        # ذخیره product_id در state
        set_state(call.from_user.id, 'order_full_name', {
            'product_id': product_id,
            'product_name': product.name,
            'product_price': product.price
        })

        text = (
            f"You are ordering: {product.name}\n"
            f"Price: {product.price:,} IRR\n\n"
            "Please enter your full name in English:"
        )
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Cancel", callback_data="order:cancel")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    finally:
        session.close()

def visa_callback_handler(bot: TeleBot, call: CallbackQuery, action: str):
    print(f"[VISA CALLBACK] Action received: {action}")  # دیباگ اصلی

    data_parts = action.split(':')
    if not data_parts:
        bot.answer_callback_query(call.id, "Invalid action", show_alert=True)
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
        if len(data_parts) > 1 and data_parts[1] == 'continue':
            # ادامه ثبت سفارش
            try:
                product_id = int(data_parts[2])
                start_order_name(bot, call, product_id)  # یا هر تابعی که برای ادامه داری
            except (IndexError, ValueError):
                bot.answer_callback_query(call.id, "Invalid product ID", show_alert=True)
        else:
            # شروع لیست محصولات
            show_products_list(bot, call)

    elif cmd == 'products':
        try:
            page = int(data_parts[1]) if len(data_parts) > 1 else 1
            print(f"[PRODUCTS] Loading page {page}")
            show_products_list(bot, call, page)
        except (IndexError, ValueError):
            print("[PRODUCTS] Invalid page number")
            bot.answer_callback_query(call.id, "Invalid page number", show_alert=True)

    elif cmd == 'product':
        try:
            product_id = int(data_parts[1])
            show_product_detail(bot, call, product_id)
        except (IndexError, ValueError):
            bot.answer_callback_query(call.id, "Invalid product ID", show_alert=True)

    elif cmd == 'guide':
        try:
            product_id = int(data_parts[1])
            show_product_guide(bot, call, product_id)
        except (IndexError, ValueError):
            bot.answer_callback_query(call.id, "Invalid guide request", show_alert=True)

    elif cmd == 'order_product':
        try:
            product_id = int(data_parts[1])
            start_order_flow(bot, call, product_id)
        except (IndexError, ValueError):
            bot.answer_callback_query(call.id, "Invalid order request", show_alert=True)

    elif cmd == 'verification_guide':
        bot.answer_callback_query(call.id, "Guide coming soon.", show_alert=True)

    elif cmd in ['charge', 'documents']:
        bot.answer_callback_query(call.id, "This section is not implemented yet.", show_alert=True)

    else:
        print(f"[VISA UNKNOWN] Unknown cmd: {cmd} (full action: {action})")
        bot.answer_callback_query(call.id, "Invalid command", show_alert=True)
        
        

def show_products_list(bot: TeleBot, call: CallbackQuery, page: int = 1):
    print(f"[SHOW LIST] Page {page} requested by user {call.from_user.id}")
    
    session = Session()
    try:
        products = session.query(Product).order_by(Product.id.desc()).all()
        print(f"[SHOW LIST] Found {len(products)} products")

        if not products:
            text = "No products available at the moment.\nPlease check back later."
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Back to Visa Menu", callback_data="visa:menu")
            )
        else:
            text = f"Available Products (Page {page}):"
            markup = products_list_keyboard(products, page)

        # Delete the previous message (photo or text) to avoid edit error
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            print("[SHOW LIST] Deleted previous message")
        except Exception as del_e:
            print(f"[SHOW LIST DELETE ERROR] {str(del_e)}")  # Continue even if delete fails

        # Send new text message
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=markup
        )
        print("[SHOW LIST] New message sent")
    except Exception as e:
        print(f"[SHOW LIST ERROR] {str(e)}")
        bot.send_message(
            call.message.chat.id,
            "Error loading products. Please try again or contact support.",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Back to Visa Menu", callback_data="visa:menu")
            )
        )
    finally:
        session.close()
        
        

def show_product_detail(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            bot.answer_callback_query(call.id, "Product not found!", show_alert=True)
            return

        text = f"Product: {product.name}\nCode: {product.code}\nPrice: {product.price:,} IRR\nDescription: {product.description_text or 'None'}"

        markup = product_detail_keyboard(product.id)

        # پیام قبلی رو حذف کن (برای جلوگیری از ارور edit روی عکس)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass  # اگر حذف نشد مهم نیست

        # پیام جدید بفرست
        if product.photo_file_id:
            bot.send_photo(
                call.message.chat.id,
                product.photo_file_id,
                caption=text,
                parse_mode='Markdown',
                reply_markup=markup
            )
        else:
            bot.send_message(
                call.message.chat.id,
                text,
                parse_mode='Markdown',
                reply_markup=markup
            )

    finally:
        session.close()

def show_product_guide(bot: TeleBot, call: CallbackQuery, product_id: int):
    """Placeholder for guide (will be editable from admin later)"""
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

        # ذخیره موقت product_id در state
        set_state(call.from_user.id, 'order_confirm_docs', {'product_id': product_id, 'product_name': product.name, 'product_price': product.price})

        text = (
            "You are about to start the order registration process.\n"
            f"Do you have the required documents?\n"
            f"It is recommended to review the required documents for the product '{product.name}' using the back button."
        )
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Continue", callback_data=f"order:continue:{product_id}"),
            InlineKeyboardButton("Back", callback_data=f"visa:product:{product_id}")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    finally:
        session.close()