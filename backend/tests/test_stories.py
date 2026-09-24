import pytest

from apps.stories.models import Story, StoryRevision
from apps.stories.rendering import render_markdown
from apps.stories.services import verify_story_integrity

from .conftest import auth, make_founder

pytestmark = pytest.mark.django_db

BODY = "We started in a garage.\n\n## Year one\n\nIt was **hard**."


def create(client, **extra):
    return client.post(
        "/api/v1/stories",
        {"title": "How we started", "dek": "A garage story", "body_markdown": BODY, **extra},
        format="json",
    )


def test_anonymous_and_readers_cannot_publish(client, reader):
    assert create(client).status_code == 403
    assert create(auth(client, reader)).status_code == 403


def test_founder_draft_publish_and_public_visibility(client, founder):
    auth(client, founder)
    res = create(client)
    assert res.status_code == 201
    slug = res.json()["slug"]
    assert res.json()["status"] == "draft"

    anon = type(client)()
    assert anon.get(f"/api/v1/stories/{slug}").status_code == 404  # drafts are invisible
    assert anon.get("/api/v1/stories").json()["results"] == []

    assert client.post(f"/api/v1/stories/{slug}/publish").status_code == 200
    detail = anon.get(f"/api/v1/stories/{slug}")
    assert detail.status_code == 200
    data = detail.json()
    assert "<strong>hard</strong>" in data["body_html"]
    assert data["author"]["is_verified_founder"] is True
    assert data["author"]["company"] == "Acme"
    assert len(data["content_hash"]) == 64
    assert anon.get("/api/v1/stories").json()["results"][0]["slug"] == slug
    assert detail["Cache-Control"].startswith("public")


def test_only_author_can_edit(client, founder):
    slug = create(auth(client, founder)).json()["slug"]
    other = auth(type(client)(), make_founder(email="bob@beta.io", handle="bob", domain="beta.io"))
    assert (
        other.patch(f"/api/v1/stories/{slug}", {"title": "pwned"}, format="json").status_code == 404
    )  # draft not even visible
    client.post(f"/api/v1/stories/{slug}/publish")
    assert (
        other.patch(f"/api/v1/stories/{slug}", {"title": "pwned"}, format="json").status_code == 403
    )
    assert other.delete(f"/api/v1/stories/{slug}").status_code == 403


def test_xss_is_stripped():
    html = render_markdown(
        "<script>alert(1)</script>\n\n[x](javascript:alert(1)) <img src=x onerror=alert(1)>"
        "\n\n![img](https://evil.example/pixel.gif)"
    )
    # Everything dangerous is either dropped or rendered as inert, escaped text.
    assert "<script" not in html
    assert 'href="javascript' not in html
    assert "<img" not in html
    assert "&lt;script&gt;" in html


def test_links_get_safe_rel():
    html = render_markdown("[site](https://example.com)")
    assert 'rel="nofollow noopener noreferrer ugc"' in html


def test_edits_create_hash_chained_revisions(client, founder):
    auth(client, founder)
    slug = create(client).json()["slug"]
    client.patch(f"/api/v1/stories/{slug}", {"body_markdown": BODY + "\n\nUpdate."}, format="json")
    story = Story.objects.get(slug=slug)
    assert story.revision_number == 2
    revs = list(story.revisions.order_by("number"))
    assert revs[1].prev_hash == revs[0].chain_hash
    assert verify_story_integrity(story)

    public = client.post(f"/api/v1/stories/{slug}/publish")
    assert public.status_code == 200
    history = type(client)().get(f"/api/v1/stories/{slug}/revisions").json()
    assert [r["number"] for r in history] == [1, 2]


def test_out_of_band_tampering_is_detected(client, founder):
    slug = create(auth(client, founder)).json()["slug"]
    # Simulate an attacker with raw DB access editing the live row.
    Story.objects.filter(slug=slug).update(body_markdown="Totally different words")
    assert not verify_story_integrity(Story.objects.get(slug=slug))


def test_revisions_are_immutable(client, founder):
    from apps.audit.models import ImmutableRecordError

    slug = create(auth(client, founder)).json()["slug"]
    rev = StoryRevision.objects.get(story__slug=slug)
    rev.body_markdown = "rewritten history"
    with pytest.raises(ImmutableRecordError):
        rev.save()
    with pytest.raises(ImmutableRecordError):
        rev.delete()


def test_feed_ignores_client_page_size(client, founder):
    auth(client, founder)
    for i in range(30):
        slug = create(client, title=f"Story {i}").json()["slug"]
        client.post(f"/api/v1/stories/{slug}/publish")
    res = type(client)().get("/api/v1/stories?page_size=1000&limit=1000")
    body = res.json()
    assert len(body["results"]) == 24
    assert body["next"] and "cursor=" in body["next"]
    assert "count" not in body  # no total count to size a scrape


def test_suspended_founder_stories_disappear(client, founder):
    auth(client, founder)
    slug = create(client).json()["slug"]
    client.post(f"/api/v1/stories/{slug}/publish")
    founder.is_suspended = True
    founder.save()
    assert type(client)().get("/api/v1/stories").json()["results"] == []


def test_body_size_limit(client, founder):
    res = create(auth(client, founder), body_markdown="x" * 70_000)
    assert res.status_code in (400, 413)


def test_search_by_title_dek_and_tag(client, founder):
    from apps.stories.models import Tag

    auth(client, founder)
    Tag.objects.create(name="Burnout", slug="burnout")
    a = create(client, title="Garage beginnings", dek="How it started").json()["slug"]
    b = create(client, title="Quiet year", dek="Running on empty", tags=["burnout"]).json()["slug"]
    c = create(client, title="Unrelated", dek="Nothing here").json()["slug"]
    for slug in (a, b, c):
        client.post(f"/api/v1/stories/{slug}/publish")
    anon = type(client)()

    def search(q):
        return {s["slug"] for s in anon.get("/api/v1/stories", {"q": q}).json()["results"]}

    assert search("garage") == {a}
    assert search("EMPTY") == {b}
    assert search("burn") == {b}  # tag name, no duplicate rows
    assert search("   ") == {a, b, c}  # blank query means no filter


def test_featured_filter_returns_only_editor_picks(client, founder):
    from django.utils import timezone

    auth(client, founder)
    picked = create(client, title="Editor pick").json()["slug"]
    other = create(client, title="Regular").json()["slug"]
    for slug in (picked, other):
        client.post(f"/api/v1/stories/{slug}/publish")
    Story.objects.filter(slug=picked).update(featured_at=timezone.now())
    res = type(client)().get("/api/v1/stories", {"featured": "1"}).json()["results"]
    assert [s["slug"] for s in res] == [picked]
