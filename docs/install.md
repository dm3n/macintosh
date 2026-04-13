# Install Guide

This guide covers local install and homelab deployment for Macintosh.

## Option A: One-Command Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/dm3n/macintosh/main/scripts/install.sh | bash
```

What this does:
- clones or updates `dm3n/macintosh`
- runs bootstrap
- creates `homelab/.env` from template if missing
- runs repository validation checks

## Option B: Manual Install

```bash
git clone https://github.com/dm3n/macintosh.git ~/lab/homelab-macintosh
cd ~/lab/homelab-macintosh
./scripts/bootstrap.sh
```

## Configure Environment

```bash
cd ~/lab/homelab-macintosh/homelab
cp -n .env.example .env
```

Populate `.env` with real values:
- `ANTHROPIC_API_KEY`
- `GEMINI_MODEL` (default `gemini-3`)
- database credentials
- Telegram bot credentials
- integration API keys (GitHub/Google/Linear/Slack)

## Homelab Deployment

From local machine:

```bash
cd ~/lab/homelab-macintosh
./homelab/scripts/deploy.sh <node-ip>
```

On remote host, compose runs from:
- `/opt/agenthub/homelab`

## Validation

```bash
cd ~/lab/homelab-macintosh
make validate
```

## Current Runtime Scope

`services/` now includes runnable scaffold implementations for every compose-defined service.
Current focus:
- working baseline runtime
- explicit service contracts
- approval queue and audit schema integration

Still pending for full production readiness:
- deep external API integration handlers
- hardened retry/idempotency policies per action type
- end-to-end integration test suite
