"""
Seed script — Populate the database with sample categories and products.
Run:  python seed.py
"""

from app import create_app
from models import db, Category, Product, User
from utils import hash_password

app = create_app()

CATEGORIES = [
    {"name": "Electronics", "description": "Smartphones, laptops, and gadgets"},
    {"name": "Clothing", "description": "Men's and women's apparel"},
    {"name": "Books", "description": "Fiction, non-fiction, and educational books"},
    {"name": "Home & Kitchen", "description": "Furniture, appliances, and decor"},
    {"name": "Sports & Outdoors", "description": "Fitness equipment and outdoor gear"},
    {"name": "Beauty & Personal Care", "description": "Skincare, makeup, and grooming"},
]

PRODUCTS = [
    # Electronics (category 1)
    {"name": "iPhone 16 Pro", "description": "Apple's flagship smartphone with A18 chip", "price": 999.99, "stock": 50, "cat": "Electronics"},
    {"name": "Samsung Galaxy S25", "description": "Samsung flagship with Snapdragon 8 Gen 4", "price": 899.99, "stock": 40, "cat": "Electronics"},
    {"name": "MacBook Air M4", "description": "Ultra-thin laptop with Apple M4 chip", "price": 1299.99, "stock": 25, "cat": "Electronics"},
    {"name": "Sony WH-1000XM6", "description": "Premium noise-cancelling wireless headphones", "price": 349.99, "stock": 100, "cat": "Electronics"},
    {"name": "iPad Pro 13-inch", "description": "M4 chip, Liquid Retina XDR display", "price": 1099.00, "stock": 30, "cat": "Electronics"},

    # Clothing (category 2)
    {"name": "Nike Air Max Sneakers", "description": "Classic running shoes with Air cushioning", "price": 129.99, "stock": 200, "cat": "Clothing"},
    {"name": "Levi's 501 Original Jeans", "description": "Iconic straight-fit denim jeans", "price": 69.99, "stock": 150, "cat": "Clothing"},
    {"name": "North Face Puffer Jacket", "description": "Insulated winter jacket with 700-fill down", "price": 249.99, "stock": 60, "cat": "Clothing"},
    {"name": "Adidas Ultraboost Shoes", "description": "Performance running shoes with Boost midsole", "price": 179.99, "stock": 80, "cat": "Clothing"},

    # Books (category 3)
    {"name": "Clean Code by Robert Martin", "description": "A handbook of agile software craftsmanship", "price": 39.99, "stock": 300, "cat": "Books"},
    {"name": "Designing Data-Intensive Applications", "description": "By Martin Kleppmann - distributed systems guide", "price": 45.99, "stock": 200, "cat": "Books"},
    {"name": "The Pragmatic Programmer", "description": "Classic software development guide - 20th anniversary edition", "price": 49.99, "stock": 250, "cat": "Books"},
    {"name": "Python Crash Course", "description": "A hands-on project-based introduction to Python", "price": 35.99, "stock": 180, "cat": "Books"},

    # Home & Kitchen (category 4)
    {"name": "Instant Pot Duo 7-in-1", "description": "Electric pressure cooker, 6 quart", "price": 89.99, "stock": 120, "cat": "Home & Kitchen"},
    {"name": "Dyson V15 Detect Vacuum", "description": "Cordless vacuum with laser dust detection", "price": 749.99, "stock": 35, "cat": "Home & Kitchen"},
    {"name": "KitchenAid Stand Mixer", "description": "Artisan series, 5-quart tilt-head stand mixer", "price": 379.99, "stock": 45, "cat": "Home & Kitchen"},
    {"name": "Nespresso Vertuo Coffee Maker", "description": "Single-serve coffee and espresso maker", "price": 199.99, "stock": 70, "cat": "Home & Kitchen"},

    # Sports & Outdoors (category 5)
    {"name": "Peloton Bike+", "description": "Indoor exercise bike with rotating screen", "price": 2495.00, "stock": 10, "cat": "Sports & Outdoors"},
    {"name": "Yeti Tundra 45 Cooler", "description": "Heavy-duty rotomolded cooler", "price": 325.00, "stock": 55, "cat": "Sports & Outdoors"},
    {"name": "Garmin Fenix 8 Watch", "description": "Premium GPS multisport smartwatch", "price": 899.99, "stock": 40, "cat": "Sports & Outdoors"},

    # Beauty & Personal Care (category 6)
    {"name": "Dyson Airwrap Styler", "description": "Multi-styler with Coanda airflow technology", "price": 599.99, "stock": 30, "cat": "Beauty & Personal Care"},
    {"name": "La Mer Moisturizing Cream", "description": "Luxury face moisturizer, 2 oz.", "price": 190.00, "stock": 90, "cat": "Beauty & Personal Care"},
    {"name": "Philips Sonicare Toothbrush", "description": "Diamond Clean Smart electric toothbrush", "price": 169.99, "stock": 110, "cat": "Beauty & Personal Care"},
]


def seed():
    """Drop all tables, recreate them, and populate with sample data."""
    with app.app_context():
        print("🗑️  Dropping existing tables...")
        db.drop_all()
        print("🔨  Creating tables...")
        db.create_all()

        # Seed categories
        cat_map = {}
        for c in CATEGORIES:
            category = Category(name=c["name"], description=c["description"])
            db.session.add(category)
            db.session.flush()  # get the ID
            cat_map[c["name"]] = category.id
            print(f"  ✅ Category: {c['name']} (id={category.id})")

        # Seed products
        for p in PRODUCTS:
            product = Product(
                name=p["name"],
                description=p["description"],
                price=p["price"],
                stock=p["stock"],
                category_id=cat_map[p["cat"]],
            )
            db.session.add(product)
            print(f"  📦 Product: {p['name']} — ${p['price']}")

        # Seed a demo user
        demo_user = User(
            username="demo",
            email="demo@example.com",
            password_hash=hash_password("demo123"),
        )
        db.session.add(demo_user)
        print(f"  👤 User: demo / demo123")

        db.session.commit()
        print(f"\n🎉  Seeded {len(CATEGORIES)} categories, {len(PRODUCTS)} products, and 1 demo user!")


if __name__ == "__main__":
    seed()
