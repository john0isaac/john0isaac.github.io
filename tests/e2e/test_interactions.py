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


def test_tapping_search_result_on_mobile_opens_it(live_server: str, mobile_page: Page) -> None:
    page = mobile_page
    page.goto(live_server)
    page.locator("[data-search-open]").first.tap()
    page.locator("#site-search-input").fill("rag")
    result = page.locator("[data-search-results] [data-result-index]").nth(1)
    href = result.get_attribute("href")
    result.tap()
    expect(page).to_have_url(f"{live_server}{href}")


def test_tapping_blog_archive_on_mobile_opens_a_post(live_server: str, mobile_page: Page) -> None:
    page = mobile_page
    page.goto(f"{live_server}/blog/")
    # Tap the icon itself: swapping it mid-tap used to close the archive instantly.
    page.locator(".blog-archive__open-btn svg:visible").tap()
    expect(page.locator(".blog-layout")).to_have_class(re.compile(r"\bis-archive-open\b"))
    # The open button sits at the bottom on phones, so the archive should open there too.
    archive = page.locator(".blog-archive")
    expect(archive).to_be_in_viewport()
    box, viewport = archive.bounding_box(), page.viewport_size
    assert box and viewport and box["y"] + box["height"] > viewport["height"] * 0.9

    page.locator("details.blog-archive__year > summary").first.tap()
    page.locator("details.blog-archive__year[open] details.blog-archive__month > summary").first.tap()
    link = page.locator("details.blog-archive__month[open] .blog-archive__post-link").first
    href = link.get_attribute("href")
    link.tap()
    expect(page).to_have_url(f"{live_server}{href}")


def test_clicking_blog_archive_post_opens_it(live_server: str, page: Page) -> None:
    # Safari moved focus to <main> on mousedown, which closed the archive before the click landed.
    page.goto(f"{live_server}/blog/")
    page.locator(".blog-archive__open-btn").click()
    page.locator("details.blog-archive__year > summary").first.click()
    page.locator("details.blog-archive__year[open] details.blog-archive__month > summary").first.click()
    link = page.locator("details.blog-archive__month[open] .blog-archive__post-link").first
    href = link.get_attribute("href")
    link.click()
    expect(page).to_have_url(f"{live_server}{href}")


def test_search_result_highlight_updates_in_place(live_server: str, page: Page) -> None:
    # Re-rendering the list on hover replaced the element under a tap, so mobile
    # taps only highlighted results instead of opening them.
    page.goto(live_server)
    page.locator("[data-search-open]").first.click()
    page.locator("#site-search-input").fill("rag")
    result = page.locator("[data-search-results] [data-result-index]").nth(1)
    result.evaluate("el => { el.dataset.original = 'yes'; }")

    result.dispatch_event("pointermove", {"pointerType": "touch"})
    expect(result).to_have_attribute("aria-selected", "false")

    result.hover()
    expect(result).to_have_attribute("aria-selected", "true")
    expect(result).to_have_attribute("data-original", "yes")


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
