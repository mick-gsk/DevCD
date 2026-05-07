---
id: ADR-018
status: proposed
date: 2026-05-07
supersedes: null
---

# Vision Delivery Contract For Action Packet And Copilot Instructions

## Context

DevCD already models `vision` on Action Packet and Continuity Packet contracts, and the
workspace setup flow already injects a managed DevCD continuity block into standard agent
instruction files.

However, current behavior does not guarantee that Action Packet `vision` is present when an
active goal exists, and does not inject a dedicated product-intent section into Copilot
workspace instructions during setup/onboard/handoff.

This creates a continuity risk: agents can optimize for locally correct next steps while
drifting from product goals, especially in cold-start sessions.

## Decision

DevCD will add an explicit vision-delivery contract with three additive guarantees.

1. Action Packet vision baseline
- When an Action Packet has an active goal, DevCD MUST attempt to populate `ActionPacket.vision`.
- Vision source priority is:
  - persisted workspace vision record (`devcd vision` runtime record), then
  - local fallback derived from workspace `VISION.md`.
- If no VisionBlock can be produced, DevCD MUST produce an explainable warning cause
  downstream in context-control reporting.

2. Copilot Product intent injection
- DevCD MUST inject a `Product intent` section inside the managed DevCD block of the Copilot
  workspace instruction file (`.github/copilot-instructions.md`) during:
  - `devcd setup`/onboard flows that write agent-ready workspace files,
  - `devcd handoff`.
- If the file does not exist at handoff time, DevCD creates it and writes the managed block.
- The injected section must be policy-safe and include:
  - product domain,
  - north-star statement,
  - provenance note (persisted vision record vs fallback derivation).

3. Context control warning transparency
- `devcd context control` MUST surface a clear warning when an active goal exists and no
  VisionBlock is available.
- Warning causes are explicit and additive:
  - vision_not_configured,
  - vision_withheld_by_policy,
  - vision_derivation_failed.

## Non-Goals

- Do not make missing vision a hard blocker for `ready_for_agent`.
- Do not mutate global or external agent configuration.
- Do not add remote export, telemetry, or write-capable MCP surfaces.
- Do not require parity injection into non-Copilot files (`CLAUDE.md`, `AGENTS.md`) in this ADR.

## Alternatives Considered

1. Keep vision optional and rely only on Action Packet consumers.
- Rejected: does not guarantee startup-time product intent as a system-level constraint.

2. Require explicit `devcd vision init` and never fallback to `VISION.md`.
- Rejected: too brittle for existing repositories with a project vision doc but no runtime record.

3. Inject product intent into all agent instruction files equally.
- Deferred: broader behavior contract and migration risk; this ADR scopes to Copilot only.

## Consequences

- Agent startup behavior becomes more aligned with product intent in cold starts.
- Instruction-file writing paths must stay contract-consistent across setup/onboard and handoff.
- Context control gains additional diagnostics that improve operator trust and explainability.

## Validation

Implementation must verify:

- Action Packet includes vision when active goal exists and at least one source is available.
- Copilot instruction managed block includes `Product intent` during setup/onboard and handoff.
- Handoff creates the Copilot instruction file when absent and still writes managed content.
- Context control text and JSON surfaces emit additive vision warning causes when appropriate.
- Existing behavior remains backward-compatible for current CLI/API/MCP consumers.

Run:

```bash
python -m pytest tests/test_agentic_context.py -q
python -m pytest tests/test_cli.py -q
python -m pytest tests/test_api.py -q
make check
```

## Related

- docs/decisions/ADR-009-agent-ready-init.md
- packages/devcd-core/src/devcd/slices/agentic_context/models.py
- packages/devcd-core/src/devcd/slices/agentic_context/service.py
- packages/devcd-core/src/devcd/slices/ambient_context/models.py
- packages/devcd-core/src/devcd/slices/ambient_context/service.py
- packages/devcd-core/src/devcd/cli.py
