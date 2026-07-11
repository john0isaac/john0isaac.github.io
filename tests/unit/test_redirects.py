"""Unit tests for the vanity redirect page generator."""

from pathlib import Path

import pytest

import main

pytestmark = pytest.mark.unit


def test_build_redirects_writes_one_page_per_slug(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "SITE_DIR", tmp_path)
    environment = main.build_environment()
    redirects = {
        "github": "https://github.com/john0isaac",
        "markdown-checker": "https://markdown-checker.readthedocs.io/en/latest/",
    }

    main.build_redirects(environment, redirects)

    for slug in redirects:
        assert (tmp_path / slug / "index.html").is_file()


def test_build_redirects_page_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "SITE_DIR", tmp_path)
    environment = main.build_environment()
    target_url = "https://linkedin.com/in/john0isaac"

    main.build_redirects(environment, {"linkedin": target_url})

    html = (tmp_path / "linkedin" / "index.html").read_text(encoding="utf-8")
    assert f'content="0; url={target_url}"' in html
    assert 'name="robots" content="noindex, nofollow"' in html
    assert f'rel="canonical" href="{target_url}"' in html
    assert f'window.location.replace("{target_url}");' in html


def test_real_redirects_constant_covers_expected_slugs() -> None:
    assert main.REDIRECTS["github"] == "https://github.com/john0isaac"
    assert main.REDIRECTS["linkedin"] == "https://linkedin.com/in/john0isaac"
    assert main.REDIRECTS["youtube"] == "https://youtube.com/@john0isaac"
    assert main.REDIRECTS["twitter"] == "https://x.com/john00isaac"
    assert main.REDIRECTS["markdown-checker"] == "https://markdown-checker.readthedocs.io/en/latest/"
