"""One supervision cycle: probe every device in parallel, then save what changed."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone

from .models import Device, Port, StatusChange
from .probes import ProbeResult, check_tcp_port, ping

# A device goes offline only after this many failed pings in a row,
# so that a single lost packet does not raise a false alert.
FAILURES_BEFORE_OFFLINE = 2

MAX_PARALLEL_CHECKS = 20


@dataclass
class DeviceCheck:
    ping: ProbeResult
    # Result of each port check, by port id.
    ports: dict[int, ProbeResult] = field(default_factory=dict)


def next_status(current: str, failures: int, reachable: bool) -> tuple[str, int]:
    """Return the new status and the new number of consecutive failures after one ping."""
    if reachable:
        return Device.Status.ONLINE, 0

    failures += 1
    if failures >= FAILURES_BEFORE_OFFLINE:
        return Device.Status.OFFLINE, failures
    return current, failures


def probe_device(device: Device) -> DeviceCheck:
    """Run the network probes of one device. Runs in a thread, so no database access here."""
    check = DeviceCheck(ping=ping(device.ip_address))
    if check.ping.reachable:
        # The ports were prefetched with the device, so this loop makes no query.
        for port in device.ports.all():
            check.ports[port.id] = check_tcp_port(device.ip_address, port.number)
    return check


def save_check(device: Device, check: DeviceCheck, now) -> StatusChange | None:
    """Store the result of one check and return the history entry if the status changed."""
    old_status = device.status
    device.status, device.consecutive_failures = next_status(
        device.status, device.consecutive_failures, check.ping.reachable
    )
    device.last_checked_at = now
    if check.ping.reachable:
        device.last_seen_at = now
    device.save(update_fields=["status", "consecutive_failures", "last_checked_at", "last_seen_at"])

    ports = list(device.ports.all())
    for port in ports:
        # A port of a device that does not answer the ping is considered closed.
        result = check.ports.get(port.id)
        port.is_open = result.reachable if result else False
        port.last_checked_at = now
    Port.objects.bulk_update(ports, ["is_open", "last_checked_at"])

    if device.status == old_status:
        return None
    return StatusChange.objects.create(
        device=device, old_status=old_status, new_status=device.status
    )


def run_cycle() -> list[StatusChange]:
    """Check every device once and return the status changes."""
    devices = list(Device.objects.prefetch_related("ports"))
    if not devices:
        return []

    # The probes wait for the network, so they run in parallel threads.
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_CHECKS) as pool:
        checks = list(pool.map(probe_device, devices))

    now = timezone.now()
    changes = []
    with transaction.atomic():
        for device, check in zip(devices, checks):
            change = save_check(device, check, now)
            if change:
                changes.append(change)
    return changes
