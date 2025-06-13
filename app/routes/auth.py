from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app import db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

_users = {}

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    required_fields = ["email", "password", "fname", "lname", "phone"]
    if not all(field in data for field in required_fields):
        return jsonify(msg="Missing required fields"), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify(msg="User already exists"), 409

    user = User(
        email=data["email"],
        fname=data["fname"],
        lname=data["lname"],
        phone=data["phone"],
        refer=data.get("refer"),
        refercode=data.get("refercode")
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return jsonify(msg="User registered successfully"), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    pw    = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(pw):
        return jsonify(msg="Invalid credentials"), 401

    access_token = create_access_token(identity=user.email)
    return jsonify(access_token=access_token), 200
