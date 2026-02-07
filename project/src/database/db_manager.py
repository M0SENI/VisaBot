# src/database/db_manager.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base, User, Referral, Order, Wallet, Transaction, SupportTicket
from config.settings import DB_PATH

engine = create_engine(DB_PATH)
Session = scoped_session(sessionmaker(bind=engine))
# در db_manager.py یا main.py
Base.metadata.create_all(engine)

def init_db():
    Base.metadata.create_all(engine)

def get_user(user_id: int) -> User:
    session = Session()
    try:
        return session.query(User).filter_by(user_id=user_id).first()
    finally:
        session.close()

def create_user(user_data: dict) -> User:
    session = Session()
    try:
        user = User(**user_data)
        session.add(user)
        session.commit()
        return user
    finally:
        session.close()

def create_order(order_data: dict) -> Order:
    session = Session()
    try:
        order = Order(**order_data)
        session.add(order)
        session.commit()
        return order
    finally:
        session.close()

def get_balance(user_id: int) -> float:
    session = Session()
    try:
        wallet = session.query(Wallet).filter_by(user_id=user_id).first()
        return wallet.balance if wallet else 0.0
    finally:
        session.close()

def update_order_status(order_id: int, status: str):
    session = Session()
    try:
        order = session.query(Order).filter_by(id=order_id).first()
        if order:
            order.status = status
            session.commit()
    finally:
        session.close()

def add_transaction(tx_data: dict):
    session = Session()
    try:
        tx = Transaction(**tx_data)
        session.add(tx)
        session.commit()
    finally:
        session.close()

# Add more CRUD as needed...