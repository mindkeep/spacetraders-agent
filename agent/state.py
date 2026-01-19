from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .spacetraders_client import APIResult, build_client, fetch_my_agent, fetch_my_ships


def analyze_fleet_readiness(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze ship readiness from state snapshot.

    Returns a dict with:
    - total_ships: count of all ships
    - idle_ships: ships ready for new actions (docked, not in transit)
    - busy_ships: ships executing actions (in transit, refueling, etc)
    - ready_for_action: bool, true if any ships are idle
    """
    ships = snapshot.get("ships") or []
    idle_count = 0
    busy_count = 0

    for ship in ships:
        if isinstance(ship, dict):
            # Check nav status: common patterns are "IN_TRANSIT", "DOCKED", "ANCHORED"
            nav_status = ship.get("nav", {}).get("status", "").upper()
            
            # Ship is idle if it's docked or anchored (not actively moving)
            if nav_status in ("DOCKED", "ANCHORED"):
                idle_count += 1
            elif nav_status in ("IN_TRANSIT", ""):
                busy_count += 1
            else:
                # Default to idle if we can't determine status
                idle_count += 1

    total = len(ships)
    return {
        "total_ships": total,
        "idle_ships": idle_count,
        "busy_ships": busy_count,
        "ready_for_action": idle_count > 0,
    }


def refresh_state(logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
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

    agent_res: APIResult = fetch_my_agent(client, logger=logger)
    if agent_res.ok and agent_res.json is not None:
        snapshot["agent"] = agent_res.json.get("data")
    else:
        snapshot["errors"].append(f"agent: {agent_res.error or agent_res.status}")

    ships_res: APIResult = fetch_my_ships(client, page=1, limit=20, logger=logger)
    if ships_res.ok and ships_res.json is not None:
        snapshot["ships"] = ships_res.json.get("data")
    else:
        snapshot["errors"].append(f"ships: {ships_res.error or ships_res.status}")

    return snapshot
