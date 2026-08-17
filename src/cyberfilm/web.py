from __future__ import annotations

import hmac
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from cyberfilm.domain import ProductionBrief, ProductionPlan, PublishApproval, RunResult, Shot
from cyberfilm.manipulation import ManipulationEngine, ManipulationResult
from cyberfilm.service import CyberFilmService

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"


class BriefRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=120)
    logline: str = Field(..., min_length=1, max_length=1000)
    audience: str = Field(..., min_length=1, max_length=120)
    budget_usd: int = Field(..., gt=0)
    max_runtime_seconds: int = Field(..., gt=0)
    approve_publication_by: str | None = Field(default=None, max_length=120)


class ProductionResponse(BaseModel):
    run_id: str
    status: str
    stage: str
    message: str
    publication_url: str | None = None
    plan: PlanResponse | None = None


class ShotRequest(BaseModel):
    shot_id: str
    description: str
    duration_seconds: int = Field(..., gt=0, le=30)
    production_objective: str
    risk_notes: list[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    treatment: str
    shots: list[ShotRequest]
    estimated_cost_usd: float = Field(..., ge=0)


class ShotResponse(BaseModel):
    shot_id: str
    description: str
    duration_seconds: int
    production_objective: str
    risk_notes: list[str]


class PlanResponse(BaseModel):
    treatment: str
    shots: list[ShotResponse]
    estimated_cost_usd: float


class ManipulationRequest(BaseModel):
    action: str = Field(..., pattern=r"^(reorder|trim|remove|add|regenerate)$")
    plan: PlanRequest
    params: dict[str, Any]


class ManipulationResponse(BaseModel):
    plan: PlanResponse
    action: str
    explanation: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    service = getattr(app.state, "service", None)
    if service is None:
        app.state.service = CyberFilmService.from_environment()
    yield
    await app.state.service.close()


def _verify_token(authorization: str | None) -> None:
    token = os.getenv("DEMO_ACCESS_TOKEN")
    environment = os.getenv("ENVIRONMENT", "development")
    if not token or environment == "development":
        return
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    provided = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(provided, token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def _production_response(result: RunResult) -> ProductionResponse:
    return ProductionResponse(
        run_id=result.run_id,
        status=result.status.value,
        stage=result.stage.value,
        message=result.message,
        publication_url=result.publication_url,
        plan=_to_plan_response(result.plan) if result.plan else None,
    )


def _to_shot_model(shot: Shot) -> ShotResponse:
    return ShotResponse(
        shot_id=shot.shot_id,
        description=shot.description,
        duration_seconds=shot.duration_seconds,
        production_objective=shot.production_objective,
        risk_notes=list(shot.risk_notes),
    )


def _to_plan(plan: PlanRequest) -> ProductionPlan:
    return ProductionPlan(
        treatment=plan.treatment,
        shots=tuple(
            Shot(
                shot_id=s.shot_id,
                description=s.description,
                duration_seconds=s.duration_seconds,
                production_objective=s.production_objective,
                risk_notes=tuple(s.risk_notes),
            )
            for s in plan.shots
        ),
        estimated_cost_usd=plan.estimated_cost_usd,
    )


def _to_plan_response(plan: ProductionPlan) -> PlanResponse:
    return PlanResponse(
        treatment=plan.treatment,
        shots=[_to_shot_model(s) for s in plan.shots],
        estimated_cost_usd=plan.estimated_cost_usd,
    )


def _manipulation_response(result: ManipulationResult) -> ManipulationResponse:
    return ManipulationResponse(
        plan=_to_plan_response(result.plan),
        action=result.action,
        explanation=result.explanation,
    )


def create_app(
    service: CyberFilmService | None = None,
    manipulation: ManipulationEngine | None = None,
) -> FastAPI:
    app = FastAPI(
        title="CyberFilm Production Control",
        description="Observability-driven AI production supervisor",
        lifespan=lifespan,
    )
    app.state.service = service or CyberFilmService.from_environment()
    app.state.manipulation = manipulation or ManipulationEngine()

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/productions", response_model=ProductionResponse)
    async def produce(
        brief: BriefRequest,
        http_request: Request,
        authorization: str | None = Header(default=None),
    ) -> ProductionResponse:
        _verify_token(authorization)
        service: CyberFilmService = http_request.app.state.service

        approval = None
        if brief.approve_publication_by:
            approval = PublishApproval(
                approved_by=brief.approve_publication_by,
                approved_at=datetime.now(UTC),
            )

        production_brief = ProductionBrief(
            project_id=brief.project_id,
            title=brief.title,
            logline=brief.logline,
            audience=brief.audience,
            budget_usd=brief.budget_usd,
            max_runtime_seconds=brief.max_runtime_seconds,
        )

        try:
            result = await service.run(production_brief, approval)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Production failed: {type(exc).__name__}",
            ) from None

        return _production_response(result)

    @app.post("/api/manipulate", response_model=ManipulationResponse)
    async def manipulate(
        request: ManipulationRequest,
        http_request: Request,
        authorization: str | None = Header(default=None),
    ) -> ManipulationResponse:
        _verify_token(authorization)
        engine: ManipulationEngine = http_request.app.state.manipulation

        try:
            result = await engine.manipulate(
                _to_plan(request.plan), request.action, request.params
            )
        except (ValueError, KeyError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Manipulation failed: {exc}",
            ) from None

        return _manipulation_response(result)

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="static")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(create_app(), host="0.0.0.0", port=port)
