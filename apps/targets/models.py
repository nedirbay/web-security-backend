"""Models for target management."""
from django.conf import settings
from django.db import models


class Target(models.Model):
    """A scan target owned by a user."""

    class VerificationMethod(models.TextChoices):
        DNS = "dns", "DNS"
        FILE = "file", "File"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="targets",
    )
    url = models.URLField(unique=True)
    is_active = models.BooleanField(default=True)
    verification_method = models.CharField(
        max_length=10,
        choices=VerificationMethod.choices,
        default=VerificationMethod.DNS,
    )
    verification_token = models.CharField(max_length=64)
    verification_status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.url} ({self.owner.email})"
