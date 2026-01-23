from pathlib import Path

from agent.persistence.sqlite import SQLitePersistence


def test_sqlite_persistence_creates_schema(tmp_path):
    db_path = tmp_path / "agent.db"
    store = SQLitePersistence(db_path)
    store.connect()

    # Ensure tables exist and basic write succeeds
    store.append_log("2024-01-01T00:00:00Z", "test", "hello")
    logs = list(store.fetch_logs())
    assert logs

    store.save_strategy_notes("2024-01-01T00:00:00Z", "notes")
    store.save_state_snapshot("2024-01-01T00:00:00Z", "{}")

    store.close()
    assert Path(db_path).exists()
