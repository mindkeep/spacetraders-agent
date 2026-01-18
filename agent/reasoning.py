from __future__ import annotations

from typing import Any, Dict, Optional
import os
import json

from dotenv import load_dotenv

from .intents import Intent, IntentType

# Load environment variables from .env file
load_dotenv()

# Ollama integration is optional; we fall back to a deterministic stub
# when the local server or model isn't available.
try:
    import ollama
except Exception:  # pragma: no cover
    ollama = None  # type: ignore


INTENT_JSON_SCHEMA = {
    "intent_type": [t.value for t in IntentType],
    "goal": "string",
    "reasoning": "string",
    "details": "object",
}


def _llm_plan(state_snapshot: Optional[Dict[str, Any]], strategy_notes: Optional[str], advisory_input: Optional[str]) -> Optional[Intent]:
    if ollama is None:
        return None

    model = os.getenv("OLLAMA_MODEL", "llama3.1")
    base_url = os.getenv("OLLAMA_BASE_URL")
    client = ollama.Client(host=base_url) if base_url else ollama
    system = (
        "You are an intent planner for a SpaceTraders agent. "
        "Output ONLY JSON with keys: intent_type, goal, reasoning, details. "
        f"intent_type must be one of: {', '.join(INTENT_JSON_SCHEMA['intent_type'])}. "
        "Do not include extra text."
    )

    user = {
        "state": state_snapshot or {},
        "notes": strategy_notes or "",
        "advisory": advisory_input or "",
        "instruction": "Propose the next high-level intent."
    }

    try:
        resp = client.chat(model=model, messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user)},
        ])
        content = resp.get("message", {}).get("content", "")
        data = json.loads(content)
        intent_type_str = str(data.get("intent_type", "")).lower()
        if intent_type_str not in [t.value for t in IntentType]:
            return None
        details = data.get("details") or {}
        return Intent(
            intent_type=IntentType(intent_type_str),
            goal=str(data.get("goal", "")) or "",
            reasoning=str(data.get("reasoning", "")) or "",
            details=details,
            advisory_source="input.md" if advisory_input else None,
        )
    except Exception:
        return None


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

    # Try LLM first if available

    llm_intent = _llm_plan(state_snapshot, strategy_notes, advisory_input)
    if llm_intent is not None:
        return llm_intent

    # Deterministic fallback stub to keep tests and wiring intact
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