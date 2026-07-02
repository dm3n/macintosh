---
name: domain-modeling
description: Create and maintain a DOMAIN.md per repo — the ubiquitous language document that defines the project's load-bearing terms, invariants, and look-alike distinctions so agents stop re-deriving the domain every session. Invoke when starting work in a repo without one, when a term is ambiguous, or after a change that alters domain meaning.
---

# Domain Modeling: The Ubiquitous Language File

Agents waste their first hour in a complex codebase re-deriving what the words mean — and misalignment hides in words that look alike but aren't. A `DOMAIN.md` at the repo root fixes both: it is the shared vocabulary between the human, the code, and every agent session, readable in two minutes.

Adapted from Matt Pocock's `domain-modeling` skill into this setup's conventions.

## What goes in DOMAIN.md

1. **Glossary** — every load-bearing domain term, one tight definition each, with the table/type/file where it lives. Group by subsystem. Define terms by what they mean in THIS codebase, not in general.
2. **Look-alikes** — the confusable pairs, explicitly disambiguated ("X is not Y: ..."). This section prevents the most expensive class of agent error.
3. **Invariants** — the rules that must always hold ("every A has exactly one B", "C is never mutated after D"). These are the assertions reviews and tests protect.
4. **Lifecycles** — for the 2-3 central entities, the state machine in one line each.
5. **Warts** — naming that lies (typos in filenames, legacy names, fields that mean something other than they say). Documented, not fixed — fixing is a separate, deliberate task.

Keep it under ~150 lines. A domain model nobody reads is decoration; length is the enemy.

## Rules

- **Repo root, named `DOMAIN.md`**, referenced from the repo's `CLAUDE.md`/`AGENTS.md` so every agent loads it.
- **Update in the same PR** that changes a domain meaning — a stale domain model is worse than none.
- **Descriptive, not aspirational** — document the code as it is, including its warts. Aspirations go in issues.
- **Terms come from the code and the team**, not from textbook DDD. If the code says `workspace`, the doc says `workspace`, even if `tenant` would be prettier.
- When two repos share one domain (FE + BE of the same product), keep copies in sync and note the pairing in each file's header.

## Building one from scratch

Fan out over: content-types/schema/models, the service layer's nouns, the API surface, and existing specs/contracts. Extract candidate terms, then keep only the ones an agent would otherwise misuse. Write the look-alikes section first — it forces precision everywhere else.
