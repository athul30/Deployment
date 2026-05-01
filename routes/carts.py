"""
Cart routes: View, add items, update quantity, remove items, clear cart.
"""

from flask import Blueprint, request, jsonify
from models import db, Cart, CartItem, Product
from utils import login_required

carts_bp = Blueprint("carts", __name__, url_prefix="/api/cart")


def _get_or_create_cart(user_id):
    """Get the user's cart, or create one if it doesn't exist."""
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart


# ──────────────────────────────────────────────
#  GET /api/cart — View current user's cart
# ──────────────────────────────────────────────
@carts_bp.route("", methods=["GET"])
@login_required
def view_cart():
    """Return the authenticated user's cart with all items."""
    cart = _get_or_create_cart(request.user_id)
    return jsonify({"cart": cart.to_dict()}), 200


# ──────────────────────────────────────────────
#  POST /api/cart/items — Add item to cart
# ──────────────────────────────────────────────
@carts_bp.route("/items", methods=["POST"])
@login_required
def add_to_cart():
    """Add a product to the user's cart (or increase quantity if already present)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400
    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    # Verify product exists and is in stock
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if product.stock < quantity:
        return jsonify({"error": f"Insufficient stock. Available: {product.stock}"}), 400

    cart = _get_or_create_cart(request.user_id)

    # Check if item already in cart
    existing_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if existing_item:
        new_qty = existing_item.quantity + quantity
        if product.stock < new_qty:
            return jsonify({
                "error": f"Insufficient stock. Available: {product.stock}, in cart: {existing_item.quantity}"
            }), 400
        existing_item.quantity = new_qty
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.session.add(item)

    db.session.commit()

    return jsonify({
        "message": "Item added to cart",
        "cart": cart.to_dict(),
    }), 200


# ──────────────────────────────────────────────
#  PUT /api/cart/items/<item_id> — Update item quantity
# ──────────────────────────────────────────────
@carts_bp.route("/items/<int:item_id>", methods=["PUT"])
@login_required
def update_cart_item(item_id):
    """Update the quantity of a cart item."""
    cart = _get_or_create_cart(request.user_id)

    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        return jsonify({"error": "Cart item not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    quantity = data.get("quantity")
    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    product = Product.query.get(item.product_id)
    if product and product.stock < quantity:
        return jsonify({"error": f"Insufficient stock. Available: {product.stock}"}), 400

    item.quantity = quantity
    db.session.commit()

    return jsonify({
        "message": "Cart item updated",
        "cart": cart.to_dict(),
    }), 200


# ──────────────────────────────────────────────
#  DELETE /api/cart/items/<item_id> — Remove item
# ──────────────────────────────────────────────
@carts_bp.route("/items/<int:item_id>", methods=["DELETE"])
@login_required
def remove_cart_item(item_id):
    """Remove a single item from the cart."""
    cart = _get_or_create_cart(request.user_id)

    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        return jsonify({"error": "Cart item not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({
        "message": "Item removed from cart",
        "cart": cart.to_dict(),
    }), 200


# ──────────────────────────────────────────────
#  DELETE /api/cart/clear — Clear entire cart
# ──────────────────────────────────────────────
@carts_bp.route("/clear", methods=["DELETE"])
@login_required
def clear_cart():
    """Remove all items from the user's cart."""
    cart = _get_or_create_cart(request.user_id)

    CartItem.query.filter_by(cart_id=cart.id).delete()
    db.session.commit()

    return jsonify({
        "message": "Cart cleared",
        "cart": cart.to_dict(),
    }), 200
