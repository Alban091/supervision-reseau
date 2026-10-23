import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the default admin account if it does not exist yet."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "projetinfo1A")
        user_model = get_user_model()

        if user_model.objects.filter(username=username).exists():
            self.stdout.write(f"Admin account '{username}' already exists.")
            return

        user_model.objects.create_superuser(username=username, email="", password=password)
        self.stdout.write(self.style.SUCCESS(f"Admin account '{username}' created."))
