from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase

from .models import Device, Port, StatusChange


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


class DeviceModelTests(TestCase):
    def test_new_device_starts_with_unknown_status(self):
        device = Device.objects.create(
            name="srv-web", kind=Device.Kind.SERVER, ip_address="10.10.0.10"
        )

        self.assertEqual(device.status, Device.Status.UNKNOWN)
        self.assertEqual(device.consecutive_failures, 0)
        self.assertEqual(str(device), "srv-web (10.10.0.10)")

    def test_same_port_cannot_be_added_twice_to_a_device(self):
        device = Device.objects.create(
            name="srv-web", kind=Device.Kind.SERVER, ip_address="10.10.0.10"
        )
        Port.objects.create(device=device, number=80, label="HTTP")

        with self.assertRaises(IntegrityError):
            Port.objects.create(device=device, number=80, label="HTTP")


class AdminPagesTests(TestCase):
    def setUp(self):
        call_command("ensure_admin", stdout=StringIO())
        self.client.login(username="admin", password="projetinfo1A")
        device = Device.objects.create(
            name="srv-web", kind=Device.Kind.SERVER, ip_address="10.10.0.10"
        )
        StatusChange.objects.create(
            device=device, old_status=Device.Status.UNKNOWN, new_status=Device.Status.ONLINE
        )

    def test_device_list_page_loads(self):
        response = self.client.get("/admin/monitoring/device/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "srv-web")

    def test_history_page_loads(self):
        response = self.client.get("/admin/monitoring/statuschange/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "srv-web")
