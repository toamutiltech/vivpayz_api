from flask import Blueprint, request, jsonify
from flask import current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from vivpayz.utils.auth import token_required  
from vivpayz import mail, db
from vivpayz.models import User, Verification
import os
from flask import send_from_directory
from flask_mail import Message
from datetime import datetime, timedelta
import json, random, string


def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route("/me", methods=["GET"])
@token_required
def get_user_profile(current_user):
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "fname": current_user.fname,
        "lname": current_user.lname,
        "phone": current_user.phone,
        "profile_image": current_user.profile_image,  # 👈 include this
    }), 200



@user_bp.route("/edit-profile", methods=["PUT"])
@token_required
def edit_profile(current_user):
    fname = request.form.get("fname")
    lname = request.form.get("lname")
    phone = request.form.get("phone")
    file = request.files.get("profile_image")

    if not fname or not lname or not phone:
        return jsonify({"error": "All fields are required"}), 400

    # Update text fields
    current_user.fname = fname
    current_user.lname = lname
    current_user.phone = phone

    # Handle image upload
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, "static/uploads")
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        current_user.profile_image = f"/static/uploads/{filename}"

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "fname": current_user.fname,
            "lname": current_user.lname,
            "phone": current_user.phone,
            "profile_image": current_user.profile_image
        }
    }), 200


@user_bp.route("/change-password", methods=["POST"])
@token_required
def change_password(current_user):
    data = request.get_json()

    old_password = data.get("old_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not old_password or not new_password or not confirm_password:
        return jsonify({"error": "All fields are required"}), 400

    if not check_password_hash(current_user.password, old_password):
        return jsonify({"error": "Old password is incorrect"}), 401

    if new_password != confirm_password:
        return jsonify({"error": "New passwords do not match"}), 400

    current_user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200


@user_bp.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('static/uploads', filename)

@user_bp.route('/users')
def get_users():
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 10

    query = User.query.filter(
        (User.fname.ilike(f'%{search}%')) |
        (User.lname.ilike(f'%{search}%')) |
        (User.email.ilike(f'%{search}%'))
    )

    users_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    users = []
    for user in users_paginated.items:
        wallets = [
            {'currency': wallet.currency, 'balance': float(wallet.balance)}
            for wallet in user.wallet
        ]

        users.append({
            'id': user.id,
            'fname': user.fname,
            'lname': user.lname,
            'email': user.email,
            'is_verified': user.is_verified,
            'wallets': wallets
        })

    return jsonify({
        'users': users,
        'total': users_paginated.total,
        'pages': users_paginated.pages,
        'current_page': users_paginated.page
    })


@user_bp.route('/<int:user_id>', methods=['GET'])
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    wallets = [
        {'currency': wallet.currency, 'balance': float(wallet.balance)}
        for wallet in user.wallet
    ]

    return jsonify({
        'user': {
            'id': user.id,
            'fname': user.fname,
            'lname': user.lname,
            'email': user.email,
            'is_verified': user.is_verified,
            'wallets': wallets
        }
    })



@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.wallet:
        db.session.delete(user.wallet)
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User and wallet deleted'})


@user_bp.route('/<int:user_id>/toggle-block', methods=['POST'])
def toggle_block(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    db.session.commit()

    return jsonify({'message': 'User status updated', 'is_verified': user.is_verified})


@user_bp.route("/send-code", methods=["POST"])
@token_required
def send_code(current_user):
    code = generate_code()
    
    verification = Verification.query.filter_by(user_id=current_user.id).first()
    if not verification:
        verification = Verification(user_id=current_user.id, status="pending")
    
    verification.method = json.dumps({"code": code})
    verification.status = "pending"
    db.session.add(verification)
    db.session.commit()

    msg = Message(
        subject="Your Vivpayz Verification Code",
        recipients=[current_user.email],
        body=f"Your verification code is: {code}"
    )

    try:
        mail.send(msg)
        return jsonify({"status": "success", "message": "Verification code sent to your email."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to send email: {str(e)}"}), 500

@user_bp.route("/verify-code", methods=["POST"])
@token_required
def verify_code(current_user):
    data = request.get_json()
    code_input = data.get("code", "").strip()

    verification = Verification.query.filter_by(user_id=current_user.id).first()
    if not verification or verification.status != "pending":
        return jsonify({"status": "error", "message": "No pending verification found."}), 400

    method_data = json.loads(verification.method or "{}")
    code_stored = method_data.get("code")

    if code_input != code_stored:
        return jsonify({"status": "error", "message": "Incorrect code."}), 400

    verification.status = "verified"
    current_user.is_verified = 1
    db.session.add(verification)
    db.session.add(current_user)
    db.session.commit()

    return jsonify({"status": "success", "message": "Account verified successfully."})

