from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsVerifiedFounder(BasePermission):
    message = "Only verified founders can do this."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated and user.is_verified_founder):
            return False
        if settings.REQUIRE_2FA_FOR_FOUNDERS and not user.totp_enabled:
            self.message = "Enable two-factor authentication before publishing."
            return False
        return True


class IsAuthorOrReadOnly(BasePermission):
    message = "You can only modify your own content."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "author_id", None) == request.user.pk


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, "owner_id", None) == request.user.pk


class IsModerator(BasePermission):
    message = "Moderator access required."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.is_moderator):
            return False
        if settings.REQUIRE_2FA_FOR_STAFF and not user.totp_enabled:
            self.message = "Staff accounts must have two-factor authentication enabled."
            return False
        return True
