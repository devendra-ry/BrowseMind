"""Main entry point for the BrowseMind CLI application."""

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel

from browsemind.agent import Agent
from browsemind.browser import get_browser
from browsemind.config import AgentConfig
from browsemind.exceptions import BrowseMindError, BrowserError, ConfigurationError, LLMError

app = typer.Typer(
    name="browsemind",
    help="AI-powered browser automation agent using Google's Gemini.",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    task: str = typer.Argument(..., help="The task for the agent to perform."),
) -> None:
    """
    Runs the agent to perform the given task.
    """

    async def _run() -> None:
        try:
            config = AgentConfig.from_env()
            agent = Agent(task=task, config=config)

            console.print(
                Panel(
                    f"[bold green]Starting Task:[/bold green]\n[yellow]{task}[/yellow]",
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
            console.print(
                Panel(
                    f"[bold red]Configuration Error:[/bold red] {e}\nError Code: {e.error_code}",
                    title="Configuration Error",
                    border_style="red",
                )
            )
        except BrowserError as e:
            console.print(
                Panel(
                    f"[bold red]Browser Error:[/bold red] {e}\nError Code: {e.error_code}",
                    title="Browser Error",
                    border_style="red",
                )
            )
        except LLMError as e:
            console.print(
                Panel(
                    f"[bold red]LLM Error:[/bold red] {e}\nError Code: {e.error_code}",
                    title="LLM Error",
                    border_style="red",
                )
            )
        except BrowseMindError as e:
            console.print(
                Panel(
                    f"[bold red]Application Error:[/bold red] {e}\nError Code: {e.error_code}",
                    title="Application Error",
                    border_style="red",
                )
            )
        except Exception as e:
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
