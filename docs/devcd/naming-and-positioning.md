# Naming and Positioning

DevCD is the current working name. It remains useful for the codebase and CLI
while the product is still pre-alpha, but it frames the project too narrowly as a
developer-only daemon.

The broader product promise is not developer context. It is continuity for
people who use AI agents:

> Stop re-explaining yourself when an agent session, tool, or workflow loses
> context.

## Product Principle

Onboarding is the product. It should be organized around real user frustrations,
not around the feature list.

The first-run experience should relieve these frustrations before it explains
architecture:

- My agent lost context and I do not want to recap everything.
- The next agent repeats a fix that already failed.
- I do not remember exactly where we stopped.
- I want useful continuity without exposing sensitive local data.
- Every agent tool has its own memory; I need a local continuity layer between
  them.
- I do not trust automation unless I can inspect what it saw, withheld, and
  decided.

## Naming Criteria

A future product name should be broader than developer workflows and less
infrastructure-shaped than "daemon". It should suggest at least one of these:

- continuity across interrupted work;
- handoff between agents or sessions;
- a private local memory boundary;
- a thread of intent that survives tool switches.

For now, do not rename packages, CLI commands, schema IDs, config paths, MCP
resource URIs, or repository URLs without a separate migration plan.

## Collision Check Snapshot

This is a practical availability snapshot from GitHub repository search, npm,
and PyPI JSON checks on 2026-05-05. It is not a trademark search and does not
prove legal availability.

| Candidate | Result | Notes |
| --- | --- | --- |
| Relay | Avoid | Heavy GitHub/npm/PyPI collisions, including Facebook Relay and agent-relay projects. |
| Continuity | Avoid | Broadly used on GitHub, npm, and PyPI; also overlaps Apple Continuity language. |
| Threadline | Avoid | npm package exists and GitHub has a local-first AI-agent memory project named `threadline`. |
| Throughline | Avoid | npm exists and multiple GitHub projects use it for AI memory/session continuity. |
| AgentRelay | Avoid | GitHub has multiple `AgentRelay` projects, including agent collaboration and context-switching tools; PyPI `agentrelay` exists. |
| AgentHandoff | Avoid | GitHub, npm, and PyPI all have direct agent-handoff collisions. |
| LocalRecall | Avoid | Strong GitHub collision: `mudler/LocalRecall`, a local memory layer for agents. |
| Mnemo / Memento | Avoid | npm and PyPI packages exist; product category can read as generic memory app. |
| AgentThread | Weak | npm/PyPI looked open, but GitHub has `agentthread` and related agent-thread projects. |
| Passalong | Possible but weak | npm/PyPI looked open; GitHub has small collisions. The name is friendly but less premium. |
| Workthread | Possible but narrow | npm/PyPI looked open; GitHub collisions are low-signal. Still sounds developer/workflow-specific. |
| Redthread | Possible | npm/PyPI looked open and GitHub collisions are low-signal. Meaning may be less obvious in English. |
| Goldenthread / Golden Thread | Possible | npm/PyPI looked open; GitHub has some low-signal collisions. Strong metaphor, but may sound abstract. |

## Current Recommendation

Keep DevCD as the implementation name for now. In public-facing copy, treat it as
a working name and position the product as:

> A local-first continuity layer for people who use AI agents.

The strongest next naming direction is not a direct descriptor like
`AgentRelay`; those collide with existing projects and keep the brand inside the
agent tooling niche. Explore names around a human thread of work instead:

- Golden Thread
- Redthread
- Passalong
- new coined names around continuity, handoff, and private recall

Any final rename should be handled as a dedicated migration with explicit changes
to package names, CLI binary, config paths, docs URLs, schemas, MCP resources,
and compatibility aliases.