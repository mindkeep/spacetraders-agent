# spacetraders-agent – Design Notes

This document captures the architectural principles and design decisions behind spacetraders-agent.

The guiding idea is simple:

> Let the agent run the game.
> Let the human advise.
> Let Python enforce reality.

---

## Design philosophy

### Clear separation of concerns

* Python is the source of truth

  * Game state
  * Derived metrics and analysis
  * Action validation
  * API execution
  * Persistence and scheduling

* LLM is the source of intent

  * Strategic reasoning
  * Goal setting
  * Planning and prioritization
  * Interpreting human advice
  * Maintaining editable strategy notes

This separation is deliberate. It prevents the LLM from hallucinating state, issuing invalid actions, or corrupting history.

---

## The agent loop

At a high level, the agent operates in a continuous loop:

1. Refresh game state
   Pull authoritative data from the SpaceTraders API into Python-managed state.

2. Update operational notes
   Record new facts, outcomes, and observations from the last iteration.

3. Incorporate human advisory input
   Read any new human guidance and treat it as strategic pressure, not a command.

4. Strategic reasoning (LLM)
   Rebuild the prompt using:

   * Current game state (summarized)
   * Current strategy notes
   * Recent immutable log summaries
   * Human advisory input

5. Intent selection (LLM)
   The LLM proposes a *structured intent*, describing what it wants to do and why.

6. Validation and execution (Python)
   Python determines whether the intent is valid, gathers any missing information, and executes the appropriate API calls.

7. Persist state
   Notes, logs, and state are saved for the next iteration.

8. Determine wait time
   There will be times while ships are in transit or not available that there is nothing for the agent to do. Given this, the LLM may ask to wait longer before the next iteration, but we should still poll game state occassionally.

---

## Notes as first-class state

The agent maintains two distinct forms of memory.

### 1. Immutable log (append-only)

Purpose:

* Preserve factual history
* Support summarization and auditing

Examples:

* Trades executed
* Systems entered
* Credits gained or lost
* Human advisory messages received

This log is never rewritten.

---

### 2. Living strategy notes (editable)

Purpose:

* Capture current goals and hypotheses
* Maintain a working plan
* Track assumptions and risks

Examples:

* "Focus on fuel arbitrage in nearby systems"
* "Allocate one ship to scouting"
* "Avoid hostile regions until credits > X"

These notes *can* be rewritten by the LLM as strategy evolves.

Separating immutable history from mutable strategy prevents the agent from rewriting the past to justify new plans.

---

## Human-in-the-loop design

Humans are treated as strategic advisors, not operators.

* Human input does not directly trigger actions
* The LLM interprets advice and decides how (or whether) to adjust plans
* The agent may partially comply, delay, or decline based on context

This preserves agent autonomy while still allowing meaningful guidance.

### Headless operation and advisory input

* The process runs without a UI and is expected to stay up as a long-running service.
* Human guidance arrives via `input.md`; the process should watch/tail this file for changes and ingest new advisory text when it appears.
* Any future UI can layer on top, but `input.md` remains the canonical advisory channel so the agent can run unattended.

---

## Intent-based control (not tool calls)

The LLM does not issue API calls.

Instead, it emits structured intents, for example:

* Explore a region
* Trade a commodity
* Reposition a ship
* Gather additional market data

Each intent includes:

* The goal
* The reasoning
* Any information required

Python translates intents into concrete API actions.

This indirection keeps execution deterministic and debuggable.

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

* LLM-driven rescheduling or tight loops
* Overwriting historical facts
* Thrashing strategies every iteration
* Treating human advice as absolute commands

The current design explicitly mitigates these risks.

---

## Guiding principle

> LLMs are good thinkers.
> Computers are good bookkeepers.
> Don’t confuse the two.
