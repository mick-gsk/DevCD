from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from devcd.kernel.settings import DevCDSettings
from devcd.slices.ambient_context.agent_layer_models import AgentLayerProfile, AgentTarget
from devcd.slices.ambient_context.agent_layer_service import (
    AGENT_LAYER_PROFILE_PATH,
    apply_agent_layer_profile,
    build_agent_layer_proposal,
    detect_workspace_agent_layer,
    load_agent_layer_profile,
)


def test_agent_layer_profile_round_trips_without_raw_content() -> None:
    profile = AgentLayerProfile(
        archetype="builder",
        agent_targets=["copilot"],
        context_pack="developer",
        surface_plan=["coding-agent", "debugging-agent"],
        workspace_fingerprint="pyproject.toml|pytest|ruff",
        policy_reason="local metadata storage is allowed by policy",
        detection_summary=["python tooling detected from pyproject.toml"],
    )

    body = profile.model_dump_json()
    restored = AgentLayerProfile.model_validate_json(body)

    assert restored.archetype == "builder"
    assert restored.agent_targets == [AgentTarget.COPILOT]
    assert "raw" not in body.lower()
    assert "secret" not in body.lower()


def test_agent_layer_profile_rejects_unknown_archetype_and_sensitive_summary() -> None:
    with pytest.raises(ValidationError):
        AgentLayerProfile(
            archetype="wizard",
            agent_targets=["copilot"],
            context_pack="developer",
            surface_plan=["coding-agent"],
            workspace_fingerprint="unknown",
            policy_reason="local metadata storage is allowed by policy",
        )

    with pytest.raises(ValidationError):
        AgentLayerProfile(
            archetype="builder",
            agent_targets=["copilot"],
            context_pack="developer",
            surface_plan=["coding-agent"],
            workspace_fingerprint="unknown",
            policy_reason="local metadata storage is allowed by policy",
            detection_summary=["raw log content: secret token=abc123"],
        )


def test_detects_existing_agent_instruction_files(tmp_path: Path) -> None:
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "copilot-instructions.md").write_text("# Copilot\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (tmp_path / ".devcd").mkdir()
    (tmp_path / ".devcd" / "openclaw-mcp.json").write_text("{}\n", encoding="utf-8")

    detection = detect_workspace_agent_layer(tmp_path)

    detected = {agent.target for agent in detection.agents if agent.status == "detected"}
    assert detected == {AgentTarget.COPILOT, AgentTarget.CODEX, AgentTarget.OPENCLAW}
    assert any(hint.name == "openclaw-mcp" for hint in detection.mcp_hints)
    assert detection.workspace_root == str(tmp_path)


def test_detects_modern_copilot_instruction_path(tmp_path: Path) -> None:
    instructions_dir = tmp_path / ".github" / "instructions"
    instructions_dir.mkdir(parents=True)
    (instructions_dir / "copilot.instructions.md").write_text(
        "# Copilot instructions\n",
        encoding="utf-8",
    )

    detection = detect_workspace_agent_layer(tmp_path)

    copilot_detection = next(
        agent for agent in detection.agents if agent.target == AgentTarget.COPILOT
    )
    assert copilot_detection.status == "detected"
    assert copilot_detection.path == ".github/instructions/copilot.instructions.md"


def test_detects_python_pytest_ruff_workspace(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n[tool.pytest.ini_options]\n[tool.ruff]\n',
        encoding="utf-8",
    )

    detection = detect_workspace_agent_layer(tmp_path)

    assert {tool.name for tool in detection.languages} == {"python"}
    assert {tool.name for tool in detection.test_tools} == {"pytest"}
    assert {tool.name for tool in detection.lint_tools} == {"ruff"}
    assert detection.devcd_state["config_exists"] is False


def test_detection_tolerates_invalid_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{not-json", encoding="utf-8")

    detection = detect_workspace_agent_layer(tmp_path)

    assert any(tool.name == "node" for tool in detection.languages)
    assert any("could not parse" in receipt for receipt in detection.policy_receipts)


def test_recommends_orchestrator_for_multi_agent_workspace(tmp_path: Path) -> None:
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "copilot-instructions.md").write_text("# Copilot\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# Claude\n", encoding="utf-8")

    detection = detect_workspace_agent_layer(tmp_path)
    proposal = build_agent_layer_proposal(detection)

    assert proposal.recommended_archetype == "orchestrator"
    assert proposal.context_pack == "developer"
    assert proposal.surface_plan == ["coding-agent", "review-agent", "subagent"]
    assert proposal.agent_targets == [AgentTarget.COPILOT, AgentTarget.CLAUDE]
    assert any(write.path == ".devcd/agent-layer-profile.json" for write in proposal.writes)


def test_recommends_builder_for_python_test_workspace(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n[tool.pytest.ini_options]\n', encoding="utf-8"
    )

    proposal = build_agent_layer_proposal(detect_workspace_agent_layer(tmp_path))

    assert proposal.recommended_archetype == "builder"
    assert proposal.context_pack == "developer"
    assert proposal.surface_plan == ["coding-agent", "debugging-agent"]
    assert proposal.agent_targets == [AgentTarget.COPILOT]


def test_requested_archetype_overrides_detection_but_keeps_receipt(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")

    proposal = build_agent_layer_proposal(
        detect_workspace_agent_layer(tmp_path), requested_archetype="researcher"
    )

    assert proposal.recommended_archetype == "researcher"
    assert proposal.context_pack == "research"
    assert any("requested archetype" in receipt for receipt in proposal.trust_receipts)


def test_apply_profile_writes_profile_and_selected_agent_targets(tmp_path: Path) -> None:
    proposal = build_agent_layer_proposal(
        detect_workspace_agent_layer(tmp_path),
        requested_archetype="builder",
        requested_agents=["copilot", "openclaw"],
    )

    result = apply_agent_layer_profile(proposal, workspace_root=tmp_path)

    profile_path = tmp_path / AGENT_LAYER_PROFILE_PATH
    assert result.profile_path == AGENT_LAYER_PROFILE_PATH.as_posix()
    assert profile_path.exists()
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()
    assert (tmp_path / ".devcd" / "openclaw-mcp.json").exists()
    assert not (tmp_path / "CLAUDE.md").exists()
    body = json.loads(profile_path.read_text(encoding="utf-8"))
    assert body["archetype"] == "builder"
    assert body["agent_targets"] == ["copilot", "openclaw"]
    assert "no remote calls" in result.trust_receipts


def test_apply_profile_respects_local_storage_policy(tmp_path: Path) -> None:
    proposal = build_agent_layer_proposal(
        detect_workspace_agent_layer(tmp_path),
        requested_archetype="builder",
        requested_agents=["copilot"],
    )

    with pytest.raises(PermissionError, match="local storage is disabled by policy"):
        apply_agent_layer_profile(
            proposal,
            workspace_root=tmp_path,
            settings=DevCDSettings(allow_local_storage=False),
        )

    assert not (tmp_path / AGENT_LAYER_PROFILE_PATH).exists()
    assert not (tmp_path / ".github" / "copilot-instructions.md").exists()


def test_load_profile_reports_missing_profile(tmp_path: Path) -> None:
    loaded = load_agent_layer_profile(tmp_path)

    assert loaded.profile is None
    assert loaded.status == "missing"
    assert loaded.next_step == "devcd onboard --yes"
