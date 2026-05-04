from __future__ import annotations

from pathlib import Path

from devcd.kernel.settings import DevCDSettings


def test_settings_loads_devcd_toml_table(tmp_path: Path) -> None:
    config_path = tmp_path / "devcd.toml"
    config_path.write_text(
        """
[devcd]
host = "127.0.0.2"
port = 9000
runtime_dir = ".local-devcd"
ledger_file = "audit.jsonl"
working_memory_ttl_seconds = 60
episodic_memory_ttl_seconds = 120
ide_coalesce_window_ms = 750
api_token = "local-token"
enabled_sources = ["ide", "git", "system"]
allowed_data_classes = ["metadata", "summary"]
allow_observation = true
allow_local_storage = false
allow_remote_export = false
allow_actions = false
""".strip(),
        encoding="utf-8",
    )

    settings = DevCDSettings.load(config_path)

    assert settings.host == "127.0.0.2"
    assert settings.port == 9000
    assert settings.ledger_path == Path(".local-devcd") / "audit.jsonl"
    assert settings.episodic_memory_ttl_seconds == 120
    assert settings.ide_coalesce_window_ms == 750
    assert settings.api_token == "local-token"
    assert settings.enabled_sources == {"ide", "git", "system"}
    assert settings.allowed_data_classes == {"metadata", "summary"}
    assert not settings.allow_local_storage
