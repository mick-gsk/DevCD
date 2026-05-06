# OpenClaw Integration

DevCD integrates with OpenClaw through the standard local MCP stdio boundary.
It is not an OpenClaw plugin, does not mutate OpenClaw configuration, and does
not require write-capable MCP tools.

The intended moment is Turn-0 continuity: a fresh OpenClaw agent reads local,
policy-filtered DevCD continuity before asking the developer to recap. If the
Action Packet is ready, the agent should start by naming the current goal, next
action, blocker, stale attempt warning, and any withheld-context policy note.

## Verified DevCD Side

The DevCD side can be checked without installing OpenClaw:

```bash
devcd integrations openclaw --smoke-test
```

This command prints a copyable local MCP snippet and verifies the shape of the
read-only MCP server in-process. It checks initialize, resources, tools, and
prompts without editing `~/.openclaw/openclaw.json`.

The MCP command OpenClaw should launch is:

```bash
devcd mcp serve
```

DevCD currently exposes read-only resources such as Continuity Packet, Action
Packet, Agent Handoff Packet, work state, policy summary, recent timeline, and
withheld-context summaries. It exposes no write-capable MCP tools.

## Configuration Shape

Use the CLI to print the current snippet:

```bash
devcd integrations openclaw
devcd integrations openclaw --json
```

The relevant shape is:

```json
{
  "mcp": {
    "servers": {
      "devcd": {
        "command": "devcd",
        "args": ["mcp", "serve"]
      }
    }
  }
}
```

Add this manually to OpenClaw configuration only when you choose to connect the
local runtime.

## What An OpenClaw Agent Should Read

At the start of a session, the agent should prefer:

1. `devcd://context/action-packet` for next-action guidance.
2. `devcd://context/policy-summary` before asking for withheld context.
3. `devcd://context/continuity-packet` for domain-neutral continuity if the
  Action Packet is not ready.
4. `devcd://context/withheld-context` to understand what was intentionally not
   included.

If an older workflow still expects it, `devcd://context/agent-handoff-packet` is
kept as a legacy developer handoff contract.

## OpenClaw Skill Draft

The first OpenClaw-native artifact is the small Skill draft at
`skills/devcd-continuity/SKILL.md`. Its job is not to install DevCD or change
OpenClaw config. Its job is to teach the agent the first move:

1. Read `devcd://context/action-packet`.
2. Read `devcd://context/policy-summary`.
3. Start with the goal, next action, blockers, `do_not_repeat`, and policy note.
4. Ask only for confirmation or correction.

This is the intended OpenClaw moment: the agent begins warm.

## Current Limitation

The DevCD MCP server and config snippet are locally verified. The full
OpenClaw-gateway end-to-end flow is intentionally not claimed here until a real
OpenClaw runtime has loaded and read the DevCD resources.

Until that verification exists, DevCD should not be described as:

- an official OpenClaw plugin;
- a ClawHub package;
- a ClawHub skill;
- an OpenClaw-native runtime component;
- an integration that automatically edits OpenClaw config.

## Artifacts

- OpenClaw Skill draft: `skills/devcd-continuity/SKILL.md`
- MCP proof notes: `examples/openclaw-mcp-context/README.md`
- Packaging analysis: `docs/devcd/openclaw-packaging-spike.md`
- Draft use case: `docs/devcd/openclaw-usecase-draft.md`
- Release readiness: `docs/devcd/release-readiness.md`
