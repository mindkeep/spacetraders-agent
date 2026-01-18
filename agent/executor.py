from __future__ import annotations

from typing import Optional

from .intents import Intent, IntentType
from .persistence.sqlite import SQLitePersistence
from .spacetraders_client import build_client


def execute_intent(intent: Intent, store: SQLitePersistence) -> None:
    """Execute the intent via Python-controlled paths.

    This is a minimal stub; it logs execution and gathers extra data for
    GATHER_MARKET_DATA when possible. Other intents are left as TODOs.
    """
    client = build_client()
    # For now, just log that we would execute this intent.
    if intent.intent_type == IntentType.GATHER_MARKET_DATA:
        store.append_log("now", "execute", "gather_market_data")
        # Future: query markets/supply chain endpoints and persist.
    elif intent.intent_type == IntentType.EXPLORE:
        store.append_log("now", "execute", "explore (TODO)")
    elif intent.intent_type == IntentType.REPOSITION:
        store.append_log("now", "execute", "reposition (TODO)")
    elif intent.intent_type == IntentType.TRADE:
        store.append_log("now", "execute", "trade (TODO)")
