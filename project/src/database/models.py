# src/database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum, JSON, func, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from config.settings import DB_PATH
import enum

Base = declarative_base()
engine = create_engine(DB_PATH)

# ──────────────────────────────────────────────────────────────
# مدل‌های جدید (Product, ProductContent, ProductGuide)
# ──────────────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description_text = Column(Text)
    photo_file_id = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    extra_contents = relationship("ProductContent", back_populates="product", cascade="all, delete-orphan")
    guides = relationship("ProductGuide", back_populates="product", cascade="all, delete-orphan")


class ProductContent(Base):
    __tablename__ = 'product_contents'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    content_type = Column(String(20))               # 'text', 'voice', 'audio', 'video', 'document'
    file_id = Column(String)                        # برای فایل‌ها
    text = Column(Text)                             # برای متن اضافی
    caption = Column(String(200))                   # کپشن برای فایل
    order = Column(Integer, default=0)              # ترتیب نمایش

    product = relationship("Product", back_populates="extra_contents")


class ProductGuide(Base):
    __tablename__ = 'product_guides'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    content_type = Column(String(20))               # text, voice, audio, video, document
    file_id = Column(String, nullable=True)
    text = Column(Text, nullable=True)
    caption = Column(String(200), nullable=True)
    order = Column(Integer, default=0)

    product = relationship("Product", back_populates="guides")


# ──────────────────────────────────────────────────────────────
# بقیه مدل‌ها بدون تغییر
# ──────────────────────────────────────────────────────────────

class CardType(enum.Enum):
    prepaid = 'prepaid'
    classic = 'classic'
    gold = 'gold'
    platinum = 'platinum'

class OrderStatus(enum.Enum):
    incomplete = 'incomplete'
    complete = 'complete'
    ready = 'ready'
    delivered = 'delivered'

class TransactionType(enum.Enum):
    deposit = 'deposit'
    withdraw = 'withdraw'
    transfer = 'transfer'
    commission = 'commission'
    payment = 'payment'

class TransactionStatus(enum.Enum):
    pending = 'pending'
    confirmed = 'confirmed'
    rejected = 'rejected'

class TicketStatus(enum.Enum):
    open = 'open'
    answered = 'answered'

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)  # Telegram user_id
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    full_name = Column(String)  # جدید
    address = Column(Text)  # جدید
    mobile = Column(String(20))  # جدید
    passport_file_id = Column(String)  # جدید
    verification_video_id = Column(String)  # جدید
    # signature_photo_id = Column(String)  # بعداً اضافه می‌شه
    is_vip = Column(Boolean, default=False)
    referral_code = Column(String, unique=True)
    referred_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())

    referrals = relationship('Referral', foreign_keys='Referral.referrer_id', backref='referrer')
    referred = relationship('Referral', foreign_keys='Referral.referred_id', backref='referred')

class Referral(Base):
    __tablename__ = 'referrals'
    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey('users.id'))
    referred_id = Column(Integer, ForeignKey('users.id'))
    commission_rate = Column(Float)
    created_at = Column(DateTime, default=func.now())
    
    
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    product_name = Column(String)
    product_price = Column(Float)
    full_name = Column(String)
    address = Column(Text)
    mobile = Column(String)
    passport_file_id = Column(String)
    verification_video_id = Column(String)
    tx_hash = Column(String)
    status = Column(String, default='pending')  # pending, suspended, done
    created_at = Column(DateTime, default=func.now())

    user = relationship('User')
    product = relationship('Product')

class Wallet(Base):
    __tablename__ = 'wallet'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    balance = Column(Float, default=0.0)

    user = relationship('User', backref='wallet')

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(Enum(TransactionType))
    amount = Column(Float)
    description = Column(String)
    tx_hash = Column(String)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending)
    created_at = Column(DateTime, default=func.now())

    user = relationship('User', backref='transactions')

class SupportTicket(Base):
    __tablename__ = 'support_tickets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(String)
    status = Column(Enum(TicketStatus), default=TicketStatus.open)
    admin_reply = Column(String)
    created_at = Column(DateTime, default=func.now())

    user = relationship('User', backref='tickets')


# Force configure mappers (اختیاری اما توصیه می‌شود در SQLAlchemy 2.0+)
Base.registry.configure()

# Create tables if not exist
Base.metadata.create_all(engine)