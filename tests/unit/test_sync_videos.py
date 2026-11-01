"""Unit tests for the YouTube sync helpers."""

import io
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from scripts.sync_videos import localize_thumbnails, thumbnail_variants


def _jpeg(width: int, height: int) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (width, height), "navy").save(out, "JPEG")
    return out.getvalue()


def test_thumbnail_variants_crop_letterbox_and_resize() -> None:
    variants = thumbnail_variants(_jpeg(640, 480))

    sizes = {suffix: Image.open(io.BytesIO(data)).size for suffix, data in variants.items()}
    assert sizes == {"-400": (400, 225), "-800": (640, 360), "": (640, 360)}


def test_localize_thumbnails_reuses_files_and_prunes_stale(tmp_path: Path) -> None:
    for name in ["keep.webp", "keep-400.webp", "keep-800.webp", "gone.webp", "old.jpg"]:
        (tmp_path / name).write_bytes(b"cached")
    videos = [{"id": "keep"}]

    with patch("scripts.sync_videos.download_best_thumbnail") as download:
        localize_thumbnails(videos, tmp_path)

    download.assert_not_called()
    assert videos[0]["thumbnail"] == "/assets/img/talks/keep.webp"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["keep-400.webp", "keep-800.webp", "keep.webp"]


def test_localize_thumbnails_downloads_missing(tmp_path: Path) -> None:
    videos = [{"id": "new"}]

    with patch("scripts.sync_videos.download_best_thumbnail", return_value=_jpeg(1280, 720)):
        localize_thumbnails(videos, tmp_path)

    assert Image.open(tmp_path / "new.webp").size == (1280, 720)
    assert Image.open(tmp_path / "new-400.webp").size == (400, 225)
    assert videos[0]["thumbnail"] == "/assets/img/talks/new.webp"
