from typing import Protocol

from cyberfilm.domain import (
    GovernanceDecision,
    ProductionBrief,
    ProductionEvent,
    ProductionPlan,
    ResearchDossier,
    SupervisorDecision,
)


class ResearchPort(Protocol):
    async def research(self, brief: ProductionBrief) -> ResearchDossier: ...


class DirectorPort(Protocol):
    async def plan(
        self, brief: ProductionBrief, research: ResearchDossier
    ) -> ProductionPlan: ...


class GovernancePort(Protocol):
    async def evaluate(
        self, brief: ProductionBrief, research: ResearchDossier, plan: ProductionPlan
    ) -> GovernanceDecision: ...


class EventStorePort(Protocol):
    async def append(self, event: ProductionEvent) -> None: ...


class ObservabilityPort(Protocol):
    async def inspect(self, run_id: str) -> SupervisorDecision: ...


class DistributionPort(Protocol):
    async def publish(
        self, brief: ProductionBrief, plan: ProductionPlan, approved_by: str
    ) -> str: ...
