from flask import Blueprint, request, jsonify
import jwt
from flask_jwt_extended import create_access_token
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
import random
from vivpayz import db
from datetime import datetime, timedelta
from vivpayz.models import User, Wallet, Card, Referral



auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def generate_unique_referral_code():
    while True:
        code = str(random.randint(1000000000, 9999999999))  # 10-digit code
        if not User.query.filter_by(refercode=code).first():
            return code


def generate_card_number():
    return str(random.randint(10**10, 10**11 - 1))  # 11-digit card number

def get_expiry_date():
    expiry_date = datetime.utcnow() + timedelta(days=365*6)
    return expiry_date.strftime("%m"), expiry_date.strftime("%Y")  # month, year


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    required_fields = ["email", "password", "fname", "lname", "phone"]
    if not all(field in data for field in required_fields):
        return jsonify(msg="Missing required fields"), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify(msg="User already exists"), 409

    # Step 1: Generate unique referral code
    referral_code = generate_unique_referral_code()

    # Step 2: Create the user
    user = User(
        email=data["email"],
        fname=data["fname"],
        lname=data["lname"],
        phone=data["phone"],
        refer=data.get("refer"),
        refercode=referral_code
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()  # Save to get user.id

    # Step 3: Check if refer code exists and insert referral
    refer_code = data.get("refer")
    if refer_code:
        referred_by = User.query.filter_by(refercode=refer_code).first()
        if referred_by:
            referral = Referral(user_id=user.id, referred_by_id=referred_by.id, referral_code=refer_code)
            db.session.add(referral)

    # Step 4: Create wallets
    for currency in ["NGN", "CFA"]:
        wallet = Wallet(user_id=user.id, currency=currency, balance=0)
        db.session.add(wallet)

    # Step 5: Create cards
    expiry_month, expiry_year = get_expiry_date()
    for currency in ["NGN", "CFA"]:
        card_number = generate_card_number()
        card = Card(
            user_id=user.id,
            currency_code=currency,
            card_number=card_number,
            card_name=f"{user.fname} {user.lname}",
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            last4=card_number[-4:]
        )
        db.session.add(card)

    db.session.commit()

    return jsonify(msg="User registered successfully"), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "fname": user.fname,
            "lname": user.lname,
            "phone": user.phone,
        }
    }), 200
