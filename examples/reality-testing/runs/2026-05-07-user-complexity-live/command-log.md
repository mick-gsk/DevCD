# Command Log (Preview je Szenario)

## S1 - Cold start setup and first handoff packet

```text
+--------------------- Traceback (most recent call last) ---------------------+
| C:\Users\mickg\DevCD\packages\devcd-core\src\devcd\cli.py:407 in setup      |
|                                                                             |
|    404         typer.echo(json.dumps(report, indent=2, sort_keys=True))     |
|    405         return                                                       |
|    406                                                                      |
| >  407     _print_setup_report(report)                                      |
|    408                                                                      |
|    409                                                                      |
|    410 def _print_setup_report(report: dict[str, Any]) -> None:             |
```

## S2 - Mid-task handoff with blocker

```text
Captured handoff for next agent: goal, failure, next_action
Ledger: .devcd\events.jsonl
Next agent starts with: devcd agentic action-packet
{
  "schema_version": "1.1",
  "current_goal": "Fix failing release gate",
  "next_action": "Inspect typecheck output",
  "recommended_agent_mode": "debugging",
  "evidence": [
    {
```

## S3 - Policy boundary deny-by-default check

```text
{
  "decision_id": "d1c420dd-653c-4d4b-95ed-f5b4003f8d62",
  "kind": "deny",
  "reason": "local scout runner start is denied by the default local-first policy",
  "operation": "agentic_runner_start",
  "source": "codex",
  "data_class": "metadata"
}

```

## S4 - MCP integration smoke path

```text
OpenClaw + DevCD MCP

Paste this snippet into: ~/.openclaw/openclaw.json

Config snippet
```json5
{
  mcp: {
    servers: {
      devcd: {
```

## S5 - Completion gate readiness

```text
Agentic completion gate
Completion gate passed
- packet_ready: true
- has_handoff: true
- current_goal: Fix failing release gate
- next_action: Inspect typecheck output
- next: done

```

