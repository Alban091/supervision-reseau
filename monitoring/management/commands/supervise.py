import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from monitoring.supervision import run_cycle

CHECK_INTERVAL_SECONDS = 3


class Command(BaseCommand):
    help = "Check every device of the inventory every 3 seconds."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run a single cycle, then stop.")

    def handle(self, *args, **options):
        if options["once"]:
            self.run_one_cycle()
            return

        self.stdout.write(f"Supervision started, one cycle every {CHECK_INTERVAL_SECONDS} s.")
        while True:
            started = time.monotonic()
            self.run_one_cycle()
            # Closes the database connection if it is broken, for example after a restart
            # of the database. A new one is opened at the next cycle.
            close_old_connections()
            elapsed = time.monotonic() - started
            time.sleep(max(0, CHECK_INTERVAL_SECONDS - elapsed))

    def run_one_cycle(self):
        try:
            changes = run_cycle()
        except Exception as error:
            # One failed cycle must not stop the supervision.
            self.stderr.write(f"Cycle failed: {error}")
            return
        for change in changes:
            self.stdout.write(f"{change.device.name}: {change.old_status} -> {change.new_status}")
