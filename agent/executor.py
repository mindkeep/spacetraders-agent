from __future__ import annotations

import logging
from typing import Optional

from .intents import Intent, IntentType
from .persistence.sqlite import SQLitePersistence
from .spacetraders_client import build_client


def execute_intent(intent: Intent, store: SQLitePersistence, logger: Optional[logging.Logger] = None) -> None:
    """Execute the intent via Python-controlled paths.

    This is a minimal stub; it logs execution and gathers extra data for
    GATHER_MARKET_DATA when possible. Other intents are left as TODOs.
    """
    log = logger or logging.getLogger("agent.executor")
    client = build_client()
    if client is None:
        log.warning("No API client available; skipping execution for %s", intent.summary())
        return

    if intent.intent_type == IntentType.GATHER_MARKET_DATA:
        store.append_log("now", "execute", "gather_market_data")
        log.info("Executing gather_market_data (placeholder)")
        # Future: query markets/supply chain endpoints and persist.
    elif intent.intent_type == IntentType.EXPLORE:
        store.append_log("now", "execute", "explore (TODO)")
        log.info("Executing explore (TODO)")
    elif intent.intent_type == IntentType.REPOSITION:
        store.append_log("now", "execute", "reposition (TODO)")
        log.info("Executing reposition (TODO)")
    elif intent.intent_type == IntentType.TRADE:
        store.append_log("now", "execute", "trade (TODO)")
        log.info("Executing trade (TODO)")
