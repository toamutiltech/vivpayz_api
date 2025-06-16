from flask import Blueprint, jsonify
from vivpayz.utils.auth import token_required
from vivpayz.models import Wallet

wallet_bp = Blueprint("wallets", __name__, url_prefix="/api/wallets")

@wallet_bp.route("/", methods=["GET"])
@token_required
def get_wallets(current_user):
    try:
        wallets = Wallet.query.filter_by(user_id=current_user.id).all()

        data = [
            {
                "currency": wallet.currency,
                "balance": float(wallet.balance),
            } for wallet in wallets
        ]

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve wallets", "message": str(e)}), 500

