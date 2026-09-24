import secrets

from django.db import transaction
from django.utils.text import slugify

from apps.audit import services as audit
from apps.common.hashing import canonical_json, sha256_hex

from .models import Story, StoryRevision
from .rendering import render_markdown


def unique_slug(title: str) -> str:
    base = slugify(title)[:100] or "story"
    return f"{base}-{secrets.token_hex(3)}"


@transaction.atomic
def save_revision(story: Story, editor, *, request=None, action: str = "story.updated") -> Story:
    """Re-render, re-hash and snapshot a story. Call after mutating content fields."""
    story.body_html = render_markdown(story.body_markdown)
    story.update_reading_time()
    new_hash = story.compute_content_hash()
    if new_hash == story.content_hash and story.revision_number:
        story.save()
        return story  # metadata-only change; no new revision

    prev = story.revisions.order_by("-number").first() if story.pk else None
    story.revision_number += 1
    story.content_hash = new_hash
    story.save()
    prev_chain = prev.chain_hash if prev else ""
    StoryRevision.objects.create(
        story=story,
        number=story.revision_number,
        title=story.title,
        dek=story.dek,
        body_markdown=story.body_markdown,
        content_hash=new_hash,
        prev_hash=prev_chain,
        chain_hash=sha256_hex(prev_chain + new_hash),
        created_by=editor,
    )
    audit.record(
        action,
        actor=editor,
        target=story,
        request=request,
        metadata={"revision": story.revision_number, "content_hash": new_hash},
    )
    return story


def verify_story_integrity(story: Story) -> bool:
    """True if the live row matches its latest revision and the revision chain is intact."""
    prev_chain = ""
    last = None
    for rev in story.revisions.order_by("number"):
        payload = {"title": rev.title, "dek": rev.dek, "body_markdown": rev.body_markdown}
        if sha256_hex(canonical_json(payload)) != rev.content_hash:
            return False
        expected_chain = sha256_hex(prev_chain + rev.content_hash)
        if rev.prev_hash != prev_chain or rev.chain_hash != expected_chain:
            return False
        prev_chain, last = rev.chain_hash, rev
    if last is None:
        return False
    return story.compute_content_hash() == last.content_hash == story.content_hash
