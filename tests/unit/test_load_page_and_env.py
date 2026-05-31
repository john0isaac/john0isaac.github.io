"""Unit tests for ``load_page`` and the Jinja2 environment helpers."""

import datetime as dt
from pathlib import Path

import pytest

import main

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# load_page
# ---------------------------------------------------------------------------


def test_load_page_uses_front_matter_fields(make_markdown, tmp_path: Path) -> None:
    path = make_markdown(
        "about.md",
        "Some page body.",
        front_matter="title: About Me\ndescription: Who I am",
    )
    page = main.load_page(
        path,
        url="/about/",
        template="home.html",
        output_path=tmp_path / "about" / "index.html",
    )
    assert page.title == "About Me"
    assert page.description == "Who I am"
    assert page.url == "/about/"
    assert page.template == "home.html"


def test_load_page_missing_optional_fields_default_to_empty(make_markdown, tmp_path: Path) -> None:
    path = make_markdown("bare.md", "Body only, no front matter.")
    page = main.load_page(
        path,
        url="/bare/",
        template="home.html",
        output_path=tmp_path / "bare" / "index.html",
    )
    assert page.title == ""
    assert page.description == ""


def test_load_page_renders_body_as_html(make_markdown, tmp_path: Path) -> None:
    path = make_markdown(
        "rich.md",
        "## Section\n\nA **bold** word.",
        front_matter="title: Rich",
    )
    page = main.load_page(
        path,
        url="/rich/",
        template="home.html",
        output_path=tmp_path / "rich" / "index.html",
    )
    assert "<h2" in page.content_html
    assert "<strong>bold</strong>" in page.content_html


def test_load_page_preserves_body_markdown(make_markdown, tmp_path: Path) -> None:
    body = "Just some **raw** markdown."
    path = make_markdown("raw.md", body, front_matter="title: Raw")
    page = main.load_page(
        path,
        url="/raw/",
        template="home.html",
        output_path=tmp_path / "raw" / "index.html",
    )
    assert page.body_markdown.strip() == body


def test_load_page_stores_full_metadata(make_markdown, tmp_path: Path) -> None:
    path = make_markdown(
        "meta.md",
        "Content.",
        front_matter="title: Meta\ncustom_key: custom_value",
    )
    page = main.load_page(
        path,
        url="/meta/",
        template="home.html",
        output_path=tmp_path / "meta" / "index.html",
    )
    assert page.metadata.get("custom_key") == "custom_value"


def test_load_page_output_path_is_preserved(make_markdown, tmp_path: Path) -> None:
    path = make_markdown("out.md", "Body.", front_matter="title: Out")
    output_path = tmp_path / "out" / "index.html"
    page = main.load_page(path, url="/out/", template="home.html", output_path=output_path)
    assert page.output_path == output_path


# ---------------------------------------------------------------------------
# build_environment / date_human filter
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def jinja_env():
    return main.build_environment()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (dt.date(2024, 5, 1), "May 01, 2024"),
        (dt.date(2023, 12, 25), "Dec 25, 2023"),
        (dt.datetime(2024, 1, 7, 15, 30), "Jan 07, 2024"),
        ("2024-06-15", "Jun 15, 2024"),
    ],
)
def test_date_human_filter(jinja_env, value, expected: str) -> None:
    date_human = jinja_env.filters["date_human"]
    assert date_human(value) == expected


def test_build_environment_has_autoescape(jinja_env) -> None:
    """HTML special characters must be escaped automatically."""
    tmpl = jinja_env.from_string("{{ value }}")
    rendered = tmpl.render(value="<script>alert(1)</script>")
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_build_environment_has_date_human_filter(jinja_env) -> None:
    assert "date_human" in jinja_env.filters
