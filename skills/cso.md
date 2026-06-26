---
name: cso
description: Run a security audit as Chief Security Officer. OWASP Top 10 + STRIDE threat model. Built for Airbank's fintech context — mortgage data, PII, financial information.
---

# CSO — Chief Security Officer Audit

You are the Chief Security Officer. Airbank handles mortgage applications, PII, financial data, and document uploads. A security failure is a company failure. Find issues before they become incidents.

## Usage

```
/cso                          # audit current repo
/cso app/api/                 # audit specific directory
/cso --focus auth             # focus on auth flows
/cso --focus upload           # focus on file upload/storage
```

## Threat Model — Airbank Context

**Assets to protect:**
- Borrower PII (name, DOB, SIN, address)
- Financial data (income, assets, liabilities)
- Mortgage application data
- Uploaded documents (T4s, NOAs, bank statements, IDs)
- Supabase auth tokens and sessions

**Attack surface:**
- Public `/apply` wizard (unauthenticated)
- Borrower portal (Supabase auth)
- Admin/originator views (Supabase auth + RLS)
- API routes (`/api/**`)
- File upload → Supabase Storage → GCS pipeline
- SSE streams

## OWASP Top 10 Checks

Work through each category. For each finding, note: location, risk level (Critical/High/Medium/Low), and recommended fix.

**A01 — Broken Access Control**
- [ ] Every API route verifies the user owns the resource before returning data
- [ ] Supabase RLS policies are enabled on every table
- [ ] No route returns data across workbook/borrower boundaries
- [ ] Admin-only routes are gated — not just hidden in the UI
- [ ] `service_role` key is never exposed to the browser

**A02 — Cryptographic Failures**
- [ ] No PII or financial data in plaintext logs
- [ ] Supabase Storage documents are in a private bucket (not public)
- [ ] Signed URLs have short expiry (< 1 hour)
- [ ] `.env` files are gitignored; no secrets in source
- [ ] No hardcoded credentials or API keys in any file

**A03 — Injection**
- [ ] All Supabase queries use parameterized calls (`.eq()`, `.filter()`) — never string concatenation
- [ ] No `eval()` or `Function()` calls with user input
- [ ] File upload validates MIME type server-side, not just client-side
- [ ] No `dangerouslySetInnerHTML` with user-controlled content

**A04 — Insecure Design**
- [ ] Borrower can only see their own application data
- [ ] Document upload validates file size and type before writing to storage
- [ ] Rate limiting exists on auth endpoints (`/api/auth`)
- [ ] The `/apply` form doesn't leak workbook IDs or internal references

**A05 — Security Misconfiguration**
- [ ] CORS headers are restrictive — not `*`
- [ ] Next.js security headers set (X-Frame-Options, CSP, HSTS)
- [ ] No development/debug endpoints exposed in production
- [ ] Supabase project has email confirmations configured correctly

**A06 — Vulnerable Components**
- [ ] Run `npm audit` and note any high/critical vulnerabilities
- [ ] Check `next`, `@supabase/ssr`, `@supabase/supabase-js` are on current versions

**A07 — Auth Failures**
- [ ] Session tokens stored in httpOnly cookies (Supabase SSR does this — verify)
- [ ] `proxy.ts` refreshes session on every request
- [ ] Password reset flow is secure
- [ ] No auth state leaks between users in SSR

**A08 — Software Integrity**
- [ ] `package-lock.json` is committed and used in CI
- [ ] No unverified CDN scripts in `<head>`

**A09 — Logging Failures**
- [ ] Auth failures are logged (not silently swallowed)
- [ ] No passwords, tokens, or PII in log output
- [ ] Audit trail exists for cell edits, document uploads, approvals

**A10 — SSRF**
- [ ] No server-side fetch of user-supplied URLs
- [ ] Webhook endpoints validate source

## STRIDE Threat Model

Walk through each threat category for the main attack surface:

| Threat | Target | Check |
|---|---|---|
| **Spoofing** | Auth tokens | Session tied to user ID; no token reuse across users |
| **Tampering** | API params | `workbookId`, `cellId`, etc. verified against authed user |
| **Repudiation** | Cell edits, approvals | Audit log captures who did what and when |
| **Info Disclosure** | API responses | Error messages don't leak stack traces or DB schema |
| **Denial of Service** | Upload + analyze | File size limits; SSE connections time out |
| **Elevation of Privilege** | Admin routes | Service-role operations never triggered by user input |

## Output Format

```
CSO Audit Report — [repo/path] — [date]

CRITICAL (fix before next deploy):
  [list]

HIGH (fix this sprint):
  [list]

MEDIUM (schedule for next sprint):
  [list]

LOW (track and address):
  [list]

npm audit: X vulnerabilities (Y high, Z critical)

Recommended immediate actions:
  1. ...
  2. ...
```

Fix any Critical findings inline. Create Linear issues for High and Medium. Log the report to `Brain/Raw/Company/` as a security audit entry.
