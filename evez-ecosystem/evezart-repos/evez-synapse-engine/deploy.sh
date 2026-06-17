#!/usr/bin/env bash
# EvezArt Synapse Engine — GCP Cloud Run Functions Deploy Script
# Usage: ./deploy.sh <GCP_PROJECT_ID> [region]
set -euo pipefail

PROJECT_ID="${1:?Usage: ./deploy.sh <GCP_PROJECT_ID> [region]}"
REGION="${2:-us-central1}"
FUNCTION_NAME="evez-synapse-broker"

echo "==> Enabling required Google Cloud APIs..."
gcloud services enable \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  --project="$PROJECT_ID"

echo "==> Creating EVEZ_GITHUB_TOKEN secret (if not exists)..."
gcloud secrets describe EVEZ_GITHUB_TOKEN --project="$PROJECT_ID" 2>/dev/null || \
  gcloud secrets create EVEZ_GITHUB_TOKEN --replication-policy=automatic --project="$PROJECT_ID"

echo ""
echo ">>> Add your GitHub PAT to the vault:"
echo "    echo -n 'github_pat_YOUR_PAT' | gcloud secrets versions add EVEZ_GITHUB_TOKEN --data-file=- --project=$PROJECT_ID"
echo ""

gcloud functions deploy "$FUNCTION_NAME" \
  --gen2 \
  --runtime=python310 \
  --region="$REGION" \
  --trigger-http \
  --entry-point=route_signal \
  --set-env-vars GCP_PROJECT_ID="$PROJECT_ID" \
  --allow-unauthenticated \
  --project="$PROJECT_ID"

FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
  --gen2 --region="$REGION" --project="$PROJECT_ID" \
  --format="value(serviceConfig.uri)")

echo "==> DEPLOYED: $FUNCTION_URL"
echo ""
echo "Test:"
echo "  curl -X POST $FUNCTION_URL -H 'Content-Type: application/json' -d '{\"action\": \"list_repos\"}'"
