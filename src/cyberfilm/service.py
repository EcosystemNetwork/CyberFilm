from typing import Any

from cyberfilm.clickhouse_events import ClickHouseEventStore
from cyberfilm.domain import ProductionBrief, ProductionPlan, RunResult
from cyberfilm.gemini_director import GeminiDirectorAdapter
from cyberfilm.grafana_observability import GrafanaObservabilityAdapter
from cyberfilm.ibm_governance import WatsonxGovernanceAdapter
from cyberfilm.parallel_research import ParallelResearchAdapter
from cyberfilm.workflow import ProductionWorkflow


class ReplitAgentRuntimeRequired:
    async def publish(
        self, brief: ProductionBrief, plan: ProductionPlan, approved_by: str
    ) -> str:
        raise RuntimeError("Publication must use the confirmation-enabled Replit Agent Runtime")


class CyberFilmService:
    def __init__(
        self,
        workflow: ProductionWorkflow,
        resources: tuple[Any, ...] = (),
    ) -> None:
        self._workflow = workflow
        self._resources = resources

    @classmethod
    def from_environment(cls) -> "CyberFilmService":
        director = GeminiDirectorAdapter()
        events = ClickHouseEventStore()
        workflow = ProductionWorkflow(
            research=ParallelResearchAdapter(),
            director=director,
            governance=WatsonxGovernanceAdapter(),
            events=events,
            observability=GrafanaObservabilityAdapter(),
            distribution=ReplitAgentRuntimeRequired(),
        )
        return cls(workflow, (director, events))

    async def run(self, brief: ProductionBrief) -> RunResult:
        return await self._workflow.run(brief)

    async def close(self) -> None:
        for resource in reversed(self._resources):
            await resource.close()
