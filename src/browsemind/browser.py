"""Browser management for the BrowseMind agent."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from bs4 import BeautifulSoup, Tag
from playwright.async_api import Browser, Page, async_playwright

from browsemind.exceptions import BrowserError


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
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=False)
            except Exception as e:
                raise BrowserError(f"Failed to launch browser: {e}", "BROWSER_LAUNCH_ERROR") from e

            try:
                yield browser
            finally:
                try:
                    await browser.close()
                except Exception as e:
                    # Log the error but don't raise it since we're in a cleanup context
                    raise BrowserError(
                        f"Failed to close browser: {e}", "BROWSER_CLOSE_ERROR"
                    ) from e
    except BrowserError:
        # Re-raise BrowserErrors as they are already properly formatted
        raise
    except Exception as e:
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
    try:
        try:
            await page.wait_for_load_state("domcontentloaded")
        except Exception as e:
            raise BrowserError(f"Failed to wait for page load: {e}", "PAGE_LOAD_ERROR") from e

        try:
            title = await page.title()
        except Exception as e:
            raise BrowserError(f"Failed to get page title: {e}", "TITLE_ERROR") from e

        try:
            # Add unique IDs to interactable elements
            await page.evaluate(
                """() => {
                const interactableElements = document.querySelectorAll('a, button, input, textarea, select');
                interactableElements.forEach((el, index) => {
                    el.setAttribute('browsemind-id', index + 1);
                });
            }"""
            )
        except Exception as e:
            raise BrowserError(f"Failed to inject browsemind IDs: {e}", "ID_INJECTION_ERROR") from e

        try:
            html = await page.content()
        except Exception as e:
            raise BrowserError(f"Failed to get page HTML: {e}", "HTML_CONTENT_ERROR") from e

        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            raise BrowserError(
                f"Failed to parse HTML with BeautifulSoup: {e}", "HTML_PARSE_ERROR"
            ) from e

        try:
            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
        except Exception as e:
            raise BrowserError(
                f"Failed to remove script/style elements: {e}", "SCRIPT_REMOVAL_ERROR"
            ) from e

        try:
            text = soup.get_text()
        except Exception as e:
            raise BrowserError(
                f"Failed to extract text from HTML: {e}", "TEXT_EXTRACTION_ERROR"
            ) from e

        try:
            interactable_elements = soup.find_all(attrs={"browsemind-id": True})
        except Exception as e:
            raise BrowserError(
                f"Failed to find interactable elements: {e}", "ELEMENT_FIND_ERROR"
            ) from e

        try:
            element_info = []
            for element in interactable_elements:
                if isinstance(element, Tag):
                    tag = element.name
                    text_content = element.get_text(strip=True)
                    browsemind_id = element["browsemind-id"]
                    element_info.append(f'<{tag} browsemind-id="{browsemind_id}"> {text_content}')
        except Exception as e:
            raise BrowserError(
                f"Failed to process interactable elements: {e}", "ELEMENT_PROCESSING_ERROR"
            ) from e

        try:
            return f"Title: {title}\n\nContent:\n{text}\n\nInteractable Elements:\n" + "\n".join(
                element_info
            )
        except Exception as e:
            raise BrowserError(f"Failed to format page content: {e}", "CONTENT_FORMAT_ERROR") from e
    except BrowserError:
        # Re-raise BrowserErrors as they are already properly formatted
        raise
    except Exception as e:
        raise BrowserError(f"Failed to get page content: {e}", "PAGE_CONTENT_ERROR") from e
