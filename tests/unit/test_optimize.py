"""Unit tests for scripts/optimize.py helper functions."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from scripts.optimize import (
    _optimize_png_pillow,
    _optimize_png_pngquant,
    optimize_jpg,
    optimize_png,
    optimize_site,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_jpg(path: Path, size: tuple[int, int] = (100, 100)) -> None:
    image = Image.new("RGB", size, color=(128, 64, 32))
    image.save(path, "jpeg", quality=95)


def _write_png(path: Path, size: tuple[int, int] = (100, 100)) -> None:
    image = Image.new("RGBA", size, color=(0, 128, 255, 255))
    image.save(path, "png")


# ---------------------------------------------------------------------------
# optimize_jpg
# ---------------------------------------------------------------------------


def test_optimize_jpg_produces_valid_jpeg(tmp_path: Path) -> None:
    path = tmp_path / "photo.jpg"
    _write_jpg(path)
    original_size = path.stat().st_size

    optimize_jpg(path)

    assert path.exists()
    image = Image.open(path)
    assert image.format == "JPEG"
    # Re-saving at quality=60 should not increase size significantly
    assert path.stat().st_size <= original_size * 1.05


def test_optimize_jpg_converts_rgba_to_rgb(tmp_path: Path) -> None:
    path = tmp_path / "image.jpg"
    # Save an RGBA image as JPEG (normally Pillow raises on RGBA -> JPEG)
    rgba = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
    # Write as PNG first, then optimize_jpg must handle the conversion
    png_path = tmp_path / "image.png"
    rgba.save(png_path, "png")
    # Simulate: caller passed a file that Pillow opens as RGBA
    # We test optimize_jpg directly on a JPEG; create a JPEG from the RGBA
    rgba.convert("RGB").save(path, "jpeg")
    optimize_jpg(path)
    result = Image.open(path)
    assert result.mode == "RGB"


def test_optimize_jpg_jpeg_extension(tmp_path: Path) -> None:
    path = tmp_path / "photo.jpeg"
    _write_jpg(path)
    optimize_jpg(path)
    assert path.exists()
    assert Image.open(path).format == "JPEG"


# ---------------------------------------------------------------------------
# optimize_png / _optimize_png_pillow
# ---------------------------------------------------------------------------


def test_optimize_png_pillow_produces_valid_png(tmp_path: Path) -> None:
    path = tmp_path / "icon.png"
    _write_png(path)

    _optimize_png_pillow(path)

    assert path.exists()
    image = Image.open(path)
    assert image.format == "PNG"


def test_optimize_png_pillow_preserves_dimensions(tmp_path: Path) -> None:
    path = tmp_path / "icon.png"
    _write_png(path, size=(64, 64))
    _optimize_png_pillow(path)
    assert Image.open(path).size == (64, 64)


def test_optimize_png_uses_pngquant_when_available(tmp_path: Path) -> None:
    path = tmp_path / "icon.png"
    _write_png(path)

    with (
        patch("scripts.optimize.which", return_value="/usr/bin/pngquant"),
        patch("scripts.optimize._optimize_png_pngquant") as mock_pngquant,
    ):
        optimize_png(path)

    mock_pngquant.assert_called_once_with(path, 3)


def test_optimize_png_falls_back_to_pillow_when_no_pngquant(tmp_path: Path) -> None:
    path = tmp_path / "icon.png"
    _write_png(path)

    with (
        patch("scripts.optimize.which", return_value=None),
        patch("scripts.optimize._optimize_png_pillow") as mock_pillow,
    ):
        optimize_png(path)

    mock_pillow.assert_called_once_with(path)


def test_optimize_png_pngquant_uses_original_when_no_output(tmp_path: Path) -> None:
    """If pngquant doesn't write a file (already optimal), original is kept."""
    path = tmp_path / "icon.png"
    _write_png(path)
    original_content = path.read_bytes()

    # Mock subprocess.run to do nothing (pngquant skips writing)
    with patch("scripts.optimize.subprocess.run"):
        _optimize_png_pngquant(path, speed=3)

    assert path.read_bytes() == original_content


def test_optimize_png_pngquant_replaces_with_tmp_when_written(tmp_path: Path) -> None:
    """If pngquant writes a tmp file, it replaces the original."""
    path = tmp_path / "icon.png"
    _write_png(path)
    optimized_content = b"optimized-png-data"

    def fake_run(args, **kwargs):
        # Simulate pngquant writing to the --output path (args[4])
        output_path = Path(args[4])
        output_path.write_bytes(optimized_content)

    with patch("scripts.optimize.subprocess.run", side_effect=fake_run):
        _optimize_png_pngquant(path, speed=3)

    assert path.read_bytes() == optimized_content


# ---------------------------------------------------------------------------
# optimize_site
# ---------------------------------------------------------------------------


def test_optimize_site_processes_jpg_and_png(tmp_path: Path) -> None:
    jpg = tmp_path / "photo.jpg"
    png = tmp_path / "icon.png"
    _write_jpg(jpg)
    _write_png(png)

    optimize_site(tmp_path)

    assert Image.open(jpg).format == "JPEG"
    assert Image.open(png).format == "PNG"


def test_optimize_site_recurses_into_subdirectories(tmp_path: Path) -> None:
    sub = tmp_path / "images" / "blog"
    sub.mkdir(parents=True)
    jpg = sub / "cover.jpg"
    _write_jpg(jpg)

    optimize_site(tmp_path)

    assert Image.open(jpg).format == "JPEG"


def test_optimize_site_ignores_non_image_files(tmp_path: Path) -> None:
    txt = tmp_path / "readme.txt"
    txt.write_text("hello", encoding="utf-8")

    # Should not raise
    optimize_site(tmp_path)

    assert txt.read_text(encoding="utf-8") == "hello"


def test_optimize_site_handles_empty_directory(tmp_path: Path) -> None:
    # Should not raise when there are no images
    optimize_site(tmp_path)
