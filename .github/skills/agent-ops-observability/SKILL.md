---
name: agent-ops-observability
description: "Use when an agent ignores instructions, loses context, misuses tools, produces weak handoffs, behaves unreliably across multiple steps, or needs observability and operational guardrails. Covers instruction loading checks, handoff discipline, context compaction, multi-agent coordination, failure-mode analysis, and verification gates for agent-driven work."
argument-hint: "Describe the unreliable agent behavior, the workflow being operated, or the handoff/observability problem to diagnose and harden."
---

## Progressive Disclosure

### Level 1 - Metadata (Auto-Loaded)
The YAML frontmatter keys `name` and `description` are the discovery signal loaded automatically.

### Level 2 - Full Instructions
The remaining SKILL.md body is the complete skill guidance and is loaded on demand.

### Level 3 - Referenced Supporting Files
- None.

# Agent Ops And Observability

Diagnose unreliable agent work by finding the first operational layer that drifted, then harden only that layer.

<HARD-GATE>
Do NOT rewrite prompts, add tools, or widen authority before naming one primary failing layer with evidence.
</HARD-GATE>

## When To Use

- An agent ignores instructions, loses context, misuses tools, or produces weak handoffs
- A multi-step or multi-agent workflow repeats work, drifts, or makes unsupported claims
- A tool is available but operationally vague, unsafe, or hard to trust
- The team needs clearer gates, runbooks, or verification around agent-driven work

## When NOT To Use

- Concrete bug or failing test first: use `systematic-debugging`
- Feature or design exploration first: use `brainstorming`
- Final completion proof only: use `verification-before-completion`

---

## Operating Model

Treat every workflow as six layers:

1. **Instruction**: what files, prompts, and hard constraints govern the task?
2. **Boundary**: what may the agent read, change, or invoke?
3. **Context**: what state must survive between turns, agents, or restarts?
4. **Tool**: what are the tool contracts, outputs, and failure modes?
5. **Workflow**: who owns research, edits, review, and approvals?
6. **Evidence**: what proof is required before any progress claim?

---

## Triage

Start with the smallest honest framing:

```text
Observed behavior:
Expected behavior:
First point of visible drift:
Smallest reproducible check:
```

Then pick one primary drift category:

- **Instruction drift**
- **Authority drift**
- **Context drift**
- **Tool drift**
- **Coordination drift**
- **Evidence drift**

If several apply, choose the first visible divergence, not the loudest symptom.

---

## Layer Checks

### Instruction

- Ask which instruction files and hard gates govern the task.
- Ask for protected areas and required validation in the agent's own words.
- Compare the answer against the actual repo rules.

Useful prompt:

What instruction files and hard constraints govern this task? Summarize the protected areas and required validation steps before continuing.

### Boundary

- Check whether the agent can name approval areas, read-only actions, and state-changing actions.
- If it acts outside bounds, reduce authority or add an approval gate. Do not rely on “be careful.”

### Context

- Verify the current goal, next action, blockers, failed attempts, and do-not-repeat notes.
- Prefer compact persisted state over long chat history.

Minimum state packet:

```text
Goal: <current target>
Next: <immediate next action>
Blocked by: <blocker or none>
Do not repeat: <known bad path>
Verify with: <specific command or check>
```

### Tool

- For each important tool, check input shape, successful output, empty or denied output, failure handling, and visible side effects.
- If the agent has to guess around a tool, the contract is too weak.

### Workflow

- In longer flows, define roles explicitly: **Lead**, **Research**, **Implement**, **Review**.
- Require one owner per step, approval before unresolved edits, approval before completion claims, and parallelism only for independent read-only work.

### Evidence

- Do not trust “done” without a named check.
- Do not trust agent-reported success without independent evidence.
- Use the cheapest falsifiable check first.
- Re-read the actual request before declaring success.

---

## Diagnosis

Write the diagnosis in this form:

```text
Primary failing layer:
Evidence:
Why this is the first real point of drift:
What downstream symptoms it caused:
```

Recommend the smallest operational change that would make the next run more reliable.

---

## Hardening Moves

- **Instruction**: reduce ambiguity, require an instruction summary, point to one source of truth.
- **Boundary**: add approval gates, mark protected areas, reduce authority.
- **Context**: persist a short handoff, store goal and blockers, compact after milestones.
- **Tool**: define exact IO, document empty and denied outcomes, trim noisy outputs.
- **Workflow**: split roles, separate research from edits and review, define parallel vs serial work.
- **Evidence**: require named checks, ban unsupported completion claims, verify user intent not just green tests.

---

## Handoff Standard

Minimum handoff packet:

```text
Goal: <current objective>
Done: <what is already true>
Next: <single next action>
Blocked by: <blocker or none>
Failed attempts: <what was tried and should not be repeated>
Files: <only the files that matter>
Verify with: <specific command or targeted check>
```

If this cannot stay short, the workflow is likely too broad or under-structured.

---

## Output Format

Always finish with a compact runbook:

```text
Problem:
Primary failing layer:
Evidence:
Next diagnostic check:
Recommended hardening move:
Verification:
```

If useful, add a second section:

```text
Suggested role split:
Suggested handoff shape:
Suggested approval gates:
```

Keep it operational.

---

## DevCD Lens

- Prefer local context over user recap when continuity artifacts exist.
- Treat policy boundaries as task context.
- Keep state-changing work explainable and MCP/continuity surfaces thin.
- Check whether continuity packets are ready, policy summaries explain withheld context, and handoffs preserve blockers and failed attempts.

---

## Completion Check

- [ ] one primary failing layer was identified
- [ ] diagnosis was evidence-based
- [ ] the hardening move matched the diagnosed layer
- [ ] handoff or workflow rules were made more explicit
- [ ] verification was named concretely

If any box is unchecked, the workflow is not hardened yet.