from django.core.management.base import BaseCommand
from django.utils.text import slugify
from faker import Faker
import random

from products.models import Product, Category

fake = Faker()


class Command(BaseCommand):
    help = "Seed database with realistic product data"

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 Seeding database...")

        self.create_categories()
        self.create_products()

        self.stdout.write(self.style.SUCCESS("✅ Seeding completed successfully"))

    def create_categories(self):
        Category.objects.all().delete()

        categories = [
            {"name": "Electronics", "theme": "gaming"},
            {"name": "Fashion", "theme": "clothes"},
            {"name": "Books", "theme": "education"},
            {"name": "Home & Kitchen", "theme": "home"},
            {"name": "Sports & Fitness", "theme": "fitness"},
        ]

        for item in categories:
            Category.objects.create(
                name=item["name"],
                slug=slugify(item["name"]),
                theme=item["theme"],
                is_active=True,
            )

        self.stdout.write("✔ Categories created")

    def create_products(self):
        Product.objects.all().delete()

        categories = list(Category.objects.all())
        products = []

        for _ in range(50):  # 50 realistic products
            products.append(
                Product(
                    name=fake.catch_phrase(),
                    description=fake.paragraph(nb_sentences=4),
                    price=round(random.uniform(99, 9999), 2),
                    category=random.choice(categories),
                    image=f"https://picsum.photos/seed/{fake.uuid4()}/400/400",
                    is_active=True,
                )
            )

        Product.objects.bulk_create(products)
        self.stdout.write("✔ 50 products created")
