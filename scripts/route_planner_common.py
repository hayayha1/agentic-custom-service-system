"""Public-only benchmark input schema. This module contains no reference answers."""
import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/evaluation/route_planner_v1"
SOURCE_FILES = [
    "app/services/agent/planning.py", "app/services/agent/planner.py",
    "app/services/agent/llm.py", "app/services/agent/contracts.py",
    "app/services/agent/tools.py", "app/services/agent/policy.py",
    "app/services/model_service.py", "app/core/config.py",
]


class PublicCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str = Field(pattern=r"^rp_[a-f0-9]{12}$")
    query: str = Field(min_length=1)
    context: dict = Field(default_factory=dict)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    return {name: file_hash(ROOT / name) for name in SOURCE_FILES}


def read_public(path):
    cases = [PublicCase.model_validate_json(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases or len({case.case_id for case in cases}) != len(cases):
        raise ValueError("Nonempty public cases with unique IDs required")
    return cases


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
