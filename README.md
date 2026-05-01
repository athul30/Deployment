# Week 10 — Product Image Upload with Auto-Thumbnail Generation

## Topics Covered
- Static and media file handling
- Image validation (type & size)
- Automatic thumbnail generation using Pillow

## Features
- **Multiple images per product** (up to 5)
- **Image validation**: allowed types (PNG, JPG, JPEG, GIF, WebP), max 5 MB per file, PIL integrity check
- **Auto-thumbnail generation**: 200×200 px thumbnails created automatically on upload
- **Primary image selection**: set any image as the product's primary display image
- **Full CRUD for images**: upload, list, set primary, delete

## Project Structure
```
week_10/
├── app.py                         # Flask app factory (with upload config)
├── models.py                      # DB models (+ ProductImage)
├── utils.py                       # JWT + password + image validation & thumbnail
├── seed.py                        # Database seeder
├── requirements.txt               # Python dependencies (+ Pillow)
├── ecommerce_images_postman.json  # Postman collection
├── README.md
├── routes/
│   ├── __init__.py
│   ├── auth.py                    # Register / Login
│   ├── products.py                # Product CRUD + Image Upload endpoints
│   ├── categories.py              # Category CRUD
│   ├── users.py                   # User profile
│   └── carts.py                   # Cart management
└── static/
    └── uploads/
        ├── products/              # Original uploaded images
        └── thumbnails/            # Auto-generated thumbnails
```

## Setup & Run

```bash
# 1. Navigate to week_10
cd week_10

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed the database
python seed.py

# 5. Run the server
python app.py
```

Server starts at: **http://127.0.0.1:5000**

## API Endpoints

### Auth
| Method | Endpoint              | Auth | Description          |
|--------|-----------------------|------|----------------------|
| POST   | `/api/auth/register`  | No   | Register new user    |
| POST   | `/api/auth/login`     | No   | Login, get JWT token |

### Products
| Method | Endpoint                  | Auth | Description                |
|--------|---------------------------|------|----------------------------|
| GET    | `/api/products`           | No   | List (paginated + filters) |
| POST   | `/api/products`           | Yes  | Create product             |
| GET    | `/api/products/<id>`      | No   | Get by ID                  |
| PUT    | `/api/products/<id>`      | Yes  | Update product             |
| DELETE | `/api/products/<id>`      | Yes  | Delete product + images    |
| GET    | `/api/products/aggregations` | No | Product statistics       |

### Product Images (NEW — Week 10)
| Method | Endpoint                                      | Auth | Description              |
|--------|-----------------------------------------------|------|--------------------------|
| POST   | `/api/products/<id>/images`                   | Yes  | Upload image(s)          |
| GET    | `/api/products/<id>/images`                   | No   | List product images      |
| PATCH  | `/api/products/<id>/images/<img_id>/primary`  | Yes  | Set primary image        |
| DELETE | `/api/products/<id>/images/<img_id>`          | Yes  | Delete an image          |

### Static Files
| URL Pattern                                  | Description        |
|----------------------------------------------|--------------------|
| `/static/uploads/products/<filename>`        | View original image |
| `/static/uploads/thumbnails/<filename>`      | View thumbnail      |

## Image Validation Rules
- **Allowed types**: PNG, JPG, JPEG, GIF, WebP
- **Max file size**: 5 MB per file
- **Max images per product**: 5
- **Thumbnail**: 200 × 200 px (auto-generated)
- **PIL integrity check**: verifies file is a genuine image (not a renamed text file)

## Testing with Postman

1. Import `ecommerce_images_postman.json` into Postman
2. Run **Login** request first (token is auto-saved)
3. For image upload:
   - Select the **Upload Single Image** or **Upload Multiple Images** request
   - In the Body tab (form-data), click **Select Files** next to the `images` field
   - Choose image file(s) from your computer
4. Check the response for `image_url` and `thumbnail_url`
5. Open those URLs in a browser to verify the images

## Demo Login
- **Username**: `demo`
- **Password**: `demo123`
