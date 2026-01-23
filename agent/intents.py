from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class IntentType(str, Enum):
    """High-level intents the LLM can propose.

    These map to Python-controlled execution paths, not direct API calls.
    """

    EXPLORE = "explore"
    TRADE = "trade"
    REPOSITION = "reposition"
    GATHER_MARKET_DATA = "gather_market_data"


@dataclass
class Intent:
    """Structured intent emitted by the LLM for Python to validate/execute."""

    intent_type: IntentType
    goal: str
    reasoning: str
    details: Dict[str, object] = field(default_factory=dict)
    advisory_source: Optional[str] = None

    def summary(self) -> str:
        """Return a compact, human-readable summary for logging/debugging."""

        return f"{self.intent_type.value}: {self.goal}"