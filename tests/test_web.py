import os

from fastapi.testclient import TestClient

from cyberfilm.domain import (
    ProductionBrief,
    PublishApproval,
    RunResult,
    RunStatus,
    Stage,
)
from cyberfilm.service import CyberFilmService
from cyberfilm.web import create_app


class WorkflowFake:
    def __init__(self) -> None:
        self.calls: list[tuple[ProductionBrief, PublishApproval | None]] = []

    async def run(self, brief, publish_approval=None):
        self.calls.append((brief, publish_approval))
        return RunResult(
            "run-1",
            RunStatus.COMPLETED,
            Stage.COMPLETE,
            "Production complete",
            publication_url="https://replit.example.app" if publish_approval else None,
        )


def test_health_endpoint():
    app = create_app(CyberFilmService(WorkflowFake()))
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_production_returns_result_without_approval():
    app = create_app(CyberFilmService(WorkflowFake()))
    client = TestClient(app)

    response = client.post(
        "/api/productions",
        json={
            "project_id": "p1",
            "title": "Neon Horizon",
            "logline": "A seed must reach the sun.",
            "audience": "sci-fi",
            "budget_usd": 100000,
            "max_runtime_seconds": 180,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["stage"] == "complete"
    assert data["publication_url"] is None


def test_approval_is_passed_to_workflow():
    workflow = WorkflowFake()
    app = create_app(CyberFilmService(workflow))
    client = TestClient(app)

    client.post(
        "/api/productions",
        json={
            "project_id": "p1",
            "title": "Neon Horizon",
            "logline": "A seed must reach the sun.",
            "audience": "sci-fi",
            "budget_usd": 100000,
            "max_runtime_seconds": 180,
            "approve_publication_by": "producer@example.com",
        },
    )

    assert len(workflow.calls) == 1
    _, approval = workflow.calls[0]
    assert isinstance(approval, PublishApproval)
    assert approval.approved_by == "producer@example.com"


def test_rejects_requests_without_token_when_protected():
    old_token = os.environ.get("DEMO_ACCESS_TOKEN")
    old_env = os.environ.get("ENVIRONMENT")
    try:
        os.environ["DEMO_ACCESS_TOKEN"] = "supersecret"
        os.environ["ENVIRONMENT"] = "production"
        app = create_app(CyberFilmService(WorkflowFake()))
        client = TestClient(app)

        no_token = client.post(
            "/api/productions",
            json={
                "project_id": "p1",
                "title": "Neon Horizon",
                "logline": "A seed must reach the sun.",
                "audience": "sci-fi",
                "budget_usd": 100000,
                "max_runtime_seconds": 180,
            },
        )
        assert no_token.status_code == 401

        wrong_token = client.post(
            "/api/productions",
            headers={"Authorization": "Bearer wrong"},
            json={
                "project_id": "p1",
                "title": "Neon Horizon",
                "logline": "A seed must reach the sun.",
                "audience": "sci-fi",
                "budget_usd": 100000,
                "max_runtime_seconds": 180,
            },
        )
        assert wrong_token.status_code == 401

        ok = client.post(
            "/api/productions",
            headers={"Authorization": "Bearer supersecret"},
            json={
                "project_id": "p1",
                "title": "Neon Horizon",
                "logline": "A seed must reach the sun.",
                "audience": "sci-fi",
                "budget_usd": 100000,
                "max_runtime_seconds": 180,
            },
        )
        assert ok.status_code == 200
    finally:
        if old_token is not None:
            os.environ["DEMO_ACCESS_TOKEN"] = old_token
        else:
            os.environ.pop("DEMO_ACCESS_TOKEN", None)
        if old_env is not None:
            os.environ["ENVIRONMENT"] = old_env
        else:
            os.environ.pop("ENVIRONMENT", None)
