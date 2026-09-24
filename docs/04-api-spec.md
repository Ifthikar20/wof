# 04 · API Specification (v1)

Base path: **`/api/v1`**, served on the same origin as the website (Next.js proxies
`/api/*` to Django). JSON only. There is no public third-party API by design.

## Conventions

- **Auth:** Django session cookie (`wof_session`; `__Host-wof_session` in production),
  HttpOnly, Secure, SameSite=Lax. Obtain a CSRF cookie with `GET /auth/csrf`, then send
  `X-CSRFToken: <wof_csrftoken>` on every unsafe method.
- **Pagination:** opaque cursor. Responses look like `{"next": url|null, "previous": url|null, "results": [...]}`.
  There is no `count` and no `page_size` parameter, which keeps enumeration expensive.
- **Errors:** one envelope for everything:
  ```json
  {"error": {"code": "invalid", "message": "Invalid request.", "fields": {"email": ["…"]}}}
  ```
- **Status codes:** 200/201/202/204, 400 validation, 401 bad credentials, 403 not
  permitted, 404 not found *or not visible to you* (drafts are indistinguishable from
  missing), 405, 429 throttled.
- **Caching:** anonymous `GET`s return `Cache-Control: public, max-age=30, s-maxage=60`.
  Authenticated responses are `private, no-store`.
- **Bot check:** endpoints marked 🤖 require `turnstile_token` in the body in production.

## Auth: `/auth`
| Method | Path | Who | Throttle | Notes |
|---|---|---|---|---|
| GET | `/auth/csrf` | any | burst | sets the CSRF cookie |
| POST | `/auth/signup` 🤖 | any | `signup` 5/h | `{email, password, handle, display_name?}` → 201 + session |
| POST | `/auth/login` | any | `auth` 10/min | `{email, password, otp?}` → 200 me; 401 `invalid_credentials` / `otp_required`; 429 `locked` |
| POST | `/auth/logout` | user | | 204 |
| GET | `/auth/me` | any | | `null` if anonymous |
| PATCH | `/auth/me` | user | `write` | `{display_name?, bio?}` |
| POST | `/auth/2fa/setup` | user | `auth` | → `{otpauth_uri}` (not active until confirmed) |
| POST | `/auth/2fa/confirm` | user | `auth` | `{code}` → enables TOTP |

## Founder verification: `/verification`
| Method | Path | Who | Notes |
|---|---|---|---|
| GET | `/verification/` | user | my latest request or `null` |
| POST | `/verification/` | user | `{company_name, company_domain, work_email, role_title, linkedin_url?, crunchbase_url?, notes?}` → 201; supersedes any open request; emails a token |
| POST | `/verification/confirm-email` | user (same one) | `{token}` → `under_review` |

## Stories
| Method | Path | Who | Notes |
|---|---|---|---|
| GET | `/stories?tag=&author=&cursor=` | any | wall feed (published, author not suspended) |
| POST | `/stories` | verified founder + 2FA | `{title, dek?, body_markdown, tags?[≤5], cover_id?}` → draft |
| GET | `/stories/{slug}` | any / author / moderator | includes `body_html`, `content_hash`, `revision_number`, `viewer`; `body_markdown` only for the author |
| PATCH | `/stories/{slug}` | author | new revision if the content changed; locked when hidden or removed |
| DELETE | `/stories/{slug}` | author | soft remove |
| POST | `/stories/{slug}/publish` | author | draft → published |
| GET | `/stories/{slug}/revisions` | any | `[{number, content_hash, chain_hash, created_at}]` |
| GET | `/me/stories` | user | my stories, drafts included |
| GET | `/founders/{handle}` | any | profile + founder block + follower count |
| GET | `/tags` | any | |

## Media
| Method | Path | Who | Notes |
|---|---|---|---|
| POST | `/media/uploads` | user | `{content_type}` → `{media_id, upload: {url, fields}}` (presigned POST, 5 min, ≤ 10 MB) |
| POST | `/media/{id}/complete` | owner | 202; enqueues sanitisation |
| GET | `/media/{id}` | owner | status: `pending`/`processing`/`ready`/`rejected` |

## Engagement
| Method | Path | Who | Notes |
|---|---|---|---|
| POST/DELETE | `/stories/{slug}/like` | user | idempotent |
| GET | `/stories/{slug}/comments` | any | visible comments only |
| POST | `/stories/{slug}/comments` 🤖 | user | `{body}`; response `status` is `visible` or `pending` (held by spam rules) |
| GET/POST | `/boards` | user | my boards / create `{name, description?, is_private?}` |
| GET/PATCH/DELETE | `/boards/{id}` | owner (GET: anyone if public) | detail includes up to 100 stories |
| POST | `/boards/{id}/saves` | owner | `{story: slug}` |
| DELETE | `/boards/{id}/saves/{slug}` | owner | |
| POST/DELETE | `/founders/{handle}/follow` | user | |
| POST | `/reports` 🤖 | user | `{target_type, target_id, reason, details?}`; duplicates → 202 |

## Moderation: `/moderation` (moderator or admin, 2FA required)
| Method | Path | Notes |
|---|---|---|
| GET | `/moderation/verifications?status=under_review` | queue including decrypted notes |
| POST | `/moderation/verifications/{id}/decision` | `{decision: approve\|reject\|needs_info, reason}`; you can't review yourself |
| GET | `/moderation/reports` | open reports |
| GET | `/moderation/comments/held` | spam-held comments |
| POST | `/moderation/actions` | `{action, target_id, reason (required), report_id?}`; actions: `hide_story`, `restore_story`, `remove_story`, `hide_comment`, `approve_comment`, `suspend_user`, `unsuspend_user`, `dismiss_report` |

## Digest: `/digest`
| Method | Path | Who | Notes |
|---|---|---|---|
| POST | `/digest/subscribe` 🤖 | any | `{email}` → always 202 with the same body (no enumeration); 10-minute resend cooldown |
| POST | `/digest/confirm` | any | `{token}` (signed, 48h) |
| POST | `/digest/unsubscribe?token=` | any | RFC 8058 one-click target; **POST only**, so link scanners can't unsubscribe people |
| GET | `/digest/issues` | any | archive (last 52 sent) |
| GET | `/digest/issues/{number}` | any | |

## Rate limits (defaults, per user or else per client IP)

| Scope | Limit | Applies to |
|---|---|---|
| burst | 60/min | every endpoint |
| sustained | 2000/day | every endpoint |
| feed | 120/min | feed, story detail, comments list, founder pages |
| auth | 10/min | login, 2FA |
| signup | 5/hour | signup |
| verification | 5/hour | verification submit and confirm |
| write | 60/hour | story create/edit, likes, saves, follows, profile |
| comment | 20/hour | comment create |
| report | 20/hour | reports |
| subscribe | 5/hour | subscribe, confirm |
| upload | 30/hour | media upload and complete |

These sit **behind** Cloudflare's edge rate limits and bot management, which absorb
volumetric abuse before it reaches the origin. The client IP comes only from the trusted
edge header (`CF-Connecting-IP`), never from a client-controlled `X-Forwarded-For`.

## Versioning
Breaking changes ship under `/api/v2` alongside v1 for at least 90 days. The only client
is our own web app, so in practice we deprecate by deploying the web app first.
