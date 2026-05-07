---
name: devils-advocate
description: "Use when a plan, feature, ADR, policy change, MCP surface, release step, or architectural direction needs aggressive stress-testing before implementation or rollout. This skill does not help build first; it finds weak assumptions, hidden blast radius, vague success criteria, and the fastest ways the idea could fail."
argument-hint: "Describe the proposal, design, decision, or rollout you want stress-tested."
---

## Progressive Disclosure

### Level 1 - Metadata (Auto-Loaded)
The YAML frontmatter keys `name` and `description` are the discovery signal loaded automatically.

### Level 2 - Full Instructions
The remaining SKILL.md body is the complete skill guidance and is loaded on demand.

### Level 3 - Referenced Supporting Files
- None.

# Devil's Advocate

Break weak plans before reality does.

<HARD-GATE>
Do NOT help implement or polish the proposal until you have named the core claim, the hidden assumptions, the fastest realistic failure path, and the missing evidence.
</HARD-GATE>

## When To Use

- Stress-test a plan, feature, ADR, policy change, release step, MCP surface, or rollout idea
- Apply when momentum is outrunning evidence or the failure cost is non-trivial

## When NOT To Use

- Open-ended ideation first: use `brainstorming`
- Requirements clarification first: use `deep-interview`
- Visual design critique first: use `critique`
- Concrete bug first: use `systematic-debugging`

---

## Review Loop

### 1. State The Proposal Fairly

```text
Proposal:
Why it sounds attractive:
What problem it claims to solve:
What “success” appears to mean:
```

If you cannot state it clearly, that is already a finding.

### 2. Extract The Hidden Assumptions

1. **User assumption**
2. **Behavior assumption**
3. **Technical assumption**
4. **Operational assumption**
5. **Policy assumption**
6. **Evidence assumption**

Call out any assumption that is currently asserted but not evidenced.

### 3. Attack The Plan

Always pressure-test these angles:

- **Failure mode**: what is the fastest realistic way this fails?
- **Blast radius**: what else breaks if this is wrong?
- **False simplicity**: what complexity is being hidden rather than removed?
- **Evidence gap**: how would we know it worked?
- **Safer alternative**: what smaller or reversible probe tests the same idea?

---

## DevCD Lens

- Does this preserve local-first behavior, or quietly expand trust boundaries?
- Does it route state-changing behavior through explicit policy reasoning?
- Does it keep CLI, API, MCP, docs, examples, and schemas aligned?
- Does it widen authority where a read-only or narrower surface would do?
- Does it create a second onboarding, continuity, or handoff path instead of strengthening the primary one?
- Does it move slice-owned logic into `kernel/` without a real second consumer?
- Does it increase explainability, or only smooth over uncertainty?

---

## Output Format

Always finish with a compact adversarial review:

```text
Verdict:
Core weakness:
Hidden assumptions:
Fastest failure path:
Blast radius:
Evidence missing:
Safer alternative:
Decision:
```

Verdict options: `proceed`, `proceed only as a smaller probe`, `do not proceed yet`, `reject`.

Be direct and specific. No strawmen, no theatrics, no implementation advice before the main weakness is named.

---

## Completion Check

- [ ] the proposal was restated fairly
- [ ] the hidden assumptions were named
- [ ] at least one fast realistic failure path was identified
- [ ] blast radius was assessed
- [ ] a safer alternative or narrower probe was considered
- [ ] the verdict is actionable, not vague

If any box is unchecked, the review is still soft.