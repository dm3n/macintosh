# Install Guide

## Option A: One-Command Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/dm3n/macintosh/main/scripts/install.sh | bash
```

## Option B: Manual Install

```bash
git clone https://github.com/dm3n/macintosh.git ~/lab/homelab-macintosh
cd ~/lab/homelab-macintosh
./scripts/bootstrap.sh
```

## Configure Runtime

```bash
cd ~/lab/homelab-macintosh/homelab
cp -n .env.example .env
```

Set required credentials:
- `ANTHROPIC_API_KEY`
- `GEMINI_MODEL` (default `gemini-3`)
- DB credentials
- GitHub token
- Google OAuth credentials
- Linear credentials for approvals

## Deploy

```bash
cd ~/lab/homelab-macintosh
./homelab/scripts/deploy.sh <node-ip>
```

Compose root on server:
- `/opt/agenthub/homelab`

## Validate

```bash
make validate
```

## Runtime Scope

- all compose-defined services have runnable scaffolds
- approval path is Linear-driven
- integration handlers are still being hardened incrementally
