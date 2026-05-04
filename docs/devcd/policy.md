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
- Action events are denied unless a future explicit policy grants them.
- Remote export is denied by default.
- Sensitive payloads should be filtered at the connector before reaching the daemon.

## Open Questions

- Which data classes count as sensitive by default?
- Should policy be configured through YAML, MCP resources, or both?
- How strict should observation-only mode be for IDE telemetry?
