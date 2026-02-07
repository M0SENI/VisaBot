# src/handlers/admin.py
from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.utils.states import set_state, clear_state
from src.database.db_manager import Session
from src.database.models import Product, ProductContent


def admin_products_menu(bot: TeleBot, call: CallbackQuery):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Add Product", callback_data="admin:add_product"),
        InlineKeyboardButton("Edit Product", callback_data="admin:edit_product"),
        InlineKeyboardButton("List Products", callback_data="admin:list_products"),
        InlineKeyboardButton("Delete Product", callback_data="admin:delete_product"),
    )
    markup.add(InlineKeyboardButton("Back to Admin Panel", callback_data="admin:main"))

    bot.edit_message_text(
        "Product Settings",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


# ── List Products ──
def admin_list_products(bot: TeleBot, call: CallbackQuery):
    session = Session()
    try:
        products = session.query(Product).order_by(Product.id.desc()).all()
        print(f"[ADMIN LIST] Found {len(products)} products")

        if not products:
            text = "No products found."
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Back to Product Settings", callback_data="admin:products")
            )
        else:
            text = "Products List:\n\n"
            for p in products:
                text += f"ID: {p.id} | Code: {p.code} | Name: {p.name} | Price: {p.price:,} IRR\n"

            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(InlineKeyboardButton("Back to Product Settings", callback_data="admin:products"))

        # Delete the previous message (photo or text) to avoid edit error
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            print("[ADMIN LIST] Deleted previous message")
        except Exception as del_e:
            print(f"[ADMIN LIST DELETE ERROR] {str(del_e)}")  # Continue even if delete fails

        # Send new text message
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=markup
        )
        print("[ADMIN LIST] New message sent")
    except Exception as e:
        print(f"[ADMIN LIST ERROR] {str(e)}")
        bot.send_message(
            call.message.chat.id,
            "Error loading products. Please try again.",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Back to Product Settings", callback_data="admin:products")
            )
        )
    finally:
        session.close()


# ── View single product (for list & delete/edit selection) ──
def admin_view_product(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            bot.answer_callback_query(call.id, "Product not found!", show_alert=True)
            return

        text = (
            f"Product ID: {product.id}\n"
            f"Code: {product.code}\n"
            f"Name: {product.name}\n"
            f"Price: {product.price:,} IRR\n"
            f"Description:\n{product.description_text or 'None'}"
        )

        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Back to List", callback_data="admin:list_products")
        )

        if product.photo_file_id:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_photo(
                call.message.chat.id,
                product.photo_file_id,
                caption=text,
                reply_markup=markup
            )
        else:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
    finally:
        session.close()


# ── Edit Product ──
def admin_edit_product(bot: TeleBot, call: CallbackQuery):
    session = Session()
    try:
        products = session.query(Product).all()
        if not products:
            text = "No products to edit."
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Back", callback_data="admin:products")
            )
        else:
            text = "Select a product to edit:"
            markup = InlineKeyboardMarkup(row_width=1)
            for p in products:
                markup.add(InlineKeyboardButton(f"{p.code} - {p.name}", callback_data=f"admin:select_edit:{p.id}"))
            markup.add(InlineKeyboardButton("Back", callback_data="admin:products"))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    finally:
        session.close()


def admin_select_edit(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            bot.answer_callback_query(call.id, "Product not found!", show_alert=True)
            return

        text = f"You selected product: {product.name}"
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(f"Change Price (Current: {product.price:,} IRR)", callback_data=f"admin:edit_price:{product.id}"))
        markup.add(InlineKeyboardButton("Edit Descriptions", callback_data=f"admin:edit_descriptions:{product.id}"))
        markup.add(InlineKeyboardButton("Back", callback_data="admin:edit_product"))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    finally:
        session.close()


def admin_edit_price(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            bot.answer_callback_query(call.id, "Product not found!", show_alert=True)
            return

        text = (
            f"Please send the new price (English numbers only)\n"
            f"Current price: {product.price:,} IRR"
        )
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Back", callback_data=f"admin:select_edit:{product.id}")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        set_state(call.from_user.id, 'admin_edit_price', {'product_id': product_id})
    finally:
        session.close()


def admin_edit_descriptions(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product or not product.description_text:
            text = "No descriptions to edit."
        else:
            text = "Current descriptions:\nSelect one to edit:"
            markup = InlineKeyboardMarkup(row_width=1)
            descriptions = product.description_text.split('\n')
            for i, desc in enumerate(descriptions, 1):
                if desc.strip():
                    markup.add(InlineKeyboardButton(f"Description {i}: {desc[:30]}...", callback_data=f"admin:edit_desc_item:{product.id}:{i}"))
            markup.add(InlineKeyboardButton("Back", callback_data=f"admin:select_edit:{product.id}"))

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
    finally:
        session.close()


# ── Delete Product ──
def admin_delete_product(bot: TeleBot, call: CallbackQuery):
    session = Session()
    try:
        products = session.query(Product).all()
        if not products:
            text = "No products to delete."
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Back", callback_data="admin:products")
            )
        else:
            text = "Select a product to delete:"
            markup = InlineKeyboardMarkup(row_width=1)
            for p in products:
                markup.add(InlineKeyboardButton(f"{p.code} - {p.name}", callback_data=f"admin:confirm_delete:{p.id}"))
            markup.add(InlineKeyboardButton("Back", callback_data="admin:products"))

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    finally:
        session.close()


def admin_confirm_delete(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            bot.answer_callback_query(call.id, "Product not found!", show_alert=True)
            return

        text = (
            f"Are you sure you want to delete this product?\n\n"
            f"ID: {product.id}\n"
            f"Name: {product.name}\n"
            f"Price: {product.price:,} IRR\n"
            f"Description: {product.description_text or 'None'}"
        )
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Yes, Delete", callback_data=f"admin:delete_confirm_yes:{product.id}"),
            InlineKeyboardButton("No", callback_data="admin:delete_product")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    finally:
        session.close()


def admin_delete_confirm_yes(bot: TeleBot, call: CallbackQuery, product_id: int):
    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        if product:
            session.delete(product)
            session.commit()
            bot.edit_message_text(
                f"Product {product.code} - {product.name} deleted successfully.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("Back to Product Settings", callback_data="admin:products")
                )
            )
        else:
            bot.answer_callback_query(call.id, "Product not found!", show_alert=True)
    finally:
        session.close()
        
        
def admin_start_add_product(bot: TeleBot, call: CallbackQuery):
    """Start the add product flow"""
    user_id = call.from_user.id
    set_state(user_id, 'admin_add_product_photo')

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Skip Photo", callback_data="admin:add_product_skip_photo"),
        InlineKeyboardButton("Back", callback_data="admin:products")
    )

    bot.edit_message_text(
        "Please send one photo of the product (or skip).",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )
    
    
def admin_skip_photo(bot: TeleBot, call: CallbackQuery):
    user_id = call.from_user.id
    set_state(user_id, 'admin_add_product_name', {'photo_file_id': None})
    bot.edit_message_text(
        "Photo skipped.\n\nPlease send the product name:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Cancel", callback_data="admin:cancel_add_product")
        )
    )