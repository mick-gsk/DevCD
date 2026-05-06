from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from devcd.slices.agentic_context.service import AgenticContextService
from devcd.slices.ambient_context.service import AmbientContextService
from devcd.slices.events.ledger import EventLedger
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine
from devcd.slices.vision_layer.models import NorthStarVersion, VisionBlock, VisionRecord
from devcd.slices.vision_layer.service import VisionService

# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestVisionRecord:
    def test_valid_record_round_trips_json(self) -> None:
        record = VisionRecord(domain="my-project", north_star="Be great.")
        json_str = record.model_dump_json()
        restored = VisionRecord.model_validate_json(json_str)
        assert restored.domain == "my-project"
        assert restored.north_star == "Be great."

    def test_blank_north_star_raises(self) -> None:
        with pytest.raises(ValueError, match="blank"):
            VisionRecord(domain="d", north_star="   ")

    def test_empty_north_star_raises(self) -> None:
        with pytest.raises(ValueError, match="blank"):
            VisionRecord(domain="d", north_star="")

    def test_north_star_strips_whitespace(self) -> None:
        record = VisionRecord(domain="d", north_star="  hello  ")
        assert record.north_star == "hello"

    def test_future_updated_at_normalized(self) -> None:
        future = datetime.now(UTC) + timedelta(hours=1)
        record = VisionRecord(domain="d", north_star="ok", updated_at=future)
        assert record.updated_at <= datetime.now(UTC)

    def test_history_field_defaults_empty(self) -> None:
        record = VisionRecord(domain="d", north_star="ok")
        assert record.history == []

    def test_north_star_version_stores_reason(self) -> None:
        v = NorthStarVersion(
            statement="old star",
            replaced_at=datetime.now(UTC),
            replaced_by_reason="project pivoted",
        )
        assert v.replaced_by_reason == "project pivoted"


class TestVisionBlock:
    def test_withheld_defaults_false(self) -> None:
        block = VisionBlock(
            domain="d",
            north_star="s",
            active_since=datetime.now(UTC),
            policy_reason="allowed",
        )
        assert block.withheld is False


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestVisionServiceInitAndLoad:
    def test_init_creates_file(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        svc.init_vision(domain="my-app", north_star="Ship fearlessly.")
        assert (tmp_path / "vision.json").exists()

    def test_load_returns_record(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        svc.init_vision(domain="my-app", north_star="Ship fearlessly.")
        loaded = svc.load()
        assert loaded is not None
        assert loaded.north_star == "Ship fearlessly."
        assert loaded.domain == "my-app"

    def test_load_returns_none_when_no_file(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        assert svc.load() is None

    def test_init_rejects_blank_north_star(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        with pytest.raises(ValueError, match="blank"):
            svc.init_vision(domain="d", north_star="   ")

    def test_init_overwrites_existing_record(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        svc.init_vision(domain="d", north_star="First star.")
        svc.init_vision(domain="d", north_star="Second star.")
        loaded = svc.load()
        assert loaded is not None
        assert loaded.north_star == "Second star."


class TestVisionServiceUpdate:
    def test_update_replaces_north_star(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        svc.init_vision(domain="d", north_star="Old.")
        svc.update_vision("New.")
        loaded = svc.load()
        assert loaded is not None
        assert loaded.north_star == "New."

    def test_update_moves_old_to_history(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        svc.init_vision(domain="d", north_star="Old.")
        svc.update_vision("New.", reason="pivoted")
        loaded = svc.load()
        assert loaded is not None
        assert len(loaded.history) == 1
        assert loaded.history[0].statement == "Old."
        assert loaded.history[0].replaced_by_reason == "pivoted"

    def test_update_caps_history_at_100(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        svc.init_vision(domain="d", north_star="Start.")
        for i in range(102):
            svc.update_vision(f"Star {i}.")
        loaded = svc.load()
        assert loaded is not None
        assert len(loaded.history) == 100

    def test_update_rejects_blank(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        svc.init_vision(domain="d", north_star="Ok.")
        with pytest.raises(ValueError, match="blank"):
            svc.update_vision("   ")

    def test_update_raises_when_no_vision(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        with pytest.raises(FileNotFoundError):
            svc.update_vision("anything")


class TestVisionServiceGetBlock:
    def test_get_block_returns_block_when_allowed(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        svc.init_vision(domain="d", north_star="Be great.")
        policy = PolicyEngine.default()
        block = svc.get_block(policy, surface="agent")
        assert block is not None
        assert block.north_star == "Be great."
        assert block.withheld is False

    def test_get_block_returns_none_when_policy_denies(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        svc.init_vision(domain="d", north_star="Be great.")
        policy = PolicyEngine(
            allow_observation=True,
            allow_local_storage=False,
            allow_remote_export=False,
            allow_actions=False,
        )
        block = svc.get_block(policy, surface="agent")
        assert block is None

    def test_get_block_returns_none_when_no_vision(self, tmp_path: Path) -> None:
        svc = VisionService(tmp_path)
        policy = PolicyEngine.default()
        assert svc.get_block(policy) is None


class TestVisionServiceCorruptFile:
    def test_corrupted_json_raises_value_error(self, tmp_path: Path) -> None:
        vision_path = tmp_path / "vision.json"
        vision_path.write_text("{not valid json!", encoding="utf-8")
        svc = VisionService(tmp_path)
        with pytest.raises(ValueError, match="corrupted"):
            svc.load()


class TestVisionServiceSensitiveContentCheck:
    def test_email_detected(self) -> None:
        warnings = VisionService.check_for_sensitive_content(
            "Contact admin@example.com for help."
        )
        assert any("email" in w.lower() for w in warnings)

    def test_long_token_detected(self) -> None:
        warnings = VisionService.check_for_sensitive_content(
            "Key: " + "A" * 45
        )
        assert len(warnings) > 0

    def test_url_credentials_detected(self) -> None:
        warnings = VisionService.check_for_sensitive_content(
            "Connect to https://user:pass@host.com"
        )
        assert any("credential" in w.lower() or "secret" in w.lower() for w in warnings)

    def test_clean_text_returns_no_warnings(self) -> None:
        warnings = VisionService.check_for_sensitive_content(
            "Build the best regression detection tool for Python projects."
        )
        assert warnings == []


class TestPolicyEngineVisionInject:
    def test_allows_when_local_storage_enabled(self) -> None:
        policy = PolicyEngine.default()
        decision = policy.decide_vision_inject("agent")
        assert decision.allowed

    def test_denies_when_local_storage_disabled(self) -> None:
        policy = PolicyEngine(
            allow_observation=True,
            allow_local_storage=False,
            allow_remote_export=False,
            allow_actions=False,
        )
        decision = policy.decide_vision_inject("agent")
        assert not decision.allowed
        assert "local storage" in decision.reason

    def test_reason_contains_surface_when_allowed(self) -> None:
        policy = PolicyEngine.default()
        decision = policy.decide_vision_inject("action_packet")
        assert decision.allowed
        assert "local agent surface" in decision.reason


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------


def _policy(allow_storage: bool = True) -> PolicyEngine:
    return PolicyEngine(
        allow_observation=True,
        allow_local_storage=allow_storage,
        allow_remote_export=False,
        allow_actions=False,
    )


def _build_ambient_service(
    tmp_path: Path,
    vision_service: VisionService | None = None,
) -> AmbientContextService:
    policy = _policy()
    memory_store = MemoryStore.with_ttl_seconds(315_360_000)
    event_ledger = EventLedger(tmp_path / "events.jsonl")
    state_engine = StateEngine(policy, memory_store, event_ledger)
    return AmbientContextService(
        state_engine=state_engine,
        memory_store=memory_store,
        policy_engine=policy,
        feedback_path=tmp_path / "context-feedback.jsonl",
        vision_service=vision_service,
    )


def _build_agentic_service(
    tmp_path: Path,
    vision_service: VisionService | None = None,
) -> AgenticContextService:
    ambient = _build_ambient_service(tmp_path, vision_service=vision_service)
    return AgenticContextService(
        ambient_context_service=ambient,
        policy_engine=ambient.policy_engine,
        vision_service=vision_service,
    )


# ---------------------------------------------------------------------------
# T012 — Injection tests
# ---------------------------------------------------------------------------


class TestVisionInjectionIntoActionPacket:
    def test_vision_is_none_when_no_service(self, tmp_path: Path) -> None:
        service = _build_agentic_service(tmp_path, vision_service=None)
        packet = service.create_action_packet(surface="coding-agent", context_pack="developer")
        assert packet.vision is None

    def test_vision_is_injected_when_service_wired_and_vision_exists(
        self, tmp_path: Path
    ) -> None:
        vs = VisionService(tmp_path)
        vs.init_vision(domain="test-project", north_star="Ship great tools.")
        service = _build_agentic_service(tmp_path, vision_service=vs)
        packet = service.create_action_packet(surface="coding-agent", context_pack="developer")
        assert packet.vision is not None
        assert packet.vision.north_star == "Ship great tools."

    def test_vision_is_none_when_no_vision_file_saved(self, tmp_path: Path) -> None:
        vs = VisionService(tmp_path)  # no init_vision call
        service = _build_agentic_service(tmp_path, vision_service=vs)
        packet = service.create_action_packet(surface="coding-agent", context_pack="developer")
        assert packet.vision is None

    def test_vision_is_withheld_when_storage_denied(self, tmp_path: Path) -> None:
        vs = VisionService(tmp_path)
        vs.init_vision(domain="test-project", north_star="Ship great tools.")
        ambient = _build_ambient_service(tmp_path, vision_service=vs)
        denied_policy = _policy(allow_storage=False)
        service = AgenticContextService(
            ambient_context_service=ambient,
            policy_engine=denied_policy,
            vision_service=vs,
        )
        packet = service.create_action_packet(surface="coding-agent", context_pack="developer")
        assert packet.vision is None or packet.vision.withheld is True


class TestVisionInjectionIntoContinuityPacket:
    def test_vision_is_none_when_no_service(self, tmp_path: Path) -> None:
        service = _build_ambient_service(tmp_path, vision_service=None)
        packet = service.create_continuity_packet()
        assert packet.vision is None

    def test_vision_is_injected_when_service_wired(self, tmp_path: Path) -> None:
        vs = VisionService(tmp_path)
        vs.init_vision(domain="proj", north_star="Deliver daily.")
        service = _build_ambient_service(tmp_path, vision_service=vs)
        packet = service.create_continuity_packet()
        assert packet.vision is not None
        assert packet.vision.north_star == "Deliver daily."


# ---------------------------------------------------------------------------


class TestVisionServiceUpdateT014:
    def test_update_adds_to_history(self, tmp_path: Path) -> None:
        vs = VisionService(tmp_path)
        vs.init_vision(domain="proj", north_star="V1 statement.")
        vs.update_vision("V2 statement.", reason="better direction")
        record = vs.load()
        assert record is not None
        assert record.north_star == "V2 statement."
        assert len(record.history) == 1
        assert record.history[0].statement == "V1 statement."

    def test_update_caps_history_at_100(self, tmp_path: Path) -> None:
        vs = VisionService(tmp_path)
        vs.init_vision(domain="proj", north_star="initial")
        for i in range(105):
            vs.update_vision(f"Version {i + 1}")
        record = vs.load()
        assert record is not None
        assert len(record.history) <= 100

    def test_update_blank_north_star_raises(self, tmp_path: Path) -> None:
        vs = VisionService(tmp_path)
        vs.init_vision(domain="proj", north_star="Valid.")
        with pytest.raises(ValueError):
            vs.update_vision("   ")

    def test_update_without_prior_vision_raises_file_not_found(
        self, tmp_path: Path
    ) -> None:
        vs = VisionService(tmp_path)
        with pytest.raises(FileNotFoundError):
            vs.update_vision("New statement.")


# ---------------------------------------------------------------------------
# T017 — CLI vision show / history tests
# ---------------------------------------------------------------------------


class TestVisionCLICommands:
    def setup_method(self) -> None:
        from devcd.cli import app as cli_app

        self.runner = CliRunner()
        self.app = cli_app

    def test_vision_show_with_no_vision_prints_guidance(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = self.runner.invoke(self.app, ["vision", "show"])
        assert result.exit_code == 0
        assert "No vision" in result.output or "devcd vision init" in result.output

    def test_vision_show_after_init_prints_north_star(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        self.runner.invoke(
            self.app,
            ["vision", "init", "--domain", "proj", "--north-star", "Great software."],
        )
        result = self.runner.invoke(self.app, ["vision", "show"])
        assert result.exit_code == 0
        assert "Great software." in result.output

    def test_vision_show_json_is_parseable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        self.runner.invoke(
            self.app,
            ["vision", "init", "--domain", "proj", "--north-star", "Hello world."],
        )
        result = self.runner.invoke(self.app, ["vision", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["north_star"] == "Hello world."

    def test_vision_history_empty_message(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        self.runner.invoke(self.app, ["vision", "init", "--domain", "p", "--north-star", "Start."])
        result = self.runner.invoke(self.app, ["vision", "history"])
        assert result.exit_code == 0
        # Either "no history" or empty table header is acceptable
        assert "history" in result.output.lower() or result.output.strip() != ""

    def test_vision_init_and_update_roundtrip_via_cli(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        r1 = self.runner.invoke(
            self.app, ["vision", "init", "--domain", "p", "--north-star", "First."]
        )
        assert r1.exit_code == 0
        r2 = self.runner.invoke(self.app, ["vision", "update", "Second."])
        assert r2.exit_code == 0
        r3 = self.runner.invoke(self.app, ["vision", "show"])
        assert "Second." in r3.output
