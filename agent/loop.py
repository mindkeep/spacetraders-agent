from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from .reasoning import plan_next_intent


DEFAULT_INPUT_PATH = Path("input.md")
DEFAULT_POLL_INTERVAL_SEC = 5.0


def _read_input(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def run_loop(
    input_path: Path = DEFAULT_INPUT_PATH,
    poll_interval_sec: float = DEFAULT_POLL_INTERVAL_SEC,
    once: bool = False,
) -> None:
    """Headless control loop stub.

    Watches the advisory file for new guidance, invokes reasoning to pick
    an intent, and delegates execution (to be implemented). In production
    this will enforce cooldowns, persistence, and scheduling.
    """

    last_seen = None
    while True:
        advisory = _read_input(input_path)
        if advisory != last_seen:
            last_seen = advisory
            intent = plan_next_intent(advisory_input=advisory)
            # TODO: validate intent against game state and execute via API client.
            print(intent.summary())  # Temporary signal for wiring tests.

        if once:
            break

        time.sleep(poll_interval_sec)
