from dataclasses import dataclass
from uuid import uuid4

from cyberfilm.domain import ProductionPlan


@dataclass(frozen=True, slots=True)
class RenderJob:
    job_id: str
    status: str
    render_url: str | None = None


class AssetGenerator:
    async def render(self, plan: ProductionPlan) -> RenderJob:
        raise NotImplementedError


class PlaceholderAssetGenerator(AssetGenerator):
    async def render(self, plan: ProductionPlan) -> RenderJob:
        return RenderJob(
            job_id=uuid4().hex[:12],
            status="queued",
            render_url=None,
        )
