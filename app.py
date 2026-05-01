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

    return app


# ── Run ──
if __name__ == "__main__":
    app = create_app()
    print("\n🛒  E-Commerce API v2.0 (Week 10) starting on http://127.0.0.1:5000")
    print("   📸 Image uploads enabled — static/uploads/products/")
    print("   🖼️  Thumbnails generated — static/uploads/thumbnails/")
    print("   Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
