from app import db
from werkzeug.security import generate_password_hash, check_password_hash

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
