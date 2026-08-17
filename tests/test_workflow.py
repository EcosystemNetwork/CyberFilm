import unittest
from datetime import UTC, datetime

from cyberfilm.domain import (
    GovernanceDecision,
    ProductionBrief,
    ProductionPlan,
    PublishApproval,
    ResearchDossier,
    RunStatus,
    Stage,
    SupervisorDecision,
)
from cyberfilm.workflow import ProductionWorkflow


class ResearchFake:
    async def research(self, brief: ProductionBrief) -> ResearchDossier:
        return ResearchDossier("Research", ("https://example.com/source",))


class DirectorFake:
    async def plan(
        self, brief: ProductionBrief, research: ResearchDossier
    ) -> ProductionPlan:
        return ProductionPlan("Treatment", ("Wide shot", "Close-up"), 125.0)


class FailingDirectorFake:
    async def plan(self, brief, research):
        raise TimeoutError("provider details must not be persisted")


class GovernanceFake:
    def __init__(self, approved: bool) -> None:
        self.approved = approved

    async def evaluate(self, brief, research, plan) -> GovernanceDecision:
        reasons = () if self.approved else ("Uncleared likeness",)
        return GovernanceDecision(self.approved, reasons, "evaluation-1")


class EventsFake:
    def __init__(self) -> None:
        self.events = []

    async def append(self, event) -> None:
        self.events.append(event)


class ObservabilityFake:
    async def inspect(self, run_id: str) -> SupervisorDecision:
        return SupervisorDecision(True, "Healthy")


class DistributionFake:
    def __init__(self) -> None:
        self.calls = 0

    async def publish(self, brief, plan, approved_by: str) -> str:
        self.calls += 1
        return "https://example.replit.app"


class ProductionWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.brief = ProductionBrief(
            project_id="project-1",
            title="Signal",
            logline="A producer races an unstable pipeline.",
            audience="independent studios",
            budget_usd=500,
            max_runtime_seconds=180,
        )
        self.events = EventsFake()
        self.distribution = DistributionFake()

    def workflow(self, approved: bool) -> ProductionWorkflow:
        return ProductionWorkflow(
            ResearchFake(),
            DirectorFake(),
            GovernanceFake(approved),
            self.events,
            ObservabilityFake(),
            self.distribution,
        )

    async def test_approved_run_requires_explicit_publication_approval(self) -> None:
        result = await self.workflow(True).run(self.brief)

        self.assertEqual(RunStatus.COMPLETED, result.status)
        self.assertIsNone(result.publication_url)
        self.assertEqual(0, self.distribution.calls)
        self.assertNotIn(Stage.DISTRIBUTION, [event.stage for event in self.events.events])

    async def test_approved_run_can_publish_after_human_approval(self) -> None:
        approval = PublishApproval("producer@example.com", datetime.now(UTC))
        result = await self.workflow(True).run(self.brief, approval)

        self.assertEqual("https://example.replit.app", result.publication_url)
        self.assertEqual(1, self.distribution.calls)

    async def test_governance_block_prevents_observability_and_distribution(self) -> None:
        result = await self.workflow(False).run(self.brief)

        self.assertEqual(RunStatus.BLOCKED, result.status)
        self.assertEqual(Stage.BLOCKED, result.stage)
        self.assertEqual(0, self.distribution.calls)
        self.assertEqual(Stage.BLOCKED, self.events.events[-1].stage)

    async def test_partner_failure_records_sanitized_current_stage(self) -> None:
        workflow = ProductionWorkflow(
            ResearchFake(),
            FailingDirectorFake(),
            GovernanceFake(True),
            self.events,
            ObservabilityFake(),
            self.distribution,
        )

        with self.assertRaises(TimeoutError):
            await workflow.run(self.brief)

        failure = self.events.events[-1]
        self.assertEqual(Stage.DIRECTION, failure.stage)
        self.assertEqual("failed", failure.event_type)
        self.assertEqual({"error_type": "TimeoutError"}, failure.attributes)


if __name__ == "__main__":
    unittest.main()
