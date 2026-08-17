# CyberFilm Deployment and Operator Setup

This document explains how to run and deploy CyberFilm safely.

## Local development

```bash
uv sync --extra dev
source .env
uv run python -m cyberfilm.web
```

Open `http://localhost:8080` for the control room.

The local environment does **not** require `DEMO_ACCESS_TOKEN` unless
`ENVIRONMENT=production` is set.

## Docker

```bash
docker build -t cyberfilm .
docker run --env-file .env -p 8080:8080 cyberfilm
```

## Google Cloud Run

1. Ensure `gcloud` is authenticated and the target project is set.
2. Export required variables:

```bash
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_CLOUD_REGION=us-central1
export CYBERFILM_SERVICE=cyberfilm
```

3. Run the deployment script:

```bash
chmod +x ops/cloud_run/deploy.sh
./ops/cloud_run/deploy.sh
```

4. Set partner secrets using Secret Manager and attach them to the service:

```bash
gcloud run services update cyberfilm \
  --region us-central1 \
  --set-secrets DEMO_ACCESS_TOKEN=demo-access-token:latest \
  --set-secrets CLICKHOUSE_PASSWORD=clickhouse-password:latest \
  --set-secrets PARALLEL_API_KEY=parallel-api-key:latest \
  --set-secrets IBM_CLOUD_API_KEY=ibm-cloud-api-key:latest \
  --set-secrets GRAFANA_SERVICE_ACCOUNT_TOKEN=grafana-token:latest \
  --set-env-vars ENVIRONMENT=production
```

Replace the secret names with the actual names in your project.

## Required environment variables

See `.env.example` for the full list. The web service needs at minimum:

- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GEMINI_MODEL`
- `PARALLEL_API_KEY`
- `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, `CLICKHOUSE_DATABASE`,
  `CLICKHOUSE_USERNAME`, `CLICKHOUSE_PASSWORD`
- `GRAFANA_URL`, `GRAFANA_SERVICE_ACCOUNT_TOKEN`
- `IBM_CLOUD_API_KEY`, `IBM_WATSONX_GOV_SERVICE_INSTANCE_ID`,
  `IBM_WATSONX_REGION`
- `DEMO_ACCESS_TOKEN` (in production)
- `ENVIRONMENT` (set to `production` to enforce the token)

## Security notes

- Do not commit `.env` files or service-account JSON to the repository.
- Use Secret Manager for all credentials in Cloud Run.
- Run the service under a dedicated, least-privilege service account.
- The Replit distribution stage is gated behind a `PublishApproval` and must
  be triggered through the confirmation-enabled ADK Agent Runtime.
