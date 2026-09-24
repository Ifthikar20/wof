import pytest
from rest_framework.settings import api_settings

pytestmark = pytest.mark.django_db


def test_feed_is_rate_limited_and_xff_cannot_bypass(client, monkeypatch):
    from rest_framework.throttling import SimpleRateThrottle

    rates = {**api_settings.DEFAULT_THROTTLE_RATES, "feed": "5/min", "burst": "100/min"}
    monkeypatch.setattr(SimpleRateThrottle, "THROTTLE_RATES", rates)
    codes = [
        client.get("/api/v1/stories", HTTP_X_FORWARDED_FOR=f"10.0.0.{i}").status_code
        for i in range(8)
    ]
    assert codes[:5] == [200] * 5
    assert 429 in codes[5:]
