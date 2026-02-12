# main.py
import telebot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import BOT_TOKEN, ADMIN_ID, WALLET_ADDRESS
from src.database.db_manager import init_db, Session
from src.utils.states import (
    set_state, get_state, get_state_data, clear_state, append_to_state_list, back_state
)
from src.database.models import Order, User, Product
from src.utils.keyboards import (
    visa_menu_keyboard, products_list_keyboard, product_detail_keyboard, get_main_menu_markup
)

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
    
    

@bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
def text_or_media_handler(message):
    user_id = message.from_user.id
    
    print(f"[HANDLER START] User: {user_id} | Type: {message.content_type} | Text: {message.text or '(no text)'}")
    
    state = get_state(user_id)
    print(f"[HANDLER] Current state: {state}")
    
    if not state:
        bot.reply_to(message, "Please use the inline buttons.")
        return

    try:
        # ── بخش ادمین: افزودن محصول ──
        if state == 'admin_add_product_photo':
            if message.content_type == 'photo':
                photo_id = message.photo[-1].file_id
                print(f"[PHOTO SAVED] File ID: {photo_id}")
                set_state(user_id, 'admin_add_product_name', {'photo_file_id': photo_id})
                bot.reply_to(
                    message,
                    "Photo received! Please send the product name:",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("Cancel", callback_data="admin:cancel_add_product")
                    )
                )
            else:
                bot.reply_to(message, "Please send a photo or click Skip.")

        elif state == 'admin_add_product_name':
            name = message.text.strip()
            if name:
                data = get_state_data(user_id) or {}
                data['name'] = name
                set_state(user_id, 'admin_add_product_price', data)
                bot.reply_to(
                    message,
                    "Name saved. Please send the product price in English numbers:",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("Cancel", callback_data="admin:cancel_add_product")
                    )
                )
            else:
                bot.reply_to(message, "Product name cannot be empty. Try again.")

        elif state == 'admin_add_product_price':
            try:
                price = int(message.text.strip())
                data = get_state_data(user_id) or {}
                data['price'] = price
                set_state(user_id, 'admin_add_product_description', data)
                bot.reply_to(
                    message,
                    "Price saved.\n\nNow send descriptions one by one. When finished, send /done:",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("Cancel", callback_data="admin:cancel_add_product")
                    )
                )
            except ValueError:
                bot.reply_to(message, "Price must be a number. Try again.")

        elif state == 'admin_add_product_description':
            text = message.text.strip()
            if text == '/done':
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
                    bot.send_message(
                        message.chat.id,
                        f"Product added successfully!\n\n"
                        f"Code: {product.code}\n"
                        f"Name: {product.name}\n"
                        f"Price: {product.price:,} IRR\n"
                        f"Description:\n{product.description_text or 'None'}\n"
                        f"Photo ID: {product.photo_file_id or 'None'}",
                        reply_markup=get_main_menu_markup(user_id)
                    )
                    clear_state(user_id)
                except Exception as e:
                    bot.send_message(message.chat.id, f"Error saving product: {str(e)}")
                finally:
                    session.close()
            else:
                append_to_state_list(user_id, 'descriptions', text)
                count = len(get_state_data(user_id).get('descriptions', []))
                bot.reply_to(message, f"Description {count} saved.\nSend next or /done to finish.")

        # ── بخش سفارش ویزا کارت ── (دقیقاً طبق فلو شما)
        elif state.startswith('order_'):
            data = get_state_data(user_id) or {}
            product_id = data.get('product_id')
            product_name = data.get('product_name', 'Unknown')
            product_price = data.get('product_price', 0)

            if not product_id:
                bot.reply_to(message, "Order session expired. Please start again.")
                clear_state(user_id)
                return

            cancel_markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Cancel", callback_data="order:cancel")
            )

            if state == 'order_full_name':
                full_name = message.text.strip()
                if full_name:
                    data['full_name'] = full_name
                    set_state(user_id, 'order_address', data)
                    bot.reply_to(
                        message,
                        "Please enter your address in English format:",
                        reply_markup=cancel_markup
                    )
                else:
                    bot.reply_to(message, "Full name cannot be empty. Try again.", reply_markup=cancel_markup)

            elif state == 'order_address':
                address = message.text.strip()
                if address:
                    data['address'] = address
                    set_state(user_id, 'order_mobile', data)
                    bot.reply_to(
                        message,
                        "Please enter your mobile number in English digits:",
                        reply_markup=cancel_markup
                    )
                else:
                    bot.reply_to(message, "Address cannot be empty. Try again.", reply_markup=cancel_markup)

            elif state == 'order_mobile':
                mobile = message.text.strip()
                if mobile.isdigit() and len(mobile) >= 10:
                    data['mobile'] = mobile
                    set_state(user_id, 'order_passport', data)
                    bot.reply_to(
                        message,
                        "Please send your passport image:",
                        reply_markup=cancel_markup
                    )
                else:
                    bot.reply_to(message, "Mobile number must be digits only and at least 10 characters.", reply_markup=cancel_markup)

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
                    bot.reply_to(
                        message,
                        "Please send the verification video:",
                        reply_markup=guide_markup
                    )
                else:
                    bot.reply_to(message, "Please send a photo of your passport.", reply_markup=cancel_markup)

            elif state == 'order_verification_video':
                print(f"[VERIFICATION VIDEO] Received content_type: {message.content_type}")
                
                file_id = None
                if message.content_type == 'video':
                    file_id = message.video.file_id
                elif message.content_type == 'document' and message.document.mime_type.startswith('video/'):
                    file_id = message.document.file_id

                if file_id:
                    data['verification_video_id'] = file_id
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
                        # Update User
                        user = session.query(User).filter_by(user_id=user_id).first()
                        if user:
                            user.full_name = data.get('full_name')
                            user.address = data.get('address')
                            user.mobile = data.get('mobile')
                            user.passport_file_id = data.get('passport_file_id')
                            user.verification_video_id = data.get('verification_video_id')
                            session.commit()

                        # Create Order
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

                        # Send to admin
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
                        markup.add(
                            InlineKeyboardButton(
                                "Open User Chat",
                                url=f"tg://user?id={user_id}"
                            )
                        )

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
                        print(f"[ORDER SAVE ERROR] {str(e)}")
                        bot.send_message(message.chat.id, f"Error submitting order: {str(e)}")
                    finally:
                        session.close()
                else:
                    bot.reply_to(message, "Transaction hash cannot be empty. Try again.", reply_markup=cancel_markup)

    except Exception as e:
        print(f"[HANDLER CRASH] {type(e).__name__}: {str(e)}")
        bot.reply_to(message, f"An error occurred: {str(e)}")
        
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