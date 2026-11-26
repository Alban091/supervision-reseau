import socket
import subprocess
from unittest import mock

from django.test import SimpleTestCase

from .probes import check_tcp_port, ping


class PingTests(SimpleTestCase):
    def test_localhost_answers(self):
        result = ping("127.0.0.1")

        self.assertTrue(result.reachable)
        self.assertIsNotNone(result.latency_ms)

    def test_no_answer_means_unreachable(self):
        no_answer = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
        with mock.patch("monitoring.probes.subprocess.run", return_value=no_answer):
            result = ping("10.10.0.99")

        self.assertFalse(result.reachable)
        self.assertIsNone(result.latency_ms)

    def test_latency_is_read_from_ping_output(self):
        output = "64 bytes from 10.10.0.10: icmp_seq=1 ttl=64 time=0.42 ms"
        answer = subprocess.CompletedProcess(args=[], returncode=0, stdout=output, stderr="")
        with mock.patch("monitoring.probes.subprocess.run", return_value=answer):
            result = ping("10.10.0.10")

        self.assertEqual(result.latency_ms, 0.42)


class TcpPortTests(SimpleTestCase):
    def test_listening_port_is_open(self):
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            server.listen()
            port = server.getsockname()[1]

            result = check_tcp_port("127.0.0.1", port)

        self.assertTrue(result.reachable)
        self.assertIsNotNone(result.latency_ms)

    def test_closed_port_is_not_open(self):
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            port = server.getsockname()[1]
        # The socket is closed here, so nothing listens on this port anymore.

        result = check_tcp_port("127.0.0.1", port)

        self.assertFalse(result.reachable)
        self.assertIsNone(result.latency_ms)
