from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from vivpayz import db
from flask_login import UserMixin

class User(db.Model):
    __tablename__ = "users"  # Optional: use this if your table name is explicitly "users"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email       = db.Column(db.String(255), unique=True, nullable=False)
    password    = db.Column(db.String(255), nullable=False)
    fname       = db.Column(db.String(255), nullable=False)
    lname       = db.Column(db.String(255), nullable=False)
    refer       = db.Column(db.String(255), nullable=True)
    refercode   = db.Column(db.String(255), nullable=True)
    phone       = db.Column(db.String(40), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)


class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    balance = db.Column(db.Numeric(15, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="wallets")

class Referral(db.Model):
    __tablename__ = 'referrals'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    referral_code = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id], backref="referrals")
    referred_by = db.relationship("User", foreign_keys=[referred_by_id], backref="referrals_made")


class PasswordReset(db.Model):
    __tablename__ = 'password_resets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    token = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Card(db.Model):
    __tablename__ = 'cards'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency_code = db.Column(db.String(3), nullable=False)
    card_number = db.Column(db.String(30), nullable=False)
    card_name = db.Column(db.String(60))
    expiry_month = db.Column(db.String(2))
    expiry_year = db.Column(db.String(2))
    last4 = db.Column(db.String(4))
    status = db.Column(db.Enum('ACTIVE', 'DISABLED'), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="cards")


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    type = db.Column(db.Enum('credit', 'debit'), nullable=False)
    purpose = db.Column(db.String(255))
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    reference = db.Column(db.String(100), nullable=False, unique=True)
    status = db.Column(db.Enum('pending', 'success', 'failed'), default='success')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'

    id = db.Column(db.Integer, primary_key=True)
    base_currency = db.Column(db.String(10), nullable=False)
    target_currency = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Numeric(18, 6), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('base_currency', 'target_currency', name='unique_pair'),
    )

    def __repr__(self):
        return f"<ExchangeRate {self.base_currency}->{self.target_currency} = {self.rate}>"
    
class CurrencyConversion(db.Model):
    __tablename__ = 'currency_conversions'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_currency = db.Column(db.String(3), nullable=False)
    to_currency = db.Column(db.String(3), nullable=False)
    from_amount = db.Column(db.Numeric(18, 2), nullable=False)
    rate = db.Column(db.Numeric(18, 6), nullable=False)
    to_amount = db.Column(db.Numeric(18, 2), nullable=False)
    status = db.Column(db.Enum('PENDING', 'SUCCESS', 'FAILED'), default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='currency_conversions')

    def __repr__(self):
        return f"<Conversion {self.from_amount} {self.from_currency} -> {self.to_amount} {self.to_currency}>"
