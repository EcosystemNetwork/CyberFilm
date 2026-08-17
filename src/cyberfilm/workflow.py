from contextlib import suppress
from uuid import uuid4

from cyberfilm.domain import (
    ProductionBrief,
    ProductionEvent,
    PublishApproval,
    RunResult,
    RunStatus,
    Stage,
)
from cyberfilm.ports import (
    DirectorPort,
    DistributionPort,
    EventStorePort,
    GovernancePort,
    ObservabilityPort,
    ResearchPort,
)


class ProductionWorkflow:
    def __init__(
        self,
        research: ResearchPort,
        director: DirectorPort,
        governance: GovernancePort,
        events: EventStorePort,
        observability: ObservabilityPort,
        distribution: DistributionPort,
    ) -> None:
        self._research = research
        self._director = director
        self._governance = governance
        self._events = events
        self._observability = observability
        self._distribution = distribution

    async def run(
        self, brief: ProductionBrief, publish_approval: PublishApproval | None = None
    ) -> RunResult:
        run_id = uuid4().hex
        stage_state = {"current": Stage.RESEARCH}
        try:
            return await self._run(run_id, brief, publish_approval, stage_state)
        except Exception as error:
            with suppress(Exception):
                await self._record(
                    run_id,
                    brief,
                    stage_state["current"],
                    "failed",
                    {"error_type": type(error).__name__},
                )
            raise

    async def _run(
        self,
        run_id: str,
        brief: ProductionBrief,
        publish_approval: PublishApproval | None,
        stage_state: dict[str, Stage],
    ) -> RunResult:
        await self._record(run_id, brief, Stage.RESEARCH, "started")
        research = await self._research.research(brief)
        await self._record(
            run_id,
            brief,
            Stage.RESEARCH,
            "completed",
            {"citation_count": len(research.citations), "risk_count": len(research.risks)},
        )

        stage_state["current"] = Stage.DIRECTION
        await self._record(run_id, brief, Stage.DIRECTION, "started")
        plan = await self._director.plan(brief, research)
        await self._record(
            run_id,
            brief,
            Stage.DIRECTION,
            "completed",
            {"shot_count": len(plan.shots), "estimated_cost_usd": plan.estimated_cost_usd},
        )

        stage_state["current"] = Stage.GOVERNANCE
        await self._record(run_id, brief, Stage.GOVERNANCE, "started")
        decision = await self._governance.evaluate(brief, research, plan)
        if not decision.approved:
            await self._record(
                run_id,
                brief,
                Stage.BLOCKED,
                "governance_blocked",
                {"reasons": list(decision.reasons)},
            )
            return RunResult(
                run_id=run_id,
                status=RunStatus.BLOCKED,
                stage=Stage.BLOCKED,
                message="Production blocked by governance policy.",
                plan=plan,
            )

        await self._record(
            run_id,
            brief,
            Stage.GOVERNANCE,
            "approved",
            {"evaluation_id": decision.evaluation_id},
        )
        stage_state["current"] = Stage.SUPERVISION
        await self._record(run_id, brief, Stage.INTELLIGENCE, "events_available")
        supervisor = await self._observability.inspect(run_id)
        await self._record(
            run_id,
            brief,
            Stage.SUPERVISION,
            "inspection_completed",
            {
                "healthy": supervisor.healthy,
                "recovery_action": supervisor.recovery_action,
            },
        )

        publication_url = None
        if publish_approval is not None:
            stage_state["current"] = Stage.DISTRIBUTION
            await self._record(
                run_id,
                brief,
                Stage.DISTRIBUTION,
                "publication_approved",
                {"approved_by": publish_approval.approved_by},
            )
            publication_url = await self._distribution.publish(
                brief, plan, publish_approval.approved_by
            )
            await self._record(
                run_id,
                brief,
                Stage.DISTRIBUTION,
                "published",
                {"publication_url": publication_url},
            )

        stage_state["current"] = Stage.COMPLETE
        await self._record(run_id, brief, Stage.COMPLETE, "completed")
        return RunResult(
            run_id=run_id,
            status=RunStatus.COMPLETED,
            stage=Stage.COMPLETE,
            message="Production workflow completed.",
            publication_url=publication_url,
            plan=plan,
        )

    async def _record(
        self,
        run_id: str,
        brief: ProductionBrief,
        stage: Stage,
        event_type: str,
        attributes: dict[str, object] | None = None,
    ) -> None:
        await self._events.append(
            ProductionEvent(
                run_id=run_id,
                project_id=brief.project_id,
                stage=stage,
                event_type=event_type,
                attributes=attributes or {},
            )
        )
