"""
Utility helpers: JWT, password hashing, login_required decorator,
and image validation + thumbnail generation (Week 10).
"""

import os
import uuid
import jwt
import bcrypt
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask import request, jsonify
from PIL import Image

SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-ecommerce-key-2026")
JWT_EXPIRY_HOURS = 24

# ──────────────────────────────────────────────
#  Image configuration
# ──────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}
MAX_FILE_SIZE = 5 * 1024 * 1024          # 5 MB per file
MAX_IMAGES_PER_PRODUCT = 5               # Maximum images per product
THUMBNAIL_SIZE = (200, 200)              # Thumbnail dimensions


# ──────────────────────────────────────────────
#  Password helpers
# ──────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ──────────────────────────────────────────────
#  JWT helpers
# ──────────────────────────────────────────────
def create_token(user_id: int, username: str) -> str:
    """Create a JWT token for the given user."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Returns the payload or raises."""
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


# ──────────────────────────────────────────────
#  Auth decorator
# ──────────────────────────────────────────────
def login_required(f):
    """Decorator that protects a route — requires a valid Bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
            request.user_id = payload["user_id"]
            request.username = payload["username"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────
#  Image helpers  (NEW — Week 10)
# ──────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    """Check if the file extension is in the allowed set."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(file_storage) -> dict:
    """
    Validate an uploaded image file.

    Checks:
      1. File is present and has a filename.
      2. File extension is allowed (png, jpg, jpeg, gif, webp).
      3. MIME / content type is allowed.
      4. File size does not exceed MAX_FILE_SIZE (5 MB).
      5. The file is a valid image that PIL can open.

    Returns a dict:
        {"valid": True,  "width": w, "height": h}   on success
        {"valid": False, "error": "reason"}          on failure
    """
    if not file_storage or file_storage.filename == "":
        return {"valid": False, "error": "No file provided"}

    # 1. Extension check
    if not allowed_file(file_storage.filename):
        return {
            "valid": False,
            "error": f"File type not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
        }

    # 2. MIME type check
    if file_storage.content_type not in ALLOWED_MIME_TYPES:
        return {
            "valid": False,
            "error": f"MIME type '{file_storage.content_type}' not allowed. "
                     f"Accepted: {', '.join(ALLOWED_MIME_TYPES)}",
        }

    # 3. Size check — Read to determine size, then seek back
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    if file_size > MAX_FILE_SIZE:
        return {
            "valid": False,
            "error": f"File size ({file_size / (1024*1024):.2f} MB) exceeds "
                     f"maximum allowed size ({MAX_FILE_SIZE / (1024*1024):.0f} MB)",
        }

    if file_size == 0:
        return {"valid": False, "error": "File is empty"}

    # 4. PIL validity check — also grab dimensions
    try:
        img = Image.open(file_storage)
        img.verify()          # verify it's a real image
        file_storage.seek(0)  # reset after verify
        img = Image.open(file_storage)
        width, height = img.size
        file_storage.seek(0)
    except Exception:
        return {"valid": False, "error": "File is not a valid image"}

    return {"valid": True, "width": width, "height": height, "size": file_size}


def generate_unique_filename(original_filename: str) -> str:
    """Generate a UUID-based filename preserving the original extension."""
    ext = original_filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


def create_thumbnail(source_path: str, thumbnail_dir: str, filename: str) -> str | None:
    """
    Create a thumbnail for the image at *source_path*.

    The thumbnail is saved inside *thumbnail_dir* with the given *filename*.
    Returns the thumbnail filename on success, or None on failure.
    """
    try:
        os.makedirs(thumbnail_dir, exist_ok=True)
        thumb_path = os.path.join(thumbnail_dir, filename)

        with Image.open(source_path) as img:
            # Convert to RGB if necessary (e.g. RGBA PNGs, palette images)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
            img.save(thumb_path, quality=85, optimize=True)

        return filename
    except Exception as exc:
        print(f"  Thumbnail generation failed: {exc}")
        return None
