# utils/keyboards.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    # Main menu as inline for callback-based navigation
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Profile", callback_data="menu:profile"),
        InlineKeyboardButton("Order Visa Card", callback_data="menu:visa_card"),
        InlineKeyboardButton("Wallet", callback_data="menu:wallet"),
        InlineKeyboardButton("Orders", callback_data="menu:orders"),
        InlineKeyboardButton("Support", callback_data="menu:support"),
        InlineKeyboardButton("VIP", callback_data="menu:vip")
    )
    return markup

def wallet_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Show Balance", callback_data="wallet:balance"),
        InlineKeyboardButton("Charge Wallet", callback_data="wallet:charge"),
        InlineKeyboardButton("Transfer", callback_data="wallet:transfer"),
        InlineKeyboardButton("Transactions", callback_data="wallet:transactions"),
        InlineKeyboardButton("Back", callback_data="menu:main")
    )
    return markup

# Example inline for confirmation
def confirm_keyboard(action: str):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Yes", callback_data=f"confirm:{action}:yes"),
        InlineKeyboardButton("No", callback_data=f"confirm:{action}:no")
    )
    return markup


# utils/keyboards.py

def visa_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("سفارش ویزاکارت", callback_data="visa:order"),
        InlineKeyboardButton("شارژ ویزا کارت", callback_data="visa:charge"),  # بعداً پیاده‌سازی
        InlineKeyboardButton("مدارک مورد نیاز", callback_data="visa:documents"),
        InlineKeyboardButton("🔙 برگشت", callback_data="menu:main")
    )
    return markup


def products_list_keyboard(products, page=1, per_page=5):
    markup = InlineKeyboardMarkup(row_width=1)
    start = (page - 1) * per_page
    end = start + per_page
    page_products = products[start:end]

    for prod in page_products:
        markup.add(InlineKeyboardButton(prod.name, callback_data=f"visa:product:{prod.id}"))

    # صفحه‌بندی
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Previous", callback_data=f"visa:products:{page-1}"))
    if len(products) > end:
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"visa:products:{page+1}"))
    if nav:
        markup.row(*nav)

    markup.add(InlineKeyboardButton("Back to Menu", callback_data="visa:menu"))
    return markup


def product_detail_keyboard(product_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Order Product", callback_data=f"visa:order_product:{product_id}"),
        InlineKeyboardButton("Guide", callback_data=f"visa:guide:{product_id}")
    )
    markup.add(InlineKeyboardButton("Back to List", callback_data="visa:products:1"))  # صفحه 1
    return markup