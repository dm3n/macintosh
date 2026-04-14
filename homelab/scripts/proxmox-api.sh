#!/usr/bin/env bash
set -euo pipefail

SECRETS_FILE="${SECRETS_FILE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.secrets/proxmox-api.env}"

if [[ ! -f "$SECRETS_FILE" ]]; then
  echo "Missing secrets file: $SECRETS_FILE" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$SECRETS_FILE"

if [[ -z "${PVE_HOST:-}" || -z "${PVE_TOKEN_ID:-}" || -z "${PVE_TOKEN_SECRET:-}" ]]; then
  echo "Missing required variables in $SECRETS_FILE (PVE_HOST, PVE_TOKEN_ID, PVE_TOKEN_SECRET)" >&2
  exit 1
fi

if [[ $# -lt 2 ]]; then
  echo "Usage: $(basename "$0") <METHOD> <API_PATH> [curl args...]" >&2
  echo "Example: $(basename "$0") GET /nodes" >&2
  exit 1
fi

method="$1"
path="$2"
shift 2

auth_header="Authorization: PVEAPIToken=${PVE_TOKEN_ID}=${PVE_TOKEN_SECRET}"
url="https://${PVE_HOST}/api2/json${path}"

curl -ksS -X "$method" -H "$auth_header" "$url" "$@"
