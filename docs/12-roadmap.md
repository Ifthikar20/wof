# 12 · Roadmap

## ✅ Milestone 0: Foundation (this repo)
- Architecture docs and ADRs.
- Django API: auth (Argon2, TOTP, lockout, breached-password check), founder
  verification, stories with hash-chained revisions, media sanitisation, likes, boards,
  comments with spam holds, follows, reports, moderation API, digest (double opt-in,
  curation, idempotent sending, one-click unsubscribe), hash-chained audit log with DB
  triggers, suspension that ends existing sessions.
- Next.js web: wall, story page, founder profile, auth, verification, editor with cover
  upload, boards, digest, 2FA setup, Turnstile, report button, nonce CSP, `robots.txt`, sitemap.
- docker-compose, CI (lint, types, tests on Postgres, deploy checks, dependency audits,
  secret scanning), Dependabot.

## Milestone 1: Private beta (≈ 6 weeks)
| Area | Work |
|---|---|
| Infra | Terraform for the reference architecture; Cloudflare WAF, bot rules, Access; object-lock audit anchoring; deploy pipeline |
| Security | External pen test; passkeys (WebAuthn) for founders and staff; email-first (magic-link) signup to close enumeration; `pip-compile --generate-hashes`; CODEOWNERS; Terms of Service page |
| Founders | QR code on the 2FA screen; re-verification reminders; story preview before publish |
| Moderation | Moderation console web UI; author notifications on hide/remove; second-reviewer sampling |
| Email | Provider bounce/complaint webhooks (signed); SPF/DKIM/DMARC; warm-up |
| Readers | Board management; choose a board when saving |
| Ops | OpenTelemetry traces/metrics; dashboards and alerts from [11](11-observability-and-operations.md) |

## Milestone 2: Public launch (≈ 8 weeks)
- Postgres full-text search (title, subtitle, body, tags) with a per-IP search throttle.
- Revision diff viewer; signed JSON export of a story's integrity chain.
- Self-serve data export and deletion.
- Registry lookups (Companies House, SEC EDGAR, OpenCorporates) shown to reviewers as
  **hints** in the verification queue.
- Transparency report page.
- Accessibility audit (external).
- Public bug bounty.

## Milestone 3: Community (post-launch)
- Founder-only community space (threads, office hours) behind verified status.
- Follow feed ("stories from founders you follow"), chronological.
- Series and collections by editors.
- Multiple digest editions (by topic), still double opt-in.
- Duplicate and plagiarism detection via shingle hashing (deterministic).

## Explicitly out of scope (by product decision)
- AI and ML of any kind ([ADR-0004](adr/0004-no-ai.md)).
- Advertising and third-party trackers.
- Public bulk API or data export of the corpus.
