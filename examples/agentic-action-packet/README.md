# Agentic Action Packet Demo

This fixture shows the shortest DevCD proof path for a fresh agent: Agent A lost context after a failed fix, and Agent B receives a policy-filtered Action Packet before asking the user to recap.

That is the whole point of the product in one move: the user does not have to
be the continuity layer between agent sessions.

## What This Demo Proves

- the next agent starts from the current goal instead of “what are we doing?”
- the last failure is visible without replaying the whole chat
- stale attempts are carried forward as do-not-repeat guidance
- withheld context is acknowledged without leaking the sensitive payload

Run the Markdown demo:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl
```

Run the machine-readable contract:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl --json
```

The fixture includes one sensitive note event. The rendered Action Packet reports that context was withheld and why, but it does not expose the private note payload.

## Read It Like A Handoff

The easiest way to evaluate the output is to imagine you are Agent B.

You should be able to answer these questions immediately from the packet:

- What is the active goal?
- What failed last?
- What should not be repeated unchanged?
- What is the next safe move?
- What was withheld by policy?

If the packet answers those cleanly, DevCD has already done the hard part.

Expected Markdown output is checked in at `action-packet.md`. JSON output includes a runtime `created_at` timestamp, so automation should assert contract fields rather than compare the whole object byte-for-byte.
