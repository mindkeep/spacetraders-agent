from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .executor import execute_intent
from .persistence.sqlite import SQLitePersistence
from .reasoning import plan_next_intent
from .state import refresh_state, analyze_fleet_readiness


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
    logger: Optional[logging.Logger] = None,
) -> None:
    """Headless control loop stub.

    Watches the advisory file for new guidance, invokes reasoning to pick
    an intent, and delegates execution (to be implemented). In production
    this will enforce cooldowns, persistence, and scheduling.
    """

    store = SQLitePersistence(Path("agent.db"))
    store.connect()
    log = logger or logging.getLogger("agent.loop")
    log.info("Starting run_loop input=%s poll=%.2fs once=%s", input_path, poll_interval_sec, once)

    last_seen = None
    while True:
        advisory = _read_input(input_path)
        if advisory != last_seen:
            last_seen = advisory
            log.info("Advisory updated len=%s", len(advisory) if advisory else 0)
            # Refresh authoritative state
            snapshot = refresh_state(logger=log)
            ts = datetime.now(timezone.utc).isoformat()
            store.save_state_snapshot(ts, payload=str(snapshot))
            if advisory:
                store.append_log(ts, "advisory", advisory)
                log.info("Logged advisory at %s", ts)
            if snapshot.get("errors"):
                log.warning("State errors: %s", snapshot.get("errors"))
            else:
                log.info("State refreshed (agent=%s ships=%s)", bool(snapshot.get("agent")), len(snapshot.get("ships") or [] if snapshot.get("ships") else 0))
            
            # Analyze fleet readiness
            readiness = analyze_fleet_readiness(snapshot)
            log.info("Fleet readiness: total=%d idle=%d busy=%d ready=%s", 
                     readiness["total_ships"], readiness["idle_ships"], readiness["busy_ships"], 
                     readiness["ready_for_action"])

            intent = plan_next_intent(state_snapshot=snapshot, advisory_input=advisory, logger=log)
            store.append_log(ts, "intent", intent.summary())
            log.info("Selected intent: %s", intent.summary())
            # Execute intent (stubbed)
            execute_intent(intent, store, logger=log)
            
            # Adjust next sleep based on fleet readiness
            # If ships are idle, check sooner; if busy, we can wait longer
            effective_poll_interval = poll_interval_sec
            if not readiness["ready_for_action"]:
                # Ships are busy; increase wait time since we can't act yet
                effective_poll_interval = min(poll_interval_sec * 2, 60.0)
                log.info("Ships busy; increasing poll interval to %.1fs", effective_poll_interval)
        
        if once:
            break
        
        time.sleep(poll_interval_sec)
