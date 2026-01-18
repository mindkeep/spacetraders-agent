import pytest

from agent.loop import run_loop


def test_run_loop_once(monkeypatch, tmp_path):
    input_file = tmp_path / "input.md"
    input_file.write_text("Test advisory")

    # Replace time.sleep to avoid delay
    monkeypatch.setattr("agent.loop.time.sleep", lambda _: None)

    # Run a single iteration; should not raise.
    run_loop(input_path=input_file, poll_interval_sec=0, once=True)


def test_run_loop_missing_file(monkeypatch, tmp_path):
    missing_file = tmp_path / "missing.md"
    monkeypatch.setattr("agent.loop.time.sleep", lambda _: None)
    run_loop(input_path=missing_file, poll_interval_sec=0, once=True)
