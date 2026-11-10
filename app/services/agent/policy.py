"""Offline-only prompt/description candidates, never arbitrary executable patches."""
import hashlib
import json
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.agent.contracts import ARGUMENT_MODELS


class AgentPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    planner_instructions: str = Field(default="", max_length=4000)
    react_instructions: str = Field(default="", max_length=4000)
    tool_descriptions: dict[str, str] = Field(default_factory=dict)
    few_shots: list[dict[str, str]] = Field(default_factory=list, max_length=10)

    @field_validator("tool_descriptions")
    @classmethod
    def known_tools(cls, value):
        if set(value) - ARGUMENT_MODELS.keys() or any(not 1 <= len(s) <= 1000 for s in value.values()):
            raise ValueError("Only known tools with bounded descriptions may be patched")
        return value

    @property
    def digest(self):
        return hashlib.sha256(json.dumps(self.model_dump(), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
