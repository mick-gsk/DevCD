from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import NamedTuple


class LayerStrategy(StrEnum):
    REPLACE = "replace"
    WRAP = "wrap"


class InstructionLayer(NamedTuple):
    source: str
    content: str
    strategy: LayerStrategy
    priority: int


class ResolvedInstruction(NamedTuple):
    content: str
    provenance: list[str]


class InstructionLayerResolver:
    def __init__(
        self,
        workspace_root: Path | None = None,
        managed_core_content: str = "",
    ) -> None:
        self._workspace_root = workspace_root or Path.cwd()
        self._managed_core_content = managed_core_content

    def resolve(self, target: str) -> ResolvedInstruction:
        layers = self._collect_layers(target)
        layers.sort(key=lambda lyr: lyr.priority, reverse=True)
        return self._compose(layers)

    def _collect_layers(self, target: str) -> list[InstructionLayer]:
        layers: list[InstructionLayer] = []

        if self._managed_core_content:
            layers.append(
                InstructionLayer(
                    source="devcd-managed-core",
                    content=self._managed_core_content,
                    strategy=LayerStrategy.REPLACE,
                    priority=0,
                )
            )

        preset_dir = self._workspace_root / ".devcd" / "presets"
        if preset_dir.is_dir():
            for preset_file in sorted(preset_dir.iterdir()):
                if preset_file.suffix == ".md" and preset_file.stem.startswith(target):
                    layers.append(
                        InstructionLayer(
                            source=f"preset:{preset_file.name}",
                            content=preset_file.read_text(encoding="utf-8"),
                            strategy=LayerStrategy.WRAP,
                            priority=50,
                        )
                    )

        override_file = self._workspace_root / ".devcd" / "instructions" / f"{target}.md"
        if override_file.is_file():
            layers.append(
                InstructionLayer(
                    source=f"workspace-override:{target}.md",
                    content=override_file.read_text(encoding="utf-8"),
                    strategy=LayerStrategy.REPLACE,
                    priority=100,
                )
            )

        return layers

    def _compose(self, layers: list[InstructionLayer]) -> ResolvedInstruction:
        if not layers:
            return ResolvedInstruction(content="", provenance=[])

        base_layer = layers[-1]
        current = base_layer.content
        provenance = [base_layer.source]

        for lyr in reversed(layers[:-1]):
            provenance.insert(0, lyr.source)
            if lyr.strategy is LayerStrategy.REPLACE:
                current = lyr.content
                break
            if lyr.strategy is LayerStrategy.WRAP:
                current = f"{lyr.content}\n\n{current}"

        return ResolvedInstruction(content=current, provenance=provenance)
