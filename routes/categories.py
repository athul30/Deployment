"""
Category routes: CRUD operations for product categories.
"""

from flask import Blueprint, request, jsonify
from models import db, Category
from utils import login_required

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


# ──────────────────────────────────────────────
#  GET /api/categories — List all categories
# ──────────────────────────────────────────────
@categories_bp.route("", methods=["GET"])
def list_categories():
    """Return all categories."""
    categories = Category.query.order_by(Category.name).all()
    return jsonify({
        "categories": [c.to_dict() for c in categories],
        "total": len(categories),
    }), 200


# ──────────────────────────────────────────────
#  POST /api/categories — Create a new category
# ──────────────────────────────────────────────
@categories_bp.route("", methods=["POST"])
@login_required
def create_category():
    """Create a new category (auth required)."""
    data = request.get_json()
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Category name is required"}), 400

    name = data["name"].strip()
    if Category.query.filter_by(name=name).first():
        return jsonify({"error": f"Category '{name}' already exists"}), 409

    category = Category(
        name=name,
        description=data.get("description", ""),
    )
    db.session.add(category)
    db.session.commit()

    return jsonify({
        "message": "Category created successfully",
        "category": category.to_dict(),
    }), 201


# ──────────────────────────────────────────────
#  GET /api/categories/<id> — Get category by ID
# ──────────────────────────────────────────────
@categories_bp.route("/<int:category_id>", methods=["GET"])
def get_category(category_id):
    """Return a single category by ID."""
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404
    return jsonify({"category": category.to_dict()}), 200


# ──────────────────────────────────────────────
#  PUT /api/categories/<id> — Update category
# ──────────────────────────────────────────────
@categories_bp.route("/<int:category_id>", methods=["PUT"])
@login_required
def update_category(category_id):
    """Update a category (auth required)."""
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "name" in data:
        new_name = data["name"].strip()
        existing = Category.query.filter_by(name=new_name).first()
        if existing and existing.id != category_id:
            return jsonify({"error": f"Category '{new_name}' already exists"}), 409
        category.name = new_name

    if "description" in data:
        category.description = data["description"]

    db.session.commit()
    return jsonify({
        "message": "Category updated successfully",
        "category": category.to_dict(),
    }), 200


# ──────────────────────────────────────────────
#  DELETE /api/categories/<id> — Delete category
# ──────────────────────────────────────────────
@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@login_required
def delete_category(category_id):
    """Delete a category (auth required). Fails if it has products."""
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404

    if category.products:
        return jsonify({
            "error": "Cannot delete category with existing products. Remove products first."
        }), 400

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully"}), 200
