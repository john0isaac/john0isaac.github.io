"""Unit tests for dataclass properties and context builders."""

import datetime as dt
from pathlib import Path

import pytest

import main

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("/blog/post/", f"{main.SITE_URL}/blog/post/"),
        ("/", f"{main.SITE_URL}/"),
        ("/projects/", f"{main.SITE_URL}/projects/"),
    ],
)
def test_page_absolute_url(url: str, expected: str) -> None:
    page = main.Page(
        title="T",
        description="D",
        url=url,
        template="home.html",
        output_path=Path("site/index.html"),
    )
    assert page.absolute_url == expected


def test_post_absolute_url(post_factory) -> None:
    post = post_factory(slug="hello")
    assert post.absolute_url == f"{main.SITE_URL}/blog/hello/"


@pytest.mark.parametrize(
    ("minutes", "expected"),
    [
        (1, "1 minute read"),
        (2, "2 minutes read"),
        (10, "10 minutes read"),
    ],
)
def test_post_read_time_label(post_factory, minutes: int, expected: str) -> None:
    post = post_factory(slug="x")
    post.read_time_minutes = minutes
    assert post.read_time_label == expected


def test_post_rss_date_is_rfc822(post_factory) -> None:
    post = post_factory(slug="x", date=dt.date(2024, 5, 1))
    # RFC 822 date string, e.g. "Wed, 01 May 2024 00:00:00 +0000"
    assert "01 May 2024" in post.rss_date
    assert post.rss_date.endswith("+0000")


def test_post_last_modified_defaults_to_publish_date(post_factory) -> None:
    post = post_factory(slug="x", date=dt.date(2024, 5, 1))
    assert post.last_modified == dt.date(2024, 5, 1)
    assert post.is_updated is False


def test_post_last_modified_uses_updated_when_later(post_factory) -> None:
    post = post_factory(slug="x", date=dt.date(2024, 5, 1), updated=dt.date(2024, 6, 10))
    assert post.last_modified == dt.date(2024, 6, 10)
    assert post.is_updated is True


def test_post_is_updated_false_when_updated_equals_date(post_factory) -> None:
    post = post_factory(slug="x", date=dt.date(2024, 5, 1), updated=dt.date(2024, 5, 1))
    assert post.is_updated is False


def test_site_navigation_structure() -> None:
    nav = main.site_navigation()
    urls = [item["url"] for item in nav]
    assert urls == ["/", "/blog/", "/projects/", "/talks/"]
    assert all({"title", "url"} <= item.keys() for item in nav)


def test_base_context_keys() -> None:
    context = main.base_context()
    assert context["site_name"] == main.SITE_NAME
    assert context["site_url"] == main.SITE_URL
    assert context["current_year"] == dt.date.today().year
    assert isinstance(context["navigation"], list)


def test_base_context_seo_keys() -> None:
    context = main.base_context()
    assert context["author_name"] == main.AUTHOR
    assert context["twitter_handle"].startswith("@")
    assert isinstance(context["same_as_links"], list)
    assert context["same_as_links"], "expected sameAs profile links"
    assert all(link.startswith("https://") for link in context["same_as_links"])
