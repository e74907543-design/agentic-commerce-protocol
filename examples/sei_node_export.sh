#!/usr/bin/env bash
set -euo pipefail

: "${SEI_API_BASE:?Set SEI_API_BASE to your SEI environment (e.g., https://sei.example.com)}"
: "${SEI_TOKEN:?Set SEI_TOKEN to a valid bearer token}"

FROM="2025-11-07T10:00:00Z"
TO="2025-11-07T11:00:00Z"
NODE_ID="3426"

curl -sS -H "Authorization: Bearer ${SEI_TOKEN}" \
  "${SEI_API_BASE}/api/v1/nodes/${NODE_ID}/reports?from=${FROM}&to=${TO}&format=pdf&include=telemetry,snapshots,motion" \
  -o "node-${NODE_ID}-report.pdf"

echo "Saved node-${NODE_ID}-report.pdf"

curl -sS -H "Authorization: Bearer ${SEI_TOKEN}" \
  "${SEI_API_BASE}/api/v1/nodes/${NODE_ID}/export.csv?from=${FROM}&to=${TO}&fields=timestamp,lat,lon,temperature,motion" \
  -o "node-${NODE_ID}-telemetry.csv"

echo "Saved node-${NODE_ID}-telemetry.csv"
