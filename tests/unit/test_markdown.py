"""Unit tests for markdown rendering and read-time estimation."""

import pytest

import main

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("markdown_text", "expected_fragment"),
    [
        ("# Heading", "<h1"),
        ("**bold**", "<strong>bold</strong>"),
        ("- a\n- b", "<ul>"),
        ("`code`", "<code>code</code>"),
        ("[link](https://example.com)", 'href="https://example.com"'),
    ],
)
def test_render_markdown_produces_html(markdown_text: str, expected_fragment: str) -> None:
    assert expected_fragment in main.render_markdown(markdown_text)


@pytest.mark.parametrize("blank", ["", "   ", "\n\n", "\t"])
def test_render_markdown_blank_returns_empty(blank: str) -> None:
    assert main.render_markdown(blank) == ""


def test_render_markdown_resets_between_calls() -> None:
    """A stateful Markdown engine must not leak footnotes across calls."""
    first = main.render_markdown("Text[^1]\n\n[^1]: A footnote.")
    second = main.render_markdown("Plain text with nothing special.")
    assert 'class="footnote"' in first
    assert 'class="footnote"' not in second


@pytest.mark.parametrize(
    ("markdown_text", "expected"),
    [
        ("# Title\n\nSome **bold** text.", "Title Some bold text."),
        ("`inline code` here", "inline code here"),
        ("[a link](https://x.com)", "a link"),
    ],
)
def test_plain_text_from_markdown(markdown_text: str, expected: str) -> None:
    assert main.plain_text_from_markdown(markdown_text) == expected


@pytest.mark.parametrize(
    ("word_count", "expected_minutes"),
    [
        (0, 1),
        (1, 1),
        (200, 1),
        (201, 2),
        (400, 2),
        (401, 3),
        (1000, 5),
    ],
)
def test_estimate_read_time_minutes(word_count: int, expected_minutes: int) -> None:
    text = " ".join(["word"] * word_count)
    assert main.estimate_read_time_minutes(text) == expected_minutes


def test_estimate_read_time_custom_wpm() -> None:
    text = " ".join(["word"] * 100)
    assert main.estimate_read_time_minutes(text, words_per_minute=50) == 2


def test_estimate_read_time_empty_is_one() -> None:
    assert main.estimate_read_time_minutes("") == 1
