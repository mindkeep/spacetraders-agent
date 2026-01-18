from __future__ import annotations

import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from .reasoning import plan_next_intent
from .persistence.sqlite import SQLitePersistence
from .state import refresh_state
from .executor import execute_intent


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

    store = SQLitePersistence(Path("agent.db"))
    store.connect()
    last_seen = None
    while True:
        advisory = _read_input(input_path)
        if advisory != last_seen:
            last_seen = advisory
            # Refresh authoritative state
            snapshot = refresh_state()
            ts = datetime.now(timezone.utc).isoformat()
            store.save_state_snapshot(ts, payload=str(snapshot))
            if advisory:
                store.append_log(ts, "advisory", advisory)

            intent = plan_next_intent(state_snapshot=snapshot, advisory_input=advisory)
            store.append_log(ts, "intent", intent.summary())
            # Execute intent (stubbed)
            execute_intent(intent, store)
            print(intent.summary())  # Temporary signal for wiring tests.

        if once:
            break

        time.sleep(poll_interval_sec)
