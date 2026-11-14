"""Accessibility tests using axe-core via Playwright."""

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Locator, Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.a11y]

axe = Axe()

FOCUS_IN_SEARCH_DIALOG = (
    "document.activeElement === document.body || !!document.activeElement.closest('#site-search-modal')"
)


def _open_search(page: Page, live_server: str, query: str = "rag") -> Locator:
    page.goto(live_server)
    page.keyboard.press("Control+k")
    search_input = page.locator("#site-search-input")
    expect(search_input).to_be_focused()
    search_input.fill(query)
    expect(page.locator("[data-search-results] [data-result-index]").nth(1)).to_be_visible()
    return search_input


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/blog/",
        "/projects/",
        "/talks/",
        "/about/",
        "/blog/zsh-config/",
    ],
)
def test_page_has_no_serious_a11y_violations(live_server: str, page: Page, path: str) -> None:
    # Skip entrance animations so axe measures final, settled colors instead of
    # mid-fade values (the ``rise`` keyframe animates opacity from 0 to 1).
    page.emulate_media(reduced_motion="reduce")
    page.goto(f"{live_server}{path}")
    results = axe.run(page)
    serious = [
        violation for violation in results.response["violations"] if violation["impact"] in {"serious", "critical"}
    ]
    assert not serious, _format_violations(serious)


def test_open_search_dialog_has_no_serious_a11y_violations(live_server: str, page: Page) -> None:
    page.emulate_media(reduced_motion="reduce")
    _open_search(page, live_server)
    results = axe.run(page)
    serious = [
        violation for violation in results.response["violations"] if violation["impact"] in {"serious", "critical"}
    ]
    assert not serious, _format_violations(serious)


def test_search_results_are_announced_as_combobox_options(live_server: str, page: Page) -> None:
    search_input = _open_search(page, live_server)
    expect(search_input).to_have_attribute("aria-expanded", "true")
    expect(search_input).to_have_attribute("aria-activedescendant", "site-search-result-0")

    page.keyboard.press("ArrowDown")
    expect(search_input).to_have_attribute("aria-activedescendant", "site-search-result-1")
    expect(page.locator("#site-search-result-1")).to_have_attribute("aria-selected", "true")
    expect(page.locator("#site-search-result-0")).to_have_attribute("aria-selected", "false")
    expect(page.locator("[data-search-status]")).to_contain_text("available")


def test_search_dialog_traps_focus_and_restores_page(live_server: str, page: Page) -> None:
    _open_search(page, live_server)
    assert page.evaluate("document.querySelector('main').inert")

    for _ in range(30):
        page.keyboard.press("Tab")
        assert page.evaluate(FOCUS_IN_SEARCH_DIALOG), "Tab moved focus behind the search dialog"

    page.keyboard.press("Escape")
    expect(page.locator("#site-search-modal")).to_be_hidden()
    assert not page.evaluate("document.querySelector('main').inert")


def test_search_filter_keeps_keyboard_focus(live_server: str, page: Page) -> None:
    _open_search(page, live_server)
    search_filter = page.locator("[data-search-filter-list] [data-search-filter]").first
    value = search_filter.get_attribute("data-search-filter")
    search_filter.focus()

    page.keyboard.press("Enter")
    focused = page.locator(":focus")
    expect(focused).to_have_attribute("data-search-filter", value or "")
    expect(focused).to_have_attribute("aria-pressed", "true")

    page.keyboard.press("Escape")
    expect(page.locator("#site-search-modal")).to_be_hidden()


def test_search_trigger_controls_dialog_and_hint_sits_outside_results(live_server: str, page: Page) -> None:
    page.goto(live_server)
    trigger = page.locator("[data-search-open]").first
    expect(page.locator(f"#{trigger.get_attribute('aria-controls')}")).to_have_attribute("role", "dialog")

    trigger.click()
    hint = page.locator("[data-search-hint]")
    expect(hint).to_be_visible()
    expect(page.locator("[data-search-results] [data-search-hint]")).to_have_count(0)

    page.locator("#site-search-input").fill("rag")
    expect(hint).to_be_hidden()


def test_collapsed_search_filters_are_not_focusable(live_server: str, page: Page) -> None:
    _open_search(page, live_server)
    page.locator("[data-search-filters-toggle]").click()
    assert page.evaluate("document.querySelector('[data-search-filters]').inert")


def test_blog_archive_moves_focus_in_and_back_out(live_server: str, page: Page) -> None:
    page.goto(f"{live_server}/blog/")
    open_button = page.locator(".blog-archive__open-btn")
    open_button.focus()

    page.keyboard.press("Enter")
    expect(page.locator("[data-blog-archive-toggle]")).to_be_focused()
    expect(open_button).to_have_attribute("aria-expanded", "true")

    page.keyboard.press("Escape")
    expect(open_button).to_be_focused()
    expect(open_button).to_have_attribute("aria-expanded", "false")


def test_code_copy_is_announced(live_server: str, page: Page, browser_name: str) -> None:
    # Chromium needs clipboard permission granted; WebKit allows writes from a click.
    if browser_name == "chromium":
        page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=live_server)
    page.goto(f"{live_server}/blog/zsh-config/")
    page.locator(".code-copy-btn").first.click()
    expect(page.locator("[data-a11y-status]")).to_have_text("Code copied to clipboard")


def _format_violations(violations: list[dict]) -> str:
    lines: list[str] = []
    for violation in violations:
        targets = [node["target"] for node in violation["nodes"]]
        lines.append(f"[{violation['impact']}] {violation['id']}: {violation['help']} -> {targets}")
    return "\n".join(lines)
