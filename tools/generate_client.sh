#!/usr/bin/env bash
set -euo pipefail

# Generate the SpaceTraders API client using openapi-python-client.
# Requires uv-managed environment with dependency installed.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SPEC_URL="https://raw.githubusercontent.com/SpaceTradersAPI/api-docs/refs/heads/main/reference/SpaceTraders.json"

uv run openapi-python-client generate \
  --url "$SPEC_URL" \
  --config codegen/openapi-python-client-config.yaml \
  --output-path codegen/api_client \
  --overwrite
