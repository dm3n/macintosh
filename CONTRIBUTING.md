# Contributing

## Philosophy

Macintosh is a long-horizon personal AI operating system. Contributions should optimize for:
- correctness
- operational safety
- reproducibility
- documentation quality

## Before You Open a PR

1. Fork and create a branch from `main`.
2. Run:
   ```bash
   ./scripts/validate-repo.sh
   ```
3. Keep changes focused and atomic.
4. Update docs for every behavior/configuration change.
5. Never commit secrets or real credentials.

## Pull Request Checklist

- [ ] Problem and outcome are clearly described.
- [ ] Validation script passes locally.
- [ ] Documentation is updated.
- [ ] No drift introduced on model/version standards (Gemini 3, Superset terminal, etc.).
- [ ] No secrets added.

## Commit Style

Use concise conventional-style messages:
- `feat: ...`
- `fix: ...`
- `docs: ...`
- `chore: ...`

## Security

If you find a security issue, do not open a public issue with exploit details.
Contact: `daniel@nodebase.ca`
