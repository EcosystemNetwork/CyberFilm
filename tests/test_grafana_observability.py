import unittest

from cyberfilm.grafana_observability import GrafanaObservabilityAdapter


class ResponseFake:
    def __init__(self, alerts) -> None:
        self.alerts = alerts
        self.checked = False

    def raise_for_status(self) -> None:
        self.checked = True

    def json(self):
        return self.alerts


class ClientFake:
    def __init__(self, alerts) -> None:
        self.response = ResponseFake(alerts)
        self.requests = []
        self.closed = False

    async def get(self, path, params):
        self.requests.append((path, params))
        return self.response

    async def aclose(self) -> None:
        self.closed = True


class GrafanaObservabilityAdapterTests(unittest.IsolatedAsyncioTestCase):
    def adapter(self, alerts):
        self.client = ClientFake(alerts)
        self.client_options = None

        def factory(**kwargs):
            self.client_options = kwargs
            return self.client

        return GrafanaObservabilityAdapter(
            url="https://cyberfilm.grafana.net",
            service_account_token="test-token",
            client_factory=factory,
        )

    async def test_reports_healthy_when_no_alerts_match_run(self) -> None:
        adapter = self.adapter([{"labels": {"run_id": "another-run"}}])

        decision = await adapter.inspect("run-1")

        self.assertTrue(decision.healthy)
        self.assertIsNone(decision.recovery_action)
        self.assertTrue(self.client.response.checked)
        self.assertTrue(self.client.closed)
        self.assertFalse(self.client_options["follow_redirects"])

    async def test_maps_highest_severity_to_allowlisted_action(self) -> None:
        adapter = self.adapter(
            [
                {"labels": {"run_id": "run-1", "severity": "warning"}},
                {"labels": {"run_id": "run-1", "severity": "critical"}},
            ]
        )

        decision = await adapter.inspect("run-1")

        self.assertFalse(decision.healthy)
        self.assertEqual("pause_generation", decision.recovery_action)

    async def test_global_alert_applies_to_every_run(self) -> None:
        adapter = self.adapter([{"labels": {"severity": "error"}}])

        decision = await adapter.inspect("run-1")

        self.assertEqual("retry_stage", decision.recovery_action)

    async def test_rejects_insecure_grafana_url(self) -> None:
        adapter = GrafanaObservabilityAdapter(
            url="http://grafana.internal", service_account_token="test-token"
        )

        with self.assertRaisesRegex(RuntimeError, "HTTPS"):
            await adapter.inspect("run-1")

    async def test_requires_credentials(self) -> None:
        adapter = GrafanaObservabilityAdapter(url="", service_account_token="")

        with self.assertRaisesRegex(RuntimeError, "GRAFANA_URL"):
            await adapter.inspect("run-1")


if __name__ == "__main__":
    unittest.main()
