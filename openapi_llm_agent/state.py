from __future__ import annotations

import logging
from typing import Optional


def get_strategy_notes(store, logger: Optional[logging.Logger] = None) -> Optional[str]:
    """Fetch current strategy notes from persistence.
    
    Strategy notes contain the LLM's complete game state tracking,
    including ships, locations, credits, and next steps.
    """
    try:
        cursor = store._conn.execute(
            "SELECT content FROM strategy_notes WHERE id = 1"
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as exc:
        if logger:
            logger.warning("Failed to fetch strategy notes: %s", exc)
        return None


def save_strategy_notes(store, ts: str, content: str, logger: Optional[logging.Logger] = None) -> None:
    """Save updated strategy notes to persistence.
    
    Args:
        store: SQLitePersistence instance
        ts: Timestamp string
        content: Updated notes content from LLM
        logger: Optional logger
    """
    try:
        store.save_strategy_notes(ts, content)
    except Exception as exc:
        if logger:
            logger.error("Failed to save strategy notes: %s", exc)
        raise


def get_recent_log_entries(store, limit: int = 20, logger: Optional[logging.Logger] = None) -> list[str]:
    """Fetch recent log entries formatted for prompt inclusion.
    
    Returns a list of strings like: "2024-01-21 14:30:45 tool_call: get_my_agent"
    """
    try:
        cursor = store._conn.execute(
            "SELECT ts, category, message FROM immutable_log ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        # Reverse to get chronological order
        return [f"{ts} {category}: {message}" for ts, category, message in reversed(rows)]
    except Exception as exc:
        if logger:
            logger.warning("Failed to fetch recent logs: %s", exc)
        return []
