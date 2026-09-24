# ADR-0006: Serve the API on the same origin via the web tier

- **Status:** Accepted
- **Date:** 2026-09-24

## Context
Cross-origin APIs need CORS with credentials. That is easy to misconfigure, and it pushes
cookies to `SameSite=None`, which weakens CSRF protection.

## Decision
The browser only talks to `https://walloffounders.com`. Next.js rewrites `/api/*` to
Django on the private network. Django is never directly exposed; the admin lives on a
separate hostname behind Cloudflare Access.

## Consequences
- ✅ First-party cookies with `SameSite=Lax`; no CORS configuration at all.
- ✅ One CSP origin (`'self'`) for API calls.
- ⚠️ The web tier is in the API request path (small latency cost). The CDN caches
  anonymous API GETs to offset it.
- ⚠️ Client IP must come from the edge header (`CF-Connecting-IP`), configured via
  `TRUSTED_PROXY_IP_HEADER`. The app never trusts `X-Forwarded-For` from clients.
