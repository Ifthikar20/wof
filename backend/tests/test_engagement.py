import pytest

from apps.engagement.models import Comment
from apps.stories.models import Story

from .conftest import auth, make_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def story(founder):
    from apps.stories import services

    s = Story(author=founder, slug="garage-1", title="Garage", body_markdown="Once upon a time")
    services.save_revision(s, founder)
    s.publish()
    s.save()
    return s


def test_like_is_idempotent(client, reader, story):
    auth(client, reader)
    for _ in range(3):
        assert client.post(f"/api/v1/stories/{story.slug}/like").status_code == 200
    story.refresh_from_db()
    assert story.like_count == 1
    client.delete(f"/api/v1/stories/{story.slug}/like")
    client.delete(f"/api/v1/stories/{story.slug}/like")
    story.refresh_from_db()
    assert story.like_count == 0


def test_anonymous_can_read_but_not_interact(client, story):
    assert client.get(f"/api/v1/stories/{story.slug}/comments").status_code == 200
    assert client.post(f"/api/v1/stories/{story.slug}/like").status_code == 403
    assert (
        client.post(
            f"/api/v1/stories/{story.slug}/comments", {"body": "hi"}, format="json"
        ).status_code
        == 403
    )


def test_spammy_comment_is_held(client, story, db):
    newbie = make_user(email="n@example.org", handle="newbie")
    auth(client, newbie)
    res = client.post(
        f"/api/v1/stories/{story.slug}/comments",
        {"body": "Great! see https://spam.example"},
        format="json",
    )
    assert res.status_code == 201
    assert res.json()["status"] == "pending"
    assert "new_account_link" in Comment.objects.get().spam_flags
    assert client.get(f"/api/v1/stories/{story.slug}/comments").json()["results"] == []


def test_clean_comment_visible(client, reader, story):
    auth(client, reader)
    res = client.post(
        f"/api/v1/stories/{story.slug}/comments", {"body": "Inspiring."}, format="json"
    )
    assert res.json()["status"] == "visible"
    story.refresh_from_db()
    assert story.comment_count == 1


def test_private_boards_are_private(client, reader, story, db):
    auth(client, reader)
    board = client.post("/api/v1/boards", {"name": "Favourites"}, format="json").json()
    assert (
        client.post(
            f"/api/v1/boards/{board['id']}/saves", {"story": story.slug}, format="json"
        ).status_code
        == 201
    )
    assert len(client.get(f"/api/v1/boards/{board['id']}").json()["stories"]) == 1

    stranger = auth(type(client)(), make_user(email="s@example.org", handle="stranger"))
    assert stranger.get(f"/api/v1/boards/{board['id']}").status_code == 404
    assert (
        stranger.post(
            f"/api/v1/boards/{board['id']}/saves", {"story": story.slug}, format="json"
        ).status_code
        == 404
    )
    assert type(client)().get(f"/api/v1/boards/{board['id']}").status_code == 404


def test_moderator_hides_reported_story(client, reader, moderator, story):
    auth(client, reader)
    assert client.get(f"/api/v1/stories/{story.slug}").json()["id"] == str(story.id)
    report = client.post(
        "/api/v1/reports",
        {"target_type": "story", "target_id": str(story.id), "reason": "plagiarism"},
        format="json",
    ).json()
    mod = auth(type(client)(), moderator)
    assert len(mod.get("/api/v1/moderation/reports").json()["results"]) == 1
    res = mod.post(
        "/api/v1/moderation/actions",
        {
            "action": "hide_story",
            "target_id": str(story.id),
            "reason": "copied from a blog",
            "report_id": report["id"],
        },
        format="json",
    )
    assert res.status_code == 201
    assert type(client)().get(f"/api/v1/stories/{story.slug}").status_code == 404
    # moderation requires a reason
    res = mod.post(
        "/api/v1/moderation/actions",
        {"action": "restore_story", "target_id": str(story.id), "reason": ""},
        format="json",
    )
    assert res.status_code == 400


def test_cannot_follow_self(client, founder):
    auth(client, founder)
    assert client.post(f"/api/v1/founders/{founder.handle}/follow").status_code == 400
