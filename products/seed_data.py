# from products.models import Category, Product

# def run():
#     # ---------------- CATEGORIES ----------------
#     categories = [
#         {"name": "Food", "slug": "food", "theme": "food"},
#         {"name": "Drinks", "slug": "drinks", "theme": "drinks"},
#         {"name": "Clothes", "slug": "clothes", "theme": "clothes"},
#         {"name": "Gaming", "slug": "gaming", "theme": "gaming"},
#     ]

#     category_map = {}

#     for cat in categories:
#         obj, _ = Category.objects.get_or_create(
#             slug=cat["slug"],
#             defaults=cat
#         )
#         category_map[cat["slug"]] = obj

#     # ---------------- PRODUCTS ----------------
#     products = [
#     # FOOD
#     {
#         "name": "Classic Burger",
#         "description": "Juicy grilled burger with fresh veggies",
#         "price": 120,
#         "category": "food",
#         "image": "https://images.unsplash.com/photo-1550547660-d9450f859349",
#     },
#     {
#         "name": "Veg Burger",
#         "description": "Healthy vegetable patty with sauce",
#         "price": 100,
#         "category": "food",
#         "image": "https://images.unsplash.com/photo-1606756790138-261d2b21cd75",
#     },
#     {
#         "name": "French Fries",
#         "description": "Crispy golden fries",
#         "price": 80,
#         "category": "food",
#         "image": "https://images.unsplash.com/photo-1541592106381-b31e9677c0e5",
#     },

#     # DRINKS
#     {
#         "name": "Cold Coffee",
#         "description": "Chilled coffee with milk",
#         "price": 90,
#         "category": "drinks",
#         "image": "https://images.unsplash.com/photo-1511920170033-f8396924c348",
#     },
#     {
#         "name": "Orange Juice",
#         "description": "Freshly squeezed juice",
#         "price": 70,
#         "category": "drinks",
#         "image": "https://images.unsplash.com/photo-1571687949920-b5d4c0d4e4c4",
#     },

#     # CLOTHES
#     {
#         "name": "Men T-Shirt",
#         "description": "Cotton casual t-shirt",
#         "price": 499,
#         "category": "clothes",
#         "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab",
#     },
#     {
#         "name": "Women Top",
#         "description": "Stylish daily wear top",
#         "price": 699,
#         "category": "clothes",
#         "image": "https://images.unsplash.com/photo-1520975916090-3105956dac38",
#     },

#     # GAMING
#     {
#         "name": "Gaming Mouse",
#         "description": "High precision RGB mouse",
#         "price": 1299,
#         "category": "gaming",
#         "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7",
#     },
#     {
#         "name": "Gaming Keyboard",
#         "description": "Mechanical keyboard with backlight",
#         "price": 2499,
#         "category": "gaming",
#         "image": "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef",
#     },
# ]


#     for p in products:
#         Product.objects.get_or_create(
#             name=p["name"],
#             category=category_map[p["category"]],
#             defaults={
#                 "description": p["description"],
#                 "price": p["price"],
#                 "image": p["image"],
#                 "is_active": True,
#             }
#         )

#     print("✅ Product seeding completed")

from faker import Faker
import random
from products.models import Category, Product

fake = Faker()

CATEGORY_CONFIG = {
    "food": "food",
    "drinks": "drink",
    "clothes": "clothing",
    "gaming": "gaming",
}

def run():
    # Create categories
    categories = {}
    for name, theme in CATEGORY_CONFIG.items():
        obj, _ = Category.objects.get_or_create(
            slug=name,
            defaults={
                "name": name.capitalize(),
                "theme": theme,
                "is_active": True,
            }
        )
        categories[name] = obj

    # Create products automatically
    for category_slug, category in categories.items():
        for _ in range(10):  # 10 products per category
            Product.objects.create(
                name=fake.word().capitalize() + " " + fake.word().capitalize(),
                description=fake.sentence(nb_words=12),
                price=random.randint(50, 3000),
                category=category,
                image=f"https://source.unsplash.com/featured/?{category_slug}",
                is_active=True,
            )

    print("✅ Automatic product seeding completed")
