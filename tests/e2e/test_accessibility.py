"""Accessibility tests using axe-core via Playwright."""

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page

pytestmark = [pytest.mark.e2e, pytest.mark.a11y]

axe = Axe()


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/blog/",
        "/projects/",
        "/talks/",
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


def _format_violations(violations: list[dict]) -> str:
    lines: list[str] = []
    for violation in violations:
        targets = [node["target"] for node in violation["nodes"]]
        lines.append(f"[{violation['impact']}] {violation['id']}: {violation['help']} -> {targets}")
    return "\n".join(lines)
