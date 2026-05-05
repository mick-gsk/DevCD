# Context Packs

Context Packs are DevCD's current extension surface. They let a workflow define
which local metadata matters, which event types are expected, which agent
surfaces can consume the result, and which policy notes should travel with the
Continuity Packet.

A Context Pack is not a plugin that executes arbitrary code. It is a local,
policy-filtered rendering contract over typed DevCD events. This keeps extension
work aligned with DevCD's local-first defaults.

## What A Pack Owns

A pack declares:

- an id such as `developer` or `research`;
- a display name and description;
- supported event sources and event types;
- supported surfaces such as `cli`, `mcp`, `coding-agent`, or `research-agent`;
- default sensitivity and policy notes;
- renderer metadata used by Continuity Packet generation.

List the built-in packs:

```bash
devcd context packs
devcd context packs --json
```

Use a pack with the live local passport:

```bash
devcd context passport --pack developer
devcd context passport --surface research-agent --pack research
```

Use a pack with a reproducible fixture:

```bash
devcd context handoff-demo \
  --events examples/research-continuity/sample-events.jsonl \
  --surface research-agent \
  --pack research
```

## Current Built-In Packs

| Pack | Purpose | Safe extension path |
| --- | --- | --- |
| `developer` | Coding-agent continuity across goals, files, git state, failures, and next actions. | Emit metadata events from IDE, Git, task, notes, or system sources. |
| `research` | Research-agent continuity across reviewed sources, note metadata, hypotheses, decisions, and failed attempts. | Use the research-session recipe or emit equivalent metadata events. |

## How To Extend DevCD Today

The safest current extension path is a recipe plus a Context Pack:

1. Define the workflow signal as a small local JSON input.
2. Convert that input into typed `DevEvent` records.
3. Mark raw text, logs, transcripts, and full content as sensitive/full-text.
4. Keep metadata events useful enough for a Continuity Packet.
5. Add or update a Context Pack declaration only when the workflow needs a new
   rendering contract.
6. Add fixture events and expected output under `examples/`.
7. Test policy withholding and packet rendering.

Recipes live in the events slice because they normalize incoming workflow data.
Context Packs live in ambient context because they define how policy-visible
state is rendered for agents.

## What Not To Do

Do not add extension mechanisms that bypass policy:

- no remote plugin loading;
- no arbitrary shell execution from a pack;
- no write-capable MCP tools for pack installation;
- no raw content ingestion without explicit sensitivity and policy tests;
- no global runtime config mutation from a pack;
- no connector that scrapes browsers, notes, SaaS tools, or repos without a
  separate policy decision and design record.

## Candidate Community Packs

Good early pack candidates are workflows where metadata is valuable without raw
content:

- issue triage: issue id, labels, current hypothesis, attempted fixes;
- code review: changed artifact refs, review findings, blocking questions;
- incident response: timeline metadata, mitigations tried, current owner;
- research: source titles, claims, decisions, rejected hypotheses;
- release readiness: checklist state, failing gate, next safe release action.

Each pack should prove the same contract: useful continuity from local metadata,
with sensitive context withheld by policy.
