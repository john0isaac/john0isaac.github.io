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
    styles = _read(built_site / "assets" / "css" / "styles.css")
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


def test_social_cards_are_generated(built_site: Path) -> None:
    social_dir = built_site / "assets" / "social"
    assert social_dir.is_dir(), "assets/social/ directory should exist after build"
    pngs = list(social_dir.glob("*.png"))
    assert pngs, "at least one social card PNG should be generated"
    post_cards = [p for p in pngs if p.name.startswith("blog-")]
    assert post_cards, "at least one blog post social card should exist"


def test_blog_post_has_og_image_meta(built_site: Path) -> None:
    post_pages = [
        path
        for path in (built_site / "blog").rglob("index.html")
        if "page" not in path.parts and path.parent.name != "blog"
    ]
    assert post_pages, "expected at least one blog post page"
    soup = BeautifulSoup(_read(post_pages[0]), "html.parser")
    og_image = soup.find("meta", attrs={"property": "og:image"})
    assert og_image is not None, "blog post should have og:image meta tag"
    content = og_image.get("content", "")
    assert "/assets/social/" in content, f"og:image should point to social card: {content}"
    assert content.endswith(".png"), f"og:image should be a PNG: {content}"


def _post_pages(built_site: Path) -> list[Path]:
    return [
        path
        for path in (built_site / "blog").rglob("index.html")
        if "page" not in path.parts and path.parent.name != "blog"
    ]


def _json_ld(soup: BeautifulSoup) -> list[dict]:
    blocks = soup.find_all("script", attrs={"type": "application/ld+json"})
    return [json.loads(block.string) for block in blocks]


def test_home_has_person_and_website_schema(built_site: Path) -> None:
    soup = BeautifulSoup(_read(built_site / "index.html"), "html.parser")
    graphs = _json_ld(soup)
    assert graphs, "home page should embed JSON-LD"
    nodes = graphs[0]["@graph"]
    types = {node["@type"] for node in nodes}
    assert {"Person", "WebSite"} <= types
    person = next(node for node in nodes if node["@type"] == "Person")
    assert person["name"]
    assert person["sameAs"], "Person should list sameAs profile links"


def test_blog_post_has_article_and_breadcrumb_schema(built_site: Path) -> None:
    soup = BeautifulSoup(_read(_post_pages(built_site)[0]), "html.parser")
    nodes = _json_ld(soup)[0]["@graph"]
    types = {node["@type"] for node in nodes}
    assert {"BlogPosting", "BreadcrumbList"} <= types
    article = next(node for node in nodes if node["@type"] == "BlogPosting")
    assert article["author"]["@type"] == "Person"
    assert article["datePublished"]
    assert article["dateModified"]


def test_blog_post_og_type_is_article(built_site: Path) -> None:
    soup = BeautifulSoup(_read(_post_pages(built_site)[0]), "html.parser")
    og_type = soup.find("meta", attrs={"property": "og:type"})
    assert og_type is not None
    assert og_type.get("content") == "article"


def test_pages_have_author_and_twitter_creator(built_site: Path) -> None:
    soup = BeautifulSoup(_read(built_site / "index.html"), "html.parser")
    assert soup.find("meta", attrs={"name": "author"}) is not None
    creator = soup.find("meta", attrs={"name": "twitter:creator"})
    assert creator is not None
    assert creator.get("content", "").startswith("@")


def test_sitemap_has_lastmod(built_site: Path) -> None:
    sitemap = _read(built_site / "sitemap.xml")
    assert "<lastmod>" in sitemap
    assert "<changefreq>" in sitemap


def test_rss_has_creator_and_categories(built_site: Path) -> None:
    rss = _read(built_site / "rss.xml")
    assert "<dc:creator>" in rss
    assert "<category>" in rss
