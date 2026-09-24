# 09 · Frontend & UX

## Design direction
**"A digest you'd want to read, laid out like a wall."** Pinterest's browsing model (a
dense masonry of cards you scan, open and save), with an editorial reading experience
(serif typography, generous measure, calm colour).

Differences from Pinterest, on purpose:
| Pinterest | Wall of Founders | Why |
|---|---|---|
| Image-first pins | **Typographic cards** when there is no cover; the title *is* the visual | Stories are text; founders shouldn't need stock photos |
| Infinite scroll | "Show more" button with cursor pagination | Readers keep their place; a natural throttle on scraping; accessible |
| Engagement-ranked home feed | Chronological wall + topic filters; ranking only in the digest | Transparent and explainable |
| Anyone can pin | Only verified founders publish; everyone can save | Trust |

## Pages (implemented)
| Route | Rendering | Purpose |
|---|---|---|
| `/` | SSR (+ client "show more") | The wall, with topic chips |
| `/s/[slug]` | SSR, personalised when logged in | Story page, actions, integrity record, conversation |
| `/f/[handle]` | SSR | Founder profile with company, verified-via domain, follow |
| `/digest`, `/digest/[number]` | SSR | Subscribe + archive |
| `/login`, `/signup` | Client | Auth (with TOTP step, Turnstile) |
| `/verify`, `/verify/confirm` | Client | Founder verification flow |
| `/write` | Client | Founder editor (draft → publish), cover upload |
| `/boards` | Client | Saved stories |
| `/settings/security` | Client | TOTP 2FA setup (manual-entry key; required before a founder can publish) |
| `/digest/confirm`, `/digest/unsubscribe` | Client | Token pages (token stripped from URL; unsubscribe needs a click) |

## Architecture
- **Next.js App Router**, TypeScript strict, Tailwind v4 with CSS-variable design tokens.
- **Same-origin API.** `next.config.ts` rewrites `/api/*` to Django on the private network.
  Cookies are first-party, CSRF works natively, and no CORS policy is needed ([ADR-0006](adr/0006-same-origin-api-proxy.md)).
- **Server components fetch server-side** (`lib/server-api.ts`, marked `server-only`) and
  forward only the session cookie when personalisation is needed. **Client components**
  use `lib/client-api.ts`, which adds `X-CSRFToken` and `credentials: same-origin`.
- **Per-request CSP nonce** in `middleware.ts`. The root layout reads headers, which makes
  every page dynamic so Next.js can stamp the nonce on its scripts. `strict-dynamic`
  lets Next load its chunks while blocking any injected script.
- **Untrusted HTML:** only `story.body_html`, which the server has already sanitised,
  goes into `dangerouslySetInnerHTML`. Everything else (comments, names, bios) is rendered
  as text by React.
- **Open-redirect guard:** `?next=` is accepted only if it is a same-site relative path (`lib/safe-redirect.ts`).
- **Route parameters** are validated with regexes before any API call.

## Design tokens
Defined once in `app/globals.css` (`:root` + `prefers-color-scheme: dark`):
`--bg, --surface, --ink, --muted, --line, --accent, --verified, --card-1…6`.
Typography: a system serif stack for reading (`Iowan Old Style`, Palatino, Georgia) and a
system sans for UI. No web-font downloads, so there are no third-party requests and no
layout shift.

## Masonry
CSS multi-column layout (`.wall { columns: N <min-width> }`) from 2 to 5 columns by
breakpoint, with `break-inside: avoid`. No JavaScript layout, no layout thrash, and it
works before hydration. Typographic cards get a deterministic tint and height from the
slug hash, which gives the wall a Pinterest rhythm that stays the same on every visit.

## Accessibility (WCAG 2.2 AA)
- Semantic landmarks (`header`, `nav`, `main`, `article`, `footer`); a single `h1` per page.
- The verified badge is an SVG with `role="img"` and a label.
- Toggle buttons use `aria-pressed` (like, editor topic selection); form errors use `role="alert"`.
- Focus-visible outlines; colour contrast checked for both themes; no motion-dependent UI.
- The "Show more" button instead of infinite scroll keeps keyboard and screen-reader users
  able to reach the footer.

## Performance budget
| Metric | Budget | Now (prod build) |
|---|---|---|
| First-load JS per route | < 130 kB | ~103–108 kB |
| LCP (4G, mid-range phone) | < 2.5 s | SSR HTML, no web fonts, lazy images |
| CLS | < 0.05 | image `width`/`height` + dominant-colour placeholder |
| API calls on first paint | 1–2, server-side | ✅ |

## Planned UX
- Moderation console (replacing Django admin for day-to-day work).
- QR code on the 2FA screen (rendered locally, never sent to a third-party QR service).
- Board management (rename, make public, pick a board when saving).
- Revision diff viewer.
- Search (Postgres full-text first).
- Reading progress and "continue reading" for logged-in readers.
