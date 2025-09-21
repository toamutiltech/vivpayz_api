from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from vivpayz import db
from flask_login import UserMixin


# ------------------------
# USERS
# ------------------------
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255))
    fname = db.Column(db.String(255), nullable=False)
    lname = db.Column(db.String(255))
    refer = db.Column(db.String(255))
    refercode = db.Column(db.String(255))
    phone = db.Column(db.String(40))
    profile_image = db.Column(db.String(225), nullable=False, default='/static/uploads/default.jpg')
    is_verified = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wallets = db.relationship('Wallet', back_populates='owner', cascade="all, delete")
    cards = db.relationship('Card', back_populates='user')
    referrals = db.relationship('Referral', foreign_keys='Referral.user_id', back_populates='user')
    referrals_made = db.relationship('Referral', foreign_keys='Referral.referred_by_id', back_populates='referred_by')
    transactions = db.relationship('Transaction', back_populates='user')
    currency_conversions = db.relationship('CurrencyConversion', back_populates='user')
    transfers = db.relationship('Transfer', back_populates='user')
    notifications = db.relationship('Notification', back_populates='user')
    payments = db.relationship('Payment', back_populates='user')
    airtime_recharges = db.relationship('AirtimeRecharge', back_populates='user')
    data_recharges = db.relationship('DataRecharge', back_populates='user')
    bills = db.relationship('Bills', back_populates='user')
    bills_payments = db.relationship('BillsPayment', back_populates='user')
    recharges = db.relationship('Recharge', back_populates='user')
    verifications = db.relationship('Verification', back_populates='user')

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)


# ------------------------
# WALLETS
# ------------------------
class Wallet(db.Model):
    __tablename__ = 'wallets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Numeric(15,2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', back_populates='wallets')
    transfers = db.relationship('Transfer', back_populates='wallet', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', back_populates='wallet')


# ------------------------
# REFERRALS
# ------------------------
class Referral(db.Model):
    __tablename__ = 'referrals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    referred_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    referral_code = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], back_populates='referrals')
    referred_by = db.relationship('User', foreign_keys=[referred_by_id], back_populates='referrals_made')


# ------------------------
# PASSWORD RESETS
# ------------------------
class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), index=True)
    token = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ------------------------
# CARDS
# ------------------------
class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    currency_code = db.Column(db.String(10))
    card_number = db.Column(db.String(30))
    card_name = db.Column(db.String(60))
    expiry_month = db.Column(db.String(10))
    expiry_year = db.Column(db.String(10))
    last4 = db.Column(db.String(10))
    status = db.Column(db.Enum('ACTIVE','DISABLED', name='card_status'),  default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='cards')


# ------------------------
# TRANSACTIONS
# ------------------------
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'))
    type = db.Column(db.Enum('credit','debit', name='transaction_type'))
    purpose = db.Column(db.String(255))
    amount = db.Column(db.Numeric(15,2))
    currency = db.Column(db.String(10))
    reference = db.Column(db.String(100), unique=True)
    status = db.Column(db.Enum('pending','success','failed', name='transaction_status'), default='success')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='transactions')
    wallet = db.relationship('Wallet', back_populates='transactions')


# ------------------------
# EXCHANGE RATES
# ------------------------
class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    id = db.Column(db.Integer, primary_key=True)
    base_currency = db.Column(db.String(10))
    target_currency = db.Column(db.String(10))
    rate = db.Column(db.Numeric(18,6))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ------------------------
# CURRENCY CONVERSIONS
# ------------------------
class CurrencyConversion(db.Model):
    __tablename__ = 'currency_conversions'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    from_currency = db.Column(db.String(10))
    to_currency = db.Column(db.String(10))
    from_amount = db.Column(db.Numeric(18,2))
    rate = db.Column(db.Numeric(18,6))
    to_amount = db.Column(db.Numeric(18,2))
    status = db.Column(db.Enum('PENDING','SUCCESS','FAILED', name='conversion_status'), default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='currency_conversions')


# ------------------------
# TRANSFERS
# ------------------------
class Transfer(db.Model):
    __tablename__ = 'transfers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)  
    amount = db.Column(db.Numeric(15,2))
    currency = db.Column(db.String(10), default='NGN')
    recipient_code = db.Column(db.String(50))
    recipient_name = db.Column(db.String(100))
    bank_code = db.Column(db.String(20))
    account_number = db.Column(db.String(20))
    reference = db.Column(db.String(50))
    status = db.Column(db.Enum('PENDING','SUCCESS','FAILED', name='transfers_status'), default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='transfers')
    wallet = db.relationship('Wallet', back_populates='transfers')



# ------------------------
# OTHER TABLES
# ------------------------
class AirtimeRecharge(db.Model):
    __tablename__ = 'airtime_recharges'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    phone = db.Column(db.String(30))
    network = db.Column(db.String(40))
    amount = db.Column(db.Numeric(18,2))
    currency_code = db.Column(db.String(10))
    status = db.Column(db.Enum('PENDING','SUCCESS','FAILED', name='airtime_status'), default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='airtime_recharges')


class Bills(db.Model):
    __tablename__ = 'bills'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    bill_type = db.Column(db.String(100))
    provider = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    amount = db.Column(db.Numeric(10,2))
    status = db.Column(db.Enum('pending','success','failed', name='bill_status'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='bills')


class BillsPayment(db.Model):
    __tablename__ = 'bills_payments'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    biller = db.Column(db.String(60))
    account_ref = db.Column(db.String(60))
    amount = db.Column(db.Numeric(18,2))
    currency_code = db.Column(db.String(10))
    status = db.Column(db.Enum('PENDING','SUCCESS','FAILED', name='billspay_status'), default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='bills_payments')


class BlacklistedToken(db.Model):
    __tablename__ = 'blacklisted_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text)
    expired_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class DataRecharge(db.Model):
    __tablename__ = 'data_recharges'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    phone = db.Column(db.String(30))
    network = db.Column(db.String(40))
    package_name = db.Column(db.String(60))
    amount = db.Column(db.Numeric(18,2))
    currency_code = db.Column(db.String(10))
    status = db.Column(db.Enum('PENDING','SUCCESS','FAILED', name='data_status'), default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='data_recharges')


class Migrations(db.Model):
    __tablename__ = 'migrations'
    id = db.Column(db.Integer, primary_key=True)
    migration = db.Column(db.String(255))
    batch = db.Column(db.Integer)


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='notifications')


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Numeric(15,2))
    currency = db.Column(db.String(10))
    reference = db.Column(db.String(100), unique=True)
    status = db.Column(db.Enum('pending','success','failed', name='payment_status'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='payments')


class Recharge(db.Model):
    __tablename__ = 'recharges'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type = db.Column(db.Enum('airtime','data', name='recharge_type'))
    network = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    amount = db.Column(db.Numeric(10,2))
    status = db.Column(db.Enum('pending','success','failed', name='recharge_status'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='recharges')


class Verification(db.Model):
    __tablename__ = 'verifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.Enum('unverified','pending','verified', name='verifications_status'), default='unverified')
    method = db.Column(db.String(50))
    document = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='verifications')
