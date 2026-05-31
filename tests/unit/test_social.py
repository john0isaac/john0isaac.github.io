"""Unit tests for social card generator."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw, ImageFont

from scripts.social import (
    CARD_HEIGHT,
    CARD_WIDTH,
    _compute_hash,
    _wrap_text,
    generate_social_card,
)

pytestmark = pytest.mark.unit

_FONTS_DIR = Path(__file__).resolve().parents[2] / "vendor" / "fonts" / "static"
_LOGO_PATH = Path(__file__).resolve().parents[2] / "src" / "images" / "logo" / "android-chrome-512x512.png"


def _regular_font(size: int = 20) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(_FONTS_DIR / "Roboto-Regular.ttf"), size)


class TestComputeHash:
    def test_deterministic(self) -> None:
        h1 = _compute_hash("Title", "Desc", "Site")
        h2 = _compute_hash("Title", "Desc", "Site")
        assert h1 == h2

    def test_different_titles_differ(self) -> None:
        assert _compute_hash("A", "Desc", "Site") != _compute_hash("B", "Desc", "Site")

    def test_different_descriptions_differ(self) -> None:
        assert _compute_hash("T", "A", "Site") != _compute_hash("T", "B", "Site")

    def test_returns_40_char_hex(self) -> None:
        result = _compute_hash("x", "y", "z")
        assert len(result) == 40
        assert all(c in "0123456789abcdef" for c in result)


class TestWrapText:
    def _draw(self, width: int = 1200) -> ImageDraw.ImageDraw:
        return ImageDraw.Draw(Image.new("RGB", (width, 100)))

    def test_short_text_stays_single_line(self) -> None:
        lines = _wrap_text(self._draw(), "Hello", _regular_font(), max_width=1000)
        assert lines == ["Hello"]

    def test_long_text_wraps_into_multiple_lines(self) -> None:
        lines = _wrap_text(self._draw(), "one two three four five six seven", _regular_font(20), max_width=80)
        assert len(lines) > 1

    def test_all_words_preserved(self) -> None:
        text = "alpha beta gamma delta epsilon"
        lines = _wrap_text(self._draw(), text, _regular_font(20), max_width=80)
        assert " ".join(lines) == text

    def test_empty_string_returns_empty_list(self) -> None:
        lines = _wrap_text(self._draw(), "", _regular_font(), max_width=1000)
        assert lines == []


class TestGenerateSocialCard:
    def test_creates_png_at_dest_path(self, tmp_path: Path) -> None:
        dest = tmp_path / "card.png"
        generate_social_card(
            title="Test Title",
            description="A short description for the social card.",
            site_name="Test Site",
            logo_path=_LOGO_PATH,
            dest_path=dest,
            fonts_dir=_FONTS_DIR,
            cache_dir=tmp_path / ".cache" / "social",
        )
        assert dest.is_file()

    def test_output_has_correct_dimensions(self, tmp_path: Path) -> None:
        dest = tmp_path / "card.png"
        generate_social_card(
            title="Dimensions Check",
            description="Verifying 1200x630.",
            site_name="Test Site",
            logo_path=_LOGO_PATH,
            dest_path=dest,
            fonts_dir=_FONTS_DIR,
            cache_dir=tmp_path / ".cache" / "social",
        )
        img = Image.open(dest)
        assert img.size == (CARD_WIDTH, CARD_HEIGHT)

    def test_cache_hit_skips_regeneration(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / ".cache" / "social"
        kwargs = dict(
            title="Cache Test",
            description="Should be cached.",
            site_name="Site",
            logo_path=_LOGO_PATH,
            fonts_dir=_FONTS_DIR,
            cache_dir=cache_dir,
        )
        # First call — populates the cache
        dest1 = tmp_path / "out1" / "card.png"
        generate_social_card(dest_path=dest1, **kwargs)
        assert dest1.is_file()

        # Second call with same inputs — should copy from cache, not re-render
        dest2 = tmp_path / "out2" / "card.png"
        with patch("scripts.social._generate_card_image") as mock_render:
            generate_social_card(dest_path=dest2, **kwargs)
            mock_render.assert_not_called()
        assert dest2.is_file()
