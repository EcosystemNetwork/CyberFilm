from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class Stage(StrEnum):
    RESEARCH = "research"
    DIRECTION = "direction"
    GOVERNANCE = "governance"
    INTELLIGENCE = "intelligence"
    SUPERVISION = "supervision"
    DISTRIBUTION = "distribution"
    COMPLETE = "complete"
    BLOCKED = "blocked"


class RunStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProductionBrief:
    project_id: str
    title: str
    logline: str
    audience: str
    budget_usd: int
    max_runtime_seconds: int


@dataclass(frozen=True, slots=True)
class ResearchDossier:
    summary: str
    citations: tuple[str, ...]
    risks: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Shot:
    shot_id: str
    description: str
    duration_seconds: int
    production_objective: str
    risk_notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProductionPlan:
    treatment: str
    shots: tuple[Shot, ...]
    estimated_cost_usd: float


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    approved: bool
    reasons: tuple[str, ...]
    evaluation_id: str | None = None


@dataclass(frozen=True, slots=True)
class SupervisorDecision:
    healthy: bool
    summary: str
    recovery_action: str | None = None


@dataclass(frozen=True, slots=True)
class PublishApproval:
    approved_by: str
    approved_at: datetime


@dataclass(frozen=True, slots=True)
class ProductionEvent:
    run_id: str
    project_id: str
    stage: Stage
    event_type: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunResult:
    run_id: str
    status: RunStatus
    stage: Stage
    message: str
    publication_url: str | None = None
    plan: ProductionPlan | None = None
