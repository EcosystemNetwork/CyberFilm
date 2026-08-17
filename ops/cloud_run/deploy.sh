#!/usr/bin/env bash
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE="${CYBERFILM_SERVICE:-cyberfilm}"

IMAGE="gcr.io/${PROJECT}/${SERVICE}"

echo "Building ${IMAGE}..."
gcloud builds submit --tag "${IMAGE}"

echo "Deploying ${SERVICE} to ${REGION}..."
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 4

echo "Deployed. Set secrets with:"
echo "  gcloud run services update ${SERVICE} --region ${REGION} --set-secrets ..."
