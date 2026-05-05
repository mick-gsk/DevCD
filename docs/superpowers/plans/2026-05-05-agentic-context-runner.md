# Agentic Context Runner Implementation Plan

> **For agentic workers:** Use subagent-driven-development to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local, policy-gated Agentic Context Runner MVP that can create Scout Tasks, optionally start allowlisted local scout processes, validate Scout Reports, and produce an Action Packet for the next agent run.

**Architecture:** Add a new `agentic_context` vertical slice that consumes ambient context and policy services. Keep runner execution local, opt-in, allowlisted, output-limited, and metadata-only. The primary product output is an Action Packet; MCP remains read-only and runner starts are denied by default.

**Tech Stack:** Python 3.11+, Pydantic v2, FastAPI, pytest + pytest-asyncio

---

### Task 1: Architectural Record And Design Gate

**Files:**
- Create: `docs/decisions/ADR-011-local-agentic-context-runner.md`
- Create: `docs/superpowers/specs/2026-05-05-agentic-context-runner-design.md`
- Create: `docs/superpowers/plans/2026-05-05-agentic-context-runner.md`

- [ ] **Step 1: Write the proposed ADR**

Record that DevCD may start local scout runners in the MVP only through
configured command templates, with policy decisions for runner start and output
storage. Keep the ADR status as `proposed`.

- [ ] **Step 2: Write the design spec**

Document product flow, slice boundaries, public models, policy rules, settings,
API, CLI, MCP non-goals, and testing strategy.

- [ ] **Step 3: Self-review the docs**

Check for placeholder text, unclear ownership, contradictions with local-first
defaults, or any claim that DevCD can run arbitrary commands.

- [ ] **Step 4: Verify docs build**

Run:

```bash
python -m mkdocs build --strict
```

Expected: PASS. If `site/` changes, leave generated site artifacts out of the
source diff unless the task explicitly updates published static output.

### Task 2: Agentic Context Models

**Files:**
- Create: `packages/devcd-core/src/devcd/slices/agentic_context/__init__.py`
- Create: `packages/devcd-core/src/devcd/slices/agentic_context/models.py`
- Create: `tests/test_agentic_context.py`

- [ ] **Step 1: Write failing model tests**

Add tests for bounded Scout Tasks, evidence-required Scout Reports, safe Runner
Command Templates, and Action Packet defaults.

<pre><code>
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from devcd.slices.agentic_context.models import (
    ActionPacket,
    RunnerCommandTemplate,
    ScoutEvidence,
    ScoutReport,
    ScoutTask,
    ScoutTaskKind,
)


def test_scout_task_defaults_to_metadata_only_context() -> None:
    task = ScoutTask(
        kind=ScoutTaskKind.IDENTIFY_CURRENT_GOAL,
        prompt="Find the active goal from visible local metadata.",
        surface="coding-agent",
        context_pack="developer",
        expected_evidence=["devcd_continuity"],
        policy_decision_id="policy-1",
    )

    assert task.schema_version == "1.0"
    assert task.data_class == "metadata"
    assert task.expires_at > task.created_at


def test_scout_report_requires_evidence() -> None:
    with pytest.raises(ValueError):
        ScoutReport(
            task_id="task-1",
            summary="Current goal is unclear.",
            confidence=0.4,
            evidence=[],
        )


def test_runner_template_rejects_shell_metacharacters() -> None:
    with pytest.raises(ValueError):
        RunnerCommandTemplate(
            id="unsafe",
            command="powershell",
            args=["-c", "echo ok; Remove-Item important"],
        )


def test_action_packet_is_ready_when_goal_and_next_action_exist() -> None:
    packet = ActionPacket(
        current_goal="Ship the agentic context runner MVP",
        next_action="Write the failing model tests",
        recommended_agent_mode="implementation",
        evidence=[
            ScoutEvidence(
                source="devcd",
                summary="Continuity packet identified the implementation task.",
                timestamp=datetime(2026, 5, 5, 12, 0, tzinfo=UTC),
                policy_reason="metadata-only local context is allowed",
            )
        ],
    )

    assert packet.ready_for_agent is True
</code></pre>

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_agentic_context.py::test_scout_task_defaults_to_metadata_only_context tests/test_agentic_context.py::test_scout_report_requires_evidence tests/test_agentic_context.py::test_runner_template_rejects_shell_metacharacters tests/test_agentic_context.py::test_action_packet_is_ready_when_goal_and_next_action_exist -q
```

Expected: FAIL because `devcd.slices.agentic_context` does not exist.

- [ ] **Step 3: Implement minimal models**

Create Pydantic v2 models with enums, validators, bounded fields, evidence, and
metadata-only defaults.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm the tests pass.

### Task 3: Settings And Policy Gates

**Files:**
- Modify: `packages/devcd-core/src/devcd/kernel/settings.py`
- Modify: `packages/devcd-core/src/devcd/slices/policy_layer/service.py`
- Modify: `tests/test_policy_layer.py`

- [ ] **Step 1: Write failing policy tests**

Add tests for default denial, allowlisted runner approval, unknown runner denial,
and output storage denial for non-metadata content.

<pre><code>
from devcd.kernel.settings import DevCDSettings
from devcd.slices.policy_layer.service import PolicyEngine


def test_agentic_runner_start_is_denied_by_default() -> None:
    engine = PolicyEngine.default()

    decision = engine.decide_agentic_runner_start("local-scout", "identify_current_goal")

    assert decision.allowed is False
    assert decision.operation == "agentic_runner_start"


def test_agentic_runner_start_allows_configured_runner() -> None:
    settings = DevCDSettings(
        allow_agentic_context_runs=True,
        agentic_context_runners=[
            {"id": "local-scout", "command": "python", "args": ["scout.py"], "enabled": True}
        ],
    )
    engine = PolicyEngine.from_settings(settings)

    decision = engine.decide_agentic_runner_start("local-scout", "identify_current_goal")

    assert decision.allowed is True
    assert "local scout runner" in decision.reason
</code></pre>

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_policy_layer.py::test_agentic_runner_start_is_denied_by_default tests/test_policy_layer.py::test_agentic_runner_start_allows_configured_runner -q
```

Expected: FAIL because the settings and policy methods do not exist.

- [ ] **Step 3: Implement settings and policy**

Add conservative settings to `DevCDSettings`, expose them through
`to_config_dict()`, pass runner configuration into `PolicyEngine`, and implement
`decide_agentic_runner_start()` plus `decide_agentic_runner_output_store()`.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm the tests pass.

### Task 4: Service Without Process Launch

**Files:**
- Create: `packages/devcd-core/src/devcd/slices/agentic_context/service.py`
- Modify: `tests/test_agentic_context.py`

- [ ] **Step 1: Write failing service tests**

Add a local service builder mirroring the ambient context tests. Verify Scout
Tasks are derived from empty or populated continuity and Action Packets can be
created without starting a process.

<pre><code>
from devcd.slices.agentic_context.service import AgenticContextService


def test_service_creates_default_scout_tasks_for_empty_context(tmp_path) -> None:
    service = build_agentic_context_service(tmp_path)

    tasks = service.create_scout_tasks(surface="coding-agent", context_pack="developer")

    assert [task.kind for task in tasks]
    assert all(task.data_class == "metadata" for task in tasks)


def test_service_creates_action_packet_without_runner(tmp_path) -> None:
    service = build_agentic_context_service(tmp_path)

    packet = service.create_action_packet(surface="coding-agent", context_pack="developer")

    assert packet.schema_version == "1.0"
    assert packet.ready_for_agent in {True, False}
    assert packet.policy_summary is not None
</code></pre>

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_agentic_context.py::test_service_creates_default_scout_tasks_for_empty_context tests/test_agentic_context.py::test_service_creates_action_packet_without_runner -q
```

Expected: FAIL because `AgenticContextService` is not implemented.

- [ ] **Step 3: Implement minimal service**

Create `AgenticContextService` with dependency injection for ambient context,
state engine, memory store, and policy engine. Implement deterministic Scout
Task creation and continuity-derived Action Packet synthesis.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm the tests pass.

### Task 5: Report Intake And Validation

**Files:**
- Modify: `packages/devcd-core/src/devcd/slices/agentic_context/service.py`
- Modify: `tests/test_agentic_context.py`

- [ ] **Step 1: Write failing report tests**

Verify accepted reports update Action Packets, evidence-free reports are
rejected, and sensitive report content is withheld.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_agentic_context.py::test_accept_scout_report_updates_next_action tests/test_agentic_context.py::test_accept_scout_report_rejects_missing_evidence tests/test_agentic_context.py::test_accept_scout_report_withholds_sensitive_content -q
```

Expected: FAIL because report intake is missing.

- [ ] **Step 3: Implement report intake**

Add `accept_scout_report(report: ScoutReport) -> ScoutReport` and keep an
in-memory report list for the MVP. Store only safe summaries in memory with a
policy reason.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm the tests pass.

### Task 6: Local Subprocess Runner Adapter

**Files:**
- Create: `packages/devcd-core/src/devcd/slices/agentic_context/runner.py`
- Modify: `tests/test_agentic_context.py`

- [ ] **Step 1: Write failing runner tests**

Use a controlled Python command that echoes a valid JSON Scout Report. Add tests
for success, timeout, invalid JSON, output truncation, and unsafe template
rejection.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_agentic_context.py::test_subprocess_runner_accepts_json_report tests/test_agentic_context.py::test_subprocess_runner_times_out_safely tests/test_agentic_context.py::test_subprocess_runner_rejects_invalid_json -q
```

Expected: FAIL because the runner adapter is missing.

- [ ] **Step 3: Implement adapter**

Implement `SubprocessScoutRunner` using `subprocess.run(...)` with explicit argv,
timeout, cwd, stdin JSON, text mode, and output byte limits. Do not use shell
execution.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm the tests pass.

### Task 7: API Routes And Host Wiring

**Files:**
- Create: `packages/devcd-core/src/devcd/slices/agentic_context/api.py`
- Modify: `packages/devcd-core/src/devcd/host.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

Cover authenticated `GET /agentic-context/tasks`, `GET /agentic-context/action-packet`,
`POST /agentic-context/reports`, and default-denied `POST /agentic-context/runs`.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_api.py::test_agentic_context_tasks_route_requires_auth_and_returns_tasks tests/test_api.py::test_agentic_context_action_packet_route_returns_packet tests/test_api.py::test_agentic_context_run_route_denies_by_default -q
```

Expected: FAIL because routes are not mounted.

- [ ] **Step 3: Implement API and host wiring**

Add `APIRouter(prefix="/agentic-context")`, a service accessor using
`request.app.state.agentic_context_service`, and mount it from `create_app()`.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm the tests pass.

### Task 8: CLI Commands

**Files:**
- Modify: `packages/devcd-core/src/devcd/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Cover `devcd agentic tasks --json`, `devcd agentic action-packet --json`,
`devcd agentic run --runner missing`, and report submission from a JSON file.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_cli.py::test_agentic_tasks_json_returns_scout_tasks tests/test_cli.py::test_agentic_action_packet_json_returns_ready_field tests/test_cli.py::test_agentic_run_missing_runner_is_denied -q
```

Expected: FAIL because `agentic` commands do not exist.

- [ ] **Step 3: Implement CLI commands**

Add `agentic_app = typer.Typer(...)`, register it under `app.add_typer`, and
render stable JSON/text output using local services loaded from `DevCDSettings`.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm the tests pass.

### Task 9: Agent-Ready Auto-Priming

**Files:**
- Modify: `packages/devcd-core/src/devcd/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing agent-ready tests**

Verify the managed block tells agents to read `devcd agentic action-packet`
before asking for recap, use Scout Tasks if not ready, and avoid asking the user
to perform DevCD bookkeeping.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_cli.py::test_agent_ready_block_prefers_agentic_action_packet -q
```

Expected: FAIL because the managed block mentions only current continuity and
capture routines.

- [ ] **Step 3: Update managed block**

Extend `_agent_instruction_block(...)` with an Agentic Context Auto-Priming
section. Keep existing capture routine and safety instructions.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm the test passes.

### Task 10: Read-Only MCP Resource

**Files:**
- Modify: `packages/devcd-core/src/devcd/slices/mcp_server/service.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Write failing MCP tests**

Verify `resources/list` includes `devcd://agentic-context/action-packet` and
that reading it returns JSON without starting a runner.

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_mcp_server.py::test_mcp_lists_agentic_action_packet_resource tests/test_mcp_server.py::test_mcp_reads_agentic_action_packet_without_runner_start -q
```

Expected: FAIL because the resource is absent.

- [ ] **Step 3: Implement read-only resource**

Add the resource using local service composition. Do not add MCP tools and do
not allow runner starts through MCP.

- [ ] **Step 4: Verify GREEN**

Run the same pytest command and confirm the tests pass.

### Task 11: Documentation And Example

**Files:**
- Modify: `README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/devcd/architecture.md`
- Modify: `docs/superpowers/agent-resurrection.md`
- Create: `examples/agentic-context/README.md`
- Create: `examples/agentic-context/scout-report.json`

- [ ] **Step 1: Write docs consistency tests if practical**

Extend existing CLI/docs tests to assert new command names appear in Getting
Started or README.

- [ ] **Step 2: Update docs**

Document that local runners are opt-in, allowlisted, output-limited, and do not
perform automatic code or Git mutations.

- [ ] **Step 3: Verify docs**

Run:

```bash
python -m mkdocs build --strict
```

Expected: PASS. Keep accidental generated `site/` output out of source changes.

### Task 12: Full Verification

**Files:**
- No new files unless verification exposes defects.

- [ ] **Step 1: Run focused test suites**

Run:

```bash
python -m pytest tests/test_agentic_context.py -q
python -m pytest tests/test_policy_layer.py -q
python -m pytest tests/test_api.py -q
python -m pytest tests/test_cli.py -q
python -m pytest tests/test_mcp_server.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full gate**

Run:

```bash
make check
```

Expected: Ruff, mypy, and pytest pass.

- [ ] **Step 3: Inspect diff**

Run:

```bash
git status --short
git diff --check
```

Expected: Only intended source, tests, docs, and example files are changed; no
whitespace errors.
