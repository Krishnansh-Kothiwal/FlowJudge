from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict


class StartupSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    summary: str
    target_users: list[str] = Field(min_length=2)
    core_features: list[str] = Field(min_length=3)
    risks: list[str] = Field(min_length=2)


class QualityReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    feedback: str


class FlowState(TypedDict):
    task: str
    plan: str
    raw_output: str
    repaired_output: str
    current_output: str
    validated: bool
    quality_passed: bool
    final: Optional[dict]
    schema_error: Optional[str]
    quality_feedback: Optional[str]
    retries: int
    provider_used: str
    provider_history: list[str]
    repair_history: list[str]
    logs: list[str]
