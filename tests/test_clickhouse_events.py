import json
import unittest
from datetime import UTC, datetime

from cyberfilm.clickhouse_events import ClickHouseEventStore
from cyberfilm.domain import ProductionEvent, Stage


class ClickHouseClientFake:
    def __init__(self) -> None:
        self.inserts = []
        self.closed = False

    async def insert(self, table, data, column_names) -> None:
        self.inserts.append((table, data, column_names))

    async def close(self) -> None:
        self.closed = True


class ClickHouseEventStoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.client = ClickHouseClientFake()
        self.factory_calls = []

        async def factory(**kwargs):
            self.factory_calls.append(kwargs)
            return self.client

        self.store = ClickHouseEventStore(
            host="example.clickhouse.cloud",
            password="test-password",
            client_factory=factory,
        )
        self.event = ProductionEvent(
            run_id="run-1",
            project_id="project-1",
            stage=Stage.RESEARCH,
            event_type="completed",
            occurred_at=datetime(2026, 8, 16, tzinfo=UTC),
            attributes={"risk_count": 2, "citation_count": 4},
        )

    async def test_inserts_structured_event_over_verified_tls(self) -> None:
        await self.store.append(self.event)

        table, data, columns = self.client.inserts[0]
        self.assertEqual("production_events", table)
        self.assertEqual("research", data[0][3])
        self.assertEqual(
            {"citation_count": 4, "risk_count": 2}, json.loads(data[0][5])
        )
        self.assertIn("attributes_json", columns)
        self.assertTrue(self.factory_calls[0]["secure"])
        self.assertTrue(self.factory_calls[0]["verify"])
        self.assertFalse(self.factory_calls[0]["autogenerate_session_id"])

    async def test_reuses_and_closes_client(self) -> None:
        await self.store.append(self.event)
        await self.store.append(self.event)
        await self.store.close()

        self.assertEqual(1, len(self.factory_calls))
        self.assertTrue(self.client.closed)

    async def test_requires_remote_credentials(self) -> None:
        store = ClickHouseEventStore(host="", password="")

        with self.assertRaisesRegex(RuntimeError, "CLICKHOUSE_HOST"):
            await store.append(self.event)


if __name__ == "__main__":
    unittest.main()
