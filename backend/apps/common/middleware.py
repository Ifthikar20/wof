class SecurityHeadersMiddleware:
    """
    Headers Django does not set itself. The API only ever returns JSON, so its CSP is
    maximally strict; the Next.js frontend sets its own nonce-based CSP for HTML pages.
    The Django admin needs its own (still strict) policy for its static assets.
    """

    API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    ADMIN_CSP = (
        "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
        "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        is_admin = request.path.startswith("/admin/")
        response.headers.setdefault(
            "Content-Security-Policy", self.ADMIN_CSP if is_admin else self.API_CSP
        )
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            response.headers["Cache-Control"] = "private, no-store"
        return response


class SuspendedUserMiddleware:
    """End the session of a suspended user on their next request. Suspension then takes
    effect immediately on every device, not just at the next login."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.is_suspended:
            from django.contrib.auth import logout

            logout(request)
        return self.get_response(request)
