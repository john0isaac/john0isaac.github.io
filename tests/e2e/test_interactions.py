"""End-to-end browser tests for interactive site behaviour."""

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_homepage_loads(live_server: str, page: Page) -> None:
    page.goto(live_server)
    expect(page).to_have_title(re.compile(r".+"))
    expect(page.locator("header.site-header")).to_be_visible()
    expect(page.locator("footer.site-footer")).to_be_visible()


def test_search_modal_opens_with_shortcut(live_server: str, page: Page) -> None:
    page.goto(live_server)
    modal = page.locator("#site-search-modal")
    expect(modal).to_be_hidden()
    page.keyboard.press("Control+k")
    expect(modal).to_be_visible()
    expect(page.locator("#site-search-input")).to_be_focused()
    page.keyboard.press("Escape")
    expect(modal).to_be_hidden()


def test_search_modal_opens_with_button(live_server: str, page: Page) -> None:
    page.goto(live_server)
    page.locator("[data-search-open]").first.click()
    expect(page.locator("#site-search-modal")).to_be_visible()


def test_search_returns_results(live_server: str, page: Page) -> None:
    page.goto(live_server)
    page.locator("[data-search-open]").first.click()
    search_input = page.locator("#site-search-input")
    search_input.fill("blog")
    expect(page.locator("[data-search-results] [data-result-index]").first).to_be_visible()


def test_theme_toggle_switches_mode(live_server: str, page: Page) -> None:
    page.goto(live_server)
    root = page.locator("html")
    before = root.get_attribute("data-theme")
    page.locator("[data-theme-toggle]").click()
    after = root.get_attribute("data-theme")
    assert before != after


def test_code_copy_button_present_on_post(live_server: str, page: Page) -> None:
    page.goto(f"{live_server}/blog/zsh-config/")
    copy_button = page.locator(".code-copy-btn").first
    expect(copy_button).to_be_visible()


def test_navigation_to_blog(live_server: str, page: Page) -> None:
    page.goto(live_server)
    page.get_by_role("link", name="Blog", exact=True).first.click()
    expect(page).to_have_url(f"{live_server}/blog/")
    active = page.locator("a.nav-link.active")
    expect(active).to_have_attribute("aria-current", "page")
