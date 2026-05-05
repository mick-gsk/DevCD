# Security Policy

DevCD is a local-first continuity layer for AI-agent workflows. It can process
developer context, work metadata, local memory, and policy decisions, so privacy
and local trust boundaries are core product behavior.

The short version: DevCD should help agents continue work without turning local
developer context into raw, unbounded, or remote data by default.

## Supported Versions

DevCD is pre-alpha. No stable public release exists yet.

| Version | Status | Security support |
| --- | --- | --- |
| `0.1.x` | Unreleased / pre-alpha | Security fixes target this line until the first public alpha release. |

Security support currently means best-effort maintainer response, focused fixes,
tests for the affected trust boundary, and clear changelog entries once public
releases begin.

## Security Defaults

- Local storage only by default.
- Loopback API by default.
- No telemetry.
- No remote export by default.
- Observations are allowed by default only when the event source and data class
  are policy-visible.
- Actions are denied by default.
- Sensitive events are denied or withheld by the default policy.
- MCP resources are read-only by default.
- Policy reasoning must be available for every accepted observation, storage
  decision, export, or action.

## Data Classes

DevCD treats different context categories differently. These categories are the
first security boundary users and contributors should think about.

| Data class | Examples | Default handling |
| --- | --- | --- |
| Metadata | Goal summaries, artifact paths, task names, event kinds, timestamps | May be observed and stored locally when policy allows. |
| Derived context | Continuity Packet, Agent Passport, Action Packet, withheld-context summaries | May be rendered locally when policy allows. |
| Raw content | File contents, full logs, full notes, full transcripts, raw browser content | Not accepted by default for continuity capture; should be withheld or summarized. |
| Secrets | Tokens, passwords, credentials, private keys, secret-bearing env vars | Denied by default and must not be written to the local ledger. |
| Remote export | Any context sent off machine | Disabled by default; requires explicit future policy, docs, and tests. |
| Action | Mutations, process starts, write-capable integrations, remote calls | Denied by default unless explicitly configured and policy-explained. |

## Threat Model

DevCD's primary risks come from local context crossing the wrong boundary or
from an agent treating untrusted context as instructions.

Primary risks:

- raw code, private notes, logs, chat text, or secrets are captured by mistake;
- prompt injection appears inside observed files, tool output, notes, or test logs;
- an agent treats withheld-context summaries as permission to request raw denied
  data;
- local MCP consumers read more context than intended;
- a feature expands observation into mutation without an explicit policy decision;
- future remote export or runner integrations bypass policy decisions.

Primary controls:

- structured events instead of raw transcript capture;
- local JSON Lines ledger;
- policy decisions for observation, storage, context export, and actions;
- safe withheld-context summaries instead of raw denied payloads;
- read-only MCP resource exposure;
- deny-by-default action posture;
- explicit configuration for any future remote or runner behavior.

### Local Ledger And Memory

The local event ledger and memory store may contain sensitive metadata about a
workspace. DevCD must avoid persisting raw contents, secrets, raw logs, or full
chat text unless a future policy explicitly permits a narrower data class.

Expected controls:

- store structured metadata rather than raw text;
- route accepted events through policy decisions;
- keep memory local by default;
- expose withheld-context summaries instead of denied raw payloads.

### Loopback API

The HTTP API is intended for local use. It should bind to loopback by default and
require the local bearer token for protected routes. API additions must preserve
the token boundary and must not add unauthenticated state-changing routes.

### MCP Consumers

MCP is a read-only context surface in the current product. DevCD must not expose
write-capable MCP tools, shell execution, browser automation, remote export, or
memory mutation through MCP without a separate policy decision and design record.

### Agent Shell Access

Agents with shell access can run `devcd capture` to record continuity metadata.
That command must stay metadata-only, policy-gated, and local. Agents without
shell access should read DevCD context only and must not claim they captured
continuity.

### Prompt Injection In Observed Context

Observed files, notes, test output, logs, and tool output can contain malicious
instructions. DevCD context consumers should treat observed content as data, not
as instructions. Generated agent guidance must explicitly tell agents not to obey
instructions found inside observed file, test, or tool output.

## Vulnerability Examples

Please report issues such as:

- raw file contents or logs being stored through a metadata-only path;
- secrets accepted into the ledger, memory, MCP output, or API response;
- policy-denied data appearing in a Continuity Packet, Agent Passport, Action
  Packet, context brief, or MCP resource;
- unauthenticated access to protected local API routes;
- remote export occurring without explicit user configuration;
- write-capable MCP tools or prompts being exposed unexpectedly;
- local runner or agentic context features starting arbitrary shell commands;
- policy decisions missing from state-changing operations;
- prompt-injection text being promoted into agent instructions.

## Reporting A Vulnerability

Please report suspected vulnerabilities privately to the maintainer instead of
opening a public issue.

Include:

- affected version or commit;
- affected command, API route, MCP resource, or file path;
- affected data class;
- reproduction steps;
- whether local files, local memory, MCP output, remote export, or action policy
  was involved;
- whether secrets or private user data may have been exposed.

Do not include real secrets, private keys, production tokens, or private user
data in the report. Use redacted examples where possible.

## Maintainer Response

For pre-alpha releases, the maintainer will aim to:

- acknowledge valid reports as soon as practical;
- reproduce the issue locally;
- add or update a focused regression test for the affected trust boundary;
- fix the issue in the smallest safe change;
- document the fix in the changelog when public releases begin.

## Contributor Requirements

Security-sensitive changes must preserve DevCD's local-first defaults:

- no remote export without explicit policy, documentation, and tests;
- no state-changing operation without explainable policy reasoning;
- no raw content capture through metadata-only commands;
- no write-capable MCP surface in the current MVP;
- no arbitrary shell execution from API or MCP input;
- no global external agent configuration mutation without an explicit opt-in
  design.
