---
name: document-release
description: Generate release notes from git history. Format for two audiences: technical (Linear/internal) and stakeholder-facing (partners, investors). Save to Brain.
---

# Document Release — Release Notes Generator

Turn git history into communication. Two formats: one for the team, one for stakeholders.

## Usage

```
/document-release                          # since last tag or last week
/document-release --since v1.2.0           # since a specific tag
/document-release --project mortgage       # single project
/document-release --audience stakeholder   # only generate stakeholder version
```

## Process

**1. Pull the commit log**

```bash
# Since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline --no-merges

# Since date
git log --since="7 days ago" --oneline --no-merges
```

Run across all active projects.

**2. Categorize commits**

Group into:
- **Features** — new user-facing functionality (✨)
- **Improvements** — enhancements to existing features (⚡)
- **Fixes** — bug fixes (🐛)
- **Infrastructure** — tooling, schema, config (🔧)
- **Security** — security fixes (🔒)

Skip: merge commits, version bumps, "wip", "fix typo" style commits unless they're meaningful.

**3. Write technical release notes (for Linear / internal)**

Full detail, technical language. Every meaningful change is listed.

**4. Write stakeholder release notes (for partners / investors)**

Plain language, outcome-focused. "We shipped X" not "We added an API endpoint for X." Focus on what changed for the user, not how it was built.

Strip any internal implementation details. These notes may be shared with LOI partners.

## Output Format

### Technical (Internal)

```markdown
## Release — [date] | [project]

### Features
- [commit summary with file context]

### Improvements
- ...

### Fixes
- ...

### Infrastructure
- ...
```

### Stakeholder

```markdown
## Airbank Product Update — [date]

**[Project Name]**

What's new:
- [outcome-focused description — what can users do now that they couldn't before]

Improvements:
- [what got faster, easier, more reliable]

Coming next:
- [1-2 things in progress]
```

**5. Save both**

- Technical: `Brain/Raw/Company/release-notes-YYYY-MM-DD-technical.md`
- Stakeholder: `Brain/Raw/Company/release-notes-YYYY-MM-DD-stakeholder.md`

The nightly brain-sync will compile these into the PKB project history.
