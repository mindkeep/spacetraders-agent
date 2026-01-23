"""Tests for OpenAPI-LLM loop and LLM-managed state."""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

from agent.loop import (
    run_loop,
    _read_input,
    _extract_wait_duration,
    STEP1_PROMPT_TEMPLATE,
    STEP2_PROMPT_TEMPLATE,
    STEP3_PROMPT_TEMPLATE,
)
from agent.state import get_strategy_notes, save_strategy_notes, get_recent_log_entries
from agent.persistence.sqlite import SQLitePersistence


class TestInputReading:
    """Test advisory input file reading."""
    
    def test_read_input_exists(self, tmp_path):
        """Test reading existing input file."""
        input_file = tmp_path / "input.md"
        input_file.write_text("Test advisory content")
        
        result = _read_input(input_file)
        assert result == "Test advisory content"
    
    def test_read_input_missing(self, tmp_path):
        """Test reading missing input file."""
        missing_file = tmp_path / "missing.md"
        result = _read_input(missing_file)
        assert result is None


class TestWaitDurationExtraction:
    """Test wait duration extraction from API responses."""
    
    def test_extract_rate_limit(self):
        """Test extracting wait from rate limit response."""
        response = {
            "error": {
                "code": 429,
                "data": {
                    "retryAfter": 60
                }
            }
        }
        
        duration = _extract_wait_duration(response)
        assert duration == 60.0
    
    def test_extract_no_wait(self):
        """Test response with no wait condition."""
        response = {
            "data": {
                "agent": {
                    "credits": 100000
                }
            }
        }
        
        duration = _extract_wait_duration(response)
        assert duration is None


class TestStrategyNotesPersistence:
    """Test strategy notes storage and retrieval."""
    
    def test_save_and_retrieve_notes(self, tmp_path):
        """Test saving and retrieving strategy notes."""
        db = tmp_path / "test.db"
        store = SQLitePersistence(db)
        store.connect()
        
        ts = datetime.now(timezone.utc).isoformat()
        notes = "# Agent Notes\n\nShip-1 is docked at X1-AA-BB. Credits: 50000."
        
        save_strategy_notes(store, ts, notes)
        
        retrieved = get_strategy_notes(store)
        assert retrieved == notes
        
        store.close()
    
    def test_update_notes(self, tmp_path):
        """Test updating strategy notes."""
        db = tmp_path / "test.db"
        store = SQLitePersistence(db)
        store.connect()
        
        ts = datetime.now(timezone.utc).isoformat()
        
        # Save initial notes
        initial_notes = "Initial state"
        save_strategy_notes(store, ts, initial_notes)
        
        # Update notes
        updated_notes = "Updated state with new ship"
        save_strategy_notes(store, ts, updated_notes)
        
        # Should get updated version
        retrieved = get_strategy_notes(store)
        assert retrieved == updated_notes
        
        store.close()


class TestLogEntries:
    """Test log entry storage and retrieval."""
    
    def test_get_recent_log_entries(self, tmp_path):
        """Test retrieving recent log entries."""
        db = tmp_path / "test.db"
        store = SQLitePersistence(db)
        store.connect()
        
        # Add several log entries
        store.append_log("2024-01-21T10:00:00Z", "tool_call", "get_my_agent")
        store.append_log("2024-01-21T10:01:00Z", "tool_result", "get_my_agent: success")
        store.append_log("2024-01-21T10:02:00Z", "tool_call", "get_my_ships")
        
        entries = get_recent_log_entries(store, limit=10)
        
        assert len(entries) == 3
        assert "get_my_agent" in entries[0]
        assert "get_my_ships" in entries[2]
        
        store.close()


class TestPromptTemplates:
    """Test that prompt templates have required placeholders."""
    
    def test_step1_template(self):
        """Test Step 1 template formatting."""
        result = STEP1_PROMPT_TEMPLATE.format(
            notes="Current notes",
            advisory="Human guidance"
        )
        assert "Current notes" in result
        assert "Human guidance" in result
    
    def test_step2_template(self):
        """Test Step 2 template formatting."""
        result = STEP2_PROMPT_TEMPLATE.format(
            notes="Current notes",
            history="tool_call: get_my_agent"
        )
        assert "Current notes" in result
        assert "tool_call: get_my_agent" in result
    
    def test_step3_template(self):
        """Test Step 3 template formatting."""
        result = STEP3_PROMPT_TEMPLATE.format(
            notes="Current notes",
            tool_name="get_my_agent",
            result='{"data": {"credits": 100000}}'
        )
        assert "Current notes" in result
        assert "get_my_agent" in result
        assert "100000" in result


class TestLoopIntegration:
    """Test main loop integration (mocked)."""
    
    def test_run_loop_missing_api_key(self, monkeypatch, tmp_path):
        """Test loop fails gracefully without API key."""
        monkeypatch.delenv("SPACETRADERS_API_KEY", raising=False)
        
        input_file = tmp_path / "input.md"
        
        with pytest.raises(ValueError, match="SPACETRADERS_API_KEY"):
            run_loop(input_path=input_file, once=True)
    
    def test_read_input_changes(self, tmp_path):
        """Test detecting input file changes."""
        input_file = tmp_path / "input.md"
        
        # Initially no file
        content1 = _read_input(input_file)
        assert content1 is None
        
        # Create file
        input_file.write_text("First advisory")
        content2 = _read_input(input_file)
        assert content2 == "First advisory"
        
        # Update file
        input_file.write_text("Updated advisory")
        content3 = _read_input(input_file)
        assert content3 == "Updated advisory"


class TestNotesInitialization:
    """Test that notes are initialized if missing."""
    
    def test_empty_notes_initialized(self, tmp_path):
        """Test that empty notes get default initialization."""
        db = tmp_path / "test.db"
        store = SQLitePersistence(db)
        store.connect()
        
        # No notes yet
        notes = get_strategy_notes(store)
        assert notes is None
        
        # After initialization
        ts = datetime.now(timezone.utc).isoformat()
        default_notes = "# SpaceTraders Agent Notes\n\nNo state yet."
        save_strategy_notes(store, ts, default_notes)
        
        notes = get_strategy_notes(store)
        assert notes is not None
        assert "No state yet" in notes
        
        store.close()
