import unittest

from cyberfilm.domain import ProductionBrief, RunResult, RunStatus, Stage
from cyberfilm.service import CyberFilmService


class WorkflowFake:
    def __init__(self) -> None:
        self.briefs = []

    async def run(self, brief, publish_approval=None):
        self.briefs.append((brief, publish_approval))
        return RunResult("run-1", RunStatus.COMPLETED, Stage.COMPLETE, "done")


class ResourceFake:
    def __init__(self, name: str, closed: list[str]) -> None:
        self.name = name
        self.closed = closed

    async def close(self) -> None:
        self.closed.append(self.name)


class CyberFilmServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_runs_workflow_without_publication_approval(self) -> None:
        workflow = WorkflowFake()
        service = CyberFilmService(workflow)
        brief = ProductionBrief("project-1", "Signal", "Logline", "studios", 500, 180)

        result = await service.run(brief)

        self.assertEqual(RunStatus.COMPLETED, result.status)
        self.assertEqual([(brief, None)], workflow.briefs)

    async def test_closes_long_lived_resources_in_reverse_order(self) -> None:
        closed = []
        service = CyberFilmService(
            WorkflowFake(),
            (ResourceFake("gemini", closed), ResourceFake("clickhouse", closed)),
        )

        await service.close()

        self.assertEqual(["clickhouse", "gemini"], closed)


if __name__ == "__main__":
    unittest.main()
