"""Database models for Kruzhok Bot"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class UserHistory(Base):
    """Model to store user's kruzhok video history"""
    __tablename__ = 'user_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    file_id = Column(String(200), nullable=False)  # Telegram file_id for kruzhok
    original_media_type = Column(String(20), nullable=False)  # 'video' or 'photo'
    effect_type = Column(Integer, nullable=False)  # 1-5 effect types
    effect_name = Column(String(50), nullable=False)  # Effect name in Uzbek
    created_at = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer, nullable=True)  # File size in bytes
    
    def __repr__(self):
        return f"<UserHistory(user_id={self.user_id}, effect={self.effect_name}, created_at={self.created_at})>"

class UserLanguage(Base):
    """Model to store user's preferred language"""
    __tablename__ = 'user_language'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    language_code = Column(String(10), nullable=False, default='uz')  # uz, ru, en
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserLanguage(user_id={self.user_id}, language={self.language_code})>"

class UserSubscription(Base):
    """Model to store user subscription and limits"""
    __tablename__ = 'user_subscription'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    is_premium = Column(Boolean, default=False)
    daily_kruzhoks_used = Column(Integer, default=0)
    daily_limit = Column(Integer, default=5)  # Free users: 5, Premium: unlimited
    last_reset_date = Column(DateTime, default=datetime.utcnow)
    premium_expires_at = Column(DateTime, nullable=True)
    referrer_id = Column(BigInteger, nullable=True)  # Who referred this user
    referral_count = Column(Integer, default=0)  # How many people this user referred
    bonus_kruzhoks = Column(Integer, default=0)  # Bonus kruzhoks from referrals
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserSubscription(user_id={self.user_id}, premium={self.is_premium}, daily_used={self.daily_kruzhoks_used})>"

class ReferralHistory(Base):
    """Model to track referral history"""
    __tablename__ = 'referral_history'
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, nullable=False, index=True)  # Who made the referral
    referred_id = Column(BigInteger, nullable=False, index=True)  # Who was referred
    bonus_kruzhoks_given = Column(Integer, default=3)  # Bonus given to referrer
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ReferralHistory(referrer={self.referrer_id}, referred={self.referred_id})>"

class PaymentRequest(Base):
    """Model to track payment requests"""
    __tablename__ = 'payment_requests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    payment_amount = Column(Integer, nullable=False)  # Amount in som
    payment_plan = Column(String(20), nullable=False)  # 'weekly' or 'monthly'
    receipt_file_id = Column(String(200), nullable=False)  # Telegram file_id of receipt
    status = Column(String(20), default='pending')  # pending, approved, rejected
    admin_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<PaymentRequest(user_id={self.user_id}, amount={self.payment_amount}, status={self.status})>"

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"sslmode": "require"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """Get database session"""
    return SessionLocal()

def save_user_history(user_id, username, first_name, file_id, original_media_type, effect_type, effect_name, file_size=None):
    """Save user's kruzhok to history"""
    session = get_db_session()
    try:
        history_entry = UserHistory(
            user_id=user_id,
            username=username,
            first_name=first_name,
            file_id=file_id,
            original_media_type=original_media_type,
            effect_type=effect_type,
            effect_name=effect_name,
            file_size=file_size
        )
        session.add(history_entry)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error saving history: {e}")
        return False
    finally:
        session.close()

def get_user_history(user_id, limit=10):
    """Get user's recent kruzhok history"""
    session = get_db_session()
    try:
        history = session.query(UserHistory).filter(
            UserHistory.user_id == user_id
        ).order_by(
            UserHistory.created_at.desc()
        ).limit(limit).all()
        return history
    except Exception as e:
        print(f"Error getting history: {e}")
        return []
    finally:
        session.close()

def get_total_user_kruzhoks(user_id):
    """Get total count of user's kruzhoks"""
    session = get_db_session()
    try:
        count = session.query(UserHistory).filter(
            UserHistory.user_id == user_id
        ).count()
        return count
    except Exception as e:
        print(f"Error getting count: {e}")
        return 0
    finally:
        session.close()

def set_user_language(user_id, username, first_name, language_code):
    """Set or update user's preferred language"""
    session = get_db_session()
    try:
        # Check if user language record exists
        user_lang = session.query(UserLanguage).filter(
            UserLanguage.user_id == user_id
        ).first()
        
        if user_lang:
            # Update existing record
            user_lang.language_code = language_code
            user_lang.username = username
            user_lang.first_name = first_name
            user_lang.updated_at = datetime.utcnow()
        else:
            # Create new record
            user_lang = UserLanguage(
                user_id=user_id,
                username=username,
                first_name=first_name,
                language_code=language_code
            )
            session.add(user_lang)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error setting user language: {e}")
        return False
    finally:
        session.close()

def get_user_language(user_id):
    """Get user's preferred language, default to 'uz' if not set"""
    session = get_db_session()
    try:
        user_lang = session.query(UserLanguage).filter(
            UserLanguage.user_id == user_id
        ).first()
        
        if user_lang:
            return user_lang.language_code
        else:
            return 'uz'  # Default to Uzbek
    except Exception as e:
        print(f"Error getting user language: {e}")
        return 'uz'
    finally:
        session.close()

def get_or_create_user_subscription(user_id, username=None, first_name=None):
    """Get or create user subscription record"""
    session = get_db_session()
    try:
        user_sub = session.query(UserSubscription).filter(
            UserSubscription.user_id == user_id
        ).first()
        
        if not user_sub:
            user_sub = UserSubscription(
                user_id=user_id,
                username=username,
                first_name=first_name
            )
            session.add(user_sub)
            session.commit()
            session.refresh(user_sub)
        
        return user_sub
    except Exception as e:
        session.rollback()
        print(f"Error getting user subscription: {e}")
        return None
    finally:
        session.close()

def can_create_kruzhok(user_id):
    """Check if user can create kruzhok (not exceeded daily limit)"""
    session = get_db_session()
    try:
        user_sub = session.query(UserSubscription).filter(
            UserSubscription.user_id == user_id
        ).first()
        
        if not user_sub:
            return True  # First time user
        
        # Check if premium user
        if user_sub.is_premium and (not user_sub.premium_expires_at or user_sub.premium_expires_at > datetime.utcnow()):
            return True
        
        # Reset daily counter if new day
        today = datetime.utcnow().date()
        if user_sub.last_reset_date.date() < today:
            user_sub.daily_kruzhoks_used = 0
            user_sub.last_reset_date = datetime.utcnow()
            session.commit()
        
        # Check daily limit (including bonus kruzhoks)
        total_available = user_sub.daily_limit + user_sub.bonus_kruzhoks
        return user_sub.daily_kruzhoks_used < total_available
        
    except Exception as e:
        print(f"Error checking kruzhok limit: {e}")
        return True
    finally:
        session.close()

def use_kruzhok(user_id, username=None, first_name=None):
    """Use one kruzhok from user's daily limit"""
    session = get_db_session()
    try:
        user_sub = session.query(UserSubscription).filter(
            UserSubscription.user_id == user_id
        ).first()
        
        if not user_sub:
            user_sub = UserSubscription(
                user_id=user_id,
                username=username,
                first_name=first_name,
                daily_kruzhoks_used=1
            )
            session.add(user_sub)
        else:
            # Use bonus kruzhoks first, then daily limit
            if user_sub.bonus_kruzhoks > 0:
                user_sub.bonus_kruzhoks -= 1
            else:
                user_sub.daily_kruzhoks_used += 1
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error using kruzhok: {e}")
        return False
    finally:
        session.close()

def get_user_limits(user_id):
    """Get user's current limits and usage"""
    session = get_db_session()
    try:
        user_sub = session.query(UserSubscription).filter(
            UserSubscription.user_id == user_id
        ).first()
        
        if not user_sub:
            return {
                'daily_used': 0,
                'daily_limit': 5,
                'bonus_kruzhoks': 0,
                'is_premium': False,
                'referral_count': 0
            }
        
        # Reset daily counter if new day
        today = datetime.utcnow().date()
        if user_sub.last_reset_date.date() < today:
            user_sub.daily_kruzhoks_used = 0
            user_sub.last_reset_date = datetime.utcnow()
            session.commit()
        
        return {
            'daily_used': user_sub.daily_kruzhoks_used,
            'daily_limit': user_sub.daily_limit,
            'bonus_kruzhoks': user_sub.bonus_kruzhoks,
            'is_premium': user_sub.is_premium and (not user_sub.premium_expires_at or user_sub.premium_expires_at > datetime.utcnow()),
            'referral_count': user_sub.referral_count
        }
    except Exception as e:
        print(f"Error getting user limits: {e}")
        return {'daily_used': 0, 'daily_limit': 5, 'bonus_kruzhoks': 0, 'is_premium': False, 'referral_count': 0}
    finally:
        session.close()

def add_referral(referrer_id, referred_id, referrer_username=None, referrer_first_name=None):
    """Add referral and give bonus kruzhoks"""
    session = get_db_session()
    try:
        # Check if referral already exists
        existing = session.query(ReferralHistory).filter(
            ReferralHistory.referred_id == referred_id
        ).first()
        
        if existing:
            return False  # User already referred by someone
        
        # Create referral record
        referral = ReferralHistory(
            referrer_id=referrer_id,
            referred_id=referred_id
        )
        session.add(referral)
        
        # Update referrer's subscription
        referrer_sub = session.query(UserSubscription).filter(
            UserSubscription.user_id == referrer_id
        ).first()
        
        if not referrer_sub:
            referrer_sub = UserSubscription(
                user_id=referrer_id,
                username=referrer_username,
                first_name=referrer_first_name
            )
            session.add(referrer_sub)
        
        referrer_sub.referral_count += 1
        referrer_sub.bonus_kruzhoks += 3  # Give 3 bonus kruzhoks
        
        # Set referrer for new user
        referred_sub = session.query(UserSubscription).filter(
            UserSubscription.user_id == referred_id
        ).first()
        
        if not referred_sub:
            referred_sub = UserSubscription(
                user_id=referred_id,
                referrer_id=referrer_id
            )
            session.add(referred_sub)
        else:
            referred_sub.referrer_id = referrer_id
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding referral: {e}")
        return False
    finally:
        session.close()

def get_referral_stats(user_id):
    """Get referral statistics for user"""
    session = get_db_session()
    try:
        referrals = session.query(ReferralHistory).filter(
            ReferralHistory.referrer_id == user_id
        ).all()
        
        total_bonus = sum(r.bonus_kruzhoks_given for r in referrals)
        
        return {
            'total_referrals': len(referrals),
            'total_bonus_kruzhoks': total_bonus
        }
    except Exception as e:
        print(f"Error getting referral stats: {e}")
        return {'total_referrals': 0, 'total_bonus_kruzhoks': 0}
    finally:
        session.close()

def create_payment_request(user_id, username, first_name, amount, plan, receipt_file_id):
    """Create a new payment request"""
    session = get_db_session()
    try:
        payment = PaymentRequest(
            user_id=user_id,
            username=username,
            first_name=first_name,
            payment_amount=amount,
            payment_plan=plan,
            receipt_file_id=receipt_file_id
        )
        session.add(payment)
        session.commit()
        session.refresh(payment)
        return payment
    except Exception as e:
        session.rollback()
        print(f"Error creating payment request: {e}")
        return None
    finally:
        session.close()

def get_pending_payments():
    """Get all pending payment requests for admin"""
    session = get_db_session()
    try:
        payments = session.query(PaymentRequest).filter(
            PaymentRequest.status == 'pending'
        ).order_by(PaymentRequest.created_at.desc()).all()
        return payments
    except Exception as e:
        print(f"Error getting pending payments: {e}")
        return []
    finally:
        session.close()

def approve_payment(payment_id, admin_response=None):
    """Approve payment and grant premium"""
    session = get_db_session()
    try:
        payment = session.query(PaymentRequest).filter(
            PaymentRequest.id == payment_id
        ).first()
        
        if not payment:
            return False
        
        # Update payment status
        payment.status = 'approved'
        payment.admin_response = admin_response
        payment.processed_at = datetime.utcnow()
        
        # Grant premium to user
        user_sub = session.query(UserSubscription).filter(
            UserSubscription.user_id == payment.user_id
        ).first()
        
        if not user_sub:
            user_sub = UserSubscription(
                user_id=payment.user_id,
                username=payment.username,
                first_name=payment.first_name
            )
            session.add(user_sub)
        
        user_sub.is_premium = True
        
        # Set premium expiry based on plan
        if payment.payment_plan == 'weekly':
            from datetime import timedelta
            user_sub.premium_expires_at = datetime.utcnow() + timedelta(days=7)
        elif payment.payment_plan == 'monthly':
            from datetime import timedelta
            user_sub.premium_expires_at = datetime.utcnow() + timedelta(days=30)
        
        session.commit()
        return payment
    except Exception as e:
        session.rollback()
        print(f"Error approving payment: {e}")
        return False
    finally:
        session.close()

def reject_payment(payment_id, admin_response):
    """Reject payment request"""
    session = get_db_session()
    try:
        payment = session.query(PaymentRequest).filter(
            PaymentRequest.id == payment_id
        ).first()
        
        if not payment:
            return False
        
        payment.status = 'rejected'
        payment.admin_response = admin_response
        payment.processed_at = datetime.utcnow()
        
        session.commit()
        return payment
    except Exception as e:
        session.rollback()
        print(f"Error rejecting payment: {e}")
        return False
    finally:
        session.close()