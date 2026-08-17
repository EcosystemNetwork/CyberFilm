import json
import unittest
from types import SimpleNamespace

from cyberfilm.domain import ProductionBrief
from cyberfilm.parallel_research import ParallelResearchAdapter


class TaskRunFake:
    def __init__(self, with_citations: bool = True) -> None:
        self.with_citations = with_citations
        self.create_args = None

    async def create(self, **kwargs):
        self.create_args = kwargs
        return SimpleNamespace(run_id="parallel-run-1")

    async def result(self, run_id: str, api_timeout: int):
        citations = []
        if self.with_citations:
            citations = [SimpleNamespace(url="https://example.com/evidence")]
        basis = [SimpleNamespace(citations=citations)]
        output = SimpleNamespace(
            content=json.dumps(
                {
                    "summary": "The audience signal is supported by current evidence.",
                    "risks": ["Music rights remain unresolved."],
                }
            ),
            basis=basis,
        )
        return SimpleNamespace(output=output)


class ParallelClientFake:
    def __init__(self, task_run: TaskRunFake) -> None:
        self.task_run = task_run
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class ParallelResearchAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.brief = ProductionBrief(
            project_id="project-1",
            title="Signal",
            logline="A producer races an unstable pipeline.",
            audience="independent studios",
            budget_usd=500,
            max_runtime_seconds=180,
        )

    async def test_returns_cited_research_and_closes_client(self) -> None:
        task_run = TaskRunFake()
        client = ParallelClientFake(task_run)
        adapter = ParallelResearchAdapter(
            api_key="test-key", client_factory=lambda **kwargs: client
        )

        dossier = await adapter.research(self.brief)

        self.assertEqual(("https://example.com/evidence",), dossier.citations)
        self.assertEqual(("Music rights remain unresolved.",), dossier.risks)
        self.assertEqual("core", task_run.create_args["processor"])
        self.assertTrue(client.closed)

    async def test_rejects_uncited_research(self) -> None:
        client = ParallelClientFake(TaskRunFake(with_citations=False))
        adapter = ParallelResearchAdapter(
            api_key="test-key", client_factory=lambda **kwargs: client
        )

        with self.assertRaisesRegex(RuntimeError, "no verifiable citations"):
            await adapter.research(self.brief)

    async def test_requires_api_key(self) -> None:
        adapter = ParallelResearchAdapter(api_key="")

        with self.assertRaisesRegex(RuntimeError, "PARALLEL_API_KEY"):
            await adapter.research(self.brief)


if __name__ == "__main__":
    unittest.main()
