# ADR-0007: Hash-chained, database-enforced append-only history

- **Status:** Accepted
- **Date:** 2026-09-24

## Context
"No one can falsely manipulate things" is a core requirement. Ordinary `updated_at`
columns and app-level logging can be rewritten by anyone with DB access, including a
compromised app.

## Decision
- Every story save creates an immutable `StoryRevision` in a per-story SHA-256 chain; the
  latest `content_hash` is shown publicly.
- Every security- or trust-relevant action appends to a global hash-chained `AuditLog`,
  serialised by a Postgres advisory lock.
- Immutability is enforced in three places: model `save()`/`delete()` guards, Postgres
  `BEFORE UPDATE OR DELETE` triggers, and role grants (INSERT/SELECT only).
- A nightly job verifies both chains and exports the audit head hash to a WORM
  (object-lock) bucket in a separate account.

We chose this over a blockchain or an external ledger: the same tamper-evidence at a
fraction of the complexity, and anchoring gives an external witness.

## Consequences
- ✅ Tampering is detectable by us and provable to others.
- ✅ Staff powers are visible and accountable.
- ⚠️ History can't be "fixed" in place; corrections are new entries (by design).
- ⚠️ Hashed rows can't hold erasable PII. Audit rows identify actors only by user UUID
  (pseudonymous), so GDPR erasure deletes or anonymises the *user row* and the chain stays
  valid. IP and user agent are kept under legitimate interest for the security-log
  retention period. See [11](../11-observability-and-operations.md).
