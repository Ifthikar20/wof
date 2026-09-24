import json

import pyotp
import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.digest.models import Subscription
from apps.engagement.models import Board, Comment, Follow, Like, Save
from apps.stories import services
from apps.stories.models import Story
from apps.verification.models import FounderProfile

from .conftest import PASSWORD, auth, make_founder, make_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def world(founder, reader):
    """A founder with a story, and a reader who likes, saves, follows and comments on it."""
    story = Story(author=founder, slug="garage", title="Garage", body_markdown="Once upon a time")
    services.save_revision(story, founder)
    story.publish()
    story.save()
    Like.objects.create(user=reader, story=story)
    board = Board.objects.create(owner=reader, name="Faves")
    Save.objects.create(board=board, story=story)
    Follow.objects.create(follower=reader, founder=founder)
    Comment.objects.create(story=story, author=reader, body="Loved this, from Rhea")
    Story.objects.filter(pk=story.pk).update(like_count=1, save_count=1, comment_count=1)
    Subscription.objects.create(email=reader.email, user=reader, status="active")
    return story


def delete(client, **body):
    return client.post(
        "/api/v1/auth/me/delete", {"password": PASSWORD, "confirm": "DELETE", **body}, format="json"
    )


def test_export_contains_the_users_data(client, reader, world):
    res = auth(client, reader).get("/api/v1/auth/me/export")
    assert res.status_code == 200
    assert "attachment" in res["Content-Disposition"]
    data = json.loads(res.content)
    assert data["account"]["email"] == reader.email
    assert data["comments"][0]["body"] == "Loved this, from Rhea"
    assert data["likes"][0]["story"] == "garage"
    assert data["boards"][0]["stories"] == ["garage"]
    assert data["following"] == ["ada"]
    assert data["digest_subscriptions"][0]["status"] == "active"
    assert "password" not in json.dumps(data["account"])


def test_founder_export_includes_stories_and_revisions(client, founder, world):
    data = json.loads(auth(client, founder).get("/api/v1/auth/me/export").content)
    assert data["founder_profile"]["company"] == "Acme"
    assert data["stories"][0]["revisions"][0]["body_markdown"] == "Once upon a time"


def test_export_requires_login(client):
    assert client.get("/api/v1/auth/me/export").status_code == 403


def test_delete_requires_password_and_typed_confirmation(reader):
    c = APIClient()
    c.login(email=reader.email, password=PASSWORD)
    assert delete(c, password="wrong").status_code == 400
    assert delete(c, confirm="yes").status_code == 400
    reader.refresh_from_db()
    assert reader.is_active


def test_delete_requires_2fa_code_when_enabled(db):
    user = make_user(email="z@example.org", handle="zed")
    user.totp_secret = pyotp.random_base32()
    user.totp_enabled = True
    user.save()
    c = APIClient()
    c.login(email=user.email, password=PASSWORD)
    assert "otp" in delete(c).json()["error"]["fields"]
    assert delete(c, otp=pyotp.TOTP(user.totp_secret).now()).status_code == 204


def test_reader_deletion_erases_personal_data(reader, world, django_capture_on_commit_callbacks):
    other_device = APIClient()
    other_device.login(email=reader.email, password=PASSWORD)
    c = APIClient()
    c.login(email=reader.email, password=PASSWORD)
    old_email, old_handle = reader.email, reader.handle
    with django_capture_on_commit_callbacks(execute=True):
        assert delete(c).status_code == 204

    user = User.objects.get(pk=reader.pk)
    assert not user.is_active and not user.has_usable_password()
    assert (
        user.email != old_email
        and user.handle != old_handle
        and user.display_name == "Deleted user"
    )
    assert not Like.objects.filter(user=user).exists()
    assert not Board.objects.filter(owner=user).exists()
    assert not Follow.objects.filter(follower=user).exists()
    assert not Subscription.objects.filter(email=old_email).exists()
    comment = Comment.objects.get(author=user)
    assert comment.body == "" and comment.status == "hidden"
    world.refresh_from_db()
    assert (world.like_count, world.save_count, world.comment_count) == (0, 0, 0)
    # every session is gone, and a confirmation went to the original address
    assert other_device.get("/api/v1/auth/me").json() is None
    assert c.get("/api/v1/auth/me").json() is None
    assert mail.outbox[-1].to == [old_email]


def test_founder_deletion_removes_stories_and_retires_handle(founder, world):
    c = APIClient()
    c.login(email=founder.email, password=PASSWORD)
    assert delete(c).status_code == 204
    world.refresh_from_db()
    assert world.status == "removed"
    assert not FounderProfile.objects.filter(user_id=founder.pk).exists()
    assert APIClient().get("/api/v1/stories").json()["results"] == []
    # nobody can re-register the deleted founder's handle to impersonate them
    res = APIClient().post(
        "/api/v1/auth/signup",
        {"email": "new@example.org", "password": "another long passphrase 55", "handle": "ada"},
        format="json",
    )
    assert res.status_code == 400 and "handle" in res.json()["error"]["fields"]


def test_superuser_cannot_self_delete(db):
    admin = User.objects.create_superuser("root@wof.test", PASSWORD, handle="rootadmin")
    c = APIClient()
    c.login(email=admin.email, password=PASSWORD)
    assert delete(c).status_code == 400


def test_other_founders_unaffected(founder, world):
    other = make_founder(email="bo@beta.io", handle="bo", domain="beta.io")
    c = APIClient()
    c.login(email=founder.email, password=PASSWORD)
    delete(c)
    assert User.objects.get(pk=other.pk).is_verified_founder
