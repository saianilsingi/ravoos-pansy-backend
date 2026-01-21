from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Create admin user if not exists"

    def handle(self, *args, **kwargs):
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")

        if not email or not password:
            self.stdout.write(self.style.ERROR("Admin env vars not set"))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING("Admin already exists"))
            return

        User.objects.create_superuser(
            email=email,
            password=password,
            name="Admin"
        )
        self.stdout.write(self.style.SUCCESS("Admin created successfully"))
