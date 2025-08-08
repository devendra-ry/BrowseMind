"""Core agent logic for the BrowseMind application."""

import asyncio
import logging

from playwright.async_api import Browser, Page

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
        # Validate task input
        if not isinstance(task, str):
            raise BrowseMindError("Task must be a string", "INVALID_TASK_TYPE")

        if len(task) > config.max_task_length:
            raise BrowseMindError(
                f"Task length ({len(task)}) exceeds maximum allowed length ({config.max_task_length})",
                "TASK_TOO_LONG",
            )

        self.task = task
        self.config = config
        self.llm = get_llm(config)
        logger.info(f"Agent initialized with task: {task}")

    async def _set_page_timeouts(self, page: Page) -> None:
        """Set timeouts for browser page operations."""
        try:
            # Set default timeout for navigation and actions
            page.set_default_timeout(self.config.browser_navigation_timeout)
            page.set_default_navigation_timeout(self.config.browser_navigation_timeout)
            logger.debug(f"Set page timeouts to {self.config.browser_navigation_timeout}ms")
        except Exception as e:
            logger.warning(f"Failed to set page timeouts: {e}")

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
            await self._set_page_timeouts(page)
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
                # Apply timeout to page content retrieval
                page_content = await asyncio.wait_for(
                    get_page_content(page),
                    timeout=self.config.browser_action_timeout / 1000.0,  # Convert to seconds
                )
                logger.debug(f"Retrieved page content (length: {len(page_content)})")

                # Check content length
                if len(page_content) > self.config.max_page_content_length:
                    logger.warning(
                        f"Page content length ({len(page_content)}) exceeds maximum allowed length "
                        f"({self.config.max_page_content_length}). Truncating content."
                    )
                    page_content = page_content[: self.config.max_page_content_length]
            except TimeoutError:
                logger.error(f"Timeout while retrieving page content at iteration {iteration}")
                raise BrowseMindError(
                    f"Timeout while retrieving page content at iteration {iteration}",
                    "CONTENT_TIMEOUT_ERROR",
                ) from None
            except Exception as e:
                logger.error(f"Failed to get page content at iteration {iteration}: {e}")
                raise BrowseMindError(
                    f"Failed to get page content at iteration {iteration}: {e}", "CONTENT_ERROR"
                ) from e

            try:
                # Apply timeout to LLM call
                action = await asyncio.wait_for(
                    get_next_action(self.llm, page_content, self.task, self.config),
                    timeout=self.config.llm_request_timeout,
                )
                logger.debug(f"Received action from LLM: {action}")
            except TimeoutError:
                logger.error(f"Timeout while getting next action from LLM at iteration {iteration}")
                raise LLMError(
                    f"Timeout while getting next action from LLM at iteration {iteration}",
                    "LLM_TIMEOUT_ERROR",
                ) from None
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
                        # Apply timeout to navigation
                        await asyncio.wait_for(
                            page.goto(url),
                            timeout=self.config.browser_navigation_timeout
                            / 1000.0,  # Convert to seconds
                        )
                        logger.info("Navigation completed successfully")
                    except TimeoutError:
                        logger.error(f"Timeout while navigating to {url}")
                        raise BrowseMindError(
                            f"Timeout while navigating to {url}", "NAVIGATION_TIMEOUT_ERROR"
                        ) from None
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
                        # Apply timeout to typing
                        await asyncio.wait_for(
                            page.type(selector, text),
                            timeout=self.config.browser_action_timeout
                            / 1000.0,  # Convert to seconds
                        )
                        if args.get("press_enter_after", False):
                            logger.info("Pressing Enter after typing")
                            await asyncio.wait_for(
                                page.press(selector, "Enter"),
                                timeout=self.config.browser_action_timeout
                                / 1000.0,  # Convert to seconds
                            )
                        logger.info("Typing completed successfully")
                    except TimeoutError:
                        logger.error(f"Timeout while typing into element {element_id}")
                        raise BrowseMindError(
                            f"Timeout while typing into element {element_id}", "TYPE_TIMEOUT_ERROR"
                        ) from None
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
                        # Apply timeout to click
                        await asyncio.wait_for(
                            page.click(selector),
                            timeout=self.config.browser_action_timeout
                            / 1000.0,  # Convert to seconds
                        )
                        logger.info("Click completed successfully")
                    except TimeoutError:
                        logger.error(f"Timeout while clicking element {element_id}")
                        raise BrowseMindError(
                            f"Timeout while clicking element {element_id}", "CLICK_TIMEOUT_ERROR"
                        ) from None
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
                    # Apply timeout to summarization
                    result = await asyncio.wait_for(
                        page.inner_text("body"),
                        timeout=self.config.browser_action_timeout / 1000.0,  # Convert to seconds
                    )
                    logger.info("Summarization completed successfully")
                    return str(result)
                except TimeoutError:
                    logger.error("Timeout while summarizing page content")
                    raise BrowseMindError(
                        "Timeout while summarizing page content", "SUMMARIZE_TIMEOUT_ERROR"
                    ) from None
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
