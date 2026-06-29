---
name: plan-design-review
description: Review a design spec or plan for UI feasibility, shadcn/ui component availability, design system consistency, and premium fintech standards. Run before implementation begins.
---

# Plan Design Review — Spec-Level Design Audit

Catch design problems before they become code problems. You are a senior designer reviewing the spec before a line of UI is written.

## Usage

```
/plan-design-review                              # review latest spec in docs/plans/
/plan-design-review docs/plans/foo.md
```

## What This Checks

**1. shadcn/ui Feasibility**

For every UI element described in the spec, verify a shadcn component exists. If the spec calls for something shadcn doesn't have, flag it now — don't let it become a custom component.

Common shadcn components available:
- Form controls: Input, Textarea, Select, Checkbox, RadioGroup, Switch, Slider
- Layout: Card, Separator, Tabs, Accordion, Collapsible
- Overlay: Dialog, Sheet, Popover, Tooltip, HoverCard, DropdownMenu
- Feedback: Alert, Badge, Progress, Skeleton, Toast (Sonner)
- Navigation: Breadcrumb, NavigationMenu, Pagination
- Data: Table, DataTable (with TanStack Table)
- Display: Avatar, Calendar, Chart (Recharts wrapper)

If the spec describes something outside this list, propose which shadcn component to adapt or flag it as a custom component that needs justification.

**2. Component Reuse**

Check if the spec introduces new components that could reuse existing ones. Flag duplication before it's built.

Look at what already exists in the project's `components/` directory. Does this spec create a fourth card variant when one would do?

**3. Design System Consistency**

Does this spec match the visual language already established?
- Same spacing system (4px grid)
- Same color tokens
- Same heading/text hierarchy
- Same button variants
- Same loading/empty state patterns

Flag any divergence from existing patterns. If the spec is better than what exists, note that the existing pattern should be updated too.

**4. Information Architecture**

Is the content organized logically for the product's users?
- Complex forms are broken into steps (wizard pattern), not one long scroll
- Data-heavy views use tables with filtering, not unstructured lists
- Actions (approve, submit, upload) are always visible, not buried

**5. Edge Cases in the Spec**

Does the spec define what happens when:
- Data is loading?
- The result is empty?
- An error occurs?
- The user is on mobile?

If not, add these to the spec before implementation.

**6. Scope Assessment**

Rate the design complexity: Simple / Medium / Complex.

- **Simple:** Uses existing shadcn components, no new patterns, 1-2 files
- **Medium:** Composing multiple components, some new layout, 3-6 files
- **Complex:** New component patterns, data-heavy views, multi-step flows, 7+ files

If Complex, recommend breaking into phases.

## Output Format

Present your review as a set of annotated sections from the spec, with comments. Then give a go/no-go recommendation:

```
Plan Design Review — [spec file] — [date]

shadcn/ui Feasibility: GO / NEEDS ADJUSTMENT
  [notes on any gaps]

Component Reuse: GO / DUPLICATION RISK
  [list any redundancies]

Design System Consistency: GO / INCONSISTENCIES FOUND
  [list divergences]

Edge Cases: COMPLETE / MISSING: [list]

Complexity: Simple / Medium / Complex

Recommendation: GO / REVISE BEFORE BUILD
  [specific changes to make to the spec]
```
