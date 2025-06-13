from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

wallet_bp = Blueprint("wallet", __name__)

@wallet_bp.route("/balance", methods=["GET"])
@jwt_required()
def get_balance():
    user_email = get_jwt_identity()
    # TODO: look up real balance from DB by user_email
    return jsonify({
        "user": user_email,
        "balance": 15000,
        "currency": "NGN",
        "status": "success"
    })
