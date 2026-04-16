# Sacred Secretion Agent

A personal practice agent that tracks the monthly lunar Gemini transit and sends
practice-guiding emails throughout the sacred secretion cycle.

## What It Does

The moon completes a full zodiac cycle in ~27.3 days. Each month when it enters
Gemini (Daniel's natal sun sign), a 2.5-day window opens — the Gethsemane phase
of the sacred secretion process. This agent:

1. Detects the transit daily using astronomical calculation (no external API)
2. Sends 7 emails across the full monthly cycle at the right moments
3. Tracks cycle state in Postgres so it never double-sends

## Email Sequence

| Trigger | Email |
|---|---|
| Moon enters Gemini | Window is open — 2.5 days |
| Day 1 of window | What to do today |
| Day 2 of window | Gethsemane — the pressure point |
| ~Hour 58 of window | Final hours — hold |
| Day 7 post-window | The ascent — signals to watch |
| Day 14 post-window | Deepen the practice |
| Day 26 post-window | Your next window opens in ~2 days |

## Required Environment Variables

```
RESEND_API_KEY=re_...
```

## Source Material

The full theoretical foundation, proof, and protocol are published at:
**[github.com/dm3n/sacred-secretion](https://github.com/dm3n/sacred-secretion)**

- **Publication I** — The Sacred Secretion (The Proof)
- **Publication II** — The Cipher of Numbers (The Mathematics)
- **Publication III** — The Map (The Protocol) ← this agent implements Publication III

## Running Locally

```bash
cd services
node agents/sacred-secretion/src/index.js
```

Set `SACRED_SCHEDULE` env var to override the cron (default: `0 7 * * *` — 7am daily).
