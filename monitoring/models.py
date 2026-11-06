from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Device(models.Model):
    """A piece of equipment watched by the supervision loop."""

    class Kind(models.TextChoices):
        SERVER = "server", "Serveur"
        PC = "pc", "PC"
        PRINTER = "printer", "Imprimante"

    class Status(models.TextChoices):
        UNKNOWN = "unknown", "Inconnu"
        ONLINE = "online", "En ligne"
        OFFLINE = "offline", "Hors ligne"

    name = models.CharField("nom", max_length=100, unique=True)
    kind = models.CharField("type", max_length=20, choices=Kind.choices)
    ip_address = models.GenericIPAddressField("adresse IP", protocol="IPv4", unique=True)

    # The fields below are updated by the supervision loop, not by hand.
    status = models.CharField("état", max_length=20, choices=Status.choices, default=Status.UNKNOWN)
    consecutive_failures = models.PositiveSmallIntegerField("échecs consécutifs", default=0)
    last_checked_at = models.DateTimeField("dernier contrôle", null=True, blank=True)
    last_seen_at = models.DateTimeField("dernière réponse", null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "équipement"

    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class Port(models.Model):
    """A TCP port to check on a device, for example 80 for a web server or 22 for SSH."""

    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="ports", verbose_name="équipement"
    )
    number = models.PositiveIntegerField(
        "numéro", validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    label = models.CharField("service", max_length=50, blank=True)

    # None means the port has not been checked yet.
    is_open = models.BooleanField("ouvert", null=True)
    last_checked_at = models.DateTimeField("dernier contrôle", null=True, blank=True)

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(fields=["device", "number"], name="unique_port_per_device")
        ]

    def __str__(self):
        return f"{self.device.name}:{self.number}"


class StatusChange(models.Model):
    """History entry written each time a device changes state."""

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="status_changes",
        verbose_name="équipement",
    )
    old_status = models.CharField("ancien état", max_length=20, choices=Device.Status.choices)
    new_status = models.CharField("nouvel état", max_length=20, choices=Device.Status.choices)
    changed_at = models.DateTimeField("date", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "changement d'état"
        verbose_name_plural = "historique des états"

    def __str__(self):
        return f"{self.device.name} : {self.old_status} -> {self.new_status}"
