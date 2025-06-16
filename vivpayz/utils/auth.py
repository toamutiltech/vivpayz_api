from functools import wraps
from flask import request, jsonify, current_app
import jwt
from vivpayz.models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return jsonify({"error": "Token is missing!"}), 401
        try:
            data = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])
        except Exception as e:
            return jsonify({"error": "Invalid token", "message": str(e)}), 401
        return f(current_user, *args, **kwargs)
    return decorated
