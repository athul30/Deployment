"""
Database models for the E-Commerce API.
Models: Category, Product, ProductImage, User, Cart, CartItem

Week 10 — Added ProductImage model for multiple product images
with file validation and auto-thumbnail generation.
"""

import os
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ──────────────────────────────────────────────
#  Category
# ──────────────────────────────────────────────
class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    products = db.relationship("Product", backref="category", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "product_count": len(self.products),
        }


# ──────────────────────────────────────────────
#  Product
# ──────────────────────────────────────────────
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cart_items = db.relationship("CartItem", backref="product", lazy=True)
    images = db.relationship(
        "ProductImage", backref="product", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock": self.stock,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "images": [img.to_dict() for img in self.images],
            "created_at": self.created_at.isoformat(),
        }


# ──────────────────────────────────────────────
#  ProductImage  (NEW — Week 10)
# ──────────────────────────────────────────────
class ProductImage(db.Model):
    """
    Stores metadata for each product image.
    - Multiple images per product.
    - Tracks original filename, stored path, thumbnail path, file size & MIME type.
    - is_primary marks the main display image.
    """
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    thumbnail_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=False)          # bytes
    mime_type = db.Column(db.String(50), nullable=False)
    width = db.Column(db.Integer, nullable=True)               # original px
    height = db.Column(db.Integer, nullable=True)               # original px
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        s3_bucket = os.environ.get("S3_BUCKET_NAME")
        s3_region = os.environ.get("AWS_REGION", "us-east-1")
        base_url = f"https://{s3_bucket}.s3.{s3_region}.amazonaws.com" if s3_bucket else "/static/uploads"

        return {
            "id": self.id,
            "product_id": self.product_id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "thumbnail_filename": self.thumbnail_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "is_primary": self.is_primary,
            "image_url": f"{base_url}/products/{self.stored_filename}",
            "thumbnail_url": (
                f"{base_url}/thumbnails/{self.thumbnail_filename}"
                if self.thumbnail_filename
                else None
            ),
            "uploaded_at": self.uploaded_at.isoformat(),
        }


# ──────────────────────────────────────────────
#  User
# ──────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    cart = db.relationship("Cart", backref="user", uselist=False, lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }


# ──────────────────────────────────────────────
#  Cart
# ──────────────────────────────────────────────
class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    items = db.relationship("CartItem", backref="cart", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        cart_items = [item.to_dict() for item in self.items]
        total = sum(item["subtotal"] for item in cart_items)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "items": cart_items,
            "total_items": len(cart_items),
            "total_price": round(total, 2),
            "created_at": self.created_at.isoformat(),
        }


# ──────────────────────────────────────────────
#  CartItem
# ──────────────────────────────────────────────
class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "product_price": self.product.price if self.product else 0,
            "quantity": self.quantity,
            "subtotal": round((self.product.price if self.product else 0) * self.quantity, 2),
        }
