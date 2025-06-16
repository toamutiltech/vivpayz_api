from flask import Blueprint, jsonify
from vivpayz.utils.auth import token_required  # or wherever your decorator lives

user_bp = Blueprint("user", __name__, url_prefix="/api/user")

@user_bp.route("/me", methods=["GET"])
@token_required
def get_user_profile(current_user):
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "fname": current_user.fname,
        "lname": current_user.lname,
        "phone": current_user.phone,
    }), 200
