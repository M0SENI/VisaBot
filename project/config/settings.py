# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))  # Placeholder for admin Telegram ID
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', '')  # Placeholder for crypto wallet
COMMISSIONS = {
    '<5': 0.05,
    '5-9': 0.075,
    '>=10': 0.10
}
DB_PATH = 'sqlite:///bot.db'  # SQLite database path
CURRENCY = 'IRR'  # Assume Iranian Rial as per specs