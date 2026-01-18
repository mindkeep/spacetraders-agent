from __future__ import annotations

from typing import Any, Dict, Optional

from .spacetraders_client import APIResult, build_client, fetch_my_agent, fetch_my_ships


def refresh_state() -> Dict[str, Any]:
    """Fetch authoritative state from SpaceTraders API (if configured).

    Returns a dict summary safe for prompt inclusion and persistence.
    If API token is missing, returns an empty snapshot with a reason.
    """
    client = build_client()
    snapshot: Dict[str, Any] = {
        "source": "SpaceTraders",
        "agent": None,
        "ships": None,
        "errors": [],
    }
    if client is None:
        snapshot["errors"].append("No SPACETRADERS_TOKEN configured or client unavailable")
        return snapshot

    agent_res: APIResult = fetch_my_agent(client)
    if agent_res.ok and agent_res.json is not None:
        snapshot["agent"] = agent_res.json.get("data")
    else:
        snapshot["errors"].append(f"agent: {agent_res.error or agent_res.status}")

    ships_res: APIResult = fetch_my_ships(client, page=1, limit=20)
    if ships_res.ok and ships_res.json is not None:
        snapshot["ships"] = ships_res.json.get("data")
    else:
        snapshot["errors"].append(f"ships: {ships_res.error or ships_res.status}")

    return snapshot
