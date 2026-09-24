"""Populate a local database with demo founders and stories. Refuses to run unless DEBUG."""

import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.stories import services
from apps.stories.models import Story, Tag
from apps.verification.models import Company, FounderProfile

TAGS = [
    "Bootstrapping",
    "Fundraising",
    "Failure",
    "Hiring",
    "Product",
    "Pivot",
    "First Customers",
    "Burnout",
    "Hardware",
    "Climate",
    "Fintech",
    "Open Source",
]

FOUNDERS = [
    ("maya", "Maya Okafor", "Solar Loop", "solarloop.energy", "Founder & CEO"),
    ("diego", "Diego Alvarez", "Tiny Ledger", "tinyledger.app", "Co-founder"),
    ("priya", "Priya Raman", "Kindred Health", "kindred.health", "Founder"),
    ("tom", "Tom Lindqvist", "Forge CAD", "forgecad.io", "CTO & Co-founder"),
    ("amara", "Amara Chen", "Pantry", "pantry.co", "Founder & CEO"),
    ("sam", "Sam Whitaker", "Openfield", "openfield.dev", "Founder"),
]

TITLES = [
    ("We ran out of money on a Tuesday", "How 11 days of panic turned into our best quarter."),
    ("The customer who said no 14 times", "Persistence, and knowing when to stop."),
    ("Why I fired myself as CEO", "Handing over the company I started was the right call."),
    ("Our first hire almost killed the company", "What we got wrong about culture fit."),
    (
        "Bootstrapped to $1M ARR with no sales team",
        "A spreadsheet, a newsletter and a lot of patience.",
    ),
    ("The pivot nobody believed in", "From B2C flop to B2B workhorse in six months."),
    ("Building hardware in a garage in 2025", "Tolerances, shipping containers, and humility."),
    ("What burnout actually felt like", "An honest account, and what changed afterwards."),
    (
        "How we landed our first 10 customers",
        "Cold emails, conference hallways and one lucky tweet.",
    ),
    ("Raising a seed round in a down market", "83 pitches, 3 term sheets, 1 decision."),
    ("Open-sourcing our core product", "Why giving it away grew revenue."),
    ("The night the servers melted", "A post-mortem of our launch day."),
    ("Selling to hospitals as a two-person startup", "Procurement, patience, and pilots."),
    ("Letting go of my co-founder", "The hardest conversation of my life."),
    ("From side project to company", "The exact moment I quit my job."),
    ("We said no to a $20M acquisition", "What we were optimising for instead."),
]

PARAGRAPHS = [
    "Nobody tells you that the hardest part of starting a company is the silence. "
    "No manager, no roadmap, nobody to tell you that you're doing it right.",
    "We had **three months of runway** and a product that nobody had asked for. "
    "So we did the only thing that made sense: we went and talked to fifty people.",
    "> The market doesn't care how hard you worked. It only cares whether you solved the problem.",
    "## What we learned\n\n- Talk to customers before writing code\n- Charge from day one\n"
    "- Hire slower than feels comfortable",
    "Looking back, the decision was obvious. At the time it felt like jumping off a cliff "
    "and building the parachute on the way down.",
    "If you're reading this in the middle of your own hard week: it gets better, "
    "and it gets clearer. Keep going, but keep your eyes open.",
]


class Command(BaseCommand):
    help = "Seed demo data (DEBUG only)."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo only runs with DEBUG=True")
        rng = random.Random(42)  # noqa: S311 - demo data
        with transaction.atomic():
            tags = [
                Tag.objects.get_or_create(name=n, defaults={"slug": n.lower().replace(" ", "-")})[0]
                for n in TAGS
            ]
            now = timezone.now()
            authors = []
            for handle, name, company, domain, title in FOUNDERS:
                user, created = User.objects.get_or_create(
                    handle=handle,
                    defaults={
                        "email": f"{handle}@{domain}",
                        "display_name": name,
                        "bio": f"{title} at {company}.",
                    },
                )
                if created:
                    user.set_password("demo-password-please-change")
                    user.save()
                co, _ = Company.objects.get_or_create(domain=domain, defaults={"name": company})
                FounderProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "company": co,
                        "title": title,
                        "verified_at": now,
                        "expires_at": now + timedelta(days=365),
                    },
                )
                authors.append(user)

            for i, (title, dek) in enumerate(TITLES):
                if Story.objects.filter(title=title).exists():
                    continue
                author = authors[i % len(authors)]
                body = "\n\n".join(rng.sample(PARAGRAPHS, k=rng.randint(3, 6)))
                story = Story(
                    author=author,
                    slug=services.unique_slug(title),
                    title=title,
                    dek=dek,
                    body_markdown=body,
                )
                services.save_revision(story, author, action="story.created")
                story.published_at = now - timedelta(hours=rng.randint(1, 24 * 20))
                story.publish()
                story.like_count = rng.randint(0, 400)
                story.save_count = rng.randint(0, 120)
                story.save()
                story.tags.set(rng.sample(tags, k=rng.randint(1, 3)))

            # Feature the most-saved story so the home hero has an editor pick.
            if not Story.objects.filter(featured_at__isnull=False).exists():
                top = (
                    Story.objects.filter(status=Story.Status.PUBLISHED)
                    .order_by("-save_count")
                    .first()
                )
                if top:
                    top.featured_at = now
                    top.save(update_fields=["featured_at"])

            if not User.objects.filter(email="admin@wof.local").exists():
                User.objects.create_superuser(
                    "admin@wof.local", "admin-demo-password", handle="wofadmin"
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(authors)} founders and {Story.objects.count()} stories. "
                "Admin: admin@wof.local / admin-demo-password (local only)."
            )
        )
