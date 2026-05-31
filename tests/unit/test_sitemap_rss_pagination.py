"""Unit tests for sitemap/RSS generation and pagination URL helpers."""

import datetime as dt
import xml.etree.ElementTree as etree
from pathlib import Path

import pytest

import main

pytestmark = pytest.mark.unit


def test_build_sitemap_is_valid_xml() -> None:
    xml_text = main.build_sitemap(["/", "/blog/", "/blog/post-one/"])
    root = etree.fromstring(xml_text)
    assert root.tag.endswith("urlset")
    locs = [loc.text for loc in root.iter() if loc.tag.endswith("loc")]
    assert f"{main.SITE_URL}/" in locs
    assert f"{main.SITE_URL}/blog/post-one/" in locs


def test_build_sitemap_absolute_urls() -> None:
    xml_text = main.build_sitemap(["/projects/"])
    assert f"{main.SITE_URL}/projects/" in xml_text


def test_build_sitemap_empty() -> None:
    xml_text = main.build_sitemap([])
    root = etree.fromstring(xml_text)
    assert list(root) == []


def test_render_rss_is_valid_xml(post_factory) -> None:
    posts = [
        post_factory(slug="newest", date=dt.date(2024, 6, 1), title="Newest"),
        post_factory(slug="older", date=dt.date(2024, 1, 1), title="Older"),
    ]
    rss = main.render_rss(posts)
    root = etree.fromstring(rss)
    assert root.tag == "rss"
    titles = [t.text for t in root.iter("title")]
    assert "Newest" in titles
    assert "Older" in titles


def test_render_rss_escapes_html(post_factory) -> None:
    post = post_factory(slug="x", title="A & B <script>", description="1 < 2 & 3")
    rss = main.render_rss([post])
    # Raw, unescaped markup must not appear in the feed.
    assert "<script>" not in rss
    assert "A &amp; B" in rss


def test_render_rss_limits_to_20(post_factory) -> None:
    posts = [post_factory(slug=str(i), date=dt.date(2024, 1, 1) + dt.timedelta(days=i)) for i in range(30)]
    rss = main.render_rss(posts)
    assert rss.count("<item>") == 20


def test_render_rss_empty_has_build_date() -> None:
    rss = main.render_rss([])
    root = etree.fromstring(rss)
    assert root.find("./channel/lastBuildDate") is not None


@pytest.mark.parametrize(
    ("page_number", "expected_url"),
    [
        (1, "/blog/"),
        (0, "/blog/"),
        (2, "/blog/page/2/"),
        (5, "/blog/page/5/"),
    ],
)
def test_blog_index_url(page_number: int, expected_url: str) -> None:
    assert main.blog_index_url(page_number) == expected_url


@pytest.mark.parametrize(
    ("page_number", "expected_suffix"),
    [
        (1, Path("blog") / "index.html"),
        (2, Path("blog") / "page" / "2" / "index.html"),
        (3, Path("blog") / "page" / "3" / "index.html"),
    ],
)
def test_blog_index_output_path(page_number: int, expected_suffix: Path) -> None:
    result = main.blog_index_output_path(page_number)
    assert result == main.SITE_DIR / expected_suffix
