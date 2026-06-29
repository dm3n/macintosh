---
name: design-shotgun
description: Generate 4-6 UI design variants for a component or screen using shadcn/ui. Show options, collect feedback, iterate until you have a winner.
---

# Design Shotgun — Explore Before You Commit

Don't build the first idea. Generate options, pick a direction, then build. This saves hours of rework on UI that looked different in your head.

## The Rule

All variants must be built with shadcn/ui components and Tailwind v4. No custom components, no raw HTML elements. If you can't build it with shadcn, the design needs to be reconsidered.

## Usage

```
/design-shotgun "document upload card"
/design-shotgun "multi-step progress bar"
/design-shotgun "data table row"
/design-shotgun components/dashboard/RowItem.tsx   # redesign an existing component
```

## Process

**1. Understand the context**

Before generating variants, clarify:
- Where does this component live? (what page, what context)
- What data does it display? (what are the real field names and types)
- What actions can the user take? (primary, secondary, destructive)
- What are the states? (loading, empty, error, populated)

If any of these are unclear, ask. One question at a time.

**2. Generate 4–6 variants**

Produce variants as actual code — not descriptions, not wireframes. Each variant is a real React component using shadcn/ui + Tailwind v4 that could be dropped into the codebase today.

Vary across these dimensions:
- **Layout:** horizontal vs. vertical, card vs. inline, modal vs. inline
- **Density:** compact (data-heavy) vs. spacious (consumer-friendly)
- **Visual weight:** prominent CTA vs. understated, bordered vs. flat
- **Information hierarchy:** what's the first thing the user sees?

Name each variant with a short descriptor: `Compact`, `Expansive`, `Minimal`, `Dashboard`, `Wizard`, `Inline`.

**3. Show variants for feedback**

Present each variant with:
- The component code
- A one-line description of the design intent
- The tradeoff (what it's good for vs. where it falls short)

Ask which variant (or combination of elements) to move forward with.

**4. Iterate**

Based on feedback, produce a refined version combining the best elements. Repeat until there's a clear winner.

**5. Hand off**

Once a direction is chosen, the winner is the implementation target. It should be clean enough to commit directly.

## Design Taste Memory

Across sessions, internalize these preferences:
- **Preferred:** Clean, high-contrast, monochrome base with a single accent color. Data tables over unstructured lists. Progress indicators on multi-step flows. Subtle borders, not colored backgrounds, for cards.
- **Avoid:** Colorful cards, gradients on primary actions, icon-heavy navigation, consumer-app patterns (stories, reactions, feeds).
- **Reference aesthetic:** Mercury, Linear, Stripe Dashboard.

## Output Format

For each variant:

```tsx
// Variant: [Name] — [one-line intent]
// Tradeoff: [what it's good for vs. where it falls short]

export function ComponentName() {
  return (
    // shadcn/ui + Tailwind v4 implementation
  )
}
```

After all variants: ask which direction to pursue.
