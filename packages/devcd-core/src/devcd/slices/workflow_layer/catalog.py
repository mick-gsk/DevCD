from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

import yaml

from devcd.slices.workflow_layer.models import WorkflowDefinition


class SourceTier(StrEnum):
    BUILTIN = "builtin"
    USER = "user"
    PROJECT = "project"
    ENV = "env"


class CatalogEntry(NamedTuple):
    name: str
    source_tier: SourceTier
    install_allowed: bool


class CatalogTrustError(ValueError):
    pass


class WorkflowCatalog:
    def __init__(
        self,
        builtin_dir: Path | None = None,
        user_dir: Path | None = None,
        project_dir: Path | None = None,
        env_url: str | None = None,
    ) -> None:
        self._builtin_dir = builtin_dir
        self._user_dir = user_dir
        self._project_dir = project_dir
        self._env_url = env_url

    @classmethod
    def from_env(cls, workspace_root: Path) -> WorkflowCatalog:
        import os

        env_url = os.environ.get("DEVCD_WORKFLOW_CATALOG_URL")
        return cls(
            builtin_dir=_builtin_workflows_dir(),
            user_dir=Path.home() / ".devcd" / "workflows",
            project_dir=workspace_root / ".devcd" / "workflows",
            env_url=env_url,
        )

    def resolve(self, name: str) -> WorkflowDefinition | None:
        for tier, source, _install_allowed in self._ordered_sources():
            defn = _lookup_in_source(name, tier, source)
            if defn is not None:
                return defn
        return None

    def list_available(self) -> list[CatalogEntry]:
        seen: dict[str, CatalogEntry] = {}
        for tier, source, _install_allowed in self._ordered_sources():
            for entry_name in _list_names_in_source(tier, source):
                if entry_name not in seen:
                    seen[entry_name] = CatalogEntry(
                        name=entry_name,
                        source_tier=tier,
                        install_allowed=_install_allowed,
                    )
        return list(seen.values())

    def validate_source(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme == "https":
            return
        if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            return
        raise CatalogTrustError(
            f"catalog URL '{url}' is not trusted: only https:// and localhost are allowed"
        )

    def _ordered_sources(
        self,
    ) -> list[tuple[SourceTier, Path | str | None, bool]]:
        sources: list[tuple[SourceTier, Path | str | None, bool]] = []
        if self._env_url:
            try:
                self.validate_source(self._env_url)
            except CatalogTrustError:
                pass
            else:
                sources.append((SourceTier.ENV, self._env_url, False))
        if self._project_dir:
            sources.append((SourceTier.PROJECT, self._project_dir, True))
        if self._user_dir:
            sources.append((SourceTier.USER, self._user_dir, True))
        if self._builtin_dir:
            sources.append((SourceTier.BUILTIN, self._builtin_dir, True))
        return sources


def _builtin_workflows_dir() -> Path:
    return Path(__file__).parent / "builtin_workflows"


def _lookup_in_source(
    name: str,
    tier: SourceTier,
    source: Path | str | None,
) -> WorkflowDefinition | None:
    if source is None or isinstance(source, str):
        return None
    path = Path(source)
    for candidate in [path / f"{name}.yaml", path / f"{name}.yml"]:
        if candidate.is_file():
            raw = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            return WorkflowDefinition.model_validate(raw)
    return None


def _list_names_in_source(tier: SourceTier, source: Path | str | None) -> list[str]:
    if source is None or isinstance(source, str):
        return []
    path = Path(source)
    if not path.is_dir():
        return []
    names = []
    for f in path.iterdir():
        if f.suffix in {".yaml", ".yml"}:
            names.append(f.stem)
    return names
