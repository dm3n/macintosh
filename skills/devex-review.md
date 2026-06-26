---
name: devex-review
description: Live developer/borrower experience audit. Actually test your onboarding flows, navigate docs, time time-to-first-action, screenshot errors. For both the borrower portal and dev setup.
---

# DevEx Review — Live Experience Audit

You are a first-time user. You've never seen this product. Your job is to find every point of friction between "I just got the link" and "I completed the core action."

## Usage

```
/devex-review borrower          # audit the borrower portal onboarding
/devex-review apply             # audit the /apply wizard flow
/devex-review dev               # audit the dev setup (bootstrap, first run)
/devex-review https://url.com   # audit a specific URL as a new user
```

## Borrower Portal Audit

**Starting state:** You have just received an invite email with a portal link. You have no account.

Walk through:
1. Open the link. What's the first thing you see?
2. Sign up or authenticate. How many steps? Any confusion?
3. Land in the portal. Is it obvious what to do next?
4. Find where to upload documents. How many clicks from landing?
5. Upload a document. Does it show progress? Does it confirm success?
6. Find your application status. Is it clear where things stand?

At each step, record:
- **Time:** seconds from previous step
- **Clarity:** is it obvious what to do? (Yes / Needed to think / Confused)
- **Friction:** what got in the way?

Target: zero confusion points, under 3 minutes from link to first document uploaded.

## Apply Wizard Audit (`/apply`)

**Starting state:** A broker just sent you the application link.

Walk through all 8 steps:
1. Does Step 1 ask for the right information in the right order?
2. Is the progress indicator clear? Do you know how many steps remain?
3. Are form labels descriptive enough without needing instructions?
4. Are validation errors helpful? ("Required" is not helpful. "Enter your full legal name as it appears on your ID" is.)
5. Does the optional path (Step 4 decision) feel natural?
6. Does the document checklist on Step 8 make sense to a first-time buyer?

Time-to-submit: how long does a complete submission take with real data?

Target: under 12 minutes for a complete application.

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

Flow: [borrower portal / apply / dev setup]
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
