from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from .models import Device, Port, StatusChange
from .probes import ProbeResult
from .supervision import next_status, run_cycle

ANSWER = ProbeResult(reachable=True, latency_ms=0.5)
NO_ANSWER = ProbeResult(reachable=False)


class NextStatusTests(SimpleTestCase):
    def test_answer_means_online(self):
        self.assertEqual(next_status(Device.Status.OFFLINE, 5, True), (Device.Status.ONLINE, 0))

    def test_one_failure_keeps_the_current_status(self):
        self.assertEqual(next_status(Device.Status.ONLINE, 0, False), (Device.Status.ONLINE, 1))

    def test_two_failures_in_a_row_mean_offline(self):
        self.assertEqual(next_status(Device.Status.ONLINE, 1, False), (Device.Status.OFFLINE, 2))


@mock.patch("monitoring.supervision.check_tcp_port", return_value=ANSWER)
class RunCycleTests(TestCase):
    def setUp(self):
        self.device = Device.objects.create(
            name="srv-web", kind=Device.Kind.SERVER, ip_address="10.10.0.10"
        )
        self.port = Port.objects.create(device=self.device, number=80, label="HTTP")

    def test_answering_device_goes_online(self, _check_tcp_port):
        with mock.patch("monitoring.supervision.ping", return_value=ANSWER):
            run_cycle()

        self.device.refresh_from_db()
        self.port.refresh_from_db()
        self.assertEqual(self.device.status, Device.Status.ONLINE)
        self.assertIsNotNone(self.device.last_seen_at)
        self.assertTrue(self.port.is_open)
        change = StatusChange.objects.get(device=self.device)
        self.assertEqual(change.old_status, Device.Status.UNKNOWN)
        self.assertEqual(change.new_status, Device.Status.ONLINE)

    def test_device_goes_offline_after_two_failed_pings(self, _check_tcp_port):
        with mock.patch("monitoring.supervision.ping", return_value=ANSWER):
            run_cycle()
        with mock.patch("monitoring.supervision.ping", return_value=NO_ANSWER):
            run_cycle()
            self.device.refresh_from_db()
            self.assertEqual(self.device.status, Device.Status.ONLINE)

            run_cycle()
            self.device.refresh_from_db()
            self.assertEqual(self.device.status, Device.Status.OFFLINE)

        self.port.refresh_from_db()
        self.assertFalse(self.port.is_open)
        self.assertEqual(StatusChange.objects.filter(new_status=Device.Status.OFFLINE).count(), 1)

    def test_no_history_when_the_status_does_not_change(self, _check_tcp_port):
        with mock.patch("monitoring.supervision.ping", return_value=ANSWER):
            run_cycle()
            run_cycle()

        self.assertEqual(StatusChange.objects.count(), 1)

    def test_supervise_command_runs_one_cycle(self, _check_tcp_port):
        with mock.patch("monitoring.supervision.ping", return_value=ANSWER):
            call_command("supervise", "--once", stdout=StringIO())

        self.device.refresh_from_db()
        self.assertEqual(self.device.status, Device.Status.ONLINE)
