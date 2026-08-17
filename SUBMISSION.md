# CyberFilm — Hackathon Submission

## Track

Grafana

## One-liner

An observability-driven AI production supervisor that plans, governs, and
publishes media productions through a real six-stage partner workflow.

## Problem

Media productions spend too much time reconciling research, budget, governance,
and distribution across disconnected tools. When something goes wrong, teams
lack a single observable source of truth to recover quickly.

## Solution

CyberFilm turns a brief into a deterministic multi-stage workflow. Each partner
contributes exactly one bounded responsibility. The control room gives
operators a live view of stage progress, governance decisions, costs, and the
approval-gated Replit handoff.

## Runtime partner use

Every partner is called in real code, not just named in documentation:

- **Google Cloud / Gemini** — `src/cyberfilm/gemini_director.py`, `src/cyberfilm/agent.py`
- **Parallel** — `src/cyberfilm/parallel_research.py`
- **IBM watsonx.governance** — `src/cyberfilm/ibm_governance.py`
- **ClickHouse** — `src/cyberfilm/clickhouse_events.py`
- **Grafana** — `src/cyberfilm/grafana_observability.py`
- **Replit** — `src/cyberfilm/replit_distribution.py`, `src/cyberfilm/replit_runtime.py`

## 3-minute demo script

| Time | Action | Narration |
| --- | --- | --- |
| 0:00 | Open control room at the hosted URL | "CyberFilm is a production control room for media teams." |
| 0:15 | Submit a brief in the form | "A producer enters a brief: a sci-fi short with budget and runtime limits." |
| 0:30 | Timeline lights up through research and direction | "Parallel researches citations, then Gemini on Vertex AI returns a bounded shot plan." |
| 0:50 | Governance appears | "IBM watsonx.governance evaluates the plan and either approves or blocks." |
| 1:05 | ClickHouse and Grafana panels | "Every event and cost is written to ClickHouse; Grafana tells us if the run is healthy." |
| 1:25 | Enter approver and re-submit | "Only with explicit approval does the workflow ask Replit to publish the screening microsite." |
| 1:45 | Replit URL returns | "Replit returns the public app URL. No automatic publication, no bypassed OAuth." |
| 2:00 | Show blocked case | "If governance rejects the plan, the run stops and the dashboard shows why." |
| 2:30 | Show the repository | "All partner adapters, tests, and deployment files are open source under Apache-2.0." |
| 2:55 | Closing | "CyberFilm: plan, govern, observe, and publish with every partner in one workflow." |

## Links

- Repository: https://github.com/EcosystemNetwork/CyberFilm
- Hosted project: *(to be set after Cloud Run deployment)*
- Demo video: *(upload to YouTube or Vimeo and link here)*

## Devpost submission checklist

- [ ] Public repository linked
- [ ] Complete open-source license visible (`LICENSE`)
- [ ] Hosted project URL provided
- [ ] 3-minute public demo video linked
- [ ] Partner track selected: Grafana
- [ ] All source, assets, and run instructions included
- [ ] Runtime partner use documented in code
