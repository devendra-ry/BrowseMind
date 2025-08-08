"""Main entry point for the BrowseMind CLI application."""

import asyncio
import logging
import os

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from browsemind.agent import Agent
from browsemind.browser import get_browser
from browsemind.config import AgentConfig
from browsemind.exceptions import BrowseMindError, BrowserError, ConfigurationError, LLMError

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="browsemind",
    help="AI-powered browser automation agent using Google's Gemini.",
    add_completion=False,
)
console = Console()


def _validate_task_input(task: str, config: AgentConfig) -> str:
    """
    Validate and sanitize the task input.

    Args:
        task: The task string to validate
        config: The agent configuration

    Returns:
        The validated task string

    Raises:
        BrowseMindError: If the task is invalid
    """
    if not isinstance(task, str):
        raise BrowseMindError("Task must be a string", "INVALID_TASK_TYPE")

    if not task.strip():
        raise BrowseMindError("Task cannot be empty", "EMPTY_TASK")

    # Trim whitespace
    task = task.strip()

    # Check length
    if len(task) > config.max_task_length:
        raise BrowseMindError(
            f"Task length ({len(task)}) exceeds maximum allowed length ({config.max_task_length})",
            "TASK_TOO_LONG",
        )

    # Basic sanitization - remove null bytes
    task = task.replace("\x00", "")

    return task


@app.command()
def run(
    task: str = typer.Argument(..., help="The task for the agent to perform."),
) -> None:
    """
    Runs the agent to perform the given task.
    """
    logger.info(f"Starting BrowseMind with task: {task}")

    async def _run() -> None:
        try:
            config = AgentConfig.from_env()

            # Validate and sanitize task input
            try:
                task_validated = _validate_task_input(task, config)
            except BrowseMindError as e:
                logger.error(f"Invalid task input: {e}")
                console.print(
                    Panel(
                        f"[bold red]Invalid Task:[/bold red] {e}",
                        title="Input Error",
                        border_style="red",
                    )
                )
                return

            agent = Agent(task=task_validated, config=config)

            console.print(
                Panel(
                    f"[bold green]Starting Task:[/bold green]\n[yellow]{task_validated}[/yellow]",
                    title="Agent Initialized",
                    border_style="blue",
                )
            )

            async with get_browser() as browser:
                result = await agent.run(browser)

                console.print(
                    Panel(
                        f"[bold green]Task Result:[/bold green]\n{result}",
                        title="Agent Finished",
                        border_style="green",
                    )
                )

        except ConfigurationError as e:
            logger.error(f"Configuration Error: {e}", exc_info=True)
            console.print(
                Panel(
                    f"[bold red]Configuration Error:[/bold red] {e}\nError Code: {e.error_code}",
                    title="Configuration Error",
                    border_style="red",
                )
            )
        except BrowserError as e:
            logger.error(f"Browser Error: {e}", exc_info=True)
            console.print(
                Panel(
                    f"[bold red]Browser Error:[/bold red] {e}\nError Code: {e.error_code}",
                    title="Browser Error",
                    border_style="red",
                )
            )
        except LLMError as e:
            logger.error(f"LLM Error: {e}", exc_info=True)
            console.print(
                Panel(
                    f"[bold red]LLM Error:[/bold red] {e}\nError Code: {e.error_code}",
                    title="LLM Error",
                    border_style="red",
                )
            )
        except BrowseMindError as e:
            logger.error(f"Application Error: {e}", exc_info=True)
            console.print(
                Panel(
                    f"[bold red]Application Error:[/bold red] {e}\nError Code: {e.error_code}",
                    title="Application Error",
                    border_style="red",
                )
            )
        except Exception as e:
            logger.critical(f"Unexpected error occurred: {e}", exc_info=True)
            console.print(
                Panel(
                    f"[bold red]An unexpected error occurred:[/bold red] {e}\n{type(e).__name__}: {str(e)}",
                    title="Critical Error",
                    border_style="red",
                )
            )

    asyncio.run(_run())


if __name__ == "__main__":
    app()
