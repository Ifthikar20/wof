# ADR-0002: Server-side sessions in HttpOnly cookies, not JWTs

- **Status:** Accepted
- **Date:** 2026-09-24

## Context
The only API client is our own web app on the same origin. We need instant revocation
(suspensions, stolen devices, staff offboarding) and XSS-resistant credential storage.

## Decision
Use Django sessions stored in Redis, with a `__Host-` prefixed cookie that is HttpOnly,
Secure and SameSite=Lax, plus Django CSRF tokens on unsafe methods. No JWTs and no tokens
in `localStorage`.

## Consequences
- ✅ JavaScript can't read the credential, so XSS can't steal it.
- ✅ Instant server-side revocation (delete the session; suspended users are logged out on their next request).
- ✅ No token-refresh logic and no signing-key management on the client.
- ⚠️ Requires CSRF handling (built in) and same-origin serving (see ADR-0006).
- ⚠️ If a native mobile app arrives, add an OAuth2/PKCE flow for that client specifically.
