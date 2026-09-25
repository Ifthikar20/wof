from django.conf import settings
from django.contrib.auth import password_validation
from rest_framework import serializers

from apps.common.hashing import sha256_hex

from .models import RESERVED_HANDLES, RetiredHandle, User


class PublicUserSerializer(serializers.ModelSerializer):
    is_verified_founder = serializers.BooleanField(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["handle", "display_name", "bio", "avatar_url", "is_verified_founder"]

    def get_avatar_url(self, obj):
        return obj.avatar.display_url if obj.avatar_id and obj.avatar.is_ready else None


class MeSerializer(PublicUserSerializer):
    class Meta(PublicUserSerializer.Meta):
        fields = PublicUserSerializer.Meta.fields + [
            "email",
            "role",
            "email_verified",
            "totp_enabled",
            "founder_status",
            "can_publish",
            "needs_2fa",
        ]
        read_only_fields = ["email", "role", "email_verified", "totp_enabled"]

    founder_status = serializers.SerializerMethodField()
    can_publish = serializers.SerializerMethodField()
    needs_2fa = serializers.SerializerMethodField()

    def get_needs_2fa(self, obj):
        """Whether the server will refuse to publish until 2FA is on (REQUIRE_2FA_FOR_FOUNDERS)."""
        return bool(
            obj.is_verified_founder and settings.REQUIRE_2FA_FOR_FOUNDERS and not obj.totp_enabled
        )

    def get_can_publish(self, obj):
        return bool(obj.is_verified_founder and not self.get_needs_2fa(obj))

    def get_founder_status(self, obj):
        profile = getattr(obj, "founder_profile", None)
        return profile.status if profile else "unverified"


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["display_name", "bio"]


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, max_length=128)
    handle = serializers.CharField(max_length=30)
    display_name = serializers.CharField(max_length=80, required=False, allow_blank=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_handle(self, value):
        value = value.strip().lower()
        User._meta.get_field("handle").run_validators(value)
        if value in RESERVED_HANDLES:
            raise serializers.ValidationError("This handle is reserved.")
        if (
            User.objects.filter(handle=value).exists()
            or RetiredHandle.objects.filter(handle_hash=sha256_hex(value)).exists()
        ):
            raise serializers.ValidationError("This handle is taken.")
        return value

    def validate(self, attrs):
        candidate = User(email=attrs["email"], handle=attrs["handle"])
        password_validation.validate_password(attrs["password"], candidate)
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128)
    otp = serializers.CharField(max_length=8, required=False, allow_blank=True)


class OtpSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=8)
