"""Main agent loop with OpenAPI-LLM integration.

This module implements a 3-step loop where the LLM maintains complete game state
in strategy notes and directly calls SpaceTraders API tools.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from jsonref import load_uri
from rich.console import Console

from .persistence.sqlite import SQLitePersistence
from .state import get_strategy_notes, save_strategy_notes, get_recent_log_entries

# Load environment variables
load_dotenv()

# Optional integrations
try:
    from openapi_llm.client.openapi import OpenAPIClient
except Exception:  # pragma: no cover
    OpenAPIClient = None  # type: ignore

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


console = Console()

DEFAULT_INPUT_PATH = Path("input.md")
DEFAULT_POLL_INTERVAL_SEC = 10.0
DEFAULT_LLM_MODEL = os.environ.get("OPENAI_MODEL", "mistral-nemo")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "http://localhost:11434/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "ollama")
ENV_API_KEY = "SPACETRADERS_API_KEY"

SYSTEM_PROMPT = """You are an autonomous agent playing SpaceTraders, a space trading and exploration game.

Your responsibilities:
- Maintain complete game state in your notes (ships, locations, credits, cargo, contracts)
- Choose and execute API tools strategically to grow your trading empire
- Learn from results and errors to improve your strategy
- Track timing information (ship arrivals, cooldowns, rate limits)
- Decide when to wait vs. when to act

Your notes are your memory. Always:
- Record the results of every tool call
- Track important identifiers (ship symbols, waypoint names, market symbols)
- Note wait states (ships in transit until time X, cooldown until time Y)
- Update your strategy based on what you learn

When you see errors, adjust your approach and try alternatives."""

STEP1_PROMPT_TEMPLATE = """You have new human guidance. Update your strategy notes to incorporate it.

CURRENT NOTES:
{notes}

HUMAN GUIDANCE:
{advisory}

Provide updated notes that incorporate this guidance while maintaining all critical game state information (ships, locations, credits, etc.)."""

STEP2_PROMPT_TEMPLATE = """Based on your current strategy, choose and execute ONE tool call.

CURRENT NOTES:
{notes}

RECENT HISTORY:
{history}

Choose a tool that advances your strategy. You can:
- Gather information (list ships, check markets, view contracts)
- Take actions (navigate, dock, refuel, trade, mine, accept contracts)
- Do NOT call 'register' - you're already registered

Call the appropriate tool now."""

STEP3_PROMPT_TEMPLATE = """Update your notes with the results of your tool call.

CURRENT NOTES:
{notes}

TOOL CALLED:
{tool_name}

RESULT:
{result}

Update your notes to include:
1. What happened (success or error)
2. New game state information from the result
3. Your next planned action
4. Any wait states (if ship is in transit, note arrival time; if cooldown, note expiry time; if rate limited, note when to retry)

Provide the complete updated notes."""


def _read_input(path: Path) -> Optional[str]:
    """Read advisory input from file."""
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _initialize_openapi_client(api_key: str, logger: Optional[logging.Logger] = None) -> Any:
    """Load SpaceTraders API spec and initialize OpenAPI client."""
    log = logger or logging.getLogger("agent.loop")
    
    if OpenAPIClient is None:
        raise RuntimeError("openapi_llm library not available")
    
    try:
        spec_url = "https://raw.githubusercontent.com/SpaceTradersAPI/api-docs/refs/heads/main/reference/SpaceTraders.json"
        log.info("Loading OpenAPI spec from %s", spec_url)
        client = OpenAPIClient.from_spec(
            openapi_spec=str(load_uri(spec_url)),
            credentials=api_key
        )
        log.info("OpenAPI client initialized")
        return client
    except Exception as e:
        log.error("Failed to initialize OpenAPI client: %s", e)
        raise


def _get_tool_definitions(client: Any) -> list[dict[str, Any]]:
    """Get tool definitions, excluding 'register'."""
    all_tools = client.tool_definitions
    tools = [t for t in all_tools if t.get("name") != "register"]
    return tools


def _extract_wait_duration(result: Any, logger: Optional[logging.Logger] = None) -> Optional[float]:
    """Extract wait duration from API response if present.
    
    Looks for rate limit headers, cooldowns, or arrival times.
    Returns wait duration in seconds, or None if no wait needed.
    """
    log = logger or logging.getLogger("agent.loop")
    
    # Check for rate limit (Retry-After header or similar)
    if isinstance(result, dict):
        # Rate limit response
        if result.get("error", {}).get("code") == 429:
            retry_after = result.get("error", {}).get("data", {}).get("retryAfter")
            if retry_after:
                log.info("Rate limited, retry after %s seconds", retry_after)
                return float(retry_after)
        
        # Check for cooldown in response data
        data = result.get("data", {})
        if "cooldown" in data:
            cooldown = data["cooldown"]
            if "expiration" in cooldown:
                # Parse expiration time and calculate wait
                try:
                    from dateutil.parser import parse
                    expiry = parse(cooldown["expiration"])
                    now = datetime.now(timezone.utc)
                    wait_sec = (expiry - now).total_seconds()
                    if wait_sec > 0:
                        log.info("Cooldown active, wait %s seconds", wait_sec)
                        return wait_sec
                except Exception:
                    pass
        
        # Check for arrival time (ship in transit)
        if "nav" in data:
            route = data["nav"].get("route", {})
            if "arrival" in route:
                try:
                    from dateutil.parser import parse
                    arrival = parse(route["arrival"])
                    now = datetime.now(timezone.utc)
                    wait_sec = (arrival - now).total_seconds()
                    if wait_sec > 0:
                        log.info("Ship in transit, arrives in %s seconds", wait_sec)
                        return wait_sec
                except Exception:
                    pass
    
    return None


def run_loop(
    input_path: Path = DEFAULT_INPUT_PATH,
    poll_interval_sec: float = DEFAULT_POLL_INTERVAL_SEC,
    once: bool = False,
    logger: Optional[logging.Logger] = None,
    prompt_debug: bool = False,
) -> None:
    """Run the main agent loop with OpenAPI-LLM integration.

    The loop operates in 3 steps:
    1. If human input changed, update notes with LLM
    2. LLM chooses and executes a tool based on notes
    3. LLM updates notes with tool results

    Args:
        input_path: Path to advisory input file (input.md)
        poll_interval_sec: Base polling interval
        once: If True, run single iteration and exit
        logger: Optional logger instance
        prompt_debug: If True, display LLM input prompts
    """
    store = SQLitePersistence(Path("agent.db"))
    store.connect()
    log = logger or logging.getLogger("agent.loop")
    log.info("Starting OpenAPI-LLM loop input=%s poll=%.2fs once=%s", input_path, poll_interval_sec, once)

    # Get API key
    api_key = os.environ.get(ENV_API_KEY)
    if not api_key:
        raise ValueError(f"Missing {ENV_API_KEY} environment variable")

    # Initialize OpenAPI client
    openapi_client = _initialize_openapi_client(api_key, logger=log)
    tools = _get_tool_definitions(openapi_client)
    log.info("Loaded %d tool definitions", len(tools))
    # Print tool names and argument names for quick visibility
    for tool in tools:
        func = tool.get("function", {})
        name = func.get("name", tool.get("name", "(unknown)"))
        params = func.get("parameters", {}).get("properties", {})
        required = set(func.get("parameters", {}).get("required", []))
        console.print(f"[green]Tool:[/green] {name}")
        if params:
            arg_list = []
            for arg_name in params.keys():
                suffix = " (required)" if arg_name in required else ""
                arg_list.append(f"{arg_name}{suffix}")
            console.print(f"[blue]Arguments:[/blue] {', '.join(arg_list)}")
        else:
            console.print("[blue]Arguments:[/blue] (none)")

    # Initialize OpenAI/Ollama client
    if OpenAI is None:
        raise RuntimeError("OpenAI library not installed")
    
    llm_client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE,
    )
    log.info("LLM client initialized (model=%s)", DEFAULT_LLM_MODEL)

    last_advisory = None
    iteration = 0
    wait_until = None  # Track when we should resume after a wait
    
    while True:
        iteration += 1
        ts = datetime.now(timezone.utc).isoformat()
        
        # Check if we need to wait
        if wait_until:
            now = datetime.now(timezone.utc)
            if now < wait_until:
                wait_sec = (wait_until - now).total_seconds()
                log.info("Waiting %.1f more seconds before next iteration", wait_sec)
                time.sleep(min(wait_sec, poll_interval_sec))
                continue
            else:
                log.info("Wait period complete, resuming")
                wait_until = None
        
        log.info("=== Iteration %d ===", iteration)
        
        # Get current notes
        notes = get_strategy_notes(store, logger=log)
        if not notes:
            notes = "# SpaceTraders Agent Notes\n\nNo state yet. First action: get agent info and list ships."
            save_strategy_notes(store, ts, notes, logger=log)
        
        # STEP 1: Check for new human input and update notes if needed
        advisory = _read_input(input_path)
        if advisory != last_advisory and advisory:
            last_advisory = advisory
            store.append_log(ts, "advisory", advisory)
            log.info("New advisory received, updating notes")
            
            try:
                prompt = STEP1_PROMPT_TEMPLATE.format(notes=notes, advisory=advisory)
                
                if prompt_debug:
                    console.print(f"\n[yellow]LLM Prompt (STEP1):[/yellow]")
                    console.print(prompt)
                
                response = llm_client.chat.completions.create(
                    model=DEFAULT_LLM_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                updated_notes = response.choices[0].message.content
                if updated_notes:
                    save_strategy_notes(store, ts, updated_notes, logger=log)
                    notes = updated_notes
                    log.info("Notes updated with human guidance")
                    
                    # Show updated notes
                    console.print(f"\n[cyan]Updated Notes (from advisory):[/cyan]")
                    console.print(updated_notes)
            except Exception as e:
                log.error("Failed to update notes with advisory: %s", e)
        
        # Get recent history for context
        history = get_recent_log_entries(store, limit=10, logger=log)
        history_text = "\n".join(history) if history else "(no history yet)"
        
        # STEP 2: LLM chooses and executes a tool
        try:
            prompt = STEP2_PROMPT_TEMPLATE.format(notes=notes, history=history_text)
            response = llm_client.chat.completions.create(
                model=DEFAULT_LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                tools=tools,
            )
            
            message = response.choices[0].message
            
            # Check if tool was called
            if not message.tool_calls:
                log.warning("LLM did not call a tool, retrying next iteration")
                console.print(f"\n[red]⚠ LLM did not call a tool[/red]")
                console.print(f"[yellow]LLM Response:[/yellow]")
                console.print(message.content or "(no content)")
                if prompt_debug:
                    console.print(f"\n[yellow]The prompt that was sent (STEP2):[/yellow]")
                    console.print(prompt)
                if once:
                    break
                time.sleep(poll_interval_sec)
                continue
            
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            log.info("LLM called tool: %s", tool_name)
            store.append_log(ts, "tool_call", tool_name)
            
            # Show LLM decision
            if prompt_debug:
                console.print(f"\n[yellow]LLM Prompt (STEP2):[/yellow]")
                console.print(prompt)
            
            console.print(f"\n[green]LLM Decision:[/green] Calling tool [bold]{tool_name}[/bold]")
            console.print(f"  Arguments: {tool_call.function.arguments}")
            
            # Execute tool via openapi_client
            try:
                result = openapi_client.invoke(response)
                store.append_log(ts, "tool_result", f"{tool_name}: success")
                log.info("Tool executed successfully")
                
                # Show API response
                console.print(f"\n[blue]API Response:[/blue]")
                console.print_json(data=result)
                
                # Check for wait conditions
                wait_duration = _extract_wait_duration(result, logger=log)
                if wait_duration and wait_duration > 0:
                    wait_until = datetime.now(timezone.utc) + timedelta(seconds=wait_duration)
                    log.info("Setting wait until %s", wait_until)
                
            except Exception as e:
                result = {"error": str(e)}
                store.append_log(ts, "tool_error", f"{tool_name}: {str(e)}")
                log.error("Tool execution failed: %s", e)
                console.print(f"\n[red]Tool Error:[/red] {e}")
        
        except Exception as e:
            log.error("Step 2 failed: %s", e)
            result = {"error": str(e)}
            tool_name = "unknown"
        
        # STEP 3: LLM updates notes with results
        try:
            result_str = json.dumps(result, indent=2) if not isinstance(result, str) else result
            prompt = STEP3_PROMPT_TEMPLATE.format(
                notes=notes,
                tool_name=tool_name,
                result=result_str
            )
            
            if prompt_debug:
                console.print(f"\n[yellow]LLM Prompt (STEP3):[/yellow]")
                console.print(prompt)
            
            response = llm_client.chat.completions.create(
                model=DEFAULT_LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            
            updated_notes = response.choices[0].message.content
            if updated_notes:
                save_strategy_notes(store, ts, updated_notes, logger=log)
                log.info("Notes updated with tool results")
                
                # Show updated notes
                console.print(f"\n[cyan]Updated Notes:[/cyan]")
                console.print(updated_notes)
        except Exception as e:
            log.error("Failed to update notes with results: %s", e)
        
        if once:
            log.info("Single iteration complete, exiting")
            break
        
        time.sleep(poll_interval_sec)
    
    log.info("Loop exited")
    store.close()


# Need to import timedelta
from datetime import timedelta


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    run_loop(once=True)
