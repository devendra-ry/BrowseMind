"""Core agent logic for the BrowseMind application."""

from playwright.async_api import Browser

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
                url = args.get("url")
                if isinstance(url, str):
                    await page.goto(url)
            elif action_name == "type":
                element_id = args.get("id")
                text = args.get("text")
                if isinstance(element_id, int) and isinstance(text, str):
                    selector = f'[browsemind-id="{element_id}"]'
                    await page.type(selector, text)
                    if args.get("press_enter_after", False):
                        await page.press(selector, "Enter")
            elif action_name == "click":
                element_id = args.get("id")
                if isinstance(element_id, int):
                    selector = f'[browsemind-id="{element_id}"]'
                    await page.click(selector)
            elif action_name == "summarize":
                # This is a placeholder. A more robust implementation would
                # involve another LLM call to summarize the content.
                result = await page.inner_text("body")
                return str(result)
            elif action_name == "finish":
                result = args.get("result", "Task finished.")
                if isinstance(result, str):
                    return result
                else:
                    return str(result)
            else:
                raise BrowseMindError(f"Unknown action: {action_name}")

        return "Max iterations reached."
