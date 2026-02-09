# main.py
import telebot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import BOT_TOKEN, ADMIN_ID , WALLET_ADDRESS
from src.database.db_manager import init_db
from src.utils.states import (
    set_state, get_state, get_state_data, clear_state, append_to_state_list , back_state
)
from src.database.models import Order , User

# ایمپورت تمام هندلرها
from src.handlers import (
    onboarding,
    profile,
    wallet,
    orders,
    support,
    vip,
    admin,
    visa_card
)

bot = telebot.TeleBot(BOT_TOKEN)
init_db()

def get_main_menu_markup(user_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Visa Card Order", callback_data="menu:visa_card"),
        InlineKeyboardButton("Wallet",          callback_data="menu:wallet"),
        InlineKeyboardButton("Profile",         callback_data="menu:profile"),
        InlineKeyboardButton("Orders",          callback_data="menu:orders"),
        InlineKeyboardButton("Support",         callback_data="menu:support"),
    )
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("Admin Panel", callback_data="admin:main"))
    return markup


# ── شروع ربات ──
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    text = (
        "Welcome to Visa Card Bot!\n"
        "Choose an option below:"
    )
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=get_main_menu_markup(user_id)
    )
    
    
@bot.message_handler(content_types=['text', 'photo'])  # فقط عکس و متن رو بگیر (بهینه‌تر)
def text_or_media_handler(message):
    user_id = message.from_user.id
    
    # لاگ اولیه - همیشه باید چاپ بشه
    print(f"[HANDLER START] User: {user_id} | Type: {message.content_type} | Text: {message.text or '(no text)'}")
    
    state = get_state(user_id)
    print(f"[HANDLER] Current state: {state}")
    
    if not state:
        print("[HANDLER] No state found - replying with menu message")
        bot.reply_to(message, "Please use the inline buttons.")
        return

    try:
        if state == 'admin_add_product_photo':
            print("[PHOTO STATE] Entering photo handler")
            if message.content_type == 'photo':
                photo_id = message.photo[-1].file_id
                print(f"[PHOTO SAVED] File ID: {photo_id}")
                
                # ذخیره state جدید
                set_state(user_id, 'admin_add_product_name', {'photo_file_id': photo_id})
                print("[STATE UPDATED] Changed to admin_add_product_name")
                
                bot.reply_to(message, "Photo received! Please send the product name:")
            else:
                print("[PHOTO STATE] Not a photo")
                bot.reply_to(message, "Please send a photo or click Skip.")
                
        elif state.startswith('order_'):
            data = get_state_data(user_id) or {}
            product_id = data.get('product_id')
            product_name = data.get('product_name', 'Unknown')
            product_price = data.get('product_price', 0)

            if not product_id:
                bot.reply_to(message, "Order session expired or invalid. Please start again.")
                clear_state(user_id)
                return

            cancel_markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Cancel", callback_data="order:cancel")
            )

            if state == 'order_full_name':
                full_name = message.text.strip() if message.text else ''
                if full_name:
                    data = get_state_data(user_id) or {}
                    data['full_name'] = full_name
                    set_state(user_id, 'order_address', data)
                    
                    # پیام مرحله بعدی رو ارسال کن
                    bot.reply_to(
                        message,
                        "Please enter your address in English format:",
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton("Cancel", callback_data="order:cancel")
                        )
                    )
                else:
                    bot.reply_to(message, "Full name cannot be empty. Try again.")

            elif state == 'order_address':
                address = message.text.strip() if message.text else ''
                if address:
                    data = get_state_data(user_id) or {}
                    data['address'] = address
                    set_state(user_id, 'order_mobile', data)
                    
                    bot.reply_to(
                        message,
                        "Please enter your mobile number in English digits:",
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton("Cancel", callback_data="order:cancel")
                        )
                    )
                else:
                    bot.reply_to(message, "Address cannot be empty. Try again.")

            elif state == 'order_mobile':
                mobile = message.text.strip() if message.text else ''
                if mobile.isdigit() and len(mobile) >= 10:
                    data['mobile'] = mobile
                    set_state(user_id, 'order_passport', data)
                    bot.reply_to(message, "Please send your passport image:", reply_markup=cancel_markup)
                else:
                    bot.reply_to(message, "Mobile number must be digits only and at least 10 characters. Try again.", reply_markup=cancel_markup)

            elif state == 'order_passport':
                if message.content_type == 'photo':
                    passport_id = message.photo[-1].file_id
                    data['passport_file_id'] = passport_id
                    set_state(user_id, 'order_verification_video', data)
                    guide_markup = InlineKeyboardMarkup(row_width=2)
                    guide_markup.add(
                        InlineKeyboardButton("Guide", callback_data="order:verification_guide"),
                        InlineKeyboardButton("Cancel", callback_data="order:cancel")
                    )
                    bot.reply_to(message, "Please send the verification video:", reply_markup=guide_markup)
                else:
                    bot.reply_to(message, "Please send a photo of your passport.", reply_markup=cancel_markup)

            elif state == 'order_verification_video':
                if message.content_type == 'video':
                    video_id = message.video.file_id
                    data['verification_video_id'] = video_id
                    deposit_amount = product_price * 0.2
                    text = (
                        f"All required files received.\n\n"
                        f"Final step: Please deposit 20% of the product price ({deposit_amount:,.0f} IRR) as deposit to the wallet address:\n"
                        f"{WALLET_ADDRESS}\n\n"
                        f"Send the transaction hash in the next message.\n"
                        f"Note: This is only a 20% deposit."
                    )
                    set_state(user_id, 'order_deposit_hash', data)
                    bot.reply_to(message, text, reply_markup=cancel_markup)
                else:
                    bot.reply_to(message, "Please send a video file.", reply_markup=cancel_markup)

            elif state == 'order_deposit_hash':
                tx_hash = message.text.strip()
                if tx_hash:
                    data['tx_hash'] = tx_hash

                    session = Session()
                    try:
                        # آپدیت User
                        user = session.query(User).filter_by(user_id=user_id).first()
                        if user:
                            user.full_name = data.get('full_name')
                            user.address = data.get('address')
                            user.mobile = data.get('mobile')
                            user.passport_file_id = data.get('passport_file_id')
                            user.verification_video_id = data.get('verification_video_id')

                        # ایجاد Order
                        order = Order(
                            user_id=user_id,
                            product_id=product_id,
                            product_name=product_name,
                            product_price=product_price,
                            full_name=data.get('full_name'),
                            address=data.get('address'),
                            mobile=data.get('mobile'),
                            passport_file_id=data.get('passport_file_id'),
                            verification_video_id=data.get('verification_video_id'),
                            tx_hash=tx_hash,
                            status='pending'
                        )
                        session.add(order)
                        session.commit()

                        # ارسال به ادمین
                        media = []
                        if data.get('passport_file_id'):
                            media.append(telebot.types.InputMediaPhoto(data['passport_file_id'], caption="Passport"))
                        if data.get('verification_video_id'):
                            media.append(telebot.types.InputMediaVideo(data['verification_video_id'], caption="Verification Video"))

                        caption = (
                            f"New Order #{order.id}\n"
                            f"User ID: {user_id}\n"
                            f"Full Name: {data.get('full_name', 'N/A')}\n"
                            f"Address: {data.get('address', 'N/A')}\n"
                            f"Mobile: {data.get('mobile', 'N/A')}\n"
                            f"Product: {product_name}\n"
                            f"Price: {product_price:,} IRR\n"
                            f"Deposit Hash: {tx_hash}\n"
                            f"Status: Pending"
                        )

                        markup = InlineKeyboardMarkup(row_width=2)
                        markup.add(
                            InlineKeyboardButton("Accept", callback_data=f"admin:accept_order:{order.id}"),
                            InlineKeyboardButton("Reject", callback_data=f"admin:reject_order:{order.id}")
                        )
                        markup.add(InlineKeyboardButton("User Profile", callback_data=f"menu:profile:{user_id}"))

                        if media:
                            bot.send_media_group(ADMIN_ID, media)
                        bot.send_message(ADMIN_ID, caption, reply_markup=markup)

                        bot.send_message(
                            message.chat.id,
                            "Your order has been submitted successfully! We will review it soon.",
                            reply_markup=get_main_menu_markup(user_id)
                        )
                        clear_state(user_id)
                    except Exception as e:
                        bot.send_message(message.chat.id, f"Error submitting order: {str(e)}")
                    finally:
                        session.close()
                else:
                    bot.reply_to(message, "Transaction hash cannot be empty. Try again.", reply_markup=cancel_markup)


        elif state == 'admin_add_product_name':
            name = message.text.strip() if message.text else ''
            print(f"[NAME STATE] Received name: '{name}'")
            
            if name:
                current_data = get_state_data(user_id) or {}
                current_data['name'] = name
                set_state(user_id, 'admin_add_product_price', current_data)
                print("[STATE UPDATED] Changed to admin_add_product_price")
                bot.reply_to(message, "Name saved. Please send the product price (English numbers only):")
            else:
                bot.reply_to(message, "Name cannot be empty. Try again.")
                
        elif state == 'order_full_name':
            full_name = message.text.strip() if message.text else ''
            if full_name:
                data = get_state_data(user_id) or {}
                data['full_name'] = full_name
                set_state(user_id, 'order_address', data)
                
                # پیام مرحله بعدی رو ارسال کن
                bot.reply_to(
                    message,
                    "Please enter your address in English format:",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("Cancel", callback_data="order:cancel")
                    )
                )
            else:
                bot.reply_to(message, "Full name cannot be empty. Try again.")

        elif state == 'admin_add_product_price':
            print("[PRICE STATE] Entering price handler")
            try:
                price_str = message.text.strip() if message.text else ''
                price = int(price_str)
                print(f"[PRICE SAVED] {price}")
                
                current_data = get_state_data(user_id) or {}
                current_data['price'] = price
                current_data['descriptions'] = []
                set_state(user_id, 'admin_add_product_description', current_data)
                print("[STATE UPDATED] Changed to admin_add_product_description")
                
                bot.reply_to(
                    message,
                    "Price saved.\n\nNow send descriptions one by one.\nWhen finished, send /done"
                )
            except ValueError:
                print("[PRICE ERROR] Invalid number")
                bot.reply_to(message, "Price must be a number (English digits only). Try again.")

        elif state == 'admin_add_product_description':
            text = message.text.strip() if message.text else ''
            print(f"[DESC STATE] Received: '{text}'")
            
            if text == '/done':
                print("[DESC STATE] /done received - saving product")
                from src.database.db_manager import Session
                from src.database.models import Product

                data = get_state_data(user_id) or {}
                session = Session()
                try:
                    product = Product(
                        code=f"PK-{session.query(Product).count() + 1:03d}",
                        name=data.get('name', 'Unnamed'),
                        price=data.get('price', 0),
                        description_text="\n".join(data.get('descriptions', [])) or None,
                        photo_file_id=data.get('photo_file_id')
                    )
                    session.add(product)
                    session.commit()
                    print(f"[PRODUCT SAVED] ID: {product.id} | Code: {product.code}")

                    reply_text = (
                        f"Product added successfully!\n\n"
                        f"Code: {product.code}\n"
                        f"Name: {product.name}\n"
                        f"Price: {product.price:,} IRR\n"
                        f"Description:\n{product.description_text or 'None'}\n"
                        f"Photo ID: {product.photo_file_id or 'None'}"
                    )
                    bot.send_message(
                        message.chat.id,
                        reply_text,
                        reply_markup=get_main_menu_markup(user_id)
                    )
                    clear_state(user_id)
                except Exception as e:
                    print(f"[SAVE ERROR] {str(e)}")
                    bot.send_message(message.chat.id, f"Error saving product: {str(e)}")
                finally:
                    session.close()
            else:
                append_to_state_list(user_id, 'descriptions', text)
                count = len(get_state_data(user_id).get('descriptions', []))
                print(f"[DESC ADDED] Total: {count}")
                bot.reply_to(message, f"Description {count} saved.\nSend next or /done to finish.")

        elif state == 'admin_edit_price':
            print("[EDIT PRICE STATE] Entering")
            try:
                new_price = int(message.text.strip())
                data = get_state_data(user_id)
                product_id = data.get('product_id')
                print(f"[EDIT PRICE] New price: {new_price} for product ID: {product_id}")
                
                session = Session()
                try:
                    product = session.query(Product).filter_by(id=product_id).first()
                    if product:
                        old_price = product.price
                        product.price = new_price
                        session.commit()
                        print("[PRICE UPDATED] Success")
                        bot.send_message(
                            message.chat.id,
                            f"Price updated!\n"
                            f"Product: {product.name} (ID: {product.id})\n"
                            f"New Price: {new_price:,} IRR (was {old_price:,})",
                            reply_markup=get_main_menu_markup(user_id)
                        )
                    clear_state(user_id)
                finally:
                    session.close()
            except ValueError:
                bot.reply_to(message, "Please send a valid number (English digits).")
            except Exception as e:
                print(f"[EDIT PRICE ERROR] {str(e)}")
                bot.reply_to(message, f"Error: {str(e)}")

    except Exception as e:
        print(f"[HANDLER CRASH] {type(e).__name__}: {str(e)}")
        bot.reply_to(message, f"An error occurred in handler: {str(e)}")
        
        
# ── دیسپچر مرکزی کال‌بک‌ها ──
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call: CallbackQuery):
    try:
        data = call.data.split(':')
        if not data:
            bot.answer_callback_query(call.id, "Invalid data")
            return

        menu = data[0]

        if menu == 'menu':
            sub = data[1] if len(data) > 1 else 'main'

            if sub == 'main':
                bot.edit_message_text(
                    "Main Menu",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_main_menu_markup(call.from_user.id)
                )

            elif sub == 'profile':
                profile.profile_handler(bot, call)
                
            elif menu == 'order' and sub == 'back':
                previous_state, previous_data = back_state(call.from_user.id)
                if previous_state:
                    print(f"[BACK] Returned to {previous_state}")
                    # نمایش دوباره پیام مرحله قبلی
                    if previous_state == 'order_full_name':
                        bot.edit_message_text(
                            "Please enter your full name in English (back from previous step):",
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=InlineKeyboardMarkup().add(
                                InlineKeyboardButton("Cancel", callback_data="order:cancel")
                            )
                        )
                    elif previous_state == 'order_address':
                        bot.edit_message_text(
                            "Please enter your address in English format (back):",
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=InlineKeyboardMarkup().add(
                                InlineKeyboardButton("Cancel", callback_data="order:cancel")
                            )
                        )
                    # برای بقیه stateها هم مشابه اضافه کن (mobile, passport, video, hash)
                    else:
                        bot.edit_message_text(
                            f"Returned to previous step: {previous_state}",
                            call.message.chat.id,
                            call.message.message_id
                        )
                    set_state(call.from_user.id, previous_state, previous_data)
                else:
                    bot.answer_callback_query(call.id, "No previous step available.", show_alert=True)
                
            elif sub == 'list_products':
                admin.admin_list_products(bot, call)
            
            elif menu == 'order' and sub == 'start':
                try:
                    product_id = int(data[2])
                    print(f"[ORDER START] Starting order for product {product_id}")
                    
                    # پیام قبلی (عکس) رو حذف کن
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                        print("[ORDER START] Deleted previous photo message")
                    except Exception as del_e:
                        print(f"[ORDER DELETE ERROR] {str(del_e)}")

                    # حالا شروع جریان سفارش با پیام جدید
                    visa_card.start_order_flow(bot, call, product_id)
                except (IndexError, ValueError):
                    bot.answer_callback_query(call.id, "Invalid product ID", show_alert=True)

            elif sub == 'edit_product':
                admin.admin_edit_product(bot, call)

            elif sub == 'delete_product':
                admin.admin_delete_product(bot, call)

            elif sub == 'wallet':
                wallet.wallet_handler(bot, call)

            elif sub == 'visa_card':
                visa_card.visa_card_handler(bot, call)

            elif sub == 'orders':
                orders.orders_handler(bot, call)   # اگر هنوز وجود ندارد، placeholder بگذار

            elif sub == 'support':
                support.support_handler(bot, call)

            elif sub == 'vip':
                vip.vip_handler(bot, call)

        elif menu == 'wallet':
            action = ':'.join(data[1:])
            wallet.wallet_callback_handler(bot, call, action)

        elif menu == 'visa':
            action = ':'.join(data[1:])
            print(f"[VISA DISPATCH] Processing action: {action}")
            visa_card.visa_callback_handler(bot, call, action)

        elif menu == 'admin':
            if call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "Access denied", show_alert=True)
                return

            sub = data[1] if len(data) > 1 else 'main'

            if sub == 'main' or sub == '':
                # Admin Panel اصلی
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(
                    InlineKeyboardButton("Product Settings", callback_data="admin:products"),
                    InlineKeyboardButton("Back to Main Menu", callback_data="menu:main")
                )
                bot.edit_message_text(
                    "Admin Panel",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup
                )

            elif sub == 'products':
                admin.admin_products_menu(bot, call)

            elif sub == 'add_product':
                admin.admin_start_add_product(bot, call)
                
            elif sub == 'add_product_skip_photo':
                admin.admin_skip_photo(bot, call)
                
            elif sub == 'cancel_add_product':
                admin.admin_cancel_add_product(bot, call)
                
            elif sub == 'list_products':
                admin.admin_list_products(bot, call)

            elif sub == 'edit_product':
                admin.admin_edit_product(bot, call)

            elif sub == 'delete_product':
                admin.admin_delete_product(bot, call)

            # انتخاب محصول برای ویرایش یا حذف
            elif sub == 'select_edit':
                product_id = int(data[2])
                admin.admin_select_edit(bot, call, product_id)

            elif sub == 'edit_price':
                product_id = int(data[2])
                admin.admin_edit_price(bot, call, product_id)

            elif sub == 'edit_descriptions':
                product_id = int(data[2])
                admin.admin_edit_descriptions(bot, call, product_id)

            # تأیید حذف
            elif sub == 'confirm_delete':
                product_id = int(data[2])
                admin.admin_confirm_delete(bot, call, product_id)

            elif sub == 'delete_confirm_yes':
                product_id = int(data[2])
                admin.admin_delete_confirm_yes(bot, call, product_id)

            # برای view در لیست
            elif sub == 'view_product':
                product_id = int(data[2])
                admin.admin_view_product(bot, call, product_id)

            elif sub == 'add_product_skip_photo':
                admin.admin_skip_photo(bot, call)
            elif sub == 'cancel_add_product':
                admin.admin_cancel_add_product(bot, call)

            else:
                bot.answer_callback_query(call.id, f"Unknown admin command: {sub}", show_alert=True)

    except Exception as e:
        print(f"Callback error: {e}")
        try:
            bot.answer_callback_query(call.id, "An error occurred", show_alert=True)
        except:
            pass


print("Bot is running...")
bot.infinity_polling(timeout=20, long_polling_timeout=30)