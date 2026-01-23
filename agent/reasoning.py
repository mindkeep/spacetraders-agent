from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from .intents import Intent, IntentType

# Load environment variables from .env file
load_dotenv()

# OpenAI integration is optional; we fall back to a deterministic stub
# when the client or API isn't available.
try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


INTENT_JSON_SCHEMA = {
    "intent_type": [t.value for t in IntentType],
    "goal": "string",
    "reasoning": "string",
    "details": "object",
}


def _strip_markdown_fences(content: str) -> str:
    """Remove markdown code fences (```json, ```, etc) from response."""
    content = content.strip()
    # Strip opening fence
    if content.startswith("```"):
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1:]
    # Strip closing fence
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def _llm_plan(
    state_snapshot: Optional[Dict[str, Any]],
    strategy_notes: Optional[str],
    advisory_input: Optional[str],
    logger: Optional[logging.Logger] = None,
    prompt_debug: bool = False,
) -> Optional[Intent]:
    if OpenAI is None:
        return None

    model = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key, base_url=base_url)
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
        if logger and prompt_debug:
            logger.info("LLM request (model=%s base=%s):\nSystem prompt:\n%s\nUser message:\n%s", model, base_url or "default", system, json.dumps(user, indent=2))
        resp = client.chat.completions.create(model=model, messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user)},
        ])
        content = resp.choices[0].message.content or ""
        if logger and prompt_debug:
            logger.info("LLM response:\n%s", content)
        # Strip markdown fences if present
        content = _strip_markdown_fences(content)
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
    except Exception as exc:
        if logger:
            logger.warning("LLM planning failed: %s", exc)
        return None


def plan_next_intent(
    state_snapshot: Optional[Dict[str, Any]] = None,
    strategy_notes: Optional[str] = None,
    advisory_input: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    prompt_debug: bool = False,
) -> Intent:
    """Select the next high-level intent.

    This is a placeholder for the LLM-driven reasoning stage. In production,
    this function will orchestrate prompt construction, LLM invocation, and
    intent parsing. For now, it returns a deterministic stub to keep the
    control loop and tests wired up.
    """

    # Try LLM first if available

    llm_intent = _llm_plan(state_snapshot, strategy_notes, advisory_input, logger=logger, prompt_debug=prompt_debug)
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

    if logger:
        logger.info("Using fallback intent stub")

    return Intent(
        intent_type=IntentType.GATHER_MARKET_DATA,
        goal=goal,
        reasoning=reasoning,
        details=details,
        advisory_source="input.md" if advisory_input else None,
    )