import json
import unittest
from types import SimpleNamespace

from cyberfilm.domain import ProductionBrief, ProductionPlan, ResearchDossier, Shot
from cyberfilm.ibm_governance import WatsonxGovernanceAdapter


class ResultFake:
    def __init__(self, metrics_result) -> None:
        self.metrics_result = metrics_result

    def to_json(self) -> str:
        return json.dumps(
            [{"name": metric.name, "value": metric.value} for metric in self.metrics_result]
        )


class EvaluatorFake:
    def __init__(self, metrics_result) -> None:
        self.metrics_result = metrics_result
        self.calls = []

    def evaluate(self, data, metrics):
        self.calls.append((data, metrics))
        return ResultFake(self.metrics_result)


def metric(name: str, value: float, limit: float = 0.1, errors=None):
    return SimpleNamespace(
        name=name,
        value=value,
        max=None,
        mean=None,
        errors=errors,
        thresholds=[SimpleNamespace(type="upper_limit", value=limit)],
    )


class WatsonxGovernanceAdapterTests(unittest.IsolatedAsyncioTestCase):
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
            ("Music rights remain unresolved.",),
        )
        self.plan = ProductionPlan(
            "A bounded treatment.",
            (Shot("shot-01", "Wide shot", 5, "Establish the scene", ()),),
            75,
        )

    def adapter(self, metrics_result):
        self.evaluator = EvaluatorFake(metrics_result)
        self.factory_options = None

        def factory(**kwargs):
            self.factory_options = kwargs
            return self.evaluator

        return WatsonxGovernanceAdapter(
            api_key="test-key",
            service_instance_id="service-1",
            evaluator_factory=factory,
        )

    async def test_approves_when_all_metrics_pass(self) -> None:
        adapter = self.adapter(
            [
                metric("input_pii", 0.01),
                metric("output_pii", 0.02),
                metric("prompt_safety_risk", 0.1, 0.5),
            ]
        )

        decision = await adapter.evaluate(self.brief, self.research, self.plan)

        self.assertTrue(decision.approved)
        self.assertEqual((), decision.reasons)
        self.assertTrue(decision.evaluation_id.startswith("watsonx-"))
        self.assertEqual("us-south", self.factory_options["region"])
        self.assertEqual(3, len(self.evaluator.calls[0][1]))

    async def test_blocks_threshold_violation(self) -> None:
        adapter = self.adapter([metric("output_pii", 0.8)])

        decision = await adapter.evaluate(self.brief, self.research, self.plan)

        self.assertFalse(decision.approved)
        self.assertIn("output_pii: 0.800 exceeds 0.100", decision.reasons)

    async def test_blocks_evaluation_errors_and_missing_scores(self) -> None:
        error_metric = metric("input_pii", 0.0, errors=["unavailable"])
        missing_metric = metric("prompt_safety_risk", 0.0)
        missing_metric.value = None
        adapter = self.adapter([error_metric, missing_metric])

        decision = await adapter.evaluate(self.brief, self.research, self.plan)

        self.assertEqual(
            ("input_pii: evaluation error", "prompt_safety_risk: missing score"),
            decision.reasons,
        )

    async def test_requires_ibm_credentials(self) -> None:
        adapter = WatsonxGovernanceAdapter(api_key="", service_instance_id="")

        with self.assertRaisesRegex(RuntimeError, "IBM_CLOUD_API_KEY"):
            await adapter.evaluate(self.brief, self.research, self.plan)


if __name__ == "__main__":
    unittest.main()
