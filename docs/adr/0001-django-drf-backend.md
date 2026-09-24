# ADR-0001: Django + Django REST Framework for the backend

- **Status:** Accepted
- **Date:** 2026-09-24

## Context
The user asked for a Python backend. The platform is public, security is the top priority,
and it needs a moderation/editorial back-office from day one. Candidates: Django + DRF,
FastAPI + SQLAlchemy, Flask.

## Decision
**Django 5.2 LTS + DRF**, structured as a modular monolith (`apps/*` per bounded context).

## Consequences
- ✅ Secure defaults out of the box: CSRF, session auth, clickjacking and security
  middleware, ORM parameterisation, password hashing framework, `check --deploy`.
- ✅ The Django admin is a free, permissioned, audited moderation console, so there's no
  bespoke back-office for the MVP.
- ✅ Mature migration tooling (including `RunPython` for Postgres triggers), an LTS
  support window to April 2028, and a large hiring pool.
- ⚠️ Synchronous by default. This is acceptable: heavy work goes to Celery, and the read
  path is CDN-cached.
- ⚠️ Less type-driven than FastAPI + Pydantic. Mitigated with explicit serializers and tests.
