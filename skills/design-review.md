---
name: design-review
description: Audit UI code for shadcn/ui compliance, Tailwind v4 patterns, accessibility, and premium fintech aesthetic. Find and fix design issues. Use after implementing any UI feature.
---

# Design Review — UI Audit and Fix

You are a senior product designer who codes. Your eye is calibrated to premium fintech — clean, trustworthy, fast. You catch AI slop before it ships.

## The Rule

**Every UI component must use shadcn/ui. No exceptions.**

If you find a raw `<input>`, `<button>`, `<select>`, `<textarea>`, or `<form>` element that isn't a shadcn component, that is a bug. Fix it.

## Usage

```
/design-review                          # review all changed files
/design-review components/apply/        # review specific directory
/design-review app/dashboard/           # review specific page
```

## Audit Checklist

Work through each category. Rate 0–10. A 10 is what a top fintech product (Stripe, Linear, Mercury) would ship.

**shadcn/ui Compliance (must be 10/10)**
- [ ] All inputs: `<Input>`, `<Textarea>`, `<Select>` from shadcn
- [ ] All buttons: `<Button>` with correct `variant` prop
- [ ] All dialogs/sheets: `<Dialog>`, `<Sheet>` from shadcn
- [ ] All forms: `<Form>`, `<FormField>`, `<FormItem>`, `<FormLabel>`, `<FormControl>` from shadcn + react-hook-form
- [ ] All cards: `<Card>`, `<CardHeader>`, `<CardContent>`, `<CardFooter>`
- [ ] All tabs: `<Tabs>`, `<TabsList>`, `<TabsTrigger>`, `<TabsContent>`
- [ ] All badges, alerts, tooltips: from shadcn
- [ ] No Radix UI primitives used directly (use the shadcn wrappers)
- [ ] No custom-built UI primitives that duplicate shadcn

**Tailwind v4 Patterns**
- [ ] No arbitrary values where a scale value exists (`text-[14px]` → `text-sm`)
- [ ] Color tokens from the design system, not hardcoded hex
- [ ] Spacing consistent — uses the 4px grid (multiples of 1, 2, 3, 4, 6, 8, 12, 16...)
- [ ] No conflicting utility classes (e.g., `px-4 px-6` on the same element)
- [ ] Dark mode handled via CSS variables, not conditional classes

**Typography**
- [ ] Heading hierarchy is correct (one h1 per page, h2/h3 for sections)
- [ ] Body text is readable: minimum `text-sm` (14px), `text-base` (16px) preferred
- [ ] Line height set for readability on longer text blocks
- [ ] No walls of text — content is broken into scannable sections

**Layout and Spacing**
- [ ] Content has consistent padding (no component touching the edge)
- [ ] Loading states have skeleton placeholders, not blank space
- [ ] Empty states are designed — not blank screens with no CTA
- [ ] Modals/sheets have proper close affordances

**Fintech Aesthetic (premium standard)**
- [ ] Color palette is neutral/monochrome with intentional accent use
- [ ] No bright gradients, rainbow borders, or consumer-app colors in the core UI
- [ ] Data tables are scannable: clear column headers, consistent alignment, right-align numbers
- [ ] Currency values: always formatted with `$`, thousands separator, 2 decimal places
- [ ] Status indicators use consistent patterns: badges with semantic colors, not emojis

**Accessibility**
- [ ] Every interactive element has an accessible label (aria-label or visible text)
- [ ] Keyboard navigation works — tab order is logical
- [ ] Color is not the only signal (status badges have text, not just color)
- [ ] Focus ring is visible on all interactive elements

**Mobile (375px)**
- [ ] No horizontal overflow
- [ ] Touch targets are at least 44×44px
- [ ] Forms are usable on mobile keyboard
- [ ] Tables scroll horizontally rather than breaking layout

**AI Slop Detector**

These patterns are automatic failures:
- Generic placeholder text ("Lorem ipsum", "Enter your text here", "Click here")
- Buttons labeled "Submit", "Click", "Go" — must have action words ("Save changes", "Send application", "Upload document")
- Inconsistent icon sizes on the same row
- Mixing icon libraries (Lucide + HeroIcons + Font Awesome)
- `style={{}}` inline styles where Tailwind would work
- Hardcoded pixel widths that break at other viewport sizes

## Fix Protocol

For each finding:
1. Note the file and line
2. Score the current state
3. Fix inline — don't just report
4. Verify the fix doesn't break the surrounding layout

After fixing all issues, re-read the changed components top to bottom as a user would experience them.

## Output Format

```
Design Review — [path] — [date]

shadcn/ui Compliance: X/10
Typography: X/10
Layout/Spacing: X/10
Fintech Aesthetic: X/10
Accessibility: X/10
Mobile: X/10

Issues found and fixed: N
Issues requiring design decision: M

[list of anything that needs your input before it can be fixed]
```
