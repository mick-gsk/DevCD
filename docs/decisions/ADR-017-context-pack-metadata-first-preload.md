---
id: ADR-017
status: proposed
date: 2026-05-07
supersedes: null
---

# Metadata-First Context Pack Preload For Continuity Packets

## Context

ADR-008 introduces Context Packs as the mechanism to broaden DevCD continuity beyond
Developer Context. The current continuity packet flow still centers on a single
selected `context_pack` and does not provide a metadata-first catalog of all
installed packs in packet headers.

This creates a startup-orientation gap for agents: they do not receive a compact,
policy-safe signal about available packs before consuming pack-specific continuity
content.

DevCD needs a tiered loading strategy consistent with local-first and policy-safe
contracts:

- pre-load minimal pack metadata for orientation,
- load full pack-specific continuity content only for the selected pack.

## Decision

Continuity Packet generation MUST use a two-tier Context Pack strategy.

Tier 1 (always included in Continuity Packet header):

- list all installed packs with metadata-only fields:
  - `id`
  - `display_name`
  - `description` (one line)

Tier 2 (pack-specific body content):

- continue rendering full pack-specific continuity content only for the explicitly
  selected `context_pack`.
- no automatic context-pack switching or intent-keyword heuristics are introduced
  by this decision.

Contract behavior:

- additive/backward-compatible packet extension only,
- existing `context_pack` selection input remains authoritative,
- existing MCP resource URIs remain unchanged,
- policy filtering and local-first defaults remain unchanged.

## Non-Goals

- Do not add automatic pack matching from goal, intent, or keywords.
- Do not add new MCP resource URIs for pack catalogs.
- Do not add remote connectors, export, telemetry, or sync.
- Do not change default pack selection behavior for existing MCP/CLI paths.

## Alternatives Considered

1. Keep current single-pack output only.
   - Rejected: agents miss startup visibility into available pack choices.
2. Auto-select pack from intent/surface heuristics.
   - Rejected for now: higher behavioral risk and hidden switching.
3. Metadata-first preload plus explicit pack selection.
   - Accepted: low risk, additive contract, clear control plane.

## Consequences

Agents get a deterministic, low-token startup header showing available Context Packs
without loading all pack bodies.

The ambient context slice remains owner of pack registry and packet assembly.
MCP remains read-only and contract-compatible while exposing the additive header
field through existing continuity resources.

Future heuristic or policy-driven pack routing, if needed, requires a separate ADR.

## Validation

Implementation must verify:

- continuity packet includes metadata-only list of installed packs;
- pack-specific enrichments remain scoped to selected `context_pack`;
- MCP `continuity-packet` (and concise variant) exposes the metadata-first list;
- continuity schema remains backward-compatible with additive field;
- existing policy-safe withheld-context behavior remains unchanged.

Run:

```bash
python -m pytest tests/test_ambient_context.py -q
python -m pytest tests/test_mcp_server.py -q
python -m pytest tests/test_cli.py -q
make check
```

## Related

- docs/decisions/ADR-008-agent-continuity-layer-and-context-packs.md
- packages/devcd-core/src/devcd/slices/ambient_context/models.py
- packages/devcd-core/src/devcd/slices/ambient_context/service.py
- packages/devcd-core/src/devcd/slices/mcp_server/service.py
- schemas/devcd-continuity-packet.schema.json
