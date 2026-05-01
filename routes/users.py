"""
User routes: Profile endpoint.
"""

from flask import Blueprint, request, jsonify
from models import User
from utils import login_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


# ──────────────────────────────────────────────
#  GET /api/users/profile — Current user profile
# ──────────────────────────────────────────────
@users_bp.route("/profile", methods=["GET"])
@login_required
def get_profile():
    """Return the currently authenticated user's profile."""
    user = User.query.get(request.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
