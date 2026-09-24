from django.conf import settings


def client_ip(request) -> str:
    """
    Return the caller's IP address.

    Client-supplied headers such as X-Forwarded-For are trivially spoofable, so they are
    only honoured when TRUSTED_PROXY_IP_HEADER names a header set by our own edge
    (e.g. Cloudflare's CF-Connecting-IP, which the origin firewall guarantees).
    """
    header = settings.TRUSTED_PROXY_IP_HEADER
    if header:
        value = request.META.get(header, "").split(",")[0].strip()
        if value:
            return value
    return request.META.get("REMOTE_ADDR", "")


def user_agent(request, limit: int = 256) -> str:
    return request.META.get("HTTP_USER_AGENT", "")[:limit]
