# spacetraders-agent

An autonomous-but-advisable LLM-driven agent for the [SpaceTraders](https://spacetraders.io/) game API.

In this project, the agent operates the game on its own, while a human plays the role of strategic advisor. The agent maintains its own plans, notes, and situational awareness, incorporates human guidance thoughtfully (not blindly), and executes actions through a deterministic Python control layer.

This is not a chat bot that "plays a game." It is a long-running system that reasons, plans, acts, and adapts.

---

## High-level goals

* Build an agent that can self-manage SpaceTraders gameplay over long horizons
* Keep authoritative game state and execution in Python, not in the LLM
* Treat LLMs as strategic reasoners, not API callers
* Maintain explicit, inspectable strategy notes and logs
* Allow humans to give advisory guidance that shapes behavior without micromanaging it

---

## Core ideas

* Python owns reality: game state, validation, execution, persistence
* The LLM owns intent: goals, prioritization, planning, reflection
* Notes are state: not chat history, not ephemeral memory
* Human input is advisory: interpreted and integrated, not directly executed

---

## How it works (in brief)

1. The agent refreshes game state from the SpaceTraders API
2. It updates its internal notes based on recent events
3. It incorporates any new human advisory input
4. The LLM reasons about what to do next
5. The LLM outputs a structured intent (not raw API calls)
6. Python validates and executes the intent via the API
7. State and notes are persisted

This loop repeats continuously, subject to cooldowns and scheduling rules enforced by Python.

---

## What this project is (and isn’t)

It is:

* A stateful, autonomous agent architecture
* A practical exploration of human–LLM collaboration
* A platform for experimenting with planning, economics, and strategy

It is not:

* A prompt-only experiment
* A fully generic agent framework
* An MCP-first or tool-driven demo

---

## Status

Early development. Expect rapid iteration and design changes.

If you’re curious about the internal architecture and design rationale, see [`design.md`](design.md).

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency and virtual environment management.

```bash
# Create/refresh the environment and install dependencies
uv sync
```

## Generated API client

We generate a typed HTTP client from the SpaceTraders OpenAPI spec using `openapi-python-client`.

```bash
# Regenerate client code
./tools/generate_client.sh
```

The output lands in `codegen/api_client/`. Regenerate after upstream spec changes.

## Running the agent (headless)

The agent is intended to run without a UI and watch `input.md` for human advisory guidance.

```bash
uv run python -m agent.loop --help  # (once wiring is added)

# For now, run the stub loop once to validate wiring
uv run python -c "from agent.loop import run_loop; run_loop(once=True)"
```

## Testing

```bash
uv run pytest
```
