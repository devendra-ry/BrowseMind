"""Core agent logic for the BrowseMind application."""

from playwright.async_api import Browser, Page

from browsemind.browser import get_page_content
from browsemind.config import AgentConfig
from browsemind.exceptions import BrowseMindError
from browsemind.llm import get_llm, get_next_action


class Agent:
    """
    The core agent that performs tasks using a browser and an LLM.
    """

    def __init__(self, task: str, config: AgentConfig):
        self.task = task
        self.config = config
        self.llm = get_llm(config)

    async def run(self, browser: Browser) -> str:
        """
        Runs the agent to perform the task.

        Args:
            browser: The browser instance for the agent to use.

        Returns:
            The result of the agent's execution.
        """
        page = await browser.new_page()
        await page.goto("about:blank")

        for _ in range(self.config.max_iterations):
            page_content = await get_page_content(page)
            action = await get_next_action(self.llm, page_content, self.task)

            action_name = action.get("action")
            args = action.get("args", {})

            if action_name == "navigate":
                await page.goto(args.get("url"))
            elif action_name == "type":
                selector = f'[browsemind-id="{args.get("id")}"]'
                await page.type(selector, args.get("text"))
            elif action_name == "click":
                selector = f'[browsemind-id="{args.get("id")}"]'
                await page.click(selector)
            elif action_name == "press_enter":
                selector = f'[browsemind-id="{args.get("id")}"]'
                await page.press(selector, "Enter")
            elif action_name == "summarize":
                # This is a placeholder. A more robust implementation would
                # involve another LLM call to summarize the content.
                return await page.inner_text("body")
            elif action_name == "finish":
                return args.get("result", "Task finished.")
            else:
                raise BrowseMindError(f"Unknown action: {action_name}")

        return "Max iterations reached."
