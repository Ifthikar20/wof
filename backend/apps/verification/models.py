import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.fields import EncryptedTextField


class Company(models.Model):
    name = models.CharField(max_length=120)
    domain = models.CharField(max_length=253, unique=True)
    website = models.URLField(blank=True)
    crunchbase_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self) -> str:
        return f"{self.name} ({self.domain})"


class FounderProfile(models.Model):
    """Current founder status of a user. History lives in VerificationRequest + AuditLog."""

    class Status(models.TextChoices):
        VERIFIED = "verified", "Verified"
        EXPIRED = "expired", "Expired (re-verification due)"
        REVOKED = "revoked", "Revoked"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="founder_profile"
    )
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="founders")
    title = models.CharField(max_length=80)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.VERIFIED)
    verified_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    linkedin_url = models.URLField(blank=True)

    @property
    def is_currently_verified(self) -> bool:
        return self.status == self.Status.VERIFIED and self.expires_at > timezone.now()

    def __str__(self) -> str:
        return f"{self.user} @ {self.company}"


class VerificationRequest(models.Model):
    class Status(models.TextChoices):
        EMAIL_PENDING = "email_pending", "Awaiting work-email confirmation"
        UNDER_REVIEW = "under_review", "Under human review"
        NEEDS_INFO = "needs_info", "More information requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn / superseded"

    OPEN_STATUSES = (Status.EMAIL_PENDING, Status.UNDER_REVIEW, Status.NEEDS_INFO)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification_requests"
    )
    company_name = models.CharField(max_length=120)
    company_domain = models.CharField(max_length=253, db_index=True)
    work_email = models.EmailField()
    role_title = models.CharField(max_length=80)
    linkedin_url = models.URLField(blank=True)
    crunchbase_url = models.URLField(blank=True)
    # Free-text evidence is encrypted at rest and purged after a decision.
    notes = EncryptedTextField(blank=True, default="")

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.EMAIL_PENDING, db_index=True
    )
    email_token_hash = models.CharField(max_length=64, blank=True, db_index=True)
    email_token_expires_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_reason = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            # At most one open request per user.
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status__in=["email_pending", "under_review", "needs_info"]),
                name="one_open_verification_per_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.work_email} [{self.status}]"
