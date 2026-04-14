#!/usr/bin/env bash
set -euo pipefail

# Simple GCP GPU model host control helper.
#
# Requirements:
# - gcloud installed and authenticated
# - permissions to compute.instances start/stop/describe
#
# Example:
#   ./homelab/scripts/gcp-model-host.sh status
#   ./homelab/scripts/gcp-model-host.sh start
#   ./homelab/scripts/gcp-model-host.sh stop

PROJECT="${PROJECT:-nodebase-473513}"
ZONE="${ZONE:-us-central1-a}"
INSTANCE="${INSTANCE:-ollama-gpu-1}"

cmd="${1:-status}"

case "$cmd" in
  start)
    gcloud compute instances start "$INSTANCE" --project "$PROJECT" --zone "$ZONE" --quiet
    ;;
  stop)
    gcloud compute instances stop "$INSTANCE" --project "$PROJECT" --zone "$ZONE" --quiet
    ;;
  status)
    gcloud compute instances describe "$INSTANCE" --project "$PROJECT" --zone "$ZONE" \
      --format="table(name,status,zone.basename(),networkInterfaces[0].accessConfigs[0].natIP)"
    ;;
  *)
    echo "Usage: $(basename "$0") {start|stop|status}" >&2
    exit 1
    ;;
esac
