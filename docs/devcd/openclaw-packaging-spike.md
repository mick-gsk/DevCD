# OpenClaw Packaging Spike

Date: 2026-05-05

## Decision Summary

DevCD should not be submitted first as an OpenClaw code plugin or general
ClawHub package. The correct first path is a documented MCP configuration use
case, followed by a small OpenClaw Skill only after the OpenClaw + DevCD MCP
flow is tested end to end.

Recommended first submission sequence:

1. Keep `examples/openclaw-mcp-context/README.md` as the current proof artifact.
2. Add an OpenClaw Skill later only if it teaches agents when and how to read
   the configured DevCD MCP resources.
3. Do not build a code plugin/package until DevCD needs OpenClaw-owned runtime
   behavior, tools, setup UI, or gateway integration beyond standard MCP client
   configuration.

## Upstream Format Findings

OpenClaw recognizes these relevant packaging surfaces:

| Format | Upstream shape | What it is for | DevCD fit today |
| --- | --- | --- | --- |
| Skill | A directory containing `SKILL.md` with required single-line frontmatter keys `name` and `description`; optional `metadata.openclaw` gates such as required binaries or config. | Teaching the agent how and when to use existing tools, commands, or workflows. Skills can be published with `clawhub skill publish <path>`. | Possible later, but only as instructions around an already-configured MCP server. |
| ClawHub skill bundle | Versioned public skill bundle with `SKILL.md`, optional supporting files, semver versions, tags, changelogs, public content, and security scans. | Discoverable distribution for reusable skills. | Plausible first registry artifact after E2E validation. |
| Code plugin package | Native plugin package with `package.json#openclaw.extensions`, built JS runtime output for published installs, `openclaw.plugin.json`, and a JSON Schema config contract. Published with `clawhub package publish <source>`. | Extending OpenClaw with runtime capabilities: tools, channels, providers, hooks, services, setup/onboarding, or plugin-shipped skills. | No-Go today. DevCD already exposes MCP stdio and does not need OpenClaw in-process code. |
| Bundle plugin | Codex/Claude/Cursor-compatible bundle layout mapped into OpenClaw plugin features. | Importing another agent runtime's bundle/plugin ecosystem. | No-Go today. DevCD is not a Codex/Claude/Cursor bundle. |
| MCP config/use case | `mcp.servers.<name>` in `~/.openclaw/openclaw.json` with stdio `command` and `args`, for example `command: "devcd", args: ["mcp", "serve"]`. | Connecting OpenClaw to a local or remote MCP server without adding an OpenClaw plugin. | Best fit today. This is the current DevCD integration boundary. |

Primary upstream references:

- OpenClaw Skills: <https://docs.openclaw.ai/tools/skills>
- Creating Skills: <https://docs.openclaw.ai/tools/creating-skills>
- ClawHub: <https://docs.openclaw.ai/tools/clawhub>
- Plugins: <https://docs.openclaw.ai/tools/plugin>
- Plugin Manifest: <https://docs.openclaw.ai/plugins/manifest>
- MCP configuration: <https://docs.openclaw.ai/gateway/configuration-reference#mcp>
- OpenClaw Security: <https://docs.openclaw.ai/gateway/security>

## 1. Skill vs Package vs Plugin vs Use Case

### Use Case / MCP Config

Use case plus MCP config is the correct representation of DevCD today.

DevCD already has a standard stdio MCP server:

```json5
{
  mcp: {
    servers: {
      devcd: {
        command: "devcd",
        args: ["mcp", "serve"],
      },
    },
  },
}
```

This maps directly to OpenClaw's `mcp.servers` config. It does not require
OpenClaw-specific code, package installation, or plugin lifecycle hooks. It also
preserves DevCD's current product boundary: a local-first context daemon that can
serve any MCP-capable client.

### Skill

A DevCD Skill can be useful, but only as a thin operating guide. It should not
try to install DevCD, mutate `openclaw.json`, start background daemons without
operator intent, or promise that DevCD is an OpenClaw-native runtime component.

A correct first skill would tell an agent:

- check whether the user has configured the `devcd` MCP server;
- ask the operator to start `devcd run` if live daemon-backed context is needed;
- read `devcd://context/agent-handoff-packet` first for continuity;
- fall back to `devcd://context/brief`, `recent-timeline`, and `policy-summary`;
- respect withheld-context summaries and never ask for hidden payloads.

The skill may mention `devcd mcp serve`, but it should frame it as the stdio MCP
command OpenClaw launches from config, not as a shell command the agent should
run ad hoc during every task.

### ClawHub Package / Code Plugin

A code plugin is not the right first package. OpenClaw plugins execute
in-process with the gateway and are treated as trusted code. They require a
native plugin manifest, config schema, package metadata, runtime entrypoints, and
publication/installation validation. DevCD does not currently need to register
OpenClaw tools, channels, providers, hooks, services, setup flows, or a context
engine slot. The MCP client registry already provides the integration point.

Building a plugin now would add supply-chain and runtime trust surface without a
matching product need.

### Bundle Plugin

No. DevCD is not a Claude, Codex, or Cursor bundle. A bundle plugin would be a
misleading format unless DevCD later ships a real compatible bundle layout.

## 2. Minimal First Submission Path

The minimal first submission path is:

1. Finish and verify the MCP use case locally with a real OpenClaw gateway.
2. Keep the integration documentation in this repository.
3. If a public OpenClaw artifact is wanted, submit a small ClawHub Skill named
   something like `devcd-context` after the E2E test passes.

The Skill should contain no secrets, no bundled credentials, no remote endpoint,
and no install script that changes OpenClaw config automatically. It should be a
human-reviewable `SKILL.md` plus, at most, examples that show the MCP config
block.

Do not open a PR to awesome/community skill lists or publish to ClawHub until the
OpenClaw gateway has actually loaded the DevCD MCP resources successfully.

## 3. Required DevCD Artifacts Before Submission

DevCD already has:

- `devcd mcp serve` stdio server;
- read-only MCP resources;
- no MCP tools or prompts;
- an OpenClaw MCP draft example in `examples/openclaw-mcp-context/README.md`;
- machine-readable agent handoff packet contract;
- policy summaries and withheld-context summaries;
- repo validation through `make check`.

DevCD still needs these artifacts before public OpenClaw submission:

1. End-to-end OpenClaw verification note showing that OpenClaw can list/read the
   DevCD MCP resources from `mcp.servers.devcd`.
2. A minimal `skills/devcd-context/SKILL.md` draft if the project chooses the
   skill path.
3. A short security note in the Skill or docs: local-first, read-only MCP,
   no tools, no prompts, no write surface, no remote export by default.
4. A copy-paste config snippet that uses only `command: "devcd"` and
   `args: ["mcp", "serve"]`.
5. A troubleshooting note for the daemon requirement: `devcd mcp serve` can
   start without opening a network listener, but live context depends on the
   local DevCD event ledger and, for daemon-backed workflows, `devcd run`.
6. A release/install story for DevCD itself. Until PyPI or another install path
   exists, docs should say install from the local checkout and should not imply
   one-command OpenClaw install.

## 4. Allowed Claims

These claims are currently allowed, based on DevCD's checked-in code and docs:

- DevCD exposes a local stdio MCP server via `devcd mcp serve`.
- The MCP server exposes read-only resources only.
- The MCP server returns an empty MCP tools list and empty MCP prompts list.
- DevCD's OpenClaw integration path is standard OpenClaw `mcp.servers` stdio
  configuration.
- DevCD is local-first by default.
- DevCD policy denies remote export by default.
- DevCD policy denies actions by default.
- Sensitive or policy-denied context is represented as withheld-context metadata
  or safe summaries instead of raw hidden payloads.
- DevCD is not OpenClaw-specific; OpenClaw is one MCP-capable consumer.

## 5. Forbidden Claims For Now

These claims are not allowed yet:

- DevCD is an official OpenClaw plugin.
- DevCD is published on ClawHub.
- DevCD is available from `openclaw skills install ...`.
- DevCD is available from `openclaw plugins install ...`.
- The OpenClaw + DevCD integration has been fully tested end to end.
- OpenClaw agents automatically read DevCD context without a configured MCP
  server or a skill/instruction path.
- DevCD can start or manage the OpenClaw gateway.
- DevCD can mutate OpenClaw configuration.
- DevCD provides OpenClaw tools, channels, providers, hooks, services, or setup
  UI.
- DevCD guarantees secret detection or complete data-loss prevention. The
  correct claim is narrower: policy-filtered resources with withheld summaries
  and no intentional MCP write/tool surface.
- DevCD is multi-tenant or adversarial-user isolation for OpenClaw. Both systems
  should be described as local/trusted-operator tools unless configured and
  isolated otherwise.

## 6. Concrete Next Steps

1. Run an OpenClaw gateway with this local repo installed so `devcd` is on
   `PATH`.
2. Add the `mcp.servers.devcd` block to a test OpenClaw config.
3. Use OpenClaw's MCP inspection/listing flow to confirm the `devcd` server is
   visible and the resource list includes `devcd://context/agent-handoff-packet`.
4. Read `devcd://context/agent-handoff-packet` from OpenClaw and capture a
   sanitized transcript or command output for this repository's example docs.
5. Update `examples/openclaw-mcp-context/README.md` from draft to verified once
   the E2E run succeeds.
6. Draft a minimal `SKILL.md` for `devcd-context` that instructs agents to read
   the configured MCP resources and respect policy summaries.
7. Validate the skill locally in an OpenClaw workspace.
8. Only after that, consider `clawhub skill publish` for the Skill.

## Go / No-Go List

### Go Now

- Document DevCD as an OpenClaw MCP configuration use case.
- Keep the integration local-first and read-only.
- Use `mcp.servers.devcd.command = "devcd"` and `args = ["mcp", "serve"]`.
- Tell agents to prefer `devcd://context/agent-handoff-packet` for continuity.
- State clearly that denied context must remain denied.

### Go After E2E Verification

- Publish or propose a small ClawHub Skill that teaches DevCD MCP usage.
- Change the OpenClaw example status from draft to verified.
- Claim OpenClaw can read DevCD MCP resources in a tested setup.

### No-Go For Now

- Publishing a ClawHub code plugin/package.
- Shipping OpenClaw runtime entrypoints or `openclaw.plugin.json`.
- Adding OpenClaw-specific code to DevCD just to package an integration that
  MCP already supports.
- Auto-editing `~/.openclaw/openclaw.json` from DevCD or from a skill.
- Claiming official OpenClaw endorsement or ClawHub availability.

## Security Notes

The recommended path preserves both projects' safety model:

- DevCD remains local-first; no remote export is introduced.
- `devcd mcp serve` uses stdio and does not open a network listener.
- The MCP surface is resources-only; it exposes no tools, prompts, shell access,
  browser automation, memory writes, or OpenClaw config writes.
- OpenClaw should treat any future skill as trusted operator-editable content;
  keep it small and reviewable.
- OpenClaw should treat any future plugin as trusted in-process gateway code;
  avoid that route until DevCD needs real OpenClaw runtime capabilities.
- No Skill or package should contain API keys, bearer tokens, local `.devcd/token`
  contents, `.openclaw` secrets, transcripts, or private event payloads.

## Final Recommendation

Submit DevCD first as an MCP configuration/use-case integration, not as a code
plugin. The first public registry artifact, if any, should be a small OpenClaw
Skill that explains how to consume the already-configured DevCD MCP resources.
A ClawHub code plugin/package is a later option only if DevCD needs to register
OpenClaw-native runtime capabilities that standard MCP cannot provide.