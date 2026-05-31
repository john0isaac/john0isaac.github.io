"""Unit tests for text/slug/date helper functions in ``main``."""

import datetime as dt
from pathlib import Path

import pytest

import main

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Hello World", "hello-world"),
        ("  Spaced  Out  ", "spaced-out"),
        ("Already-slug", "already-slug"),
        ("Special!@#Chars", "special-chars"),
        ("Multiple---Dashes", "multiple-dashes"),
        ("UPPER_case_Mix", "upper-case-mix"),
        ("café crème", "caf-cr-me"),
        ("123 numbers 456", "123-numbers-456"),
        ("---leading and trailing---", "leading-and-trailing"),
    ],
)
def test_slugify(value: str, expected: str) -> None:
    assert main.slugify(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (dt.date(2024, 5, 1), dt.date(2024, 5, 1)),
        (dt.datetime(2024, 5, 1, 13, 30), dt.date(2024, 5, 1)),
        ("2023-12-25", dt.date(2023, 12, 25)),
    ],
)
def test_date_from_value_valid(value: object, expected: dt.date) -> None:
    assert main.date_from_value(value) == expected


@pytest.mark.parametrize("value", [42, None, ["2024-01-01"], 3.14])
def test_date_from_value_invalid(value: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        main.date_from_value(value)


@pytest.mark.parametrize(
    ("front_matter", "body", "expected_meta"),
    [
        ("title: Hello\ndate: 2024-01-01", "Body text", {"title": "Hello", "date": dt.date(2024, 1, 1)}),
        ("title: Only Title", "More body", {"title": "Only Title"}),
    ],
)
def test_parse_document_with_front_matter(make_markdown, front_matter: str, body: str, expected_meta: dict) -> None:
    path = make_markdown("post.md", body, front_matter=front_matter)
    metadata, parsed_body = main.parse_document(path)
    assert metadata == expected_meta
    assert parsed_body.strip() == body


def test_parse_document_without_front_matter(make_markdown) -> None:
    path = make_markdown("plain.md", "Just content, no front matter.")
    metadata, body = main.parse_document(path)
    assert metadata == {}
    assert body == "Just content, no front matter."


def test_parse_document_empty_front_matter(make_markdown) -> None:
    path = make_markdown("empty.md", "Body", front_matter="")
    metadata, body = main.parse_document(path)
    assert metadata == {}
    assert body.strip() == "Body"


@pytest.mark.parametrize(
    ("body", "expected_excerpt"),
    [
        ("First paragraph.\n\nSecond paragraph.", "First paragraph."),
        ("Lead in <!-- more --> hidden rest", "Lead in"),
        ("Single paragraph only", "Single paragraph only"),
        ("", ""),
    ],
)
def test_split_excerpt(body: str, expected_excerpt: str) -> None:
    excerpt, full = main.split_excerpt(body)
    assert excerpt == expected_excerpt
    if body.strip():
        assert full


def test_split_excerpt_more_marker_keeps_full_body() -> None:
    excerpt, full = main.split_excerpt("Intro <!-- more --> The rest of it.")
    assert excerpt == "Intro"
    assert "The rest of it." in full


@pytest.mark.parametrize(
    ("stem", "metadata", "expected"),
    [
        ("2024-01-15-my-post", {}, "my-post"),
        ("plain-name", {}, "plain-name"),
        ("2024-01-15-ignored", {"slug": "Custom Slug"}, "custom-slug"),
        ("2024-12-31-end-of-year-review", {}, "end-of-year-review"),
    ],
)
def test_post_slug(stem: str, metadata: dict, expected: str) -> None:
    assert main.post_slug(Path(f"{stem}.md"), metadata) == expected
