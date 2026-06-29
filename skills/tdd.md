---
name: tdd
description: Lean test-driven development for non-trivial logic. Use before implementing a feature or bugfix that has real logic. Write the failing test first, then make it pass.
---

# TDD: Test First for Real Logic

Use this for anything with logic worth getting right: calculations, parsers, state machines, validation, data transforms, API contracts, bug reproductions. Skip it for trivial UI glue and one-liners (use judgment, per the Karpathy baseline).

## The Cycle

1. **Red.** Write one failing test that states the success criterion. Run it. Watch it fail for the right reason (it asserts the thing you care about, not a typo).
2. **Green.** Write the minimum code to make it pass. Nothing speculative (Simplicity First).
3. **Refactor.** Clean up with the test as your safety net. Tests stay green.

Repeat one behavior at a time.

## For bugs

"Fix the bug" becomes: write a test that reproduces the bug (red), then fix until green. The test is the proof it is fixed and the guard against regression. Pairs with `/debug`.

## What to test

- The logic, the edge cases, the error paths. Invalid inputs, empty states, boundaries.
- Not framework internals, third-party libraries, or trivial passthroughs.

## Stack notes

- Frontend-heavy work often has thin unit coverage. Put TDD where the logic actually lives (`lib/` utilities, API route handlers, data shaping), and use `/qa` for live UI behavior.
- A failing test you can run beats a plan you cannot verify. If a surface has no test runner, the "test" can be a minimal script or a `/qa` flow with an explicit pass/fail criterion.
