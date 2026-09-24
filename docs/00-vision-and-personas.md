# 00 · Vision & Personas

## The one-liner

**Wall of Founders is the modern Reader's Digest for builders**: a Pinterest-style wall of
first-person stories written by founders *we have verified*, plus a weekly email digest of
the best ones.

## Why it should exist

We are in the information era, and most founder content online has three problems:

1. **Provenance.** You rarely know whether "a founder" really founded anything.
2. **Integrity.** Posts are silently edited, ghost-written or scraped and re-posted.
3. **Signal.** Feeds reward outrage and engagement bait instead of useful lived experience.

Wall of Founders answers each one with an architectural commitment, not just a policy:

| Problem | Commitment | Mechanism |
|---|---|---|
| Provenance | Only verified founders can publish | Company-domain email proof + human review of public evidence ([06](06-founder-verification.md)) |
| Integrity | Nothing changes without a record | Immutable, hash-chained story revisions and audit log, enforced in the database ([07](07-content-integrity-and-moderation.md)) |
| Signal | Curation you can explain | Deterministic ranking plus editor picks, and no AI ([08](08-email-digest.md), [ADR-0004](adr/0004-no-ai.md)) |

## Personas

### Reader (the public), no account needed
- Browses the wall, filters by topic, reads stories and founder profiles.
- **Wants:** fast, beautiful and trustworthy reading; a weekly email with no spam.
- **With a free account:** likes, saves stories to boards (Pinterest "pins"), comments,
  follows founders, reports abuse.

### Founder (verified)
- Everything a Reader can do, plus: writes, edits and publishes stories, and carries a
  verified badge on their profile, stories and comments.
- **Wants:** a credible place to tell their story that won't be copied and mangled, and
  proof that they wrote it.
- **Must:** keep 2FA enabled and re-verify every 12 months.

### Moderator
- Works the verification queue, the report queue and held comments.
- Can hide or restore stories, hide comments and suspend users. **Cannot** edit a
  founder's words (content fields are read-only even in the admin).
- Every action needs a written reason and is written to the audit log.

### Editor
- Picks the week's stories for the digest and approves the draft issue before it is sent.

### Admin
- Manages staff roles and configuration. Also bound by 2FA and SSO, and also audited.

## Glossary

| Term | Meaning |
|---|---|
| **Wall** | The public masonry feed of published stories |
| **Story** | A founder's first-person article (Markdown source, sanitised HTML render) |
| **Revision** | An immutable snapshot of a story's text, chained by SHA-256 |
| **Content hash** | SHA-256 of a story's title, subtitle and body, shown publicly on every story |
| **Board** | A user's collection of saved stories (private by default) |
| **Digest / Issue** | The weekly curated email and its public web archive |
| **Verification request** | A founder's claim: company, work email and evidence links |
| **Audit log** | Append-only, hash-chained record of every security-relevant event |
