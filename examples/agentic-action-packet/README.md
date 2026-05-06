# Agentic Action Packet Demo

This fixture shows the shortest DevCD proof path for a fresh agent: Agent A lost context after a failed fix, and Agent B receives a policy-filtered Action Packet before asking the user to recap.

Run the Markdown demo:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl
```

Run the machine-readable contract:

```bash
devcd agentic action-packet-demo --events examples/agentic-action-packet/sample-events.jsonl --json
```

The fixture includes one sensitive note event. The rendered Action Packet reports that context was withheld and why, but it does not expose the private note payload.

Expected Markdown output is checked in at `action-packet.md`. JSON output includes a runtime `created_at` timestamp, so automation should assert contract fields rather than compare the whole object byte-for-byte.
