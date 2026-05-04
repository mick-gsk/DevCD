from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DevCDSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEVCD_", extra="forbid")

    host: str = "127.0.0.1"
    port: int = 8765
    runtime_dir: Path = Path(".devcd")
    ledger_file: str = "events.jsonl"
    working_memory_ttl_seconds: int = Field(default=300, ge=1)
    episodic_memory_ttl_seconds: int = Field(default=604800, ge=1)
    ide_coalesce_window_ms: int = Field(default=500, ge=1)
    api_token: str | None = None
    enabled_sources: set[str] = Field(
        default_factory=lambda: {
            "ide",
            "git",
            "task",
            "notes",
            "system",
        }
    )
    allowed_data_classes: set[str] = Field(default_factory=lambda: {"metadata"})
    allow_observation: bool = True
    allow_local_storage: bool = True
    allow_remote_export: bool = False
    allow_actions: bool = False

    @property
    def ledger_path(self) -> Path:
        return self.runtime_dir / self.ledger_file

    @classmethod
    def load(cls, path: Path | None = None) -> DevCDSettings:
        config_path = path or Path(os.environ.get("DEVCD_CONFIG", "devcd.toml"))
        if not config_path.exists():
            return cls()

        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        raw_settings = data.get("devcd", data)
        if not isinstance(raw_settings, dict):
            raise ValueError("DevCD config must contain a table of settings")
        return cls(**raw_settings)

    def to_config_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "runtime_dir": str(self.runtime_dir),
            "ledger_file": self.ledger_file,
            "working_memory_ttl_seconds": self.working_memory_ttl_seconds,
            "episodic_memory_ttl_seconds": self.episodic_memory_ttl_seconds,
            "ide_coalesce_window_ms": self.ide_coalesce_window_ms,
            "api_token": self.api_token,
            "enabled_sources": sorted(self.enabled_sources),
            "allowed_data_classes": sorted(self.allowed_data_classes),
            "allow_observation": self.allow_observation,
            "allow_local_storage": self.allow_local_storage,
            "allow_remote_export": self.allow_remote_export,
            "allow_actions": self.allow_actions,
        }
        return {k: v for k, v in result.items() if v is not None}
