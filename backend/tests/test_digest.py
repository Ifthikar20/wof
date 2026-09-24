from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.digest import services
from apps.digest.models import DigestDelivery, DigestIssue, Subscription
from apps.stories.models import Story

from .conftest import make_founder

pytestmark = pytest.mark.django_db


def confirm_token():
    return mail.outbox[-1].body.split("token=")[1].split()[0]


def test_double_opt_in_and_no_enumeration(client):
    r1 = client.post("/api/v1/digest/subscribe", {"email": "a@example.org"}, format="json")
    r2 = client.post("/api/v1/digest/subscribe", {"email": "a@example.org"}, format="json")
    assert r1.status_code == r2.status_code == 202
    assert r1.json() == r2.json()
    assert len(mail.outbox) == 1  # resend cooldown prevents mail-bombing
    assert Subscription.objects.get().status == "pending"
    assert (
        client.post("/api/v1/digest/confirm", {"token": confirm_token()}, format="json").status_code
        == 200
    )
    assert Subscription.objects.get().status == "active"


def test_forged_tokens_rejected(client):
    assert client.post("/api/v1/digest/confirm", {"token": "abc"}, format="json").status_code == 400
    assert client.post("/api/v1/digest/unsubscribe?token=abc").status_code == 400


def _stories(n):
    stories = []
    for i in range(n):
        f = make_founder(
            email=f"f{i}@c{i}.io", handle=f"founder{i}", company=f"C{i}", domain=f"c{i}.io"
        )
        s = Story.objects.create(
            author=f,
            slug=f"s-{i}",
            title=f"Story {i}",
            body_markdown="x",
            status=Story.Status.PUBLISHED,
            like_count=i,
            published_at=timezone.now() - timedelta(hours=i),
        )
        stories.append(s)
    # a second story by founder0 must not appear twice
    Story.objects.create(
        author=stories[0].author,
        slug="dup",
        title="Dup",
        body_markdown="x",
        status=Story.Status.PUBLISHED,
        like_count=100,
        published_at=timezone.now(),
    )
    return stories


def test_build_and_send_is_idempotent_with_unsubscribe_headers():
    _stories(5)
    sub = Subscription.objects.create(email="r@example.org", status="active")
    issue = services.build_issue()
    authors = [i.story.author_id for i in issue.items.all()]
    assert len(authors) == len(set(authors))  # one story per founder

    issue.status = DigestIssue.Status.SCHEDULED
    issue.save()
    assert services.send_issue(issue.pk) == 1
    msg = mail.outbox[-1]
    assert msg.extra_headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    unsub_url = msg.extra_headers["List-Unsubscribe"].strip("<>")

    DigestIssue.objects.filter(pk=issue.pk).update(status=DigestIssue.Status.SENDING)
    assert services.send_issue(issue.pk) == 0  # retry does not double-send
    assert DigestDelivery.objects.count() == 1

    from rest_framework.test import APIClient

    token = unsub_url.split("token=")[1]
    res = APIClient().post(f"/api/v1/digest/unsubscribe?token={token}")
    assert res.status_code == 200
    sub.refresh_from_db()
    assert sub.status == "unsubscribed"


def test_unsubscribe_get_never_mutates(client):
    sub = Subscription.objects.create(email="g@example.org", status="active")
    from apps.digest.tokens import make_unsubscribe_token

    res = client.get(f"/api/v1/digest/unsubscribe?token={make_unsubscribe_token(sub.id)}")
    assert res.status_code == 405
    sub.refresh_from_db()
    assert sub.status == "active"


def test_too_few_stories_skips_issue():
    _stories(1)
    assert services.build_issue() is None
