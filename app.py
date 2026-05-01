"""
E-Commerce Backend API — Flask Application Factory

Week 10 — Added:
  - Static / media file handling (UPLOAD_FOLDER, THUMBNAIL_FOLDER)
  - Image validation (type & size checks via Pillow)
  - Automatic thumbnail generation for product images
"""

import os
from flask import Flask, jsonify
from dotenv import load_dotenv
load_dotenv()

from models import db
from routes.auth import auth_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.users import users_bp
from routes.carts import carts_bp


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="static")

    # ── Configuration ──
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or f"sqlite:///{os.path.join(base_dir, 'ecommerce.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "super-secret-ecommerce-key-2026")

    # ── Media / Upload configuration (Week 10) ──
    app.config["UPLOAD_FOLDER"] = os.path.join(base_dir, "static", "uploads", "products")
    app.config["THUMBNAIL_FOLDER"] = os.path.join(base_dir, "static", "uploads", "thumbnails")
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB total request limit

    # Ensure upload directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["THUMBNAIL_FOLDER"], exist_ok=True)

    # ── Init extensions ──
    db.init_app(app)

    # ── Register blueprints ──
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(carts_bp)

    # ── Create tables ──
    with app.app_context():
        db.create_all()

    # ── Root endpoint ──
    @app.route("/")
    def index():
        return jsonify({
            "message": "🛒 E-Commerce API is running!",
            "version": "2.0.0 — Week 10 (Image Upload & Thumbnails)",
            "endpoints": {
                "auth": "/api/auth  (register, login)",
                "products": "/api/products  (CRUD + search + filters + pagination + aggregations)",
                "product_images": "/api/products/<id>/images  (upload, list, set-primary, delete)",
                "categories": "/api/categories  (CRUD)",
                "users": "/api/users  (profile)",
                "cart": "/api/cart  (view, add, update, remove, clear)",
            },
            "image_upload_info": {
                "accepted_types": ["png", "jpg", "jpeg", "gif", "webp"],
                "max_file_size": "5 MB per file",
                "max_images_per_product": 5,
                "thumbnail_size": "200x200 px",
                "upload_field_name": "images",
            },
        }), 200

    # ── Seed endpoint (for production DB) ──
    @app.route("/api/seed", methods=["POST"])
    def seed_database():
        from models import Category, Product, User
        from utils import hash_password

        # Check if already seeded
        if Category.query.first():
            return jsonify({"message": "Database already seeded!", "categories": Category.query.count(), "products": Product.query.count()}), 200

        categories_data = [
            {"name": "Electronics", "description": "Smartphones, laptops, and gadgets"},
            {"name": "Clothing", "description": "Men's and women's apparel"},
            {"name": "Books", "description": "Fiction, non-fiction, and educational books"},
            {"name": "Home & Kitchen", "description": "Furniture, appliances, and decor"},
            {"name": "Sports & Outdoors", "description": "Fitness equipment and outdoor gear"},
            {"name": "Beauty & Personal Care", "description": "Skincare, makeup, and grooming"},
        ]

        products_data = [
            {"name": "iPhone 16 Pro", "description": "Apple flagship with A18 chip", "price": 999.99, "stock": 50, "cat": "Electronics"},
            {"name": "Samsung Galaxy S25", "description": "Samsung flagship with Snapdragon 8 Gen 4", "price": 899.99, "stock": 40, "cat": "Electronics"},
            {"name": "MacBook Air M4", "description": "Ultra-thin laptop with Apple M4 chip", "price": 1299.99, "stock": 25, "cat": "Electronics"},
            {"name": "Sony WH-1000XM6", "description": "Premium noise-cancelling headphones", "price": 349.99, "stock": 100, "cat": "Electronics"},
            {"name": "Nike Air Max Sneakers", "description": "Classic running shoes", "price": 129.99, "stock": 200, "cat": "Clothing"},
            {"name": "Levi's 501 Original Jeans", "description": "Iconic straight-fit denim jeans", "price": 69.99, "stock": 150, "cat": "Clothing"},
            {"name": "Clean Code by Robert Martin", "description": "A handbook of agile software craftsmanship", "price": 39.99, "stock": 300, "cat": "Books"},
            {"name": "Python Crash Course", "description": "Hands-on introduction to Python", "price": 35.99, "stock": 180, "cat": "Books"},
            {"name": "Instant Pot Duo 7-in-1", "description": "Electric pressure cooker, 6 quart", "price": 89.99, "stock": 120, "cat": "Home & Kitchen"},
            {"name": "Dyson V15 Detect Vacuum", "description": "Cordless vacuum with laser dust detection", "price": 749.99, "stock": 35, "cat": "Home & Kitchen"},
            {"name": "Peloton Bike+", "description": "Indoor exercise bike with rotating screen", "price": 2495.00, "stock": 10, "cat": "Sports & Outdoors"},
            {"name": "Garmin Fenix 8 Watch", "description": "Premium GPS multisport smartwatch", "price": 899.99, "stock": 40, "cat": "Sports & Outdoors"},
            {"name": "Dyson Airwrap Styler", "description": "Multi-styler with Coanda airflow", "price": 599.99, "stock": 30, "cat": "Beauty & Personal Care"},
            {"name": "La Mer Moisturizing Cream", "description": "Luxury face moisturizer", "price": 190.00, "stock": 90, "cat": "Beauty & Personal Care"},
        ]

        cat_map = {}
        for c in categories_data:
            cat = Category(name=c["name"], description=c["description"])
            db.session.add(cat)
            db.session.flush()
            cat_map[c["name"]] = cat.id

        for p in products_data:
            product = Product(name=p["name"], description=p["description"], price=p["price"], stock=p["stock"], category_id=cat_map[p["cat"]])
            db.session.add(product)

        demo_user = User(username="demo", email="demo@example.com", password_hash=hash_password("demo123"))
        db.session.add(demo_user)
        db.session.commit()

        return jsonify({
            "message": "Database seeded successfully!",
            "categories": len(categories_data),
            "products": len(products_data),
            "demo_user": {"username": "demo", "password": "demo123"}
        }), 201

    return app


# ── Run ──
if __name__ == "__main__":
    app = create_app()
    print("\n🛒  E-Commerce API v2.0 (Week 10) starting on http://127.0.0.1:5000")
    print("   📸 Image uploads enabled — static/uploads/products/")
    print("   🖼️  Thumbnails generated — static/uploads/thumbnails/")
    print("   Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
