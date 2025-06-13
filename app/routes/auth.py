from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# In-memory “user store” for demo—swap out for your DB later
_users = {}

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    pw    = data.get("password")

    if not email or not pw:
        return jsonify(msg="Missing email or password"), 400
    if email in _users:
        return jsonify(msg="User already exists"), 409

    _users[email] = generate_password_hash(pw)
    return jsonify(msg="User registered"), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    pw    = data.get("password")

    pw_hash = _users.get(email)
    if not pw_hash or not check_password_hash(pw_hash, pw):
        return jsonify(msg="Bad credentials"), 401

    # Create a token with the user's email as identity
    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token), 200
