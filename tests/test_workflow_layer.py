from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from devcd.slices.policy_layer.service import PolicyEngine
from devcd.slices.workflow_layer.catalog import CatalogTrustError, WorkflowCatalog
from devcd.slices.workflow_layer.engine import WorkflowEngine
from devcd.slices.workflow_layer.models import (
    CommandStep,
    GateStep,
    RunState,
    RunStatus,
    ShellStep,
    WorkflowDefinition,
)
from devcd.slices.workflow_layer.resolver import InstructionLayerResolver

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_workflow(steps: list[dict]) -> WorkflowDefinition:
    return WorkflowDefinition.model_validate(
        {"name": "test-workflow", "description": "test", "version": "1.0", "steps": steps}
    )


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------


def test_run_status_terminal_states() -> None:
    from devcd.slices.workflow_layer.models import RunStatus

    terminal = {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.ABORTED}
    non_terminal = {RunStatus.RUNNING, RunStatus.PAUSED}

    for status in terminal:
        state = RunState(workflow_name="x", status=status)
        assert state.is_terminal()

    for status in non_terminal:
        state = RunState(workflow_name="x", status=status)
        assert not state.is_terminal()


# ---------------------------------------------------------------------------
# engine: happy path
# ---------------------------------------------------------------------------


def test_engine_completes_command_only_workflow(tmp_path: Path) -> None:
    definition = _make_workflow(
        [{"type": "command", "name": "version", "args": ["--version"]}]
    )
    policy = PolicyEngine.default()
    engine = WorkflowEngine(runs_dir=tmp_path / "runs", policy_engine=policy)

    # command step shells out to 'devcd version --version' which may not succeed
    # in test env; we care about engine mechanics, not CLI invocation
    state = engine.execute(definition)

    assert state.run_id
    assert state.workflow_name == "test-workflow"
    assert len(state.step_results) == 1
    assert state.status in {RunStatus.COMPLETED, RunStatus.FAILED}


def test_engine_uses_injected_command_runner(tmp_path: Path) -> None:
    definition = _make_workflow(
        [{"type": "command", "name": "context", "args": ["passport"]}]
    )

    from devcd.slices.workflow_layer.engine import CommandExecutionResult

    def fake_runner(_step: CommandStep) -> CommandExecutionResult:
        return CommandExecutionResult(returncode=0, stdout="ok", stderr="")

    engine = WorkflowEngine(runs_dir=tmp_path / "runs", command_runner=fake_runner)
    state = engine.execute(definition)

    assert state.status == RunStatus.COMPLETED
    assert state.step_results[0].status.value == "completed"
    assert state.step_results[0].output == "ok"


def test_engine_pauses_at_gate(tmp_path: Path) -> None:
    definition = _make_workflow(
        [
            {"type": "gate", "message": "Human approval required"},
        ]
    )
    engine = WorkflowEngine(runs_dir=tmp_path / "runs")

    state = engine.execute(definition)

    assert state.status == RunStatus.PAUSED
    assert state.current_step_index == 1  # points to next step after gate
    run_dir = tmp_path / "runs" / state.run_id
    assert (run_dir / "state.json").is_file()
    assert (run_dir / "workflow.yaml").is_file()


def test_engine_resume_from_paused_gate(tmp_path: Path) -> None:
    definition = _make_workflow(
        [
            {"type": "gate", "message": "Please approve"},
        ]
    )
    engine = WorkflowEngine(runs_dir=tmp_path / "runs")

    paused_state = engine.execute(definition)
    assert paused_state.status == RunStatus.PAUSED

    resumed_state = engine.resume(paused_state.run_id)
    assert resumed_state.status == RunStatus.COMPLETED
    assert resumed_state.current_step_index == 1


def test_engine_resume_multi_step_workflow(tmp_path: Path) -> None:
    definition = _make_workflow(
        [
            {"type": "gate", "message": "Step 1 gate"},
            {"type": "gate", "message": "Step 2 gate"},
        ]
    )
    engine = WorkflowEngine(runs_dir=tmp_path / "runs")

    state = engine.execute(definition)
    assert state.status == RunStatus.PAUSED
    assert state.current_step_index == 1  # past first gate

    state = engine.resume(state.run_id)
    assert state.status == RunStatus.PAUSED
    assert state.current_step_index == 2  # past second gate

    state = engine.resume(state.run_id)
    assert state.status == RunStatus.COMPLETED


def test_engine_resume_terminal_run_is_noop(tmp_path: Path) -> None:
    definition = _make_workflow(
        [{"type": "gate", "message": "gate"}]
    )
    engine = WorkflowEngine(runs_dir=tmp_path / "runs")
    paused = engine.execute(definition)
    completed = engine.resume(paused.run_id)
    assert completed.status == RunStatus.COMPLETED

    still_completed = engine.resume(completed.run_id)
    assert still_completed.status == RunStatus.COMPLETED


def test_engine_persists_state_after_each_step(tmp_path: Path) -> None:
    definition = _make_workflow(
        [
            {"type": "gate", "message": "gate"},
        ]
    )
    engine = WorkflowEngine(runs_dir=tmp_path / "runs")
    state = engine.execute(definition)

    run_dir = tmp_path / "runs" / state.run_id
    persisted = RunState.model_validate_json((run_dir / "state.json").read_text(encoding="utf-8"))
    assert persisted.run_id == state.run_id
    assert persisted.status == RunStatus.PAUSED


def test_engine_list_runs(tmp_path: Path) -> None:
    definition = _make_workflow([{"type": "gate", "message": "gate"}])
    engine = WorkflowEngine(runs_dir=tmp_path / "runs")

    engine.execute(definition)
    engine.execute(definition)

    runs = engine.list_runs()
    assert len(runs) == 2


# ---------------------------------------------------------------------------
# engine: policy enforcement
# ---------------------------------------------------------------------------


def test_engine_denies_shell_step_by_default(tmp_path: Path) -> None:
    definition = _make_workflow(
        [{"type": "shell", "run": "echo hello"}]
    )
    policy = PolicyEngine.default()
    engine = WorkflowEngine(runs_dir=tmp_path / "runs", policy_engine=policy)

    state = engine.execute(definition)

    assert state.status == RunStatus.ABORTED
    assert state.step_results[0].status.value == "aborted"
    assert "policy" in state.step_results[0].error


def test_engine_allows_shell_step_when_actions_permitted(tmp_path: Path) -> None:
    definition = _make_workflow(
        [{"type": "shell", "run": "echo hello"}]
    )
    policy = PolicyEngine(
        allow_observation=True,
        allow_local_storage=True,
        allow_remote_export=False,
        allow_actions=True,
    )
    engine = WorkflowEngine(runs_dir=tmp_path / "runs", policy_engine=policy)

    state = engine.execute(definition)

    assert state.status in {RunStatus.COMPLETED, RunStatus.FAILED}


# ---------------------------------------------------------------------------
# catalog
# ---------------------------------------------------------------------------


def test_catalog_resolves_from_project_dir(tmp_path: Path) -> None:
    workflows_dir = tmp_path / ".devcd" / "workflows"
    workflows_dir.mkdir(parents=True)
    _write_yaml(
        workflows_dir / "my-flow.yaml",
        {"name": "my-flow", "steps": []},
    )
    catalog = WorkflowCatalog(project_dir=workflows_dir)

    result = catalog.resolve("my-flow")

    assert result is not None
    assert result.name == "my-flow"


def test_catalog_returns_none_for_missing_name(tmp_path: Path) -> None:
    catalog = WorkflowCatalog(project_dir=tmp_path)
    assert catalog.resolve("nonexistent") is None


def test_catalog_trust_raises_for_http_url() -> None:
    catalog = WorkflowCatalog()
    with pytest.raises(CatalogTrustError, match="not trusted"):
        catalog.validate_source("http://example.com/catalog")


def test_catalog_trust_allows_https() -> None:
    catalog = WorkflowCatalog()
    catalog.validate_source("https://example.com/catalog")


def test_catalog_trust_allows_localhost() -> None:
    catalog = WorkflowCatalog()
    catalog.validate_source("http://localhost:8080/catalog")


def test_catalog_list_available_with_tiers(tmp_path: Path) -> None:
    builtin_dir = tmp_path / "builtin"
    project_dir = tmp_path / "project"
    builtin_dir.mkdir()
    project_dir.mkdir()
    _write_yaml(builtin_dir / "shared.yaml", {"name": "shared", "steps": []})
    _write_yaml(project_dir / "shared.yaml", {"name": "shared", "steps": []})
    _write_yaml(project_dir / "extra.yaml", {"name": "extra", "steps": []})

    catalog = WorkflowCatalog(builtin_dir=builtin_dir, project_dir=project_dir)
    entries = catalog.list_available()
    names = [e.name for e in entries]

    assert "shared" in names
    assert "extra" in names
    shared_entry = next(e for e in entries if e.name == "shared")
    assert shared_entry.source_tier.value == "project"


def test_catalog_skips_untrusted_env_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEVCD_WORKFLOW_CATALOG_URL", "http://evil.example.com/catalog")
    project_dir = tmp_path / ".devcd" / "workflows"
    project_dir.mkdir(parents=True)
    _write_yaml(project_dir / "safe.yaml", {"name": "safe", "steps": []})
    catalog = WorkflowCatalog.from_env(tmp_path)
    result = catalog.resolve("safe")
    assert result is not None


# ---------------------------------------------------------------------------
# resolver
# ---------------------------------------------------------------------------


def test_resolver_returns_managed_core_when_no_layers(tmp_path: Path) -> None:
    resolver = InstructionLayerResolver(
        workspace_root=tmp_path,
        managed_core_content="## Managed core",
    )
    resolved = resolver.resolve("copilot")
    assert resolved.content == "## Managed core"
    assert "devcd-managed-core" in resolved.provenance


def test_resolver_workspace_override_replaces_core(tmp_path: Path) -> None:
    override_dir = tmp_path / ".devcd" / "instructions"
    override_dir.mkdir(parents=True)
    (override_dir / "copilot.md").write_text("# Workspace override", encoding="utf-8")

    resolver = InstructionLayerResolver(
        workspace_root=tmp_path,
        managed_core_content="## Managed core",
    )
    resolved = resolver.resolve("copilot")

    assert resolved.content == "# Workspace override"
    assert any("workspace-override" in p for p in resolved.provenance)


def test_resolver_preset_wraps_core(tmp_path: Path) -> None:
    preset_dir = tmp_path / ".devcd" / "presets"
    preset_dir.mkdir(parents=True)
    (preset_dir / "copilot-team.md").write_text("## Team rules", encoding="utf-8")

    resolver = InstructionLayerResolver(
        workspace_root=tmp_path,
        managed_core_content="## Managed core",
    )
    resolved = resolver.resolve("copilot")

    assert "## Team rules" in resolved.content
    assert "## Managed core" in resolved.content


def test_resolver_is_deterministic_regardless_of_discovery_order(tmp_path: Path) -> None:
    override_dir = tmp_path / ".devcd" / "instructions"
    override_dir.mkdir(parents=True)
    (override_dir / "agent.md").write_text("# Override", encoding="utf-8")

    r1 = InstructionLayerResolver(workspace_root=tmp_path, managed_core_content="core")
    r2 = InstructionLayerResolver(workspace_root=tmp_path, managed_core_content="core")

    assert r1.resolve("agent").content == r2.resolve("agent").content


# ---------------------------------------------------------------------------
# policy: new workflow / catalog / instruction methods
# ---------------------------------------------------------------------------


def test_policy_denies_shell_step() -> None:
    policy = PolicyEngine.default()
    step = ShellStep(run="echo hi")
    decision = policy.decide_workflow_step_execute(step)
    assert not decision.allowed
    assert "shell" in decision.reason


def test_policy_allows_command_step() -> None:
    policy = PolicyEngine.default()
    step = CommandStep(name="capture")
    decision = policy.decide_workflow_step_execute(step)
    assert decision.allowed


def test_policy_allows_gate_step() -> None:
    policy = PolicyEngine.default()
    step = GateStep(message="approve")
    decision = policy.decide_workflow_step_execute(step)
    assert decision.allowed


def test_policy_denies_community_catalog_install() -> None:
    policy = PolicyEngine.default()
    decision = policy.decide_catalog_install(source_tier="community", install_allowed=False)
    assert not decision.allowed
    assert "install_allowed=False" in decision.reason


def test_policy_allows_project_catalog_install() -> None:
    policy = PolicyEngine.default()
    decision = policy.decide_catalog_install(source_tier="project", install_allowed=True)
    assert decision.allowed


def test_policy_denies_instruction_write_outside_allowed_dirs() -> None:
    policy = PolicyEngine.default()
    decision = policy.decide_instruction_layer_write("AGENTS.md", "workspace-override")
    assert not decision.allowed
    assert ".devcd/" in decision.reason or ".github/" in decision.reason


def test_policy_allows_instruction_write_to_devcd_dir() -> None:
    policy = PolicyEngine.default()
    decision = policy.decide_instruction_layer_write(
        ".devcd/instructions/copilot.md", "workspace-override"
    )
    assert decision.allowed


def test_policy_allows_instruction_write_to_github_dir() -> None:
    policy = PolicyEngine.default()
    decision = policy.decide_instruction_layer_write(
        ".github/copilot-instructions.md", "managed-core"
    )
    assert decision.allowed
