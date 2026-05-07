---
id: ADR-019
status: proposed
date: 2026-05-07
supersedes: null
---

# Workflow Orchestration, Catalog Trust Boundary, and Instruction Layering

## Context

Analysis of spec-kit (github/spec-kit) identified three high-leverage patterns that address
known gaps in DevCD's local-first agent continuity:

1. **Resumable workflow orchestration with human gates** — DevCD currently captures continuity
   metadata and exposes action packets, but has no way to define, execute, or resume a
   structured multi-step workflow. Agents lose track of partially completed plans across
   sessions.

2. **Trust-bounded catalog stack** — DevCD ships built-in skills and templates, but has no
   principled resolution order when workspace, user, or community sources provide competing
   definitions. Discovery and installation are conflated.

3. **Priority-based instruction layering** — The current managed-block injection writes a
   single DevCD block into agent instruction files. There is no contract for how workspace
   overrides, team/org presets, or DevCD-managed content compose or supersede one another.

All three patterns must respect DevCD's local-first privacy defaults, the observation-allowed
/ mutation-denied policy baseline, and the existing continuity packet / action packet
contracts.

## Decision

### 1. Workflow Layer Slice

DevCD will add a new vertical slice `workflow_layer` under
`packages/devcd-core/src/devcd/slices/workflow_layer/`.

**Models** (`models.py`):

- `WorkflowDefinition` — Pydantic model parsed from a YAML workflow file. Fields: `name`,
  `description`, `version`, `steps: list[StepDefinition]`.
- `StepDefinition` — discriminated union by `type`: `command | shell | gate`.
- `RunState` — Pydantic model persisted to `.devcd/workflows/runs/<run_id>/state.json`.
  Fields: `run_id`, `workflow_name`, `status: RunStatus`, `current_step_index`,
  `step_results: list[StepResult]`, `started_at`, `updated_at`.
- `RunStatus` — enum: `running | paused | completed | failed | aborted`.
- `StepResult` — `step_index`, `step_type`, `status`, `output`, `error`, `started_at`,
  `ended_at`.

**Engine** (`engine.py`):

- `WorkflowEngine.execute(definition, run_id)` — starts or resumes execution. Persists
  `RunState` after every step via `_save_run_state()`. Returns when the workflow completes,
  fails, or pauses at a gate.
- `WorkflowEngine.resume(run_id)` — loads persisted `RunState`, rehydrates the definition
  from the run directory snapshot, resumes from `current_step_index`.
- On `gate` step: sets `RunStatus.PAUSED`, writes state, returns control to caller.
- On `command`/`shell` step: executes via subprocess with a configurable timeout; captures
  stdout/stderr; marks step failed on non-zero exit.
- Policy gate: before executing any step, engine calls
  `PolicyEngine.decide_workflow_step_execute(step)`. If denied, step is marked `aborted`
  and run halts.

**Run directory layout** (`.devcd/workflows/runs/<run_id>/`):

```
state.json          # RunState model, updated after each step
workflow.yaml       # snapshot of workflow definition at run start
```

**Step types (v1)**:

| Type      | Behaviour                                                         |
|-----------|-------------------------------------------------------------------|
| `command` | Runs a named built-in command (e.g. `devcd capture`) via API     |
| `shell`   | Runs an arbitrary shell string; requires explicit policy permit   |
| `gate`    | Pauses execution; resumes require explicit `devcd workflow resume`|

Out of scope for v1: `if`, `switch`, `while`, `do-while`, `fan-out`, `fan-in`, `prompt`.

### 2. Catalog Stack

DevCD will add a `WorkflowCatalog` with a trust-ordered resolution stack:

```
env (DEVCD_WORKFLOW_CATALOG_URL)
→ project  (.devcd/catalog.yaml)
→ user     (~/.devcd/catalog.yaml)
→ built-in (shipped with devcd-core)
```

**Trust rules**:

- Remote catalog URLs MUST use `https://` (localhost exception for developer testing only).
- Community / remote catalogs resolve to `install_allowed: False` by default. Agents can
  discover workflow definitions but cannot install them without an explicit policy permit.
- Conflict resolution: higher-priority source wins; provenance is recorded in resolved
  definition metadata.

**`WorkflowCatalog` responsibilities** (`catalog.py`):

- `resolve(name)` → `WorkflowDefinition | None` with provenance metadata.
- `list_available()` → list of `(name, source_tier, install_allowed)`.
- `validate_source(url)` → raises `CatalogTrustError` for non-HTTPS non-localhost URLs.

### 3. Layered Instruction Resolver

DevCD will add an `InstructionLayerResolver` that composes agent instruction content from
multiple ordered sources:

**Layer priority (highest → lowest)**:

```
workspace override  (.devcd/instructions/<target>.md)
team/org preset     (.devcd/presets/<preset>.md)
DevCD managed core  (built-in block content)
```

**Composition strategies** (v1):

- `replace` — higher-priority layer replaces the lower entirely.
- `wrap` — higher-priority layer wraps lower with header/footer markers.

**Contract**:

- `InstructionLayerResolver.resolve(target)` returns a single composed string that is
  deterministic regardless of installation order.
- The resolver records provenance per layer so `devcd context control` can surface which
  layers contributed to the current instruction content.
- `upsert_managed_agent_block()` in `agent_layer_service.py` remains the write surface;
  the resolver only produces content — it does not write files.

**Out of scope for v1**: `prepend`/`append` strategies, automatic AGENTS.md / CLAUDE.md
orchestration.

### 4. Policy Integration

`PolicyEngine` will gain three new decision methods:

- `decide_workflow_step_execute(step: StepDefinition)` — allows `command`/`gate` by default;
  denies `shell` unless explicitly permitted by workspace policy.
- `decide_catalog_install(source_tier, install_allowed)` — denies install for community
  sources unless `install_allowed=True` in catalog metadata.
- `decide_instruction_layer_write(target, layer_source)` — allows managed-core writes;
  denies workspace-override writes that target files outside `.devcd/` and `.github/`.

### 5. CLI Surface

New `devcd workflow` sub-app:

```
devcd workflow run <path-or-name>   # start or resume by name/path
devcd workflow status [run_id]      # show RunState summary
devcd workflow resume <run_id>      # resume a PAUSED run
devcd workflow info <path-or-name>  # describe workflow without executing
```

Output format is Action-Packet-compatible (structured JSON for `--json`, human-readable by
default).

### 6. MCP Surface (additive, read-only)

Add two new read-only MCP resource URIs:

- `devcd://workflow/runs` — list of recent run summaries.
- `devcd://workflow/runs/{run_id}` — full `RunState` for a specific run.

`tools/list` and `prompts/list` remain empty. No write surfaces are introduced.

## Non-Goals

- No fan-out / fan-in or while / do-while step types in v1.
- No remote catalog installs without explicit policy permit.
- No automatic mutation hooks; agents must invoke captures explicitly.
- No new telemetry, sync, or remote export surfaces.
- No parity injection into AGENTS.md / CLAUDE.md by the resolver in v1.
- No breaking changes to existing `devcd setup`, `onboard`, `context`, or `agentic` commands.

## Alternatives Considered

1. **Re-use spec-kit directly as a dependency** — Rejected: spec-kit is an application, not a
   library. Importing it would pull in uncontrolled surface area and conflict with DevCD's
   local-first, policy-explicit boundaries.

2. **Single monolithic workflow runner without catalog** — Deferred: works for v1 workflow
   execution but misses the trust-boundary goal; catalog is additive and can be phased in
   after the slice MVP.

3. **Instruction layering via AGENTS.md/CLAUDE.md orchestration** — Deferred to a follow-up
   ADR: broader contract risk, requires careful migration path for repo owners who already
   customise these files.

4. **MCP write surface for workflow triggers** — Rejected: violates the read-only MCP
   product boundary established in ADR-003.

## Consequences

- A new vertical slice `workflow_layer` is added. Slice owns models, engine, catalog, and
  tests. It does not depend on other slices except `policy_layer`.
- `policy_layer` gains three new decision methods; existing decisions remain unchanged.
- `agent_layer_service` gains the `InstructionLayerResolver` as a collaborator for content
  production; write responsibility stays with existing `upsert_managed_agent_block`.
- `.devcd/workflows/runs/` becomes a new local state directory. Operators must include it
  in backup / gitignore guidance.
- MCP resource list grows by two URIs; existing URI contracts are unchanged.
- CLI gains `devcd workflow` sub-app; all other commands remain backward-compatible.

## Validation

Implementation must verify:

- `WorkflowEngine` completes a two-step (command + gate) workflow, pauses at gate, persists
  `RunState`, and resumes correctly from persisted state.
- `WorkflowEngine` denies a `shell` step when `PolicyEngine` returns deny.
- `WorkflowCatalog` raises `CatalogTrustError` for non-HTTPS non-localhost URLs.
- `WorkflowCatalog` returns `install_allowed=False` for community-tier sources by default.
- `InstructionLayerResolver.resolve()` returns the same composed string regardless of
  layer insertion order.
- `devcd workflow run / status / resume / info` commands function correctly for
  happy-path and gate-pause scenarios.
- MCP `devcd://workflow/runs` resource returns current run summaries; tools/prompts empty.
- `make check` passes with no new failures.

Run:

```bash
python -m pytest tests/test_workflow_layer.py -q
python -m pytest tests/test_policy_layer.py -q
python -m pytest tests/test_cli.py -q
python -m pytest tests/test_mcp_server.py -q
make check
```

## Related

- docs/decisions/ADR-001-vertical-slice-architecture.md
- docs/decisions/ADR-003-read-only-mcp-context-server.md
- docs/decisions/ADR-005-policy-explainability-cli.md
- docs/decisions/ADR-007-agent-continuity-golden-path-contract.md
- docs/decisions/ADR-009-agent-ready-init.md
- packages/devcd-core/src/devcd/slices/policy_layer/service.py
- packages/devcd-core/src/devcd/slices/ambient_context/agent_layer_service.py
- specs/003-agent-vision-layer/plan.md
