"""Minification helpers for HTML, CSS, and JS assets."""

from pathlib import Path

import csscompressor  # type: ignore[import-untyped]
import htmlmin  # type: ignore[import-untyped]
import jsmin as jsmin_module  # type: ignore[import-untyped]


def minify_html(content: str) -> str:
    return str(
        htmlmin.minify(
            content,
            remove_comments=False,
            remove_empty_space=True,
            remove_all_empty_space=False,
            reduce_empty_attributes=True,
            reduce_boolean_attributes=False,
            remove_optional_attribute_quotes=True,
            convert_charrefs=True,
            keep_pre=True,
        )
    )


def minify_css(content: str) -> str:
    return str(csscompressor.compress(content))


def minify_js(content: str) -> str:
    return str(jsmin_module.jsmin(content, quote_chars="'\"\\`"))


def minify_site(site_dir: Path) -> None:
    """Minify all HTML, CSS, and JS files in the built site directory in-place.

    Files already named *.min.css / *.min.js are skipped - they are
    pre-minified vendor assets (Bootstrap, FontAwesome, etc.).
    """
    for path in site_dir.rglob("*.html"):
        path.write_text(minify_html(path.read_text(encoding="utf-8")), encoding="utf-8")

    for path in site_dir.rglob("*.css"):
        if ".min." in path.name:
            continue
        path.write_text(minify_css(path.read_text(encoding="utf-8")), encoding="utf-8")

    for path in site_dir.rglob("*.js"):
        if ".min." in path.name:
            continue
        path.write_text(minify_js(path.read_text(encoding="utf-8")), encoding="utf-8")
