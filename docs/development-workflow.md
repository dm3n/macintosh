# Development Workflow

This repository uses a superpowers-era workflow: focused execution loops with explicit validation, not legacy fixed-role Architect/Coder/QA chains.

## Core Loop

```text
Problem / Spec
  -> Scope + constraints
  -> Implement focused change
  -> Validate (tests/lint/build/checks)
  -> Review diff quality
  -> Ship via PR to main
```

## Source of Truth

- Issues and prioritization: **Linear**
- Code and review: **GitHub**
- Deploys: **Vercel** (where applicable)
- System memory/context: **Brain PKB**

## Branch Strategy

- `main` is protected and deployable.
- Work happens in focused branches: `feature/*`, `fix/*`, `chore/*`, `docs/*`.
- Every merge should be reversible and documented.

## PR Standard

Each PR should include:
- what changed
- why it changed
- how it was verified
- rollback considerations (if operationally relevant)

## Verification Standard

Before merge:
- run repo-level validation (`./scripts/validate-repo.sh`)
- run project-specific checks where touched
- verify docs if behavior/config changed

## Linear Integration

- Every non-trivial change maps to a Linear issue.
- PRs link back to Linear issue IDs.
- Approval-gated automation decisions are tracked in Linear.

## Local Dev References

```bash
# Airbank Platform
cd "/Users/dm3n/Airbank/Airbank Platform"
npm run dev

# ROGI
cd "/Users/dm3n/Projects/rogi"
npm run dev -- --port 3002
```

Terminal baseline: Superset + Zsh.
