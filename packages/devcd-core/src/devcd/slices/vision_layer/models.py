from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class NorthStarVersion(BaseModel):
    statement: str = Field(min_length=1, max_length=1000)
    replaced_at: datetime
    replaced_by_reason: str | None = Field(default=None, max_length=300)


class VisionRecord(BaseModel):
    schema_version: str = "1.0"
    domain: str = Field(min_length=1, max_length=200)
    north_star: str = Field(min_length=1, max_length=1000)
    rationale: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    history: list[NorthStarVersion] = Field(default_factory=list, max_length=100)
    guided: bool = False

    @field_validator("north_star", mode="before")
    @classmethod
    def north_star_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("north_star must not be blank or whitespace-only")
        return stripped

    @model_validator(mode="after")
    def normalize_future_timestamps(self) -> VisionRecord:
        now = datetime.now(UTC)
        if self.updated_at > now:
            self.updated_at = now
        if self.created_at > now:
            self.created_at = now
        return self


class VisionBlock(BaseModel):
    domain: str = Field(min_length=1, max_length=200)
    north_star: str = Field(min_length=1, max_length=1000)
    active_since: datetime
    policy_reason: str = Field(min_length=1, max_length=500)
    withheld: bool = False
