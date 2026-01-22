# spacetraders-agent – Design Notes

This document captures the architectural principles and design decisions behind spacetraders-agent.

The guiding idea is simple:

> Let the agent run the game.
> Let the human advise.
> Let Python enforce reality.

---

## Design philosophy

### LLM-managed state with Python execution

The agent now operates with the LLM maintaining game state in strategy notes rather than Python managing authoritative state.

* **LLM responsibilities:**
  * Track complete game state in notes (ships, locations, credits, cargo, etc.)
  * Maintain strategy and tactical plans
  * Execute tool calls via OpenAPI
  * Learn from results and errors
  * Incorporate human guidance
  * Decide when to wait (ships in transit, cooldowns, rate limits)

* **Python responsibilities:**
  * Provide OpenAPI tool definitions from SpaceTraders spec
  * Execute tool calls through openapi_llm
  * Persist notes and log history
  * Handle rate limiting and wait states
  * Capture and feed back execution errors

This approach trusts the LLM to maintain accurate state by recording tool results in notes, making the system more autonomous and adaptive.

---

## The agent loop

The agent operates in a 3-step cycle with LLM-managed state:

### Step 1: Incorporate Human Input (if present)

When new advisory input arrives:
* LLM reads current strategy notes
* LLM reads human guidance
* LLM updates notes to reflect new priorities or constraints
* Human input becomes part of the strategic context

### Step 2: Execute Tool Call

Based on current notes and recent history:
* LLM selects appropriate SpaceTraders API tool to call
* Tool definitions provided via openapi_llm from OpenAPI spec
* LLM can gather data (list ships, check markets) or take actions (navigate, trade)
* Tool execution results or errors are captured

### Step 3: Update Notes with Results

After tool execution:
* LLM receives tool results (success data or error messages)
* LLM updates strategy notes with:
  * Current game state (ships, locations, credits, cargo)
  * What just happened (action taken, data gathered)
  * What to do next (immediate next steps)
  * Wait states (ships in transit, cooldowns, rate limits)
* Notes become the authoritative state for the next iteration

### Wait Handling

The loop intelligently pauses when:
* **API rate limits** are encountered → wait prescribed duration
* **Ships in transit** → wait until arrival time
* **Cooldowns active** → wait until cooldown expires
* **No immediate actions** → poll at reduced frequency

Wait states are detected from API responses and LLM note updates.

---

## Error feedback and learning

Execution errors guide the LLM's next decision:

* When a tool call fails, Python captures:
  * The tool that was called
  * The error message from the API
  * Full context (parameters, response)

* Errors are logged in immutable history for audit

* In Step 3, the LLM receives error information and:
  * Updates notes with what went wrong
  * Adjusts strategy to avoid repeating the mistake
  * Plans alternative approaches

This direct error-to-LLM feedback enables rapid adaptation without separate error context tables.

---

## Notes as complete game state

Strategy notes now serve as the **single source of truth** for game state between iterations.

The LLM maintains in notes:
* **Current state:** ships (names, locations, status), credits, cargo, contracts
* **Recent actions:** what tools were called, what happened
* **Strategy:** current goals, priorities, plans
* **Next steps:** immediate actions to take
* **Wait states:** expected completion times, cooldowns

Python trusts the LLM to maintain accurate state by:
* Recording all tool results
* Tracking identifiers (ship symbols, waypoint names, etc.)
* Noting timing information (arrival times, cooldowns)

This makes the agent more autonomous - the LLM has complete context and control.

---

## Human-in-the-loop design

Humans provide strategic guidance through `input.md`:

* Human writes advisory text to `input.md`
* Loop detects new input
* LLM reads notes + human input in Step 1
* LLM decides how to incorporate guidance
* LLM updates notes to reflect new priorities

The agent remains autonomous - it interprets and adapts human guidance rather than blindly following commands.

---

## Direct tool calling (via openapi_llm)

The LLM calls SpaceTraders API tools directly:

* Tool definitions generated from OpenAPI spec
* LLM sees all available endpoints (except register)
* LLM chooses tools based on strategy in notes
* openapi_llm handles tool execution
* Results flow back to LLM for note updates

Benefits:
* Maximum flexibility - LLM can call any valid API endpoint
* No Python translation layer between intent and action
* Direct error messages improve learning
* Self-documenting through OpenAPI schema

### Persistence and logging

* Authoritative game state, operational logs, and strategy notes are stored in SQLite for durability and easy inspection.
* Treat SQLite as the single source of truth for persisted data; any file-based logs are secondary/derived artifacts.
* Persistence should cover both immutable history and editable strategy notes to avoid drift between memory and reality.

---

## MCP and tooling considerations

This project deliberately starts without an MCP (Model Control Protocol) server.

Reasons:

* The agent is domain-specific (SpaceTraders)
* Python mediates all execution anyway
* MCP adds complexity without immediate benefit

MCP may be introduced later if:

* Multiple agents share the same toolset
* Models need to be swapped freely
* SpaceTraders becomes one tool among many

If introduced, MCP would expose high-level actions, not raw API endpoints.

---

## Failure modes to guard against

* **State drift:** LLM must accurately record tool results in notes
* **Rate limiting:** Respect API limits and wait appropriately  
* **Tight loops:** Detect wait states to avoid wasted API calls
* **Ignoring errors:** Ensure errors are incorporated into strategy
* **Losing context:** Notes must retain critical identifiers and timing

The current design addresses these through:
* Explicit note update step after each tool call
* Wait detection from API responses
* Error logging and feedback
* LLM responsibility for state tracking

---

## Guiding principle

> LLMs can track state in context.
> Python handles tools and timing.
> Trust the LLM to learn and adapt.
