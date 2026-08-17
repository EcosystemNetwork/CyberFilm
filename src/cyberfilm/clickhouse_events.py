import json
import os
from collections.abc import Callable
from typing import Any

import clickhouse_connect

from cyberfilm.domain import ProductionEvent


class ClickHouseEventStore:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        client_factory: Callable[..., Any] = clickhouse_connect.get_async_client,
    ) -> None:
        self._host = host if host is not None else os.getenv("CLICKHOUSE_HOST")
        self._port = port or int(os.getenv("CLICKHOUSE_PORT", "8443"))
        self._database = database or os.getenv("CLICKHOUSE_DATABASE", "default")
        self._username = username or os.getenv("CLICKHOUSE_USERNAME", "default")
        self._password = password if password is not None else os.getenv("CLICKHOUSE_PASSWORD")
        self._client_factory = client_factory
        self._client: Any | None = None

    async def append(self, event: ProductionEvent) -> None:
        client = await self._get_client()
        await client.insert(
            "production_events",
            [
                [
                    event.occurred_at,
                    event.run_id,
                    event.project_id,
                    event.stage.value,
                    event.event_type,
                    json.dumps(event.attributes, separators=(",", ":"), sort_keys=True),
                ]
            ],
            column_names=[
                "occurred_at",
                "run_id",
                "project_id",
                "stage",
                "event_type",
                "attributes_json",
            ],
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self._host or not self._password:
            raise RuntimeError(
                "CLICKHOUSE_HOST and CLICKHOUSE_PASSWORD are required for production events"
            )
        self._client = await self._client_factory(
            host=self._host,
            port=self._port,
            database=self._database,
            username=self._username,
            password=self._password,
            secure=True,
            verify=True,
            autogenerate_session_id=False,
        )
        return self._client
