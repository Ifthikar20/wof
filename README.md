# Wall of Founders

**The modern Reader's Digest for builders.** A Pinterest-style wall of first-person
stories written by **verified founders**, plus a weekly email digest of the best ones.

- **Anyone** can browse, read and share, with no account needed.
- **Readers** with a free account can like, save to boards, comment, follow and report.
- **Founders** prove who they are (a company-domain email plus human-reviewed
  LinkedIn/Crunchbase evidence) and can then publish.
- **Every edit is on the record**: each story carries a public SHA-256 and an immutable,
  hash-chained revision history. Every privileged action lands in a tamper-evident audit log.
- **No AI anywhere.** Curation and moderation are deterministic and explainable.

| The wall | A story |
|---|---|
| Masonry of typographic and cover cards, topic filters, verified badges | Serif reading view, like/save/report, integrity record, conversation |

## Documentation

| # | Doc | What's inside |
|---|---|---|
| 00 | [Vision & personas](docs/00-vision-and-personas.md) | Why this exists, who it serves, glossary |
| 01 | [Product requirements](docs/01-product-requirements.md) | Features by role with implementation status, NFRs, non-goals |
| 02 | [System architecture](docs/02-system-architecture.md) | Components, diagrams, request flows, sync vs async, scaling path |
| 03 | [Data model](docs/03-data-model.md) | ER diagram, every table, constraints, retention |
| 04 | [API spec](docs/04-api-spec.md) | All v1 endpoints, auth, pagination, errors, rate limits |
| 05 | [Security architecture](docs/05-security-architecture.md) | Trust boundaries, STRIDE threat model, anti-scraping, headers, secrets, residual risks |
| 06 | [Founder verification](docs/06-founder-verification.md) | State machine, checks, reviewer checklist, abuse scenarios |
| 07 | [Content integrity & moderation](docs/07-content-integrity-and-moderation.md) | Hash chains, audit log, staff powers, spam rules, SLAs |
| 08 | [Email digest](docs/08-email-digest.md) | Double opt-in, curation formula, idempotent sending, deliverability |
| 09 | [Frontend & UX](docs/09-frontend-and-ux.md) | Pages, design tokens, masonry, CSP, accessibility, perf budget |
| 10 | [Infrastructure & deployment](docs/10-infrastructure-and-deployment.md) | Reference cloud architecture, CI/CD, backups/DR, costs |
| 11 | [Observability & operations](docs/11-observability-and-operations.md) | Logs, metrics, alerts, runbooks, key rotation |
| 12 | [Roadmap](docs/12-roadmap.md) | What's done, beta, launch, community |
| 13 | [Accounts & authentication](docs/13-accounts-and-authentication.md) | One account with earned founder status, login protections, the timed sign-up prompt |
| ADR | [Architecture decisions](docs/adr/) | Django, sessions not JWT, Postgres, no AI, uploads, same-origin API, hash chains |

## Stack

| Layer | Choice |
|---|---|
| Web | Next.js 15 (App Router, TypeScript, Tailwind v4), nonce-based CSP |
| API | Django 5.2 LTS + Django REST Framework, Python 3.12 |
| Jobs | Celery + Redis (image sanitisation, email, digest, integrity checks) |
| Data | PostgreSQL 16 (append-only triggers, least-privilege roles), Redis |
| Media | S3 / R2 (MinIO locally), presigned uploads, re-encoded + EXIF-stripped |
| Edge | Cloudflare (WAF, bot management, CDN, Turnstile, Access) |

## Repository layout

```
backend/            Django project
  apps/common/      security primitives (throttles, permissions, encryption, CSP, Turnstile)
  apps/audit/       hash-chained append-only audit log
  apps/accounts/    users, sessions, TOTP 2FA, lockout
  apps/verification/ founder verification workflow
  apps/stories/     stories, revisions, media pipeline, feed
  apps/engagement/  likes, boards, comments, follows, reports
  apps/moderation/  moderator API, spam rules
  apps/digest/      weekly digest
  tests/            pytest suite (security-focused)
frontend/           Next.js app
infra/              Postgres roles, MinIO bootstrap
docs/               architecture docs + ADRs
```

## Quick start (Docker)

```bash
cp .env.example .env
make up                 # postgres, redis, minio, mailpit, api, worker, beat, web
make seed               # demo founders + stories (DEBUG only)
```

| URL | What |
|---|---|
| http://localhost:3000 | The wall |
| http://localhost:8000/admin/ | Moderation console (`admin@wof.local` / `admin-demo-password`, local only) |
| http://localhost:8025 | Mailpit: verification and digest emails land here |

Demo founder logins: `maya@solarloop.energy` / `demo-password-please-change` (see
`seed_demo.py` for the rest).

## Running without Docker

```bash
# backend (SQLite + no Redis needed for tests)
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest                                   # uses wof.settings.test

# frontend
cd frontend && npm ci && npm run dev     # expects the API on http://127.0.0.1:8000
```

## Quality gates (run in CI)

```bash
make lint     # ruff (incl. bandit rules) + eslint
make test     # pytest (SQLite locally, PostgreSQL in CI) + tsc + eslint
```
CI also runs `manage.py check --deploy` against the production settings, `pip-audit`,
`npm audit` and gitleaks.

## Security

Please report vulnerabilities privately; see [SECURITY.md](SECURITY.md). The full design
is in [docs/05-security-architecture.md](docs/05-security-architecture.md).
