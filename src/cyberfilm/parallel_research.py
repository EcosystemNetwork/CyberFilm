import json
import os
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from parallel import AsyncParallel

from cyberfilm.domain import ProductionBrief, ResearchDossier

OUTPUT_SCHEMA = {
    "type": "json",
    "json_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "risks": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 12,
            },
        },
        "required": ["summary", "risks"],
    },
}


class ParallelResearchAdapter:
    def __init__(
        self,
        api_key: str | None = None,
        processor: str = "core",
        client_factory: Callable[..., Any] = AsyncParallel,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("PARALLEL_API_KEY")
        self._processor = processor
        self._client_factory = client_factory

    async def research(self, brief: ProductionBrief) -> ResearchDossier:
        if not self._api_key:
            raise RuntimeError("PARALLEL_API_KEY is required for production research")

        client = self._client_factory(api_key=self._api_key, max_retries=2, timeout=60.0)
        try:
            task = await client.task_run.create(
                input=self._build_input(brief),
                task_spec={"output_schema": OUTPUT_SCHEMA},
                processor=self._processor,
            )
            result = await client.task_run.result(task.run_id, api_timeout=900)
        finally:
            await client.close()

        if result.output is None:
            raise RuntimeError(f"Parallel task {task.run_id} completed without output")

        content = json.loads(result.output.content)
        citations = self._citations(result.output.basis)
        if not citations:
            raise RuntimeError(f"Parallel task {task.run_id} returned no verifiable citations")

        return ResearchDossier(
            summary=str(content["summary"]),
            citations=citations,
            risks=tuple(str(risk) for risk in content["risks"]),
        )

    @staticmethod
    def _build_input(brief: ProductionBrief) -> str:
        return (
            "Research this proposed media production using current, authoritative web sources. "
            "Identify audience signals, comparable productions, location or subject constraints, "
            "and rights, likeness, trademark, music, or factual-verification risks. Do not state "
            "that anything is legally cleared; identify evidence and unresolved questions.\n\n"
            f"Title: {brief.title}\n"
            f"Logline: {brief.logline}\n"
            f"Audience: {brief.audience}\n"
            f"Budget USD: {brief.budget_usd}\n"
            f"Maximum runtime seconds: {brief.max_runtime_seconds}"
        )

    @staticmethod
    def _citations(basis: list[Any]) -> tuple[str, ...]:
        urls: set[str] = set()
        for field_basis in basis:
            for citation in field_basis.citations:
                parsed = urlsplit(citation.url)
                if parsed.scheme in {"http", "https"} and parsed.hostname:
                    urls.add(citation.url)
        return tuple(sorted(urls))
