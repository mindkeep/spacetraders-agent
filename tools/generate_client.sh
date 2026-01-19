#!/usr/bin/env bash
set -euo pipefail

# Generate the SpaceTraders API client using OpenAPI Generator (python-nextgen).
# Requires the pip-installed CLI: `pip install openapi-generator-cli`.
# If you're using uv, you can install it via `uv pip install openapi-generator-cli`.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SPEC_URL="https://raw.githubusercontent.com/SpaceTradersAPI/api-docs/refs/heads/main/reference/SpaceTraders.json"
OUTPUT_DIR="$ROOT_DIR/codegen/spacetraders_api_client"

# Clean output directory to avoid stale files
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

ADDITIONAL_PROPS="packageName=spacetraders_api_client,httpClient=httpx"

if ! command -v openapi-generator-cli >/dev/null 2>&1; then
  echo "Error: 'openapi-generator-cli' not found. Install via 'uv pip install openapi-generator-cli'." >&2
  exit 1
fi

echo "Generating client with openapi-generator-cli (python)..."
openapi-generator-cli generate \
  -g python \
  -i "$SPEC_URL" \
  -o "$OUTPUT_DIR" \
  --additional-properties "$ADDITIONAL_PROPS" \
  --skip-validate-spec

echo "Client generated at: $OUTPUT_DIR"
