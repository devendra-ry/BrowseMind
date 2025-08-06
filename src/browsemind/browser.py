"""Browser management for the BrowseMind agent."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup

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
            browser = await p.chromium.launch(headless=False)
            yield browser
            await browser.close()
    except Exception as e:
        raise BrowserError(f"Failed to manage browser lifecycle: {e}") from e


async def get_page_content(page: Page) -> str:
    """
    Retrieves the visible content of the page, including interactable elements
    with unique IDs for the agent to use.

    Args:
        page: The Playwright page object.

    Returns:
        A string containing the page's title and a simplified representation of its content.
    """
    try:
        await page.wait_for_load_state("domcontentloaded")
        title = await page.title()

        # Add unique IDs to interactable elements
        await page.evaluate("""() => {
            const interactableElements = document.querySelectorAll('a, button, input, textarea, select');
            interactableElements.forEach((el, index) => {
                el.setAttribute('browsemind-id', index + 1);
            });
        }""")

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        text = soup.get_text()
        interactable_elements = soup.find_all(attrs={
            "browsemind-id": True
        })

        element_info = []
        for element in interactable_elements:
            tag = element.name
            text_content = element.get_text(strip=True)
            browsemind_id = element['browsemind-id']
            element_info.append(f'<{tag} browsemind-id="{browsemind_id}"> {text_content}')

        return f"Title: {title}\n\nContent:\n{text}\n\nInteractable Elements:\n" + "\n".join(
            element_info
        )
    except Exception as e:
        raise BrowserError(f"Failed to get page content: {e}") from e