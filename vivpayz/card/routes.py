from flask import Blueprint, jsonify
from vivpayz.utils.auth import token_required
from vivpayz.models import Card

card_bp = Blueprint("cards", __name__, url_prefix="/api/cards")

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
