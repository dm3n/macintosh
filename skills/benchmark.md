---
name: benchmark
description: Run performance benchmarks on Airbank apps. Lighthouse scores, Core Web Vitals, API response times, bundle size. Compare before/after for any optimization work.
---

# Benchmark — Performance Measurement

Measure before you optimize. Know your numbers before and after any performance-related change.

## Usage

```
/benchmark http://localhost:3000          # full Lighthouse + vitals
/benchmark http://localhost:3004/apply   # specific page
/benchmark --api /api/workbooks          # API response time only
/benchmark --bundle                      # Next.js bundle analysis
```

## What Gets Measured

**Lighthouse (via browser)**
- Performance score (target: ≥ 90)
- Accessibility score (target: ≥ 95)
- Best Practices score (target: ≥ 90)
- SEO score (target: ≥ 90)

**Core Web Vitals**
- LCP (Largest Contentful Paint) — target: < 2.5s
- INP (Interaction to Next Paint) — target: < 200ms
- CLS (Cumulative Layout Shift) — target: < 0.1

**API Response Times**

For key Airbank API routes, measure median and p95:
- `GET /api/workbooks` — list workbooks
- `GET /api/workbooks/[id]/cells` — fetch all cells
- `GET /api/workbooks/[id]/analyze` — SSE stream (time to first event)
- `POST /api/workbooks/[id]/documents` — document upload

**Bundle Size**

Run `next build` and check:
- First load JS (target: < 100kb per route)
- Largest chunks
- Any unexpected large dependencies

## Process

1. Run baseline measurements before any changes
2. Make your optimization changes
3. Run measurements again
4. Report the delta

For CI/before-after comparisons, always capture:
```
[metric]: [before] → [after] ([delta])
```

## Output Format

```
Benchmark Report — [URL] — [date]

Lighthouse:
  Performance: X/100 (target: ≥90)
  Accessibility: X/100 (target: ≥95)
  Best Practices: X/100
  SEO: X/100

Core Web Vitals:
  LCP: Xs (target: <2.5s)  [PASS/FAIL]
  INP: Xms (target: <200ms) [PASS/FAIL]
  CLS: X (target: <0.1)     [PASS/FAIL]

API Response Times (median / p95):
  GET /api/workbooks: Xms / Xms
  GET /api/workbooks/[id]/cells: Xms / Xms

Bundle:
  First load JS (/): Xkb
  First load JS (/dashboard): Xkb
  Largest chunk: [name] Xkb

Findings:
  [list of bottlenecks with root cause]

Recommended fixes:
  [ordered by impact]
```
