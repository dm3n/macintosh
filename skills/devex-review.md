---
name: devex-review
description: Live developer/user experience audit. Actually test your onboarding flows, navigate docs, time time-to-first-action, screenshot errors. For both the product onboarding and dev setup.
---

# DevEx Review — Live Experience Audit

You are a first-time user. You've never seen this product. Your job is to find every point of friction between "I just got the link" and "I completed the core action."

## Usage

```
/devex-review onboarding        # audit the new user onboarding
/devex-review workflow          # audit the core product workflow
/devex-review dev               # audit the dev setup (bootstrap, first run)
/devex-review https://url.com   # audit a specific URL as a new user
```

## New User Onboarding Audit

**Starting state:** You have just received a sign-up or invite link. You have no account.

Walk through:
1. Open the link. What's the first thing you see?
2. Sign up or authenticate (Clerk). How many steps? Any confusion?
3. Land in the app. Is it obvious what to do next?
4. Find where to upload financial documents. How many clicks from landing?
5. Upload a document. Does it show progress? Does it confirm success?
6. Find your analysis status. Is it clear where things stand?

At each step, record:
- **Time:** seconds from previous step
- **Clarity:** is it obvious what to do? (Yes / Needed to think / Confused)
- **Friction:** what got in the way?

Target: zero confusion points, under 3 minutes from link to first document uploaded.

## Core Workflow Audit

**Starting state:** A logged-in user wants to complete the product's core action (run an analysis on a client's financials).

Walk through the workflow end to end:
1. Does the first step ask for the right information in the right order?
2. Is progress through the workflow clear? Do you know how much remains?
3. Are form labels descriptive enough without needing instructions?
4. Are validation errors helpful? ("Required" is not helpful. "Enter the reporting period as YYYY-MM" is.)
5. Do optional or branching paths feel natural?
6. Does the output make sense to a finance professional seeing it for the first time?

Time-to-complete: how long does the core workflow take with real data?

Target: a finance professional completes the core workflow without hesitation.

## Dev Setup Audit

**Starting state:** Someone just cloned the macintosh repo for the first time.

```bash
git clone https://github.com/dm3n/macintosh.git ~/lab/homelab-macintosh
```

Walk through the install:
1. Run `./scripts/install.sh`. Does it work? Are errors clear?
2. Is the `.env.example` complete? Are the required keys obvious?
3. Run `docker compose up -d`. Does it come up cleanly?
4. Can you reach the first service? How long does it take?

Time-to-running: minutes from clone to first working service.

Target: under 10 minutes, zero ambiguous steps.

## Output Format

```
DevEx Review — [target] — [date]

Flow: [onboarding / core workflow / dev setup]
Time to core action: X minutes Y seconds

Friction Points Found:
  1. [step] — [what the problem is] — [severity: Critical/High/Medium]
  2. ...

Screenshots:
  [note any screens that were captured]

Fixes Applied:
  [list of inline fixes]

Remaining Issues:
  [list of issues that need design/product decisions]

DX Score: X/10
(10 = first-time user completes core action without hesitation)
```
