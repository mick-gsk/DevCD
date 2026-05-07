---
id: ADR-016
status: proposed
date: 2026-05-07
supersedes: null
---

# Typed Do-Not-Repeat Entries With Rationale

## Context

DevCD currently exposes `do_not_repeat` as a list of strings in continuity and
action-packet surfaces. That tells an agent what to avoid, but not why. Without
explicit rationale, a follow-up agent can relitigate or retry rejected paths.

The handoff contract is a public compatibility surface across CLI, MCP, schema,
fixtures, and docs. The change must stay local-first, metadata-only, and
policy-visible.

## Decision

Replace string-only `do_not_repeat` entries with a typed object:

- `path: str` (what to avoid)
- `rationale: str | None` (why it was rejected)

The owning continuity slice defines and normalizes this type. Agentic action
packets reuse the same type.

Compatibility rule:

- Input: keep backward compatibility by accepting legacy string entries and
  coercing them to `{ "path": <legacy_string>, "rationale": null }`.
- Output: emit only typed object entries for public surfaces after this change.

Versioning rule:

- Bump `ActionPacket.schema_version` from `1.0` to `1.1` because the typed
  `do_not_repeat` field is part of that contract.
- Do not perform a repo-wide schema-version unification in this change.

CLI capture rule:

- Add `--rationale` to `devcd capture` and `devcd handoff`.
- `--rationale` is valid only when capturing failure metadata, so rationale is
  tied to failure-derived stale-attempt guidance.

## Non-Goals

- Do not add a generic decision-history subsystem.
- Do not add remote export, telemetry, or MCP write capabilities.
- Do not change local-first policy defaults.
- Do not perform broad schema-version cleanup outside the Action Packet target.

## Consequences

Agents get stronger continuity semantics: they can distinguish a rejected path
from the policy-visible reason for rejection.

Public handoff schema and fixtures must update in lockstep with CLI/MCP output.
Legacy event payloads remain consumable through input coercion.

## Validation

Implementation must verify:

- continuity models accept legacy string `do_not_repeat` input and normalize it;
- action packets emit typed entries and use schema version `1.1`;
- `devcd capture` and `devcd handoff` accept `--rationale` for failures and
  reject invalid usage;
- handoff JSON schema and fixture match typed entry output;
- MCP handoff and action packet surfaces reflect typed entries.

Run:

```bash
python -m pytest tests/test_ambient_context.py -q
python -m pytest tests/test_agentic_context.py -q
python -m pytest tests/test_cli.py -q
python -m pytest tests/test_mcp_server.py -q
make check
```