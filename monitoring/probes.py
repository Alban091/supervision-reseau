"""Network probes used by the supervision loop to check if a device answers."""

import re
import socket
import subprocess
import time
from dataclasses import dataclass

TIMEOUT_SECONDS = 1

# Round-trip time printed by ping, for example "time=0.42 ms".
PING_TIME = re.compile(r"time=([\d.]+) ms")


@dataclass
class ProbeResult:
    reachable: bool
    latency_ms: float | None = None


def ping(ip_address: str, timeout: int = TIMEOUT_SECONDS) -> ProbeResult:
    """Send one ICMP echo request and wait at most `timeout` seconds for the answer."""
    command = ["ping", "-c", "1", "-n", "-W", str(timeout), ip_address]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 1)
    except subprocess.TimeoutExpired:
        return ProbeResult(reachable=False)

    if completed.returncode != 0:
        return ProbeResult(reachable=False)

    match = PING_TIME.search(completed.stdout)
    latency_ms = float(match.group(1)) if match else None
    return ProbeResult(reachable=True, latency_ms=latency_ms)


def check_tcp_port(ip_address: str, port: int, timeout: float = TIMEOUT_SECONDS) -> ProbeResult:
    """Try to open a TCP connection: the port is open if the connection succeeds."""
    start = time.perf_counter()
    try:
        with socket.create_connection((ip_address, port), timeout=timeout):
            pass
    except OSError:
        # Refused connection, timeout or unreachable host.
        return ProbeResult(reachable=False)

    latency_ms = (time.perf_counter() - start) * 1000
    return ProbeResult(reachable=True, latency_ms=round(latency_ms, 2))
