import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.common.fields import EncryptedTextField

handle_validator = RegexValidator(
    r"^[a-z0-9](?:[a-z0-9_]{1,28}[a-z0-9])$",
    "Handles are 3-30 chars: lowercase letters, digits and underscores.",
)
RESERVED_HANDLES = {
    "admin",
    "api",
    "root",
    "support",
    "moderator",
    "staff",
    "founders",
    "wall",
    "walloffounders",
    "help",
    "security",
    "digest",
    "about",
    "login",
    "signup",
}


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("role", User.Role.ADMIN)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("handle", email.split("@")[0][:30].lower())
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        READER = "reader", "Reader"
        MODERATOR = "moderator", "Moderator"
        ADMIN = "admin", "Admin"

    # UUID primary keys: no sequential IDs to enumerate.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    handle = models.CharField(max_length=30, unique=True, validators=[handle_validator])
    display_name = models.CharField(max_length=80, blank=True)
    bio = models.CharField(max_length=280, blank=True)
    avatar = models.ForeignKey(
        "stories.Media", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.READER)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Django-admin access
    is_suspended = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    totp_secret = EncryptedTextField(blank=True, default="")
    totp_enabled = models.BooleanField(default=False)
    totp_last_used_step = models.BigIntegerField(default=0)  # replay protection

    failed_login_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.handle or self.email

    # --- roles --------------------------------------------------------------------------
    @property
    def is_moderator(self) -> bool:
        return self.role in {self.Role.MODERATOR, self.Role.ADMIN} and not self.is_suspended

    @property
    def is_verified_founder(self) -> bool:
        if self.is_suspended:
            return False
        profile = getattr(self, "founder_profile", None)
        return bool(profile and profile.is_currently_verified)

    # --- brute-force protection ---------------------------------------------------------
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_failed_login(self) -> None:
        self.failed_login_count += 1
        over = self.failed_login_count - settings.LOGIN_MAX_FAILURES
        if over >= 0:
            minutes = min(2**over, settings.LOGIN_LOCKOUT_MAX_MINUTES)
            self.locked_until = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=["failed_login_count", "locked_until"])

    def register_successful_login(self) -> None:
        if self.failed_login_count or self.locked_until:
            self.failed_login_count = 0
            self.locked_until = None
            self.save(update_fields=["failed_login_count", "locked_until"])
