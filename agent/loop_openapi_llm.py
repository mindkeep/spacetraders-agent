"""OpenAPI-LLM integration loop.

This module provides a simplified agent loop that leverages openapi_llm
to automatically generate tool definitions from the SpaceTraders OpenAPI spec,
allowing the LLM to call any endpoint it wants to try and make credits.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv
from rich.console import Console
from jsonref import load_uri

# Load environment variables from .env file
load_dotenv()

# Optional LLM integration
try:
    from openapi_llm.client.openapi import OpenAPIClient
except Exception:  # pragma: no cover
    OpenAPIClient = None  # type: ignore

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


console = Console()
DEFAULT_LLM_MODEL = os.environ.get("OPENAI_MODEL", "mistral-nemo")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "http://localhost:11434/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "ollama")
ENV_API_KEY = "SPACETRADERS_API_KEY"


def _initialize_openapi_client(api_key: str) -> Any:
    """Load the SpaceTraders API spec and initialize the OpenAPI client.
    
    Args:
        api_key: SpaceTraders API key for authentication
        
    Returns:
        Initialized OpenAPIClient instance
    """
    console.print("[bold cyan]Initializing OpenAPI client...[/bold cyan]")
    
    if OpenAPIClient is None:
        console.print("[red]✗ openapi_llm not installed[/red]")
        raise RuntimeError("openapi_llm library not available")
    
    try:
        spec_url = "https://raw.githubusercontent.com/SpaceTradersAPI/api-docs/refs/heads/main/reference/SpaceTraders.json"
        client = OpenAPIClient.from_spec(
            openapi_spec=str(load_uri(spec_url)),
            credentials=api_key
        )
        console.print("[green]✓[/green] Initialized OpenAPI client")
        return client
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize OpenAPI client: {e}[/red]")
        raise


def _get_tool_definitions(client: Any) -> list[dict[str, Any]]:
    """Get tool definitions from the client, excluding the 'register' tool.
    
    Args:
        client: OpenAPIClient instance
        
    Returns:
        List of tool definitions excluding the register tool
    """
    all_tools = client.tool_definitions
    
    # Filter out the register tool
    tools = [t for t in all_tools if t.get("name") != "register"]
    
    console.print(f"[cyan]Found {len(tools)} tools (excluded: register)[/cyan]")
    return tools


def _format_api_response(response: Any, title: str = "API Response") -> None:
    """Pretty print API response using rich console."""
    console.print(f"\n[bold blue]{title}[/bold blue]")
    try:
        if isinstance(response, str):
            response_data = json.loads(response)
        else:
            response_data = response
        console.print_json(data=response_data)
    except (json.JSONDecodeError, TypeError):
        console.print(response)


def _llm_call(
    llm_client: Any,
    tools: list[dict[str, Any]],
    user_message: str,
    logger: Optional[logging.Logger] = None,
) -> Optional[Any]:
    """Make a call to the LLM with available tools.
    
    Args:
        llm_client: OpenAI client instance
        tools: List of available tool definitions
        user_message: The user message to send to the LLM
        logger: Optional logger instance
        
    Returns:
        The LLM's response or None if unavailable
    """
    if llm_client is None:
        if logger:
            logger.warning("OpenAI client not available; skipping LLM call")
        console.print("[yellow]⚠ OpenAI client not available; cannot call LLM[/yellow]")
        return None

    if logger:
        logger.info("Making LLM call with user message: %s", user_message)

    try:
        console.print("\n[bold cyan]Calling LLM...[/bold cyan]")
        response = llm_client.chat.completions.create(
            model=DEFAULT_LLM_MODEL,
            messages=[{"role": "user", "content": user_message}],
            tools=tools,
        )
        
        console.print("\n[bold cyan]LLM Response:[/bold cyan]")
        
        # Print the assistant's thinking/response
        if response.choices and response.choices[0].message:
            msg = response.choices[0].message
            if msg.content:
                console.print(f"[green]{msg.content}[/green]")
            
            # Print tool calls if any
            if msg.tool_calls:
                console.print("\n[bold yellow]Tool Calls:[/bold yellow]")
                for tool_call in msg.tool_calls:
                    console.print_json(data={"id": tool_call.id, "function": {"name": tool_call.function.name, "arguments": tool_call.function.arguments}})
        
        return response
    except Exception as e:
        if logger:
            logger.error("LLM call failed: %s", e)
        console.print(f"[red]✗ LLM call failed: {e}[/red]")
        return None


def _execute_tool_call(
    openapi_client: Any,
    llm_response: Any,
    logger: Optional[logging.Logger] = None,
) -> Any:
    """Execute tool calls from the LLM response using the OpenAPI client.
    
    Args:
        openapi_client: OpenAPIClient instance
        llm_response: Response from the LLM with tool calls
        logger: Optional logger instance
        
    Returns:
        The result of the tool call(s)
    """
    if logger:
        logger.info("Executing tool call from LLM response")

    try:
        result = openapi_client.invoke(llm_response)
        _format_api_response(result, title="API Response")
        return result
    except Exception as e:
        if logger:
            logger.error("Tool execution failed: %s", e)
        console.print(f"[red]✗ Tool execution failed: {e}[/red]")
        return None


def run_loop_openapi_llm(
    api_key: Optional[str] = None,
    once: bool = False,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Run the OpenAPI-LLM agent loop.
    
    Initializes the OpenAI client (pointing to local Ollama)
    3. Extracts tool definitions from OpenAPI spec (excluding register)
    4. Prompts the LLM (via OpenAI/Ollama) to call tools to make credits
    5. Uses openapi_client.invoke() to execute the LLM's tool calls
    6. Repeats until stopped
    
    Args:
        api_key: Optional SpaceTraders API key (defaults to env var)
        once: If True, run a single iteration and exit
        logger: Optional logger instance
    """
    log = logger or logging.getLogger("agent.loop_openapi_llm")
    log.info("Starting OpenAPI-LLM loop (once=%s)", once)

    # Get API key
    api_key = api_key or os.environ.get(ENV_API_KEY)
    if not api_key:
        console.print("[red]✗ No SpaceTraders API key found. Set SPACETRADERS_API_KEY environment variable.[/red]")
        raise ValueError(f"Missing {ENV_API_KEY}")

    # Initialize OpenAPI client with credentials
    openapi_client = _initialize_openapi_client(api_key)
    
    # Get tool definitions (excluding register)
    tools = _get_tool_definitions(openapi_client)
    
    # Initialize OpenAI client pointing to local Ollama
    if OpenAI is None:
        console.print("[red]✗ OpenAI client not available[/red]")
        raise RuntimeError("OpenAI library not installed")
    
    llm_client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE,
    )
    console.print("[green]✓[/green] Initialized OpenAI client (Ollama backend)")

    # Main loop
    iteration = 0
    while True:
        iteration += 1
        console.print(f"\n[bold]=== Iteration {iteration} ===[/bold]")
        
        user_message = (
            "You are an agent playing the SpaceTraders game. "
            "Use the available tools to make credits and expand your trading empire. "
            "Call tools strategically to explore, trade, and grow your wealth. "
            "What should we do next?"
        )
        
        # Call LLM
        llm_response = _llm_call(llm_client, tools, user_message, logger=log)
        
        # Execute tool calls from the LLM response
        if llm_response:
            result = _execute_tool_call(openapi_client, llm_response, logger=log)
            if result:
                log.info("Tool execution complete")
        
        if once:
            console.print("\n[cyan]Single iteration complete. Exiting.[/cyan]")
            break
        
        console.print("\n[dim]Ready for next iteration...[/dim]")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger = logging.getLogger("agent.loop_openapi_llm")
    
    try:
        run_loop_openapi_llm(once=True, logger=logger)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.exception("Fatal error")
