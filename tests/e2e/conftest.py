"""Fixtures shared by the browser tests, which run on both Chromium and WebKit."""

from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page, Playwright

# A phone that matches each engine, so WebKit runs approximate iOS Safari.
MOBILE_DEVICES = {"chromium": "Pixel 5", "webkit": "iPhone 13"}


@pytest.fixture
def mobile_page(browser: Browser, browser_name: str, playwright: Playwright) -> Iterator[Page]:
    """A touch-enabled phone page for the current browser engine."""
    context = browser.new_context(**playwright.devices[MOBILE_DEVICES[browser_name]])
    page = context.new_page()
    try:
        yield page
    finally:
        context.close()
