from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.verification import views as verification_views

# Django admin is the moderation/editorial console. It requires a staff account whose
# session passed TOTP at login (see accounts.views.LoginView); in production it is
# additionally only reachable through Cloudflare Access (SSO + device posture).
_default_has_permission = admin.site.has_permission


def _admin_has_permission(request):
    if not _default_has_permission(request):
        return False
    if settings.REQUIRE_2FA_FOR_STAFF:
        return bool(request.user.totp_enabled and request.session.get("otp_verified"))
    return True


admin.site.has_permission = _admin_has_permission
admin.site.site_header = "Wall of Founders - Moderation"
admin.site.site_title = "WoF admin"


def healthz(_request):
    return JsonResponse({"ok": True})


api_v1 = [
    path("auth/", include("apps.accounts.urls")),
    # No trailing slashes anywhere: the Next.js /api proxy strips them, and Django's
    # APPEND_SLASH redirect would then loop.
    path("verification", verification_views.MyVerificationView.as_view()),
    path("verification/confirm-email", verification_views.ConfirmEmailView.as_view()),
    path("", include("apps.stories.urls")),
    path("", include("apps.engagement.urls")),
    path("moderation/", include("apps.moderation.urls")),
    path("digest/", include("apps.digest.urls")),
]

urlpatterns = [
    path("healthz", healthz),
    path("api/v1/", include(api_v1)),
    path(settings.ADMIN_URL, admin.site.urls),
]
