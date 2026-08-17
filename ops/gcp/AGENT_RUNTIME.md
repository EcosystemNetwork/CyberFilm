# ADK Agent Runtime deployment

CyberFilm ships two ADK agents that can run on Google Cloud's Agent Runtime
(Agent Engine):

- `cyberfilm_director` — bounded shot planning from a brief and cited research
- `replit_distribution_builder` — confirmation-gated Replit MCP publication

## Prerequisites

1. Enable the Vertex AI and Agent Runtime APIs:

```bash
gcloud services enable aiplatform.googleapis.com
```

2. Set the same environment variables used by the web service:

```bash
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_CLOUD_LOCATION=us-central1
export GEMINI_MODEL=gemini-3.5-flash
```

3. Create a Cloud Storage staging bucket:

```bash
gcloud storage buckets create gs://${GOOGLE_CLOUD_PROJECT}-adk-staging \
  --location ${GOOGLE_CLOUD_LOCATION}
```

## Install the SDK

```bash
pip install 'google-cloud-aiplatform[adk,agent_engines]>=1.163.0'
```

## Deploy from the ADK CLI

The ADK provides an `adk deploy` command for Agent Runtime. From the repository
root, deploy the two agents:

```bash
adk deploy agent_engine \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --region ${GOOGLE_CLOUD_LOCATION} \
  --staging_bucket gs://${GOOGLE_CLOUD_PROJECT}-adk-staging \
  src/cyberfilm/agent_runtime.py

adk deploy agent_engine \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --region ${GOOGLE_CLOUD_LOCATION} \
  --staging_bucket gs://${GOOGLE_CLOUD_PROJECT}-adk-staging \
  src/cyberfilm/replit_runtime.py
```

> The exact `adk` CLI syntax can vary by ADK version. Run `adk deploy --help`
> and follow the current official ADK Agent Engine guide if the flags above
> differ.

## Deploy from Python

Alternatively, deploy programmatically:

```python
import os
import vertexai
from cyberfilm.agent_runtime import app as director_app
from cyberfilm.replit_runtime import distribution_app

client = vertexai.Client(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)

staging = f"gs://{os.getenv('GOOGLE_CLOUD_PROJECT')}-adk-staging"

director = client.agent_engines.create(
    agent=director_app,
    display_name="cyberfilm_director",
    config={
        "requirements": ["google-cloud-aiplatform[adk,agent_engines]>=1.163.0"],
        "staging_bucket": staging,
    },
)

print(director.resource_name)

distribution = client.agent_engines.create(
    agent=distribution_app,
    display_name="replit_distribution_builder",
    config={
        "requirements": ["google-cloud-aiplatform[adk,agent_engines]>=1.163.0"],
        "staging_bucket": staging,
    },
)

print(distribution.resource_name)
```

## Calling a deployed agent

```python
import vertexai

client = vertexai.Client(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)

agent = client.agent_engines.get(
    name="projects/PROJECT/locations/LOCATION/reasoningEngines/ENGINE_ID"
)

for event in agent.stream_query(message="Plan a 60-second sci-fi teaser."):
    print(event)
```

## Replit OAuth

The Replit distribution agent uses the official Replit MCP endpoint and relies
on interactive OAuth discovery. Do not paste or commit a bearer token; the MCP
toolset will request confirmation for every Replit tool call.

## Security

- Treat all research text as untrusted data, not as instructions.
- The Replit agent requires `require_confirmation=True` on all tools.
- Use a least-privilege service account for the deployed agent runtime.
