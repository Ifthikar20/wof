# ADR-0005: Presigned direct uploads + mandatory server-side re-encoding

- **Status:** Accepted
- **Date:** 2026-09-24

## Context
User images are the riskiest input: polyglots, decompression bombs, EXIF GPS leaks,
malformed files that exploit decoders, and they're large.

## Decision
1. The browser uploads **directly to a private bucket** using a presigned POST pinned to
   one key, one content type, at most 10 MB and 5 minutes. The API never buffers file bytes.
2. A **worker** (no inbound network) checks magic bytes, runs `verify()`, applies a pixel
   cap, and **fully re-encodes** to WebP without metadata. It produces a watermarked
   ≤ 1200 px display variant and a 480 px thumbnail in a separate public bucket served only
   through the CDN.
3. Only `ready` media owned by the author can be attached to a story.

## Consequences
- ✅ Decoder exploits are contained to an isolated worker; published bytes are always freshly generated.
- ✅ No location or device metadata leaks; originals are never public, which blocks full-resolution scraping.
- ⚠️ Upload is asynchronous (the client polls status). Accepted.
- ⚠️ Keep Pillow patched (Dependabot + pip-audit in CI).
