# CyberFilm

CyberFilm is an observability-driven AI production supervisor for media teams.
It turns a production brief into a deterministic, multi-stage workflow powered by
Gemini on Google Cloud's Agentic Cinema stack. Each stage is governed, measured,
and observed before the next one runs.

## Partner ecosystem

CyberFilm's primary hackathon track is **Grafana**. The same workflow also uses
**Parallel**, **ClickHouse**, **IBM watsonx.governance**, and **Replit** as
complementary partner capabilities.

| Partner | Role |
| --- | --- |
| **Parallel** | Cited research on rights, audience, market, and references |
| **Gemini on Vertex AI / ADK** | Bounded, schema-constrained production planning |
| **IBM watsonx.governance** | Policy evaluation and approval gating |
| **ClickHouse** | Production event and cost ledger |
| **Grafana** | Operational supervision and recovery signals |
| **Replit** | Confirmation-gated screening/campaign microsite publication |

External side effects and recovery actions are approval-gated. Partner failures
degrade safely and remain visible rather than being silently replaced with fake
data.

## Production workflow

1. **Parallel** researches the brief and returns a dossier with citations and risks.
2. **Gemini** converts the brief and dossier into a bounded shot plan.
3. **IBM watsonx.governance** evaluates the plan and can block execution.
4. **ClickHouse** records every stage, cost, and decision.
5. **Grafana** provides the live supervision signal used to decide recovery.
6. **Replit** builds or updates the screening microsite only after explicit approval.

## Architecture

- `src/cyberfilm/workflow.py` — deterministic stage orchestration
- `src/cyberfilm/service.py` — long-lived partner client composition
- `src/cyberfilm/web.py` — FastAPI control-room API
- `web/index.html` — hosted production control room
- `src/cyberfilm/agent.py` — ADK Agent Runtime definition for the director
- `src/cyberfilm/agent_runtime.py` — ADK runtime bootstrap
- `src/cyberfilm/gemini_director.py` — live Vertex AI director
- `src/cyberfilm/parallel_research.py` — Parallel Task API research adapter
- `src/cyberfilm/clickhouse_events.py` — ClickHouse event ledger
- `src/cyberfilm/grafana_observability.py` — Grafana supervision adapter
- `src/cyberfilm/ibm_governance.py` — IBM watsonx.governance adapter
- `src/cyberfilm/replit_distribution.py` — Replit MCP distribution adapter
- `src/cyberfilm/replit_runtime.py` — Replit ADK runtime bootstrap

## Local quickstart

```bash
cp .env.example .env
# fill in .env with your partner credentials
uv sync --extra dev
source .env
uv run python -m cyberfilm.web
```

Open `http://localhost:8080` for the control room.

Run the test suite:

```bash
uv run pytest
uv run ruff check .
```

## Usage

1. Open the control room.
2. Submit a brief: project id, title, logline, audience, budget, runtime.
3. Watch the six-stage timeline fill in as each partner completes.
4. If governance approves, enter an approver email and run again to publish.
5. The returned `publication_url` is the Replit screening microsite.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Docker and Google Cloud Run setup.

## Security

- No secrets are committed to the repository.
- All partner credentials come from environment variables or secret managers.
- Replit publication is gated by an explicit `PublishApproval`.
- The web API requires a bearer token in production via `DEMO_ACCESS_TOKEN`.
- Research content is treated as untrusted data, not as instructions.
- Workflow failures are recorded with a sanitized error type, not raw exception text.

## License

[Apache License 2.0](LICENSE)
