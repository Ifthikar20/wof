# 09 · Frontend & UX

## Design direction
**"A digest you'd want to read, laid out like a wall."** Pinterest's browsing model (a
dense masonry of cards you scan, open and save), with an editorial reading experience
(serif typography, generous measure, calm colour).

What we borrow from Pinterest:
- **Pin-width masonry**: 236px columns, as many as fit (5 at 1440px), 2 on phones.
- **Cards that are almost all visual**, with rounded 16px corners and minimal text underneath (author, verified badge, company).
- **Hover overlay** on desktop: the card darkens, shows its topic, and offers a red **Save** pill that saves in place without leaving the wall.
- **Header**: Home/Digest pills, a big grey pill search bar, an avatar menu.
- **Topic chips**: grey pills, black when selected, sticky under the header.
- **A promoted "pin"** for the digest inside the grid (dismissible).

What we do differently, on purpose:
| Pinterest | Wall of Founders | Why |
|---|---|---|
| Image-first pins | **Typographic posters** (gradient + serif title) when there is no cover | Stories are text; founders shouldn't need stock photos |
| Infinite scroll | "Show more" button with cursor pagination | Readers keep their place; a natural throttle on scraping; accessible |
| Engagement-ranked home feed | Chronological wall + topic filters + search; ranking only in the digest | Transparent and explainable |
| Anyone can pin | Only verified founders publish; everyone can save | Trust |

## Visual language
- **Type:** *Instrument Serif* for display titles (one weight, set large and tight) and
  *Inter* (variable) for interface text. Both are self-hosted from npm (`@fontsource`),
  so there are no third-party font requests and the CSP stays `'self'`.
- **Colour:** calm paper tones, **ink-black** primary actions, one warm accent (`--accent`,
  terracotta), and Pinterest red kept only for **Save**.
- **Smooth background:** `.ambient` is a fixed layer of three large, heavily blurred colour
  fields drifting over 40–50 s, plus faint film grain. It is static when the user prefers
  reduced motion.
- **Glass:** the header and sticky topic bar are frosted (`.glass`, backdrop blur).
- **Full-frame imagery:** the home page opens with a full-bleed **hero** showing the
  editor's featured story (`/stories?featured=1`) over its cover photo, or over our own
  artwork. The digest page and the split-screen log-in and sign-up pages use full-frame
  artwork too.
- **Artwork:** `public/art/*.webp` are original illustrations (a skyline of rounded tiles
  at dusk, night and morning, with film grain), rendered from code for this project. No
  stock or AI imagery. Replace them with real photography whenever it's available.
- **Logo:** a tiny masonry wall: three columns of staggered rounded tiles, with one tile
  in the accent colour (the pinned story). `components/Logo.tsx`, `app/icon.svg`.
- **CSS layering:** component classes (`.btn`, `.chip`, `.input`, `.wall`…) live in
  `@layer components`, so Tailwind utilities such as `hidden sm:inline-flex` can override them.

## Pages (implemented)
| Route | Rendering | Purpose |
|---|---|---|
| `/` | SSR (+ client "show more") | The wall, with topic chips |
| `/s/[slug]` | SSR, personalised when logged in | Story page, actions, integrity record, conversation |
| `/f/[handle]` | SSR | Founder profile with company, verified-via domain, follow |
| `/digest`, `/digest/[number]` | SSR | Subscribe + archive |
| `/login`, `/signup` | Client | Auth (with TOTP step, Turnstile); `/signup?intent=founder` is the founder path |
| `/verify`, `/verify/confirm` | Client | Founder verification flow |
| `/write` | Client | Founder editor (draft → publish), cover upload |
| `/boards` | Client | Saved stories |
| `/settings/security` | Client | TOTP 2FA setup (manual-entry key; required before a founder can publish) |
| `/digest/confirm`, `/digest/unsubscribe` | Client | Token pages (token stripped from URL; unsubscribe needs a click) |

## Auth prompt
Logged-out visitors can read everything. After 45 s they get a dismissible prompt, and
90 s after dismissing it a firm one (no close button; page blurred, `inert`, scroll-locked).
It offers **Join as a reader**, **I'm a founder** (same account, then straight to `/verify`)
and **Log in**. It never appears on auth, verification, settings or email-token pages, to
logged-in users, or to crawlers. The visit clock lives in `sessionStorage`, so it survives
navigation. It is a nudge, not a security control. Full behaviour:
[13-accounts-and-authentication.md](13-accounts-and-authentication.md).

`SessionProvider` fetches `/auth/me` once per page load and shares it with the header and the prompt.

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
CSS multi-column layout (`.wall { column-width: 236px }`, so the browser fits as many
Pinterest-width columns as it can; phones reset to exactly 2), with `break-inside: avoid`. No JavaScript layout, no layout thrash, and it
works before hydration. Typographic cards get a deterministic tint and height from the
slug hash, which gives the wall a Pinterest rhythm that stays the same on every visit. The hover overlay is CSS-only (`.pin:hover .pin-overlay`) and is hidden on touch devices (`@media (hover: none)`).

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
