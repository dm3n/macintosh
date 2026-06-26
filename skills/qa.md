---
name: qa
description: Run a live browser QA session against a URL or local port. Opens a real browser, navigates through key flows, finds and reports bugs. Use before shipping any feature.
---

# QA — Live Browser Testing

Open a real browser, walk through the app like a user, find what CI doesn't catch.

## Usage

```
/qa https://staging.url.com
/qa http://localhost:3000
/qa http://localhost:3004/apply   # specific path
```

## What This Does

You are the QA lead. Your job is to find bugs that pass CI but break in production. You navigate the app like a real user, not a test suite.

## Process

**1. Identify key flows**

Before opening the browser, list the flows you will test based on what changed. For Airbank projects:

- Mortgage Platform: borrower `/apply` wizard (all 8 steps), portal login, document upload, data room viewer
- QoE Platform: workbook creation, document upload, analysis SSE stream, cell editing, export
- ROGI: all 8 wizard steps, submission, confirmation

If given a specific path, focus on that feature and its dependencies.

**2. Open the browser and navigate**

Use the browser tool to open the URL. Navigate through each flow step by step. At every screen:

- Check for visual regressions (layout breaks, missing elements, overflow)
- Check for console errors (open DevTools if available)
- Fill out forms with realistic test data — not empty strings, not "test"
- Click every interactive element in the flow
- Test edge cases: empty states, error states, loading states

**3. Document what you find**

For each bug found, record:
- **Where:** URL + specific element
- **What:** What happened vs. what should happen
- **Severity:** Critical (blocks flow) / Major (degrades UX) / Minor (cosmetic)
- **Reproduction:** Exact steps

**4. Fix or file**

- Fix Critical and Major bugs inline if the cause is clear from inspection
- File Minor bugs as Linear issues if they require investigation
- Re-test after every fix before continuing

**5. Report**

After all flows are tested, output a summary:

```
QA Report — [URL] — [date]

Flows tested: X
Bugs found: Y (Z critical, W major, V minor)
Fixed inline: N
Filed to Linear: M

[bug list with severity]

Status: PASS / FAIL / PASS WITH NOTES
```

## Stack-Specific Checks

Always verify these for Airbank projects:

- **Auth:** Supabase session cookie present; redirect to login on 401
- **SSE streams:** `/api/workbooks/[id]/analyze` — progress events firing, no hung connections
- **File upload:** drag-and-drop + click-to-browse both work; progress indicator shows
- **shadcn/ui:** no raw HTML form elements — every input, button, select must be a shadcn component
- **Mobile:** resize to 375px width and verify nothing breaks
- **Next.js:** no hydration errors in console; no `proxy.ts` vs `middleware.ts` conflicts

## Pass Criteria

A flow PASSES when:
- All steps complete without error
- No console errors (warnings are ok)
- No visual breaks at 1440px and 375px
- All shadcn/ui components render correctly
- Loading and error states are handled

A flow FAILS when:
- Any step throws an unhandled error
- A form cannot be submitted
- A critical UI element is missing or broken
