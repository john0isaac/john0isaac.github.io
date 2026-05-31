"""Integration tests that build the full site and inspect its output."""

import json
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

pytestmark = pytest.mark.integration


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _all_html(built_site: Path) -> list[Path]:
    return list(built_site.rglob("*.html"))


def test_core_pages_exist(built_site: Path) -> None:
    for relative in [
        "index.html",
        "blog/index.html",
        "projects/index.html",
        "talks/index.html",
        "404.html",
    ]:
        assert (built_site / relative).is_file(), relative


def test_feeds_and_indexes_exist(built_site: Path) -> None:
    for relative in ["search.json", "rss.xml", "sitemap.xml", "robots.txt"]:
        assert (built_site / relative).is_file(), relative


def test_no_unrendered_template_syntax(built_site: Path) -> None:
    # Jinja control tags should never survive rendering. Code samples may
    # legitimately contain ``{{ }}``/``{% %}``, so strip <code>/<pre> first.
    control_pattern = re.compile(r"{%.*?%}|{{\s*\w+.*?}}")
    offenders: list[Path] = []
    for path in _all_html(built_site):
        soup = BeautifulSoup(_read(path), "html.parser")
        for snippet in soup.select("code, pre"):
            snippet.decompose()
        if control_pattern.search(soup.get_text()):
            offenders.append(path)
    assert not offenders, f"Unrendered template syntax in: {offenders}"


def test_every_page_has_shared_partials(built_site: Path) -> None:
    for path in _all_html(built_site):
        if path.name == "404.html":
            # 404 still has header/footer; check anyway.
            pass
        soup = BeautifulSoup(_read(path), "html.parser")
        assert soup.select_one("header.site-header"), f"missing header in {path}"
        assert soup.select_one("footer.site-footer"), f"missing footer in {path}"
        assert soup.select_one("#site-search-modal"), f"missing search modal in {path}"


def test_navbar_marks_active_page(built_site: Path) -> None:
    soup = BeautifulSoup(_read(built_site / "blog" / "index.html"), "html.parser")
    active = soup.select_one("a.nav-link.active")
    assert active is not None
    assert active.get("aria-current") == "page"
    assert active["href"] == "/blog/"


def test_project_tech_tags_are_spans_not_buttons(built_site: Path) -> None:
    soup = BeautifulSoup(_read(built_site / "projects" / "index.html"), "html.parser")
    tags = soup.select(".project-tech-tag")
    assert tags, "expected at least one project tech tag"
    assert all(tag.name == "span" for tag in tags)


def test_talks_have_youtube_links(built_site: Path) -> None:
    soup = BeautifulSoup(_read(built_site / "talks" / "index.html"), "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    assert any("youtube.com/watch?v=" in href for href in links)


def test_comments_use_preferred_color_scheme(built_site: Path) -> None:
    post_pages = [
        path
        for path in (built_site / "blog").rglob("index.html")
        if "page" not in path.parts and path.parent.name != "blog"
    ]
    assert post_pages, "expected at least one blog post page"
    soup = BeautifulSoup(_read(post_pages[0]), "html.parser")
    giscus = soup.find("script", attrs={"data-repo": True})
    assert giscus is not None
    assert giscus["data-theme"] == "preferred_color_scheme"


def test_search_json_is_valid_records(built_site: Path) -> None:
    data = json.loads(_read(built_site / "search.json"))
    assert isinstance(data, list)
    assert data, "search index should not be empty"
    kinds = {record["kind"] for record in data}
    assert kinds <= {"page", "post"}
    for record in data:
        assert {"title", "url", "kind"} <= record.keys()


def test_css_imports_are_all_copied(built_site: Path) -> None:
    styles = _read(built_site / "assets" / "styles.css")
    imported = re.findall(r"@import\s+(?:url\()?['\"]([^'\"]+)['\"]", styles)
    assert imported, "styles.css should @import partials"
    for name in imported:
        # CSS imports may be absolute URL paths (e.g. /assets/foo.css); strip
        # the leading "/" so Path joining resolves relative to the site root.
        target = (built_site / name.lstrip("/")).resolve()
        assert target.is_file(), f"missing imported stylesheet: {name}"


def test_blog_pagination_output(built_site: Path) -> None:
    # With more than 10 posts, a second page should exist.
    assert (built_site / "blog" / "index.html").is_file()
    page_two = built_site / "blog" / "page" / "2" / "index.html"
    if page_two.is_file():
        soup = BeautifulSoup(_read(page_two), "html.parser")
        assert soup.select_one("header.site-header")
