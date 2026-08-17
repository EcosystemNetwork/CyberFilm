import hmac
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from cyberfilm.domain import ProductionBrief, PublishApproval, RunResult
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
    )


def create_app(service: CyberFilmService | None = None) -> FastAPI:
    app = FastAPI(
        title="CyberFilm Production Control",
        description="Observability-driven AI production supervisor",
        lifespan=lifespan,
    )
    app.state.service = service or CyberFilmService.from_environment()

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
