from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase


class EnsureAdminCommandTests(TestCase):
    def test_creates_default_admin(self):
        call_command("ensure_admin", stdout=StringIO())

        admin = get_user_model().objects.get(username="admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("projetinfo1A"))

    def test_running_twice_keeps_a_single_admin(self):
        call_command("ensure_admin", stdout=StringIO())
        call_command("ensure_admin", stdout=StringIO())

        self.assertEqual(get_user_model().objects.filter(username="admin").count(), 1)


class HealthViewTests(TestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
