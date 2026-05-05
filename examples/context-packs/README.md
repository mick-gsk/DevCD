# Context Pack Examples

This directory shows the current extension pattern for DevCD Context Packs.

Context Packs are metadata rendering contracts, not executable plugins. They are
extended by adding local event recipes, fixtures, tests, and pack declarations in
the relevant slice.

## Inspect Built-In Packs

```bash
devcd context packs
devcd context packs --json
```

## Developer Pack

The developer pack is the default coding-agent continuity path:

```bash
devcd context passport --pack developer
```

It expects metadata such as goals, Git branch changes, artifact references,
failed attempts, test failures, blockers, and suggested next actions.

## Research Pack

The research pack demonstrates a non-developer workflow without adding remote
connectors:

```bash
devcd recipe research-session \
  --input examples/event-source-recipes/research-session/input.json \
  --output research-events.jsonl

devcd context handoff-demo \
  --events research-events.jsonl \
  --surface research-agent \
  --pack research
```

The input includes synthetic raw text fields so policy withholding can be tested.
Those raw fields must not appear in the rendered Continuity Packet.

## Adding A Pack

Before adding a new built-in pack:

1. Add a local recipe or metadata event fixture.
2. Add tests for event normalization and policy withholding.
3. Add or update the Context Pack declaration.
4. Add a reproducible example under `examples/`.
5. Run `make check` and `mkdocs build --strict`.

Do not add remote scraping, connector credentials, arbitrary command execution,
or write-capable MCP tools as part of a pack.
