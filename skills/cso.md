---
name: cso
description: Run a security audit as Chief Security Officer. OWASP Top 10 + STRIDE threat model. Built for a web/fintech context: user PII, uploaded documents, and financial or otherwise sensitive data.
---

# CSO — Chief Security Officer Audit

You are the Chief Security Officer. Your app handles user PII, uploaded documents, and financial or otherwise sensitive data. A security failure is a company failure. Find issues before they become incidents.

## Usage

```
/cso                          # audit current repo
/cso app/api/                 # audit specific directory
/cso --focus auth             # focus on auth flows
/cso --focus upload           # focus on file upload/storage
```

## Threat Model — Context

**Assets to protect:**
- User PII (names, emails, contact details)
- Financial or otherwise sensitive user data
- Uploaded documents and files
- Supabase auth tokens and sessions
- Third-party integration credentials

**Attack surface:**
- Authenticated app (Supabase auth)
- Multi-tenant data isolation
- API routes (`/api/**`)
- File upload to storage pipeline
- Third-party data integrations
- SSE streams

## OWASP Top 10 Checks

Work through each category. For each finding, note: location, risk level (Critical/High/Medium/Low), and recommended fix.

**A01 — Broken Access Control**
- [ ] Every API route verifies the user owns the resource before returning data
- [ ] Tenant/authorization checks are enforced on every data access path
- [ ] No route returns data across tenant boundaries
- [ ] Admin-only routes are gated — not just hidden in the UI
- [ ] `service_role` key is never exposed to the browser

**A02 — Cryptographic Failures**
- [ ] No PII or financial data in plaintext logs
- [ ] Uploaded documents are stored in a private bucket (not public)
- [ ] Signed URLs have short expiry (< 1 hour)
- [ ] `.env` files are gitignored; no secrets in source
- [ ] No hardcoded credentials or API keys in any file

**A03 — Injection**
- [ ] All database queries use parameterized calls, never string concatenation
- [ ] No `eval()` or `Function()` calls with user input
- [ ] File upload validates MIME type server-side, not just client-side
- [ ] No `dangerouslySetInnerHTML` with user-controlled content

**A04 — Insecure Design**
- [ ] Each user can only see their own tenant's data
- [ ] Document upload validates file size and type before writing to storage
- [ ] Rate limiting exists on authentication endpoints
- [ ] Unauthenticated endpoints don't leak internal IDs or references

**A05 — Security Misconfiguration**
- [ ] CORS headers are restrictive — not `*`
- [ ] Next.js security headers set (X-Frame-Options, CSP, HSTS)
- [ ] No development/debug endpoints exposed in production
- [ ] Supabase auth has email/session settings configured correctly

**A06 — Vulnerable Components**
- [ ] Run `npm audit` and note any high/critical vulnerabilities
- [ ] Check `next`, `@supabase/ssr`, and other core dependencies are on current versions

**A07 — Auth Failures**
- [ ] Session tokens stored in httpOnly cookies (Supabase does this — verify)
- [ ] `proxy.ts` refreshes session on every request
- [ ] Password reset flow is secure
- [ ] No auth state leaks between users in SSR

**A08 — Software Integrity**
- [ ] `package-lock.json` is committed and used in CI
- [ ] No unverified CDN scripts in `<head>`

**A09 — Logging Failures**
- [ ] Auth failures are logged (not silently swallowed)
- [ ] No passwords, tokens, or PII in log output
- [ ] Audit trail exists for data edits, document uploads, approvals

**A10 — SSRF**
- [ ] No server-side fetch of user-supplied URLs
- [ ] Webhook endpoints validate source

## STRIDE Threat Model

Walk through each threat category for the main attack surface:

| Threat | Target | Check |
|---|---|---|
| **Spoofing** | Auth tokens | Session tied to user ID; no token reuse across users |
| **Tampering** | API params | `resourceId`, `recordId`, etc. verified against authed user |
| **Repudiation** | Data edits, approvals | Audit log captures who did what and when |
| **Info Disclosure** | API responses | Error messages don't leak stack traces or DB schema |
| **Denial of Service** | Upload + processing | File size limits; SSE connections time out |
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
