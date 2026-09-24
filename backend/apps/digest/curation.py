"""
Deterministic digest curation (no AI):

  1. Editor picks (Story.featured_at within the window) always go first.
  2. Remaining slots are filled by an engagement score with time decay:
         score = (likes + 2*saves + 1.5*comments + 1) / (age_hours + 2) ** 1.5
     (a Hacker-News-style gravity formula: transparent and hard to game cheaply,
     because likes/saves need real accounts and are rate-limited).
  3. Diversity: at most one story per founder and per company per issue.
  4. Only currently-verified founders' published stories are eligible.
"""

from datetime import timedelta

from django.utils import timezone

from apps.stories.models import Story

MIN_ITEMS, MAX_ITEMS = 3, 7
WINDOW = timedelta(days=7)


def score(story: Story, now) -> float:
    age_hours = max((now - story.published_at).total_seconds() / 3600, 0)
    points = story.like_count + 2 * story.save_count + 1.5 * story.comment_count + 1
    return points / (age_hours + 2) ** 1.5


def select_stories(now=None) -> list[tuple[Story, bool]]:
    now = now or timezone.now()
    candidates = [
        s
        for s in Story.objects.filter(
            status=Story.Status.PUBLISHED,
            published_at__gte=now - WINDOW,
            author__is_suspended=False,
        ).select_related("author__founder_profile__company")
        if s.author.is_verified_founder
    ]
    picks = sorted(
        (s for s in candidates if s.featured_at and s.featured_at >= now - WINDOW),
        key=lambda s: s.featured_at,
    )
    rest = sorted((s for s in candidates if s not in picks), key=lambda s: -score(s, now))

    chosen: list[tuple[Story, bool]] = []
    seen_authors, seen_companies = set(), set()
    for story, is_pick in [(s, True) for s in picks] + [(s, False) for s in rest]:
        company = story.author.founder_profile.company_id
        if story.author_id in seen_authors or company in seen_companies:
            continue
        chosen.append((story, is_pick))
        seen_authors.add(story.author_id)
        seen_companies.add(company)
        if len(chosen) == MAX_ITEMS:
            break
    return chosen
