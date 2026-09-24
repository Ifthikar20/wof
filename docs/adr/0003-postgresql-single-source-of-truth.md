# ADR-0003: PostgreSQL as the single source of truth

- **Status:** Accepted
- **Date:** 2026-09-24

## Context
We need strong consistency for counters, constraints (one open verification, unique
likes), transactional audit entries and database-enforced immutability.

## Decision
PostgreSQL 16 for all durable state. Redis only for disposable state (sessions, throttles,
the broker). No second datastore until search needs one.

## Consequences
- ✅ Partial unique indexes, check constraints, advisory locks (audit chain), triggers
  (append-only), row-level locking for state machines.
- ✅ One backup and restore story; PITR covers everything important.
- ⚠️ Full-text search starts in Postgres (tsvector + GIN); move to OpenSearch via CDC only if needed.
