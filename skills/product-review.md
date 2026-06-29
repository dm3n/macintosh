---
name: product-review
description: YC-style product interrogation before building anything. Six forcing questions that reframe what you're actually building. Challenge scope, find the real pain, generate better alternatives.
---

# Product Review — Office Hours

Stop. Before you build, answer the hard questions. This is the conversation that happens at YC office hours when the partner looks at your deck and says "I don't think you've found the real problem yet."

## Usage

```
/product-review                          # interrogate whatever you're about to build
/product-review "client invite flow"     # specific feature
/product-review --mode reduce            # push scope down aggressively
/product-review --mode expand            # find what you're missing
```

## Modes

- **Default:** Challenge framing, find the real pain, generate alternatives
- `--mode reduce`: Aggressively cut scope. What's the smallest thing that tests the hypothesis?
- `--mode expand`: Find adjacent value. What are you leaving on the table?

## The Six Forcing Questions

Ask these in order. Don't move to the next until the current one is answered clearly.

**1. What is the specific pain?**

Not the feature request, the pain. "I want a document upload component" is a feature. "Users drop off at the document step because they don't know what to upload" is the pain.

Ask: "Tell me about the last time this problem actually hurt someone. What happened?"

If the answer is vague or hypothetical, push harder. Real pains have real examples.

**2. Who has this pain most acutely?**

Not "finance professionals." Which finance professionals? Analysts running the numbers? Reviewers signing off? Deal leads? The narrower the answer, the better the solution will be.

For Finsider: which user are we solving for? The analyst doing the work, the reviewer, or the client receiving the output?

**3. What does success look like in 30 days?**

Not "users will love it." A specific, measurable outcome. "The document request completion rate goes from 40% to 70%" or "an analyst can review a deal in 10 minutes instead of 45."

If there's no metric, the feature is aesthetic, not strategic.

**4. What have you already tried?**

What's the current workaround? Why isn't it good enough? The delta between the workaround and the solution is where the real value lives.

**5. What are you NOT building?**

Every feature decision is also a decision to not build something else. What are the three adjacent things you're explicitly leaving out, and why?

If you can't answer this, the scope isn't controlled.

**6. What would make this a 10x better product?**

Ignore constraints for a moment. If resources and time were unlimited, what would this become? The answer usually reveals what the current feature is actually heading toward — and whether it's heading the right direction.

## After the Questions

Synthesize the answers into:

1. **The real problem statement** (one sentence, specific, measurable)
2. **The right scope** for this sprint (not the wishlist — the wedge)
3. **Three alternative approaches** — the one you described, a simpler version, and a more ambitious version
4. **A recommendation** — which approach, and why, given where Finsider is right now

## Finsider Context

Apply to every product decision:
- Narrow beats broad. Solve one workflow well before widening.
- Build for the finance professionals actually using Mitch today.
- Every feature should either win a customer or help a user deliver analysis faster. If it doesn't, it's a distraction.
- Speed of learning > feature completeness. Ship the smallest thing that reveals whether the hypothesis is true.

## Output Format

```
Product Review — [feature] — [date]

The Real Pain:
  [one sentence]

Who It Hurts Most:
  [specific persona]

Success in 30 Days:
  [measurable outcome]

Scope Decision:
  Building: [what's in]
  Not building: [what's explicitly out]

Three Approaches:
  1. [minimal] — [tradeoff]
  2. [proposed] — [tradeoff]
  3. [ambitious] — [tradeoff]

Recommendation: [approach N] because [reason]

Start with: [the first thing to build]
```
