# 11 · Observability & Operations

## Logging
- **Structured JSON** to stdout (`LOGGING` in `settings/base.py`), shipped to the log
  platform (Datadog, Grafana Loki or CloudWatch).
- **Never logged:** passwords, tokens, session IDs, cookies, request bodies, TOTP codes,
  verification notes. Emails are only logged as a salted hash.
- Correlation: Cloudflare `CF-Ray` is propagated as `request_id` (⏳ middleware).
- Retention: 30 days hot, 1 year archived. **Security-relevant events live in the audit
  log, not in app logs.**

## Metrics (RED + business)
| Metric | Source | Alert |
|---|---|---|
| Request rate, error rate, p95 latency per route | Edge + app (Prometheus / OTel ⏳) | 5xx > 1% for 5 min; p95 > 800 ms for 10 min |
| 429 rate by scope | DRF throttle hits | Sudden spike → possible scrape or attack |
| `auth.login_failed` per minute | Audit log | > 50/min globally or > 20/min per IP → credential stuffing |
| Verification queue age | DB | Oldest `under_review` > 3 business days |
| Report queue age by reason | DB | `false_claim` or `harassment` older than 4 h |
| Media processing failures | Celery | Rejection rate > 20% |
| Celery queue depth and task latency | Broker | Depth > 1000 or email latency > 10 min |
| Digest send progress, bounce and complaint rates | Provider webhooks ⏳ | Complaints > 0.08% |
| **Audit chain status** | Nightly `verify_chain_task` | **Any break → page immediately (SEV-1)** |

## Scrape and abuse detection (⏳)
Daily job over edge logs:
- IPs or ASNs whose request count sits far above the p99 of human sessions;
- clients walking cursor chains deeper than N pages without HTML page views;
- many 404s on `/stories/{slug}` (slug guessing);
- the same user-agent across many IPs.
Response: bot-management rule → challenge → block. Log to the incident tracker.

## On-call & incident severity
| SEV | Examples | Response |
|---|---|---|
| 1 | Audit chain broken; data breach suspected; site down | Page immediately, 15-minute acknowledgement, incident channel, status page |
| 2 | Login failing; digest double-sending; verification emails not sent | Page during business hours, 1-hour acknowledgement |
| 3 | Elevated 429s; slow queues | Ticket |

## Runbooks

### RB-1: Audit chain broken
1. Freeze: switch the app to read-only mode (feature flag ⏳) and revoke `wof_app` write grants if needed.
2. `manage.py verify_audit_chain` → the first bad entry ID.
3. Compare the head hash with the last anchored value in the object-lock bucket to bound when it happened.
4. Pull Postgres logs and IAM/DB audit logs for that window: who had superuser or owner access?
5. Restore affected rows from PITR into a forensic copy; diff them.
6. Rotate all DB credentials and field-encryption keys; open a post-mortem.

### RB-2: Credential-stuffing wave
1. Confirm via the `auth.login_failed` spike and the distribution of source IPs and ASNs.
2. Cloudflare: raise bot-fight mode; add a managed challenge on `/api/v1/auth/login`.
3. Temporarily tighten the `auth` throttle via env and redeploy.
4. Force a password reset for accounts with successful logins from flagged IPs; email the users.

### RB-3: Fake founder discovered
1. Revoke the founder profile (admin action, audited); hide their stories with reason `false_claim`.
2. Search for related requests: same domain, similar names, same IP ranges.
3. Review the approving moderator's other decisions (second-review sample).
4. Post a public correction if the story was in a digest.

### RB-4: Digest problem mid-send
1. Leave the issue in `sending`. Don't reset it: the idempotent delivery table makes a restart safe.
2. If the content is wrong, stop the email workers, fix the issue in the admin and restart.
   Subscribers who were already claimed won't get it twice.

### RB-5: Key rotation
- `FIELD_ENCRYPTION_KEYS`: prepend a new key → deploy → run the re-encrypt management
  command (⏳) → remove the old key → deploy.
- `DJANGO_SECRET_KEY`: set the new key and move the old one to `SECRET_KEY_FALLBACKS` for
  48h (keeps signed digest links and sessions working), then remove it.

## Compliance & privacy operations
- Data-subject requests: self-serve export and deletion in Settings › Your data; anything else handled within 30 days.
- Account deletion: anonymise the user row; published stories are unpublished unless
  retained for legal reasons; audit entries reference the user only by UUID (pseudonymous), so history stays intact while the person becomes unidentifiable.
- Maintain a records-of-processing register and a sub-processor list (Cloudflare, AWS,
  email provider).
