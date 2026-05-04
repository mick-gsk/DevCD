# DevCD Policy Layer

The default DevCD policy is conservative:

```yaml
observe: allow
store: allow-local
export: deny
action: deny
```

Every decision records a reason. This creates an audit trail for why an event was observed, stored, exported, or rejected.

## MVP Rules

- Observation events are allowed unless they are marked sensitive.
- Local storage gates both the JSON Lines ledger and working-memory writes.
- Action events are denied unless a future explicit policy grants them.
- Remote export is denied by default.
- Sensitive payloads should be filtered at the connector before reaching the daemon.

## Ambient Context Exports

Ambient work state and agent briefs are treated as exports even when the requesting surface is local. The current default policy allows metadata-only local context export and denies disallowed data classes. Denied sources and data classes are omitted from the brief and reported as withheld context when it is safe to disclose the reason.

Proactive suggestions are advisory context, not actions. They may explain a likely next step, but they do not mutate files, run commands, or contact remote services. Dismissing a suggestion records a local cooldown so the same blocker does not keep reappearing.

Context memory inspection, correction, and deletion operate only on policy-visible local memory items. Local context-control mutations receive an explicit policy decision, corrections carry an audit reason, and deleted or expired items are excluded from later work-state derivation.

## Open Questions

- Which data classes count as sensitive by default?
- Should policy be configured through YAML, MCP resources, or both?
- How strict should observation-only mode be for IDE telemetry?
