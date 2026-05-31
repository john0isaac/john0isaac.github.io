"""Unit tests for scripts/minify.py helper functions."""

from pathlib import Path

import pytest

from scripts.minify import minify_css, minify_html, minify_js, minify_site

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# minify_html
# ---------------------------------------------------------------------------


def test_minify_html_collapses_whitespace() -> None:
    source = "<html>\n  <body>\n    <p>Hello</p>\n  </body>\n</html>"
    result = minify_html(source)
    assert "\n" not in result
    assert "Hello" in result


def test_minify_html_removes_optional_attribute_quotes() -> None:
    source = '<meta name="viewport" content="width=device-width">'
    result = minify_html(source)
    # htmlmin removes quotes from single-token attribute values
    assert "name=viewport" in result


def test_minify_html_preserves_pre_content() -> None:
    source = "<pre>  indented\n  code  </pre>"
    result = minify_html(source)
    assert "  indented\n  code  " in result


def test_minify_html_keeps_comments_by_default() -> None:
    # minify_html is called with remove_comments=False
    source = "<!-- keep me --><p>text</p>"
    result = minify_html(source)
    assert "<!-- keep me -->" in result


# ---------------------------------------------------------------------------
# minify_css
# ---------------------------------------------------------------------------


def test_minify_css_removes_whitespace() -> None:
    source = "body {\n    margin: 0;\n    padding: 0;\n}"
    result = minify_css(source)
    assert "\n" not in result
    assert "margin:0" in result


def test_minify_css_removes_comments() -> None:
    source = "/* global reset */\nbody { margin: 0; }"
    result = minify_css(source)
    assert "/*" not in result


def test_minify_css_empty_string() -> None:
    assert minify_css("") == ""


# ---------------------------------------------------------------------------
# minify_js
# ---------------------------------------------------------------------------


def test_minify_js_removes_comments() -> None:
    source = "// single-line comment\nvar x = 1;"
    result = minify_js(source)
    assert "//" not in result
    assert "x" in result


def test_minify_js_removes_block_comments() -> None:
    source = "/* block */\nvar y = 2;"
    result = minify_js(source)
    assert "/*" not in result


def test_minify_js_preserves_string_content() -> None:
    source = 'var s = "hello world";'
    result = minify_js(source)
    assert "hello world" in result


def test_minify_js_empty_string() -> None:
    result = minify_js("")
    # jsmin may return empty or just whitespace for empty input
    assert result.strip() == ""


# ---------------------------------------------------------------------------
# minify_site
# ---------------------------------------------------------------------------


def test_minify_site_processes_html_css_js(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html>  <body>  </body>  </html>", encoding="utf-8")
    (tmp_path / "style.css").write_text("body {\n  margin: 0;\n}", encoding="utf-8")
    (tmp_path / "app.js").write_text("// comment\nvar x = 1;", encoding="utf-8")

    minify_site(tmp_path)

    assert "\n" not in (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "\n" not in (tmp_path / "style.css").read_text(encoding="utf-8")
    assert "//" not in (tmp_path / "app.js").read_text(encoding="utf-8")


def test_minify_site_skips_pre_minified_files(tmp_path: Path) -> None:
    original_css = "body {\n  margin: 0;\n}"
    original_js = "// comment\nvar x = 1;"
    (tmp_path / "bootstrap.min.css").write_text(original_css, encoding="utf-8")
    (tmp_path / "jquery.min.js").write_text(original_js, encoding="utf-8")

    minify_site(tmp_path)

    # *.min.* files must be left untouched
    assert (tmp_path / "bootstrap.min.css").read_text(encoding="utf-8") == original_css
    assert (tmp_path / "jquery.min.js").read_text(encoding="utf-8") == original_js


def test_minify_site_recurses_into_subdirectories(tmp_path: Path) -> None:
    sub = tmp_path / "blog" / "post"
    sub.mkdir(parents=True)
    (sub / "index.html").write_text("<p>  hello  </p>", encoding="utf-8")

    minify_site(tmp_path)

    result = (sub / "index.html").read_text(encoding="utf-8")
    assert "  hello  " not in result
    assert "hello" in result
