"""
Auth routes: Register and Login.
"""

from flask import Blueprint, request, jsonify
from models import db, User
from utils import hash_password, check_password, create_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ──────────────────────────────────────────────
#  POST /api/auth/register
# ──────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # Validation
    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # Check duplicates
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    # Create user
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    db.session.add(user)
    db.session.commit()

    token = create_token(user.id, user.username)

    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict(),
        "token": token,
    }), 201


# ──────────────────────────────────────────────
#  POST /api/auth/login
# ──────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password(password, user.password_hash):
        return jsonify({"error": "Invalid username or password"}), 401

    token = create_token(user.id, user.username)

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "token": token,
    }), 200
