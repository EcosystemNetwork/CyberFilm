import unittest
from types import SimpleNamespace

from cyberfilm.agent import ProductionPlanOutput
from cyberfilm.domain import ProductionBrief, ResearchDossier
from cyberfilm.gemini_director import GeminiDirectorAdapter


def output(cost: float = 75, duration: int = 8) -> ProductionPlanOutput:
    return ProductionPlanOutput.model_validate(
        {
            "treatment": "A production team stabilizes a transparent and observable workflow.",
            "shots": [
                {
                    "shot_id": "shot-01",
                    "description": "A wide shot reveals the production control room at dawn.",
                    "duration_seconds": duration,
                    "production_objective": "Establish the production environment.",
                    "risk_notes": ["Location release is unresolved."],
                }
            ],
            "estimated_cost_usd": cost,
            "assumptions": [],
        }
    )


class ModelsFake:
    def __init__(self, plan: ProductionPlanOutput) -> None:
        self.plan = plan
        self.calls = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(parsed=self.plan, text=self.plan.model_dump_json())


class AioFake:
    def __init__(self, plan: ProductionPlanOutput) -> None:
        self.models = ModelsFake(plan)
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class ClientFake:
    def __init__(self, plan: ProductionPlanOutput) -> None:
        self.aio = AioFake(plan)


class GeminiDirectorAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.brief = ProductionBrief(
            project_id="project-1",
            title="Signal",
            logline="A producer races an unstable pipeline.",
            audience="independent studios",
            budget_usd=500,
            max_runtime_seconds=180,
        )
        self.research = ResearchDossier(
            "Current audience research.",
            ("https://example.com/source",),
            ("Location release is unresolved.",),
        )

    def adapter(self, plan: ProductionPlanOutput) -> GeminiDirectorAdapter:
        self.client = ClientFake(plan)
        self.factory_options = None

        def factory(**kwargs):
            self.factory_options = kwargs
            return self.client

        return GeminiDirectorAdapter(project="project-1", client_factory=factory)

    async def test_calls_vertex_ai_with_schema_and_returns_plan(self) -> None:
        adapter = self.adapter(output())

        plan = await adapter.plan(self.brief, self.research)
        await adapter.close()

        self.assertEqual(75, plan.estimated_cost_usd)
        self.assertIn("shot-01", plan.shots[0])
        self.assertTrue(self.factory_options["vertexai"])
        self.assertTrue(self.client.aio.closed)
        call = self.client.aio.models.calls[0]
        self.assertEqual("gemini-3.5-flash", call["model"])
        self.assertEqual(ProductionPlanOutput, call["config"].response_schema)

    async def test_rejects_plan_over_brief_budget(self) -> None:
        adapter = self.adapter(output(cost=600))

        with self.assertRaisesRegex(RuntimeError, "exceeds"):
            await adapter.plan(self.brief, self.research)

    async def test_rejects_plan_over_brief_runtime(self) -> None:
        brief = ProductionBrief(
            project_id="project-1",
            title="Signal",
            logline="A producer races an unstable pipeline.",
            audience="independent studios",
            budget_usd=500,
            max_runtime_seconds=5,
        )
        adapter = self.adapter(output(duration=8))

        with self.assertRaisesRegex(RuntimeError, "runtime"):
            await adapter.plan(brief, self.research)

    async def test_requires_google_cloud_project(self) -> None:
        adapter = GeminiDirectorAdapter(project="")

        with self.assertRaisesRegex(RuntimeError, "GOOGLE_CLOUD_PROJECT"):
            await adapter.plan(self.brief, self.research)


if __name__ == "__main__":
    unittest.main()
