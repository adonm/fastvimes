"""Quick Playwright verification test."""

import pytest
from playwright.async_api import async_playwright


@pytest.mark.playwright 
def test_playwright_import():
    """Verify Playwright can be imported."""
    import playwright
    assert hasattr(playwright, 'async_api')


@pytest.mark.playwright
async def test_playwright_launch():
    """Verify Playwright browser can launch."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        assert browser is not None
        await browser.close()


if __name__ == "__main__":
    print("✓ Playwright test imports work")
