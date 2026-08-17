import os
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

import httpx

from cyberfilm.domain import SupervisorDecision

RECOVERY_ACTIONS = {
    "critical": "pause_generation",
    "error": "retry_stage",
    "warning": "request_review",
}


class GrafanaObservabilityAdapter:
    def __init__(
        self,
        url: str | None = None,
        service_account_token: str | None = None,
        client_factory: Callable[..., Any] = httpx.AsyncClient,
    ) -> None:
        self._url = url if url is not None else os.getenv("GRAFANA_URL")
        self._token = (
            service_account_token
            if service_account_token is not None
            else os.getenv("GRAFANA_SERVICE_ACCOUNT_TOKEN")
        )
        self._client_factory = client_factory

    async def inspect(self, run_id: str) -> SupervisorDecision:
        client = self._client()
        try:
            response = await client.get(
                "/api/alertmanager/grafana/api/v2/alerts",
                params={"active": "true", "silenced": "false", "inhibited": "false"},
            )
            response.raise_for_status()
            alerts = response.json()
        finally:
            await client.aclose()

        matching = [
            alert
            for alert in alerts
            if alert.get("labels", {}).get("run_id") in {None, "", run_id}
        ]
        if not matching:
            return SupervisorDecision(True, "Grafana reports no active production alerts.")

        severities = [
            str(alert.get("labels", {}).get("severity", "warning")).lower()
            for alert in matching
        ]
        severity = max(severities, key=self._severity_rank)
        action = RECOVERY_ACTIONS.get(severity, "request_review")
        return SupervisorDecision(
            healthy=False,
            summary=f"Grafana reports {len(matching)} active production alert(s).",
            recovery_action=action,
        )

    def _client(self) -> Any:
        if not self._url or not self._token:
            raise RuntimeError(
                "GRAFANA_URL and GRAFANA_SERVICE_ACCOUNT_TOKEN are required for supervision"
            )
        parsed = urlsplit(self._url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise RuntimeError("GRAFANA_URL must be an absolute HTTPS URL")
        return self._client_factory(
            base_url=self._url.rstrip("/"),
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=httpx.Timeout(15.0),
            follow_redirects=False,
        )

    @staticmethod
    def _severity_rank(severity: str) -> int:
        return {"warning": 1, "error": 2, "critical": 3}.get(severity, 1)
