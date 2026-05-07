from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from devcd.slices.events.models import DevEvent, EventSensitivity, EventSource


class RecipeField(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    required: bool = False
    sensitive: bool = False


class CustomRecipeDefinition(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    event_source: EventSource = EventSource.TASK
    event_type: str = Field(min_length=1)
    fields: list[RecipeField] = Field(default_factory=list)


def events_from_custom_recipe(
    definition: CustomRecipeDefinition,
    values: dict[str, Any],
) -> list[DevEvent]:
    """Convert a custom recipe definition + field values into DevCD events."""
    missing = [f.name for f in definition.fields if f.required and f.name not in values]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")

    sensitive_fields = {f.name for f in definition.fields if f.sensitive}
    sensitivity = (
        EventSensitivity.SENSITIVE
        if any(k in sensitive_fields for k in values)
        else EventSensitivity.NORMAL
    )

    payload: dict[str, Any] = {"recipe": definition.name, **values}

    return [
        DevEvent(
            source=definition.event_source,
            type=definition.event_type,
            sensitivity=sensitivity,
            payload=payload,
        )
    ]


def load_custom_recipes(workspace_root: Path) -> list[CustomRecipeDefinition]:
    """Load all custom recipe YAML files from .devcd/recipes/."""
    recipes_dir = workspace_root / ".devcd" / "recipes"
    if not recipes_dir.is_dir():
        return []
    result: list[CustomRecipeDefinition] = []
    for path in sorted(recipes_dir.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        result.append(CustomRecipeDefinition.model_validate(raw))
    return result
