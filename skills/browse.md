---
name: browse
description: Open a URL in a real browser, extract relevant information, and summarize findings. Use for researching docs, checking competitor UX, or reading content that requires JavaScript.
---

# Browse — Real Browser Web Research

Fetch and read a URL using a real browser. Use when the page requires JavaScript, needs authentication context, or is too complex for a plain HTTP fetch.

## Usage

```
/browse https://supabase.com/docs/guides/auth/server-side/nextjs
/browse https://ui.shadcn.com/docs/components/data-table
/browse https://stripe.com/docs/api/charges   -- extract: pagination params
/browse https://linear.app/changelog          -- extract: recent API changes
```

## When to Use

- API documentation that requires JS to render
- shadcn/ui component docs to check props and usage
- Competitor product UX research
- Changelog pages to check for breaking changes
- Any URL where WebFetch fails or returns incomplete content

## Process

1. Open the URL in the browser
2. Wait for the page to fully load (handle SPAs, lazy-loaded content)
3. Extract the relevant information based on the request
4. Summarize findings in a structured format
5. If the user asked to save findings, write to `Brain/Raw/Research/`

## Output Format

```
Browse Result — [URL] — [date]

Summary:
[2-4 sentence summary of what you found]

Key findings:
- [bullet points of relevant info]

Source: [URL]
```

For research sessions (multiple URLs on a topic), group findings by topic rather than by URL.
