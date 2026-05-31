"""Unit tests for author loading and resolution."""

import textwrap

import pytest

import main

pytestmark = pytest.mark.unit


def test_load_authors_normalizes_entries(make_markdown) -> None:
    path = make_markdown(
        ".authors.yml",
        textwrap.dedent(
            """\
            authors:
              john:
                name: John Aziz
                description: Engineer
                avatar: /img/john.png
                url: https://johnaziz.org
              jane:
                name: Jane Doe
            """
        ),
    )
    authors = main.load_authors(path)
    assert authors["john"] == {
        "id": "john",
        "name": "John Aziz",
        "description": "Engineer",
        "avatar": "/img/john.png",
        "url": "https://johnaziz.org",
    }
    # Missing fields default to empty strings.
    assert authors["jane"]["name"] == "Jane Doe"
    assert authors["jane"]["description"] == ""
    assert authors["jane"]["url"] == ""


@pytest.mark.parametrize(
    "yaml_text",
    [
        "not_a_mapping",
        "- just\n- a\n- list",
        "authors: not_a_mapping",
        "something_else:\n  key: value",
    ],
)
def test_load_authors_invalid_shapes_return_empty(make_markdown, yaml_text: str) -> None:
    path = make_markdown(".authors.yml", yaml_text)
    assert main.load_authors(path) == {}


def test_load_authors_skips_non_dict_details(make_markdown) -> None:
    path = make_markdown(
        ".authors.yml",
        textwrap.dedent(
            """\
            authors:
              good:
                name: Good Author
              bad: just-a-string
            """
        ),
    )
    authors = main.load_authors(path)
    assert "good" in authors
    assert "bad" not in authors


def test_resolve_post_authors_known_and_unknown() -> None:
    lookup = {
        "john": {
            "id": "john",
            "name": "John Aziz",
            "description": "Engineer",
            "avatar": "",
            "url": "https://johnaziz.org",
        }
    }
    resolved = main.resolve_post_authors(["john", "ghost"], lookup)
    assert resolved[0]["name"] == "John Aziz"
    # Unknown author falls back to an id-only profile.
    assert resolved[1] == {
        "id": "ghost",
        "name": "ghost",
        "description": "",
        "avatar": "",
        "url": "",
    }


def test_resolve_post_authors_empty_list() -> None:
    assert main.resolve_post_authors([], {}) == []
