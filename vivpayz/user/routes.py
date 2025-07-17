from flask import Blueprint, request, jsonify
from flask import current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from vivpayz.utils.auth import token_required  
from vivpayz import db
from vivpayz.models import User
import os
from flask import send_from_directory

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
