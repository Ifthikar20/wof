"""The no-Docker local storage backend must honour the same contract as S3."""

import io

import pytest
from django.core import signing
from PIL import Image
from rest_framework.test import APIClient

from apps.stories import storage
from apps.stories.models import Media

from .conftest import auth

pytestmark = pytest.mark.django_db


@pytest.fixture
def local(settings, tmp_path):
    settings.LOCAL_MEDIA_ROOT = tmp_path / "media"
    settings.DEBUG = True
    import importlib

    from django.urls import clear_url_caches

    import wof.urls

    importlib.reload(wof.urls)
    clear_url_caches()
    yield tmp_path / "media"
    settings.LOCAL_MEDIA_ROOT = ""
    importlib.reload(wof.urls)
    clear_url_caches()


def jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (640, 400), (10, 120, 200)).save(buf, format="JPEG")
    return buf.getvalue()


def test_presigned_upload_points_at_local_view_with_signed_token(local, client, reader):
    auth(client, reader)
    res = client.post("/api/v1/media/uploads", {"content_type": "image/jpeg"}, format="json")
    assert res.status_code == 201
    upload = res.json()["upload"]
    assert upload["url"].endswith("/api/v1/media/local-upload")
    tok = storage.read_upload_token(upload["fields"]["token"])
    assert tok["ct"] == "image/jpeg" and tok["key"].startswith(f"u/{reader.pk.hex}/")


def test_full_local_upload_pipeline(
    local, client, reader, settings, django_capture_on_commit_callbacks
):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    auth(client, reader)
    res = client.post("/api/v1/media/uploads", {"content_type": "image/jpeg"}, format="json").json()
    media_id, fields = res["media_id"], res["upload"]["fields"]

    # Anonymous client: the token, not the cookie, authorises the upload (like an S3 policy).
    up = APIClient().post(
        "/api/v1/media/local-upload",
        {**fields, "file": io.BytesIO(jpeg())},
        format="multipart",
    )
    assert up.status_code == 201, up.content
    assert (local / "private" / storage.read_upload_token(fields["token"])["key"]).exists()

    with django_capture_on_commit_callbacks(execute=True):
        done = client.post(f"/api/v1/media/{media_id}/complete")
    assert done.status_code == 202
    media = Media.objects.get(pk=media_id)
    assert media.status == "ready", media.rejection_reason
    assert (local / "public" / media.display_key).exists()

    served = APIClient().get(f"/local-media/{media.display_key}")
    assert served.status_code == 200 and served["Content-Type"] == "image/webp"
    assert b"".join(served.streaming_content)[:4] == b"RIFF"


def test_upload_rejects_bad_token_wrong_type_and_traversal(local, client, reader):
    auth(client, reader)
    fields = client.post(
        "/api/v1/media/uploads", {"content_type": "image/png"}, format="json"
    ).json()["upload"]["fields"]
    anon = APIClient()
    assert (
        anon.post(
            "/api/v1/media/local-upload",
            {"token": "x", "file": io.BytesIO(b"1")},
            format="multipart",
        ).status_code
        == 403
    )
    forged = signing.dumps(
        {"key": "../../etc/passwd", "ct": "image/png"}, salt=storage.UPLOAD_TOKEN_SALT
    )
    assert (
        anon.post(
            "/api/v1/media/local-upload",
            {"token": forged, "Content-Type": "image/png", "file": io.BytesIO(b"1")},
            format="multipart",
        ).status_code
        == 400
    )
    wrong = anon.post(
        "/api/v1/media/local-upload",
        {**fields, "Content-Type": "image/jpeg", "file": io.BytesIO(b"1")},
        format="multipart",
    )
    assert wrong.status_code == 400
    assert anon.get("/local-media/../private/x").status_code == 404
    with pytest.raises(ValueError):
        storage.safe_key("m/../../x")


def test_local_backend_off_by_default(client, reader):
    assert client.get("/local-media/m/x/display.webp").status_code == 404
    assert APIClient().post("/api/v1/media/local-upload", {}, format="multipart").status_code == 404
