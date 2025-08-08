"""Core agent logic for the BrowseMind application."""

import logging

from playwright.async_api import Browser

from browsemind.browser import get_page_content
from browsemind.config import AgentConfig
from browsemind.exceptions import BrowseMindError, LLMError
from browsemind.llm import get_llm, get_next_action

logger = logging.getLogger(__name__)


class Agent:
    """
    The core agent that performs tasks using a browser and an LLM.
    """

    def __init__(self, task: str, config: AgentConfig):
        self.task = task
        self.config = config
        self.llm = get_llm(config)
        logger.info(f"Agent initialized with task: {task}")

    async def run(self, browser: Browser) -> str:
        """
        Runs the agent to perform the task.

        Args:
            browser: The browser instance for the agent to use.

        Returns:
            The result of the agent's execution.

        Raises:
            BrowseMindError: If an error occurs during agent execution.
        """
        try:
            page = await browser.new_page()
            await page.goto("about:blank")
            logger.info("Browser page initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser page: {e}")
            raise BrowseMindError(
                f"Failed to initialize browser page: {e}", "PAGE_INIT_ERROR"
            ) from e

        for iteration in range(self.config.max_iterations):
            logger.info(f"Starting iteration {iteration + 1}/{self.config.max_iterations}")
            try:
                page_content = await get_page_content(page)
                logger.debug(f"Retrieved page content (length: {len(page_content)})")
            except Exception as e:
                logger.error(f"Failed to get page content at iteration {iteration}: {e}")
                raise BrowseMindError(
                    f"Failed to get page content at iteration {iteration}: {e}", "CONTENT_ERROR"
                ) from e

            try:
                action = await get_next_action(self.llm, page_content, self.task)
                logger.debug(f"Received action from LLM: {action}")
            except LLMError:
                # Re-raise LLM errors as they are already properly formatted
                raise
            except Exception as e:
                logger.error(f"Failed to get next action from LLM at iteration {iteration}: {e}")
                raise LLMError(
                    f"Failed to get next action from LLM at iteration {iteration}: {e}",
                    "LLM_ACTION_ERROR",
                ) from e

            # Validate action structure
            if not isinstance(action, dict):
                logger.error(f"LLM returned invalid action type: {type(action)}, expected dict")
                raise LLMError(
                    f"LLM returned invalid action type: {type(action)}, expected dict",
                    "INVALID_ACTION_TYPE",
                )

            action_name = action.get("action")
            args = action.get("args", {})

            if not isinstance(action_name, str):
                logger.error(f"LLM returned invalid action name: {action_name}, expected string")
                raise LLMError(
                    f"LLM returned invalid action name: {action_name}, expected string",
                    "INVALID_ACTION_NAME",
                )

            logger.info(f"Executing action: {action_name} with args: {args}")

            if action_name == "navigate":
                url = args.get("url")
                if isinstance(url, str):
                    try:
                        logger.info(f"Navigating to URL: {url}")
                        await page.goto(url)
                        logger.info("Navigation completed successfully")
                    except Exception as e:
                        logger.error(f"Failed to navigate to {url}: {e}")
                        raise BrowseMindError(
                            f"Failed to navigate to {url}: {e}", "NAVIGATION_ERROR"
                        ) from e
                else:
                    logger.error(f"Invalid URL for navigate action: {url}")
                    raise LLMError(
                        f"Invalid URL for navigate action: {url}", "INVALID_NAVIGATION_URL"
                    )
            elif action_name == "type":
                element_id = args.get("id")
                text = args.get("text")
                if isinstance(element_id, int) and isinstance(text, str):
                    try:
                        selector = f'[browsemind-id="{element_id}"]'
                        logger.info(f"Typing '{text}' into element {element_id}")
                        await page.type(selector, text)
                        if args.get("press_enter_after", False):
                            logger.info("Pressing Enter after typing")
                            await page.press(selector, "Enter")
                        logger.info("Typing completed successfully")
                    except Exception as e:
                        logger.error(f"Failed to type into element {element_id}: {e}")
                        raise BrowseMindError(
                            f"Failed to type into element {element_id}: {e}", "TYPE_ERROR"
                        ) from e
                else:
                    logger.error(
                        f"Invalid parameters for type action: id={element_id}, text={text}"
                    )
                    raise LLMError(
                        f"Invalid parameters for type action: id={element_id}, text={text}",
                        "INVALID_TYPE_PARAMS",
                    )
            elif action_name == "click":
                element_id = args.get("id")
                if isinstance(element_id, int):
                    try:
                        selector = f'[browsemind-id="{element_id}"]'
                        logger.info(f"Clicking element {element_id}")
                        await page.click(selector)
                        logger.info("Click completed successfully")
                    except Exception as e:
                        logger.error(f"Failed to click element {element_id}: {e}")
                        raise BrowseMindError(
                            f"Failed to click element {element_id}: {e}", "CLICK_ERROR"
                        ) from e
                else:
                    logger.error(f"Invalid element ID for click action: {element_id}")
                    raise LLMError(
                        f"Invalid element ID for click action: {element_id}", "INVALID_CLICK_ID"
                    )
            elif action_name == "summarize":
                # This is a placeholder. A more robust implementation would
                # involve another LLM call to summarize the content.
                try:
                    logger.info("Summarizing page content")
                    result = await page.inner_text("body")
                    logger.info("Summarization completed successfully")
                    return str(result)
                except Exception as e:
                    logger.error(f"Failed to summarize page content: {e}")
                    raise BrowseMindError(
                        f"Failed to summarize page content: {e}", "SUMMARIZE_ERROR"
                    ) from e
            elif action_name == "finish":
                result = args.get("result", "Task finished.")
                logger.info(f"Task finished with result: {result}")
                if isinstance(result, str):
                    return result
                else:
                    return str(result)
            else:
                logger.error(f"Unknown action: {action_name}")
                raise BrowseMindError(f"Unknown action: {action_name}", "UNKNOWN_ACTION")

        logger.info("Max iterations reached")
        return "Max iterations reached."
