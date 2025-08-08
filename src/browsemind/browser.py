"""Browser management for the BrowseMind agent."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from bs4 import BeautifulSoup, Tag
from playwright.async_api import Browser, Page, async_playwright

from browsemind.exceptions import BrowserError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_browser() -> AsyncGenerator[Browser, None]:
    """
    An asynchronous context manager for creating and cleaning up a browser instance.

    Yields:
        The created browser instance.

    Raises:
        BrowserError: If the browser fails to start or close.
    """
    try:
        logger.info("Initializing browser")
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=False)
                logger.info("Browser launched successfully")
            except Exception as e:
                logger.error(f"Failed to launch browser: {e}")
                raise BrowserError(f"Failed to launch browser: {e}", "BROWSER_LAUNCH_ERROR") from e

            try:
                yield browser
            finally:
                try:
                    logger.info("Closing browser")
                    await browser.close()
                    logger.info("Browser closed successfully")
                except Exception as e:
                    logger.error(f"Failed to close browser: {e}")
                    # Log the error but don't raise it since we're in a cleanup context
                    raise BrowserError(
                        f"Failed to close browser: {e}", "BROWSER_CLOSE_ERROR"
                    ) from e
    except BrowserError:
        # Re-raise BrowserErrors as they are already properly formatted
        raise
    except Exception as e:
        logger.error(f"Failed to manage browser lifecycle: {e}")
        raise BrowserError(
            f"Failed to manage browser lifecycle: {e}", "BROWSER_LIFECYCLE_ERROR"
        ) from e


async def get_page_content(page: Page) -> str:
    """
    Retrieves the visible content of the page, including interactable elements
    with unique IDs for the agent to use.

    Args:
        page: The Playwright page object.

    Returns:
        A string containing the page's title and a simplified representation of its content.

    Raises:
        BrowserError: If any step in retrieving page content fails.
    """
    logger.info("Retrieving page content")
    try:
        try:
            logger.debug("Waiting for page to load")
            await page.wait_for_load_state("domcontentloaded")
            logger.debug("Page loaded successfully")
        except Exception as e:
            logger.error(f"Failed to wait for page load: {e}")
            raise BrowserError(f"Failed to wait for page load: {e}", "PAGE_LOAD_ERROR") from e

        try:
            title = await page.title()
            logger.debug(f"Page title: {title}")
        except Exception as e:
            logger.error(f"Failed to get page title: {e}")
            raise BrowserError(f"Failed to get page title: {e}", "TITLE_ERROR") from e

        try:
            logger.debug("Injecting browsemind IDs into interactable elements")
            # Add unique IDs to interactable elements
            await page.evaluate(
                """() => {
                const interactableElements = document.querySelectorAll('a, button, input, textarea, select');
                interactableElements.forEach((el, index) => {
                    el.setAttribute('browsemind-id', index + 1);
                });
            }"""
            )
            logger.debug("browsemind IDs injected successfully")
        except Exception as e:
            logger.error(f"Failed to inject browsemind IDs: {e}")
            raise BrowserError(f"Failed to inject browsemind IDs: {e}", "ID_INJECTION_ERROR") from e

        try:
            logger.debug("Retrieving page HTML")
            html = await page.content()
            logger.debug(f"Retrieved HTML content (length: {len(html)})")
        except Exception as e:
            logger.error(f"Failed to get page HTML: {e}")
            raise BrowserError(f"Failed to get page HTML: {e}", "HTML_CONTENT_ERROR") from e

        try:
            logger.debug("Parsing HTML with BeautifulSoup")
            soup = BeautifulSoup(html, "html.parser")
            logger.debug("HTML parsed successfully")
        except Exception as e:
            logger.error(f"Failed to parse HTML with BeautifulSoup: {e}")
            raise BrowserError(
                f"Failed to parse HTML with BeautifulSoup: {e}", "HTML_PARSE_ERROR"
            ) from e

        try:
            logger.debug("Removing script and style elements")
            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            logger.debug("Script and style elements removed")
        except Exception as e:
            logger.error(f"Failed to remove script/style elements: {e}")
            raise BrowserError(
                f"Failed to remove script/style elements: {e}", "SCRIPT_REMOVAL_ERROR"
            ) from e

        try:
            logger.debug("Extracting text from HTML")
            text = soup.get_text()
            logger.debug(f"Extracted text (length: {len(text)})")
        except Exception as e:
            logger.error(f"Failed to extract text from HTML: {e}")
            raise BrowserError(
                f"Failed to extract text from HTML: {e}", "TEXT_EXTRACTION_ERROR"
            ) from e

        try:
            logger.debug("Finding interactable elements")
            interactable_elements = soup.find_all(attrs={"browsemind-id": True})
            logger.debug(f"Found {len(interactable_elements)} interactable elements")
        except Exception as e:
            logger.error(f"Failed to find interactable elements: {e}")
            raise BrowserError(
                f"Failed to find interactable elements: {e}", "ELEMENT_FIND_ERROR"
            ) from e

        try:
            logger.debug("Processing interactable elements")
            element_info = []
            for element in interactable_elements:
                if isinstance(element, Tag):
                    tag = element.name
                    text_content = element.get_text(strip=True)
                    browsemind_id = element["browsemind-id"]
                    element_info.append(f'<{tag} browsemind-id="{browsemind_id}"> {text_content}')
            logger.debug(f"Processed {len(element_info)} interactable elements")
        except Exception as e:
            logger.error(f"Failed to process interactable elements: {e}")
            raise BrowserError(
                f"Failed to process interactable elements: {e}", "ELEMENT_PROCESSING_ERROR"
            ) from e

        try:
            result = f"Title: {title}\n\nContent:\n{text}\n\nInteractable Elements:\n" + "\n".join(
                element_info
            )
            logger.info(f"Page content formatted successfully (length: {len(result)})")
            return result
        except Exception as e:
            logger.error(f"Failed to format page content: {e}")
            raise BrowserError(f"Failed to format page content: {e}", "CONTENT_FORMAT_ERROR") from e
    except BrowserError:
        # Re-raise BrowserErrors as they are already properly formatted
        raise
    except Exception as e:
        logger.error(f"Failed to get page content: {e}")
        raise BrowserError(f"Failed to get page content: {e}", "PAGE_CONTENT_ERROR") from e
