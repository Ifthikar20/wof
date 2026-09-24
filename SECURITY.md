# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue. Email **security@walloffounders.com** (placeholder,
to be replaced before launch) with:

- a description of the issue and its impact,
- steps to reproduce or a proof of concept,
- affected URLs, endpoints or files.

We will acknowledge within **2 business days**, give an initial assessment within
**5 business days**, and keep you updated until it's fixed. We won't pursue legal action
for good-faith research that follows this policy.

## In scope
- `walloffounders.com` and its subdomains; the code in this repository.
- Especially: founder impersonation or verification bypass, content tampering that evades
  the revision or audit chains, account takeover, access to other users' private data
  (emails, drafts, private boards, verification evidence), stored XSS, CSRF, IDOR, SSRF,
  and upload-pipeline bypasses.

## Out of scope
- Volumetric DoS; social engineering of staff; physical attacks.
- Reports from automated scanners without a demonstrated impact.
- Missing headers on endpoints that return no HTML, unless you can show impact.
- Scraping public content at human-scale rates (see the anti-scraping section of the
  security architecture for what we defend against).

## Rules of engagement
- Only test against accounts you own; don't access or modify other users' data.
- Stop and report as soon as you reach sensitive data.
- Don't publish anything before we have released a fix (coordinated disclosure, 90 days by default).
