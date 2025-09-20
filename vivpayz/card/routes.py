from flask import Blueprint, jsonify
from vivpayz.utils.auth import token_required
from vivpayz.models import User, Wallet, Card
import random
from vivpayz import db
from datetime import datetime, timedelta

card_bp = Blueprint("cards", __name__, url_prefix="/api/cards")

def generate_card_number():
    return str(random.randint(10**10, 10**11 - 1))  # 11-digit card number

def get_expiry_date():
    expiry_date = datetime.utcnow() + timedelta(days=365*6)
    return expiry_date.strftime("%m"), expiry_date.strftime("%Y")  # month, year

@card_bp.route("/", methods=["GET"])
@token_required
def get_cards(current_user):
    try:
        cards = Card.query.filter_by(user_id=current_user.id).all()

        data = [
            {
                "currency_code": card.currency_code,
                "card_number": card.card_number,
                "card_name": card.card_name,
                "expiry_month": card.expiry_month,
                "expiry_year": card.expiry_year,
                "last4": card.last4,
                "status": card.status
            } for card in cards
        ]

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve cards", "message": str(e)}), 500

@card_bp.route("/create", methods=["GET"])
@token_required
def create_cards(current_user):
    try:
        # Step 1: Create wallets if they don't exist
        for currency in ["NGN", "XOF"]:
            wallet = Wallet.query.filter_by(user_id=current_user.id, currency=currency).first()
            if not wallet:
                wallet = Wallet(user_id=current_user.id, currency=currency, balance=0)
                db.session.add(wallet)

        # Step 2: Check if cards already exist for the user
        existing_cards = Card.query.filter_by(user_id=current_user.id).all()
        existing_currencies = {c.currency_code for c in existing_cards}

        # Step 3: Only create missing cards
        expiry_month, expiry_year = get_expiry_date()
        for currency in ["NGN", "XOF"]:
            if currency not in existing_currencies:
                card_number = generate_card_number()
                card = Card(
                    user_id=current_user.id,
                    currency_code=currency,
                    card_number=card_number,
                    card_name=f"{current_user.fname} {current_user.lname}",
                    expiry_month=expiry_month,
                    expiry_year=expiry_year,
                    last4=card_number[-4:]
                )
                db.session.add(card)

        db.session.commit()

        return jsonify(msg="Card(s) created successfully"), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

