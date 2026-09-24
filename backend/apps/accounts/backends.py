from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Authenticate by (lower-cased) email; ModelBackend already runs a dummy hash on
    unknown users to equalise timing and prevent account enumeration."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        email = (email or kwargs.get("username") or "").strip().lower()
        return super().authenticate(request, username=email, password=password)
