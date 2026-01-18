from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from httpx import Response as HTTPXResponse

# Load environment variables from .env file
load_dotenv()

try:
    from codegen.spacetraders_api_client.client import AuthenticatedClient
    from codegen.spacetraders_api_client.api.agents.get_my_agent import sync_detailed as get_my_agent
    from codegen.spacetraders_api_client.api.fleet.get_my_ships import sync_detailed as get_my_ships
except ImportError:
    AuthenticatedClient = None  # type: ignore
    get_my_agent = None  # type: ignore
    get_my_ships = None  # type: ignore


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
    # The generated client returns a typed Response with .content (bytes) and .status_code
    log_enabled = os.getenv(ENV_LOG_API, "").lower() in ("true", "1")
    try:
        status = int(getattr(resp_obj, "status_code"))
        content = getattr(resp_obj, "content")
        parsed_json = json.loads(content.decode("utf-8")) if content else None
        ok = 200 <= status < 300
        
        if log_enabled and logger and parsed_json is not None:
            logger.info("API Response [%s] status=%d:\n%s", endpoint, status, _pretty(parsed_json))
        
        return APIResult(ok=ok, status=status, json=parsed_json, raw=content)
    except Exception as e:
        try:
            # If we got a httpx.Response instead
            if isinstance(resp_obj, HTTPXResponse):
                status = resp_obj.status_code
                content = resp_obj.content
                parsed_json = resp_obj.json()
                ok = 200 <= status < 300
                
                if log_enabled and logger and parsed_json is not None:
                    logger.info("API Response [%s] status=%d:\n%s", endpoint, status, _pretty(parsed_json))
                
                return APIResult(ok=ok, status=status, json=parsed_json, raw=content)
        except Exception:
            pass
        return APIResult(ok=False, status=-1, json=None, raw=None, error=str(e))


def _pretty(data: Any) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)


def build_client(token: Optional[str] = None, base_url: str = DEFAULT_BASE_URL) -> Optional[AuthenticatedClient]:
    """Create an AuthenticatedClient if codegen is importable and token exists."""
    if AuthenticatedClient is None:
        return None
    tok = token or os.getenv(ENV_API_KEY)
    if not tok:
        return None
    # Construct client; allow reasonable defaults.
    return AuthenticatedClient(
        base_url=base_url,
        token=tok,
        verify_ssl=True,
        timeout=30.0,
        raise_on_unexpected_status=False,
    )


def fetch_my_agent(client: AuthenticatedClient, logger: Optional[logging.Logger] = None) -> APIResult:
    if get_my_agent is None:
        return APIResult(ok=False, status=-1, json=None, raw=None, error="client unavailable")
    
    log_enabled = os.getenv(ENV_LOG_API, "").lower() in ("true", "1")
    endpoint = "GET /my/agent"
    
    if log_enabled and logger:
        logger.info("API Request [%s]", endpoint)
    
    resp = get_my_agent(client=client)
    return _parse_response(resp, endpoint=endpoint, logger=logger)


def fetch_my_ships(client: AuthenticatedClient, page: int = 1, limit: int = 10, logger: Optional[logging.Logger] = None) -> APIResult:
    if get_my_ships is None:
        return APIResult(ok=False, status=-1, json=None, raw=None, error="client unavailable")
    
    log_enabled = os.getenv(ENV_LOG_API, "").lower() in ("true", "1")
    endpoint = f"GET /my/ships?page={page}&limit={limit}"
    
    if log_enabled and logger:
        logger.info("API Request [%s]", endpoint)
    
    resp = get_my_ships(client=client, page=page, limit=limit)
    return _parse_response(resp, endpoint=endpoint, logger=logger)
