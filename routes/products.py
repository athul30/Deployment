"""
Product routes: CRUD + Pagination + Advanced Search Filters + Aggregations
+ Image Upload with Validation & Auto-Thumbnail Generation (Week 10).
"""

import os
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func
from models import db, Product, Category, ProductImage
from utils import (
    login_required,
    validate_image,
    generate_unique_filename,
    create_thumbnail,
    MAX_IMAGES_PER_PRODUCT,
)
from storage import upload_file_to_s3, delete_file_from_s3

products_bp = Blueprint("products", __name__, url_prefix="/api/products")


# ──────────────────────────────────────────────
#  GET /api/products — List with pagination, search & filters
# ──────────────────────────────────────────────
@products_bp.route("", methods=["GET"])
def list_products():
    """
    List products with pagination, search, and filters.

    Query params:
        page        - Page number (default: 1)
        per_page    - Items per page (default: 10, max: 50)
        search      - Text search on product name (case-insensitive LIKE)
        category_id - Filter by category ID
        min_price   - Minimum price
        max_price   - Maximum price
        in_stock    - 'true' to show only products with stock > 0
        sort_by     - Sort field: price | name | created_at (default: created_at)
        sort_order  - asc | desc (default: desc)
    """
    # ── Pagination params ──
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = min(per_page, 50)  # cap at 50
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10

    # ── Build query ──
    query = Product.query

    # Search by name
    search = request.args.get("search", "", type=str).strip()
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    # Filter by category
    category_id = request.args.get("category_id", type=int)
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Filter by price range
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Filter by stock availability
    in_stock = request.args.get("in_stock", "").lower()
    if in_stock == "true":
        query = query.filter(Product.stock > 0)

    # ── Sorting ──
    sort_by = request.args.get("sort_by", "created_at", type=str).lower()
    sort_order = request.args.get("sort_order", "desc", type=str).lower()

    sort_columns = {
        "price": Product.price,
        "name": Product.name,
        "created_at": Product.created_at,
    }
    sort_column = sort_columns.get(sort_by, Product.created_at)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # ── Paginate ──
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "products": [p.to_dict() for p in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
        "filters_applied": {
            "search": search or None,
            "category_id": category_id,
            "min_price": min_price,
            "max_price": max_price,
            "in_stock": in_stock == "true",
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    }), 200


# ──────────────────────────────────────────────
#  GET /api/products/aggregations — Product stats
# ──────────────────────────────────────────────
@products_bp.route("/aggregations", methods=["GET"])
def product_aggregations():
    """
    Return aggregate statistics for the product catalog:
      - Total count
      - Average, min, max price
      - Total inventory value
      - Per-category breakdown
    """
    # Overall aggregations
    overall = db.session.query(
        func.count(Product.id).label("total_products"),
        func.avg(Product.price).label("avg_price"),
        func.min(Product.price).label("min_price"),
        func.max(Product.price).label("max_price"),
        func.sum(Product.price * Product.stock).label("total_inventory_value"),
        func.sum(Product.stock).label("total_stock"),
    ).first()

    # Per-category aggregations
    category_stats_query = (
        db.session.query(
            Category.id,
            Category.name,
            func.count(Product.id).label("product_count"),
            func.avg(Product.price).label("avg_price"),
            func.min(Product.price).label("min_price"),
            func.max(Product.price).label("max_price"),
            func.sum(Product.stock).label("total_stock"),
        )
        .join(Product, Category.id == Product.category_id)
        .group_by(Category.id, Category.name)
        .order_by(func.count(Product.id).desc())
        .all()
    )

    category_stats = []
    for row in category_stats_query:
        category_stats.append({
            "category_id": row.id,
            "category_name": row.name,
            "product_count": row.product_count,
            "avg_price": round(row.avg_price, 2) if row.avg_price else 0,
            "min_price": row.min_price,
            "max_price": row.max_price,
            "total_stock": row.total_stock or 0,
        })

    # Price distribution (ranges)
    price_ranges = [
        {"label": "Under $25", "min": 0, "max": 25},
        {"label": "$25 - $50", "min": 25, "max": 50},
        {"label": "$50 - $100", "min": 50, "max": 100},
        {"label": "$100 - $500", "min": 100, "max": 500},
        {"label": "$500+", "min": 500, "max": None},
    ]
    price_distribution = []
    for pr in price_ranges:
        q = Product.query.filter(Product.price >= pr["min"])
        if pr["max"] is not None:
            q = q.filter(Product.price < pr["max"])
        count = q.count()
        price_distribution.append({
            "range": pr["label"],
            "count": count,
        })

    return jsonify({
        "overall": {
            "total_products": overall.total_products or 0,
            "avg_price": round(overall.avg_price, 2) if overall.avg_price else 0,
            "min_price": overall.min_price,
            "max_price": overall.max_price,
            "total_inventory_value": round(overall.total_inventory_value, 2) if overall.total_inventory_value else 0,
            "total_stock": overall.total_stock or 0,
        },
        "by_category": category_stats,
        "price_distribution": price_distribution,
    }), 200


# ──────────────────────────────────────────────
#  POST /api/products — Create product
# ──────────────────────────────────────────────
@products_bp.route("", methods=["POST"])
@login_required
def create_product():
    """Create a new product (auth required)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    name = data.get("name", "").strip()
    price = data.get("price")
    category_id = data.get("category_id")

    if not name:
        return jsonify({"error": "Product name is required"}), 400
    if price is None or not isinstance(price, (int, float)) or price < 0:
        return jsonify({"error": "A valid non-negative price is required"}), 400
    if not category_id:
        return jsonify({"error": "category_id is required"}), 400

    # Verify category exists
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": f"Category with id {category_id} not found"}), 404

    product = Product(
        name=name,
        description=data.get("description", ""),
        price=float(price),
        stock=data.get("stock", 0),
        category_id=category_id,
    )
    db.session.add(product)
    db.session.commit()

    return jsonify({
        "message": "Product created successfully",
        "product": product.to_dict(),
    }), 201


# ──────────────────────────────────────────────
#  GET /api/products/<id> — Get product by ID
# ──────────────────────────────────────────────
@products_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Return a single product by ID (includes image details)."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"product": product.to_dict()}), 200


# ──────────────────────────────────────────────
#  PUT /api/products/<id> — Update product
# ──────────────────────────────────────────────
@products_bp.route("/<int:product_id>", methods=["PUT"])
@login_required
def update_product(product_id):
    """Update a product (auth required)."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "name" in data:
        product.name = data["name"].strip()
    if "description" in data:
        product.description = data["description"]
    if "price" in data:
        if not isinstance(data["price"], (int, float)) or data["price"] < 0:
            return jsonify({"error": "Price must be a non-negative number"}), 400
        product.price = float(data["price"])
    if "stock" in data:
        product.stock = int(data["stock"])
    if "category_id" in data:
        category = Category.query.get(data["category_id"])
        if not category:
            return jsonify({"error": f"Category with id {data['category_id']} not found"}), 404
        product.category_id = data["category_id"]

    db.session.commit()
    return jsonify({
        "message": "Product updated successfully",
        "product": product.to_dict(),
    }), 200


# ──────────────────────────────────────────────
#  DELETE /api/products/<id> — Delete product
# ──────────────────────────────────────────────
@products_bp.route("/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id):
    """Delete a product and all its images (auth required)."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Remove image files from disk
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    thumb_dir = current_app.config["THUMBNAIL_FOLDER"]
    for img in product.images:
        _delete_image_files(upload_dir, thumb_dir, img)

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200


# ══════════════════════════════════════════════
#  IMAGE UPLOAD ENDPOINTS  (NEW — Week 10)
# ══════════════════════════════════════════════


# ──────────────────────────────────────────────
#  POST /api/products/<id>/images — Upload images
# ──────────────────────────────────────────────
@products_bp.route("/<int:product_id>/images", methods=["POST"])
@login_required
def upload_product_images(product_id):
    """
    Upload one or more images for a product.

    • Accepts multipart/form-data with field name "images" (multiple files).
    • Validates each file: extension, MIME type, size (≤ 5 MB), and image integrity.
    • Generates a thumbnail automatically for every uploaded image.
    • Maximum 5 images per product.

    Optional form field:
        primary_index  — zero-based index of the file that should be marked as primary.
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Check for files in request
    if "images" not in request.files:
        return jsonify({"error": "No 'images' field in request. Send files with key 'images'."}), 400

    files = request.files.getlist("images")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files selected for upload"}), 400

    # Check total image limit
    existing_count = ProductImage.query.filter_by(product_id=product_id).count()
    if existing_count + len(files) > MAX_IMAGES_PER_PRODUCT:
        return jsonify({
            "error": f"Upload would exceed the limit of {MAX_IMAGES_PER_PRODUCT} images "
                     f"per product. Currently: {existing_count}, trying to add: {len(files)}.",
        }), 400

    primary_index = request.form.get("primary_index", type=int)

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    thumb_dir = current_app.config["THUMBNAIL_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(thumb_dir, exist_ok=True)

    uploaded = []
    errors = []

    for idx, file in enumerate(files):
        # ── Validate ──
        validation = validate_image(file)
        if not validation["valid"]:
            errors.append({
                "file": file.filename,
                "error": validation["error"],
            })
            continue

        # ── Save original ──
        stored_name = generate_unique_filename(file.filename)
        save_path = os.path.join(upload_dir, stored_name)
        file.save(save_path)

        # ── Generate thumbnail ──
        thumb_name = f"thumb_{stored_name}"
        thumb_result = create_thumbnail(save_path, thumb_dir, thumb_name)

        # ── Upload to S3 if configured ──
        if os.environ.get("S3_BUCKET_NAME"):
            upload_file_to_s3(save_path, f"products/{stored_name}", file.content_type)
            if thumb_result:
                upload_file_to_s3(os.path.join(thumb_dir, thumb_result), f"thumbnails/{thumb_result}", file.content_type)

        # ── Determine primary flag ──
        is_primary = False
        if primary_index is not None and idx == primary_index:
            is_primary = True
        elif primary_index is None and existing_count == 0 and idx == 0:
            # Auto-set first image as primary if product has none
            is_primary = True

        # Clear existing primary if we're setting a new one
        if is_primary:
            ProductImage.query.filter_by(
                product_id=product_id, is_primary=True
            ).update({"is_primary": False})

        # ── Persist record ──
        image_record = ProductImage(
            product_id=product_id,
            original_filename=file.filename,
            stored_filename=stored_name,
            thumbnail_filename=thumb_result,
            file_size=validation["size"],
            mime_type=file.content_type,
            width=validation.get("width"),
            height=validation.get("height"),
            is_primary=is_primary,
        )
        db.session.add(image_record)
        db.session.flush()  # get the ID
        uploaded.append(image_record.to_dict())

    db.session.commit()

    response = {
        "message": f"Successfully uploaded {len(uploaded)} image(s)",
        "uploaded": uploaded,
        "product": product.to_dict(),
    }
    if errors:
        response["errors"] = errors

    status_code = 201 if uploaded else 400
    return jsonify(response), status_code


# ──────────────────────────────────────────────
#  GET /api/products/<id>/images — List product images
# ──────────────────────────────────────────────
@products_bp.route("/<int:product_id>/images", methods=["GET"])
def list_product_images(product_id):
    """Return all images for a product."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    images = ProductImage.query.filter_by(product_id=product_id).order_by(
        ProductImage.is_primary.desc(), ProductImage.uploaded_at
    ).all()

    return jsonify({
        "product_id": product_id,
        "product_name": product.name,
        "images": [img.to_dict() for img in images],
        "total": len(images),
    }), 200


# ──────────────────────────────────────────────
#  PATCH /api/products/<id>/images/<img_id>/primary — Set primary image
# ──────────────────────────────────────────────
@products_bp.route("/<int:product_id>/images/<int:image_id>/primary", methods=["PATCH"])
@login_required
def set_primary_image(product_id, image_id):
    """Set a specific image as the primary image for the product."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    image = ProductImage.query.filter_by(id=image_id, product_id=product_id).first()
    if not image:
        return jsonify({"error": "Image not found for this product"}), 404

    # Clear existing primary
    ProductImage.query.filter_by(product_id=product_id, is_primary=True).update(
        {"is_primary": False}
    )
    image.is_primary = True
    db.session.commit()

    return jsonify({
        "message": f"Image {image_id} set as primary",
        "image": image.to_dict(),
    }), 200


# ──────────────────────────────────────────────
#  DELETE /api/products/<id>/images/<img_id> — Delete single image
# ──────────────────────────────────────────────
@products_bp.route("/<int:product_id>/images/<int:image_id>", methods=["DELETE"])
@login_required
def delete_product_image(product_id, image_id):
    """Delete a single product image and its thumbnail."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    image = ProductImage.query.filter_by(id=image_id, product_id=product_id).first()
    if not image:
        return jsonify({"error": "Image not found for this product"}), 404

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    thumb_dir = current_app.config["THUMBNAIL_FOLDER"]
    _delete_image_files(upload_dir, thumb_dir, image)

    was_primary = image.is_primary
    db.session.delete(image)
    db.session.commit()

    # If the deleted image was primary, promote the next available image
    if was_primary:
        next_img = ProductImage.query.filter_by(product_id=product_id).first()
        if next_img:
            next_img.is_primary = True
            db.session.commit()

    return jsonify({
        "message": "Image deleted successfully",
        "product": product.to_dict(),
    }), 200


# ──────────────────────────────────────────────
#  Helper — remove files from disk
# ──────────────────────────────────────────────
def _delete_image_files(upload_dir, thumb_dir, image_record):
    """Silently remove the original and thumbnail files from disk (and S3 if configured)."""
    if os.environ.get("S3_BUCKET_NAME"):
        if image_record.stored_filename:
            delete_file_from_s3(f"products/{image_record.stored_filename}")
        if image_record.thumbnail_filename:
            delete_file_from_s3(f"thumbnails/{image_record.thumbnail_filename}")

    for directory, filename in [
        (upload_dir, image_record.stored_filename),
        (thumb_dir, image_record.thumbnail_filename),
    ]:
        if filename:
            path = os.path.join(directory, filename)
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
