# CyberFilm

CyberFilm is an observability-driven AI production supervisor for media teams. It uses Gemini on Google Cloud's Gemini Enterprise Agent Platform to plan and coordinate deterministic production workflows, while Grafana Cloud provides the live operational context used to detect failures, control cost, and guide recovery.

## Partner ecosystem

CyberFilm's primary submission track is Grafana. The production workflow also integrates IBM, Parallel, ClickHouse, and Replit as complementary partner capabilities.

## Production workflow

1. **Parallel** researches rights, locations, audiences, and market context with citations.
2. **Gemini Enterprise Agent Platform** turns the brief and research into a schema-constrained production plan.
3. **IBM watsonx.governance** records and evaluates the agent run before production can continue.
4. **ClickHouse** stores stage transitions, tool calls, costs, quality scores, and approvals.
5. **Grafana** provides the production control room; the supervisor uses live telemetry to diagnose failures and choose allowlisted recovery actions.
6. **Replit** creates or updates an interactive screening and campaign app after explicit human approval.

External side effects and recovery actions are approval-gated. Partner failures degrade safely and remain visible rather than being silently replaced with fake data.

## License

[MIT License](LICENSE)
