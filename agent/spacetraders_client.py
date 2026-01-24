from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import sys
from pathlib import Path
from httpx import Response as HTTPXResponse

# Load environment variables from .env file
load_dotenv()

# Ensure generated client package is importable without installation
_ROOT = Path(__file__).resolve().parents[1]
_CODEGEN_PKG = _ROOT / "codegen" / "spacetraders_api_client"
if str(_CODEGEN_PKG) not in sys.path:
    sys.path.insert(0, str(_CODEGEN_PKG))

from spacetraders_api_client import ApiClient, Configuration
from spacetraders_api_client.api.agents_api import AgentsApi
from spacetraders_api_client.api.fleet_api import FleetApi

DEFAULT_BASE_URL = "https://api.spacetraders.io/v2"
ENV_API_KEY = "SPACETRADERS_API_KEY"
ENV_LOG_API = "LOG_API"  # Set to "true" or "1" to enable verbose API logging


@dataclass
class APIResult:
    ok: bool
    status: int
    json: Optional[Dict[str, Any]]
    raw: Optional[bytes]
    error: Optional[str] = None


def _parse_response(resp_obj: Any, endpoint: str = "unknown", logger: Optional[logging.Logger] = None) -> APIResult:
    # Support ApiResponse (status_code + raw_data) and httpx.Response
    log_enabled = os.getenv(ENV_LOG_API, "").lower() in ("true", "1")

    # ApiResponse duck-typing
    if hasattr(resp_obj, "status_code") and hasattr(resp_obj, "raw_data"):
        try:
            status = int(getattr(resp_obj, "status_code"))
            raw = getattr(resp_obj, "raw_data")
            parsed_json = json.loads(raw.decode("utf-8")) if raw else None
            ok = 200 <= status < 300
            if log_enabled and logger and parsed_json is not None:
                logger.info("API Response [%s] status=%d:\n%s", endpoint, status, _pretty(parsed_json))
            return APIResult(ok=ok, status=status, json=parsed_json, raw=raw)
        except Exception as e:
            return APIResult(ok=False, status=-1, json=None, raw=None, error=str(e))

    # httpx.Response fallback
    if isinstance(resp_obj, HTTPXResponse):
        status = resp_obj.status_code
        content = resp_obj.content
        try:
            parsed_json = resp_obj.json()
        except Exception:
            parsed_json = json.loads(content.decode("utf-8")) if content else None
        ok = 200 <= status < 300
        if log_enabled and logger and parsed_json is not None:
            logger.info("API Response [%s] status=%d:\n%s", endpoint, status, _pretty(parsed_json))
        return APIResult(ok=ok, status=status, json=parsed_json, raw=content)

    # Unknown object pattern
    return APIResult(ok=False, status=-1, json=None, raw=None, error="Unrecognized response object")


def _pretty(data: Any) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)


def build_client(token: Optional[str] = None, base_url: str = DEFAULT_BASE_URL) -> Optional[ApiClient]:
    """Create an ApiClient using Configuration and bearer token."""
    tok = token or os.getenv(ENV_API_KEY)
    if not tok:
        return None
    cfg = Configuration(host=base_url, access_token=tok)
    return ApiClient(cfg)


def fetch_my_agent(client: ApiClient, logger: Optional[logging.Logger] = None) -> APIResult:
    log_enabled = os.getenv(ENV_LOG_API, "").lower() in ("true", "1")
    endpoint = "GET /my/agent"

    if log_enabled and logger:
        logger.info("API Request [%s]", endpoint)

    api = AgentsApi(client)
    resp = api.get_my_agent_without_preload_content()
    return _parse_response(resp, endpoint=endpoint, logger=logger)


def fetch_my_ships(client: ApiClient, page: int = 1, limit: int = 10, logger: Optional[logging.Logger] = None) -> APIResult:
    log_enabled = os.getenv(ENV_LOG_API, "").lower() in ("true", "1")
    endpoint = f"GET /my/ships?page={page}&limit={limit}"

    if log_enabled and logger:
        logger.info("API Request [%s]", endpoint)

    api = FleetApi(client)
    resp = api.get_my_ships_without_preload_content(page=page, limit=limit)
    return _parse_response(resp, endpoint=endpoint, logger=logger)

if __name__ == "__main__":
    # Simple test of client and fetching agent info
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("spacetraders_client_test")

    api_client = build_client(token=os.getenv(ENV_API_KEY))
    if not api_client:
        logger.error("API client could not be created. Check your API key.")
        exit(1)

    agent_result = fetch_my_agent(api_client, logger=logger)
    if agent_result.ok:
        logger.info("Fetched agent info successfully:\n%s", _pretty(agent_result.json))
    else:
        logger.error("Failed to fetch agent info: %s", agent_result.error or "Unknown error")
