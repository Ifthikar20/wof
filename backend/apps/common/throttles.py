"""
Rate limiting. DRF's default get_ident() trusts X-Forwarded-For when NUM_PROXIES is
unset, which lets an attacker rotate fake IPs; every throttle here uses client_ip().
"""

from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle

from .net import client_ip


class ClientIpMixin:
    def get_ident(self, request):
        return client_ip(request)


class BurstRateThrottle(ClientIpMixin, SimpleRateThrottle):
    scope = "burst"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = f"u{request.user.pk}"
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class SustainedRateThrottle(BurstRateThrottle):
    scope = "sustained"


class ScopedThrottle(ClientIpMixin, ScopedRateThrottle):
    pass
