# 01 · Product Requirements

Status legend: ✅ implemented in this repo · 🟡 partially implemented · ⏳ planned (see [12-roadmap](12-roadmap.md))

## Functional requirements

### Public reading (no account)
| ID | Requirement | Status |
|---|---|---|
| R-1 | Masonry wall of published stories, newest first, cursor pagination | ✅ |
| R-2 | Filter the wall by topic tag | ✅ |
| R-3 | Story page: title, subtitle, author, verified badge, company and role, reading time | ✅ |
| R-4 | Founder profile page with their stories | ✅ |
| R-5 | Public edit history per story (revision numbers and hashes) | ✅ |
| R-6 | Public digest archive | ✅ |
| R-7 | Server-rendered pages with Open Graph metadata for sharing and SEO | ✅ |
| R-8 | Search (title, subtitle, topic) | ✅ substring · full-text ⏳ |
| R-9 | Timed sign-up prompt: soft after 45 s, then non-dismissible; exempt for auth pages and crawlers | ✅ ([13](13-accounts-and-authentication.md)) |

### Reader account
| ID | Requirement | Status |
|---|---|---|
| A-1 | Sign up with email, password and handle; log in and out | ✅ |
| A-2 | Optional TOTP 2FA (required for founders and staff) | ✅ (manual-key setup; QR ⏳) |
| A-3 | Like and unlike stories (idempotent) | ✅ |
| A-4 | Save stories to boards; boards private by default | ✅ |
| A-5 | Comment (plain text, rate-limited, spam-held) | ✅ |
| A-6 | Follow founders | ✅ |
| A-7 | Report a story, comment or user | ✅ story UI · API for all types |
| A-8 | Subscribe to the digest with double opt-in; one-click unsubscribe | ✅ |
| A-9 | Export or delete my data (GDPR/CCPA) | ✅ Settings › Your data |
| A-10 | Reset a forgotten password; change password (signs out other devices) | ✅ |

### Founder
| ID | Requirement | Status |
|---|---|---|
| F-1 | Submit a verification request (company, domain email, LinkedIn/Crunchbase) | ✅ |
| F-2 | Confirm the work email through a single-use link that expires in 24h | ✅ |
| F-3 | See the status of my request and the moderator's note | ✅ |
| F-4 | Write a draft in Markdown, add a cover image and up to 5 topics | ✅ |
| F-5 | Publish a draft; edit a published story (new public revision) | ✅ |
| F-6 | Remove my own story (soft delete; revisions retained) | ✅ |
| F-7 | 2FA required before publishing (configurable, on by default) | ✅ |
| F-8 | Re-verify every 12 months | ✅ (expiry job; re-verify reminder email ⏳) |

### Staff
| ID | Requirement | Status |
|---|---|---|
| S-1 | Verification review queue: approve, reject, or request more info with a reason | ✅ API + admin |
| S-2 | Report queue, held-comment queue | ✅ |
| S-3 | Hide, restore or remove a story; hide or approve a comment; suspend a user; reason required | ✅ |
| S-4 | Digest: automatic weekly draft, editor adjusts, approves and schedules | ✅ admin |
| S-5 | Read-only, tamper-evident audit log viewer and chain verification | ✅ |
| S-6 | Dedicated moderation web UI (beyond Django admin) | ⏳ |

## Non-functional requirements

| Area | Target |
|---|---|
| **Security** | OWASP ASVS Level 2 as baseline; see [05](05-security-architecture.md) |
| **Integrity** | 100% of content changes produce an immutable revision and an audit entry |
| **Performance** | Wall first byte < 300 ms at p95 (CDN-cached anonymous reads); LCP < 2.5 s on 4G |
| **Availability** | 99.9% monthly for reading; writes may degrade to read-only during incidents |
| **Scalability** | 1M monthly readers and 10k founders on the reference architecture ([10](10-infrastructure-and-deployment.md)) |
| **Privacy** | Collect as little data as possible: no third-party trackers, no ad pixels, evidence purged after review |
| **Accessibility** | WCAG 2.2 AA |
| **Email** | Gmail/Yahoo bulk-sender compliance: SPF, DKIM, DMARC, RFC 8058 one-click unsubscribe, complaint rate < 0.1% |

## Explicit non-goals
- **No AI or ML anywhere**: no generated content, recommendations, moderation or
  summarisation. Everything is deterministic and explainable ([ADR-0004](adr/0004-no-ai.md)).
- No ads, and no selling of reader data.
- No direct messages at launch (a major abuse vector; revisit after v1).
- No bulk export or public firehose API. Reading is for humans ([05 §Anti-scraping](05-security-architecture.md#anti-scraping--anti-download)).
