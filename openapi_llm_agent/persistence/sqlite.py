from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS immutable_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    category TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS strategy_notes (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    updated_ts TEXT NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS error_context (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    ts TEXT NOT NULL,
    intent_summary TEXT,
    error_message TEXT NOT NULL,
    details TEXT NOT NULL
);
"""


class SQLitePersistence:
    """Minimal SQLite wrapper for logs, notes, and state snapshots."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA foreign_keys=ON;")
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def append_log(self, ts: str, category: str, message: str) -> None:
        if self._conn is None:
            raise RuntimeError("Persistence not connected")
        self._conn.execute(
            "INSERT INTO immutable_log (ts, category, message) VALUES (?, ?, ?)",
            (ts, category, message),
        )
        self._conn.commit()

    def save_strategy_notes(self, ts: str, content: str) -> None:
        if self._conn is None:
            raise RuntimeError("Persistence not connected")
        self._conn.execute(
            "REPLACE INTO strategy_notes (id, updated_ts, content) VALUES (1, ?, ?)",
            (ts, content),
        )
        self._conn.commit()

    def save_state_snapshot(self, ts: str, payload: str) -> None:
        if self._conn is None:
            raise RuntimeError("Persistence not connected")
        self._conn.execute(
            "INSERT INTO state_snapshot (ts, payload) VALUES (?, ?)",
            (ts, payload),
        )
        self._conn.commit()

    def fetch_logs(self, limit: int = 100) -> Iterable[tuple]:
        if self._conn is None:
            raise RuntimeError("Persistence not connected")
        cursor = self._conn.execute(
            "SELECT ts, category, message FROM immutable_log ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return cursor.fetchall()

    def save_error_context(self, ts: str, intent_summary: str, error_message: str, details: str) -> None:
        """Save error context for the current iteration.
        
        This replaces any previous error context (id=1) to keep only the most recent failure.
        Errors are separate from the immutable log and are meant to inform the next LLM iteration.
        """
        if self._conn is None:
            raise RuntimeError("Persistence not connected")
        self._conn.execute(
            "REPLACE INTO error_context (id, ts, intent_summary, error_message, details) VALUES (1, ?, ?, ?, ?)",
            (ts, intent_summary, error_message, details),
        )
        self._conn.commit()

    def fetch_error_context(self) -> Optional[tuple]:
        """Fetch the current error context, if any.
        
        Returns a tuple of (ts, intent_summary, error_message, details) or None.
        """
        if self._conn is None:
            raise RuntimeError("Persistence not connected")
        cursor = self._conn.execute(
            "SELECT ts, intent_summary, error_message, details FROM error_context WHERE id = 1"
        )
        return cursor.fetchone()

    def clear_error_context(self) -> None:
        """Clear the current error context after a successful iteration."""
        if self._conn is None:
            raise RuntimeError("Persistence not connected")
        self._conn.execute("DELETE FROM error_context WHERE id = 1")
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
