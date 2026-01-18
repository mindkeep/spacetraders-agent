from __future__ import annotations

from typing import Any, Dict, Optional

from .intents import Intent, IntentType


def plan_next_intent(
    state_snapshot: Optional[Dict[str, Any]] = None,
    strategy_notes: Optional[str] = None,
    advisory_input: Optional[str] = None,
) -> Intent:
    """Select the next high-level intent.

    This is a placeholder for the LLM-driven reasoning stage. In production,
    this function will orchestrate prompt construction, LLM invocation, and
    intent parsing. For now, it returns a deterministic stub to keep the
    control loop and tests wired up.
    """

    goal = "Assess market opportunities"
    reasoning = "Placeholder: replace with LLM-driven strategy selection."
    details = {
        "state_summary": bool(state_snapshot),
        "notes_present": bool(strategy_notes),
        "advisory_present": bool(advisory_input),
    }

    return Intent(
        intent_type=IntentType.GATHER_MARKET_DATA,
        goal=goal,
        reasoning=reasoning,
        details=details,
        advisory_source="input.md" if advisory_input else None,
    )