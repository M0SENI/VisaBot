# src/handlers/wallet.py
from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.database.db_manager import get_balance, add_transaction, get_user
from src.database.models import Transaction, TransactionType
from src.utils.keyboards import main_menu_keyboard
from config.settings import CURRENCY
from datetime import datetime

# --- منوی اصلی والت ---
def wallet_handler(bot: TeleBot, call: CallbackQuery):
    user_id = call.from_user.id
    balance = get_balance(user_id)
    
    text = f"""
💰 **کیف پول شما**

موجودی فعلی: **{balance:,.0f}** {CURRENCY}

انتخاب کنید:
    """.strip()
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💳 نمایش موجودی", callback_data="wallet:balance"),
        InlineKeyboardButton("🔋 شارژ کیف پول", callback_data="wallet:charge"),
        InlineKeyboardButton("📜 تاریخچه تراکنش‌ها", callback_data="wallet:transactions:1"),
        InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu:main")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')


# --- مدیریت کال‌بک‌های والت ---
def wallet_callback_handler(bot: TeleBot, call: CallbackQuery, action: str):
    user_id = call.from_user.id
    data_parts = action.split(':')
    cmd = data_parts[0]

    if cmd == 'balance':
        balance = get_balance(user_id)
        bot.answer_callback_query(call.id, f"موجودی شما: {balance:,.0f} {CURRENCY}", show_alert=True)

    elif cmd == 'charge':
        show_charge_options(bot, call)

    elif cmd == 'charge_amount':
        amount = int(data_parts[1])
        show_charge_confirm(bot, call, amount)

    elif cmd == 'confirm_charge':
        amount = int(data_parts[1])
        confirm_charge(bot, call, amount)

    elif cmd == 'transactions':
        page = int(data_parts[1]) if len(data_parts) > 1 else 1
        show_transactions(bot, call, user_id, page)

    else:
        bot.answer_callback_query(call.id, "دستور نامعتبر!")


# --- نمایش گزینه‌های شارژ ---
def show_charge_options(bot: TeleBot, call: CallbackQuery):
    markup = InlineKeyboardMarkup(row_width=2)
    amounts = [100000, 500000, 1000000, 2000000, 5000000]
    buttons = []
    for amount in amounts:
        text = f"{amount:,.0f} {CURRENCY}"
        buttons.append(InlineKeyboardButton(text, callback_data=f"wallet:charge_amount:{amount}"))
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="menu:wallet"))

    bot.edit_message_text(
        f"🔋 مبلغ شارژ را انتخاب کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


# --- تأیید شارژ ---
def show_charge_confirm(bot: TeleBot, call: CallbackQuery, amount: int):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"wallet:confirm_charge:{amount}"),
        InlineKeyboardButton("❌ لغو", callback_data="menu:wallet")
    )

    text = f"""
✅ **درخواست شارژ کیف پول**

مبلغ: **{amount:,.0f}** {CURRENCY}

پس از تأیید، لینک پرداخت کریپتو (مثلاً TRX یا USDT) برای شما ارسال می‌شود.

(در نسخه فعلی: شارژ به صورت mock انجام می‌شود و موجودی اضافه می‌شود)
    """.strip()

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')


# --- انجام شارژ (mock - بعداً واقعی می‌کنی) ---
def confirm_charge(bot: TeleBot, call: CallbackQuery, amount: int):
    user_id = call.from_user.id

    # اضافه کردن به والت (در نسخه واقعی: بعد از تأیید پرداخت دستی یا خودکار)
    from src.database.db_manager import Session
    session = Session()
    try:
        wallet = session.query(Wallet).filter_by(user_id=user_id).first()
        if wallet:
            wallet.balance += amount
            session.commit()
    finally:
        session.close()

    # ثبت تراکنش
    add_transaction({
        'user_id': user_id,
        'type': TransactionType.deposit.value,
        'amount': amount,
        'description': f'شارژ کیف پول (mock)',
        'status': 'confirmed'
    })

    bot.edit_message_text(
        f"✅ شارژ موفق!\n\nمبلغ {amount:,.0f} {CURRENCY} به کیف پول شما اضافه شد.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 بازگشت به والت", callback_data="menu:wallet")
        )
    )
    bot.answer_callback_query(call.id, "شارژ انجام شد!")


# --- نمایش تاریخچه تراکنش‌ها (با صفحه‌بندی ساده) ---
def show_transactions(bot: TeleBot, call: CallbackQuery, user_id: int, page: int = 1):
    from src.database.db_manager import Session
    session = Session()
    try:
        transactions = session.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).all()
    finally:
        session.close()

    if not transactions:
        text = "📜 هنوز هیچ تراکنشی ندارید."
    else:
        per_page = 5
        start = (page - 1) * per_page
        end = start + per_page
        page_transactions = transactions[start:end]

        text_lines = [f"📜 تاریخچه تراکنش‌ها (صفحه {page})\n"]
        for tx in page_transactions:
            emoji = "➕" if tx.type == 'deposit' else "➖" if tx.type in ['withdraw', 'payment'] else "🔄"
            status = "✅" if tx.status == 'confirmed' else "⏳" if tx.status == 'pending' else "❌"
            date = tx.created_at.strftime("%Y-%m-%d %H:%M")
            text_lines.append(
                f"{emoji} {tx.amount:,.0f} {CURRENCY} | {tx.description}\n   {status} {date}"
            )
        text = "\n".join(text_lines)

    markup = InlineKeyboardMarkup(row_width=3)
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀ قبلی", callback_data=f"wallet:transactions:{page-1}"))
    if len(transactions) > page * per_page:
        nav_buttons.append(InlineKeyboardButton("بعدی ▶", callback_data=f"wallet:transactions:{page+1}"))
    if nav_buttons:
        markup.add(*nav_buttons)
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="menu:wallet"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)