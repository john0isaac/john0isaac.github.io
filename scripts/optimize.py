"""Image optimization helpers for PNG and JPG/JPEG assets.

PNG optimization uses ``pngquant`` (lossy, external binary) when it is
available on PATH, and falls back to Pillow lossless compression otherwise.
JPG/JPEG optimization uses Pillow to reduce quality and enable progressive
encoding.
"""

import subprocess
from pathlib import Path
from shutil import which

from PIL import Image

# Default optimization
_JPG_QUALITY = 60
_JPG_PROGRESSIVE = True
_PNG_SPEED = 3  # pngquant: 1 = slow/best quality, 11 = fast/worst


def optimize_jpg(path: Path, quality: int = _JPG_QUALITY, progressive: bool = _JPG_PROGRESSIVE) -> None:
    """Re-save a JPEG at reduced quality with optional progressive encoding."""
    image: Image.Image = Image.open(path)
    if image.mode in ("RGBA", "P", "LA"):
        image = image.convert("RGB")
    image.save(path, "jpeg", quality=quality, optimize=True, progressive=progressive)


def optimize_png(path: Path, speed: int = _PNG_SPEED) -> None:
    """Optimize a PNG file.

    Uses ``pngquant`` (lossy) when available on PATH for maximum compression.
    Falls back to Pillow lossless optimization when ``pngquant`` is not found.
    """
    if which("pngquant"):
        _optimize_png_pngquant(path, speed)
    else:
        _optimize_png_pillow(path)


def _optimize_png_pngquant(path: Path, speed: int) -> None:
    tmp = path.with_suffix(".opt.png")
    subprocess.run(
        [
            "pngquant",
            "--force",
            "--skip-if-larger",
            "--output",
            str(tmp),
            "--speed",
            str(speed),
            "--strip",
            str(path),
        ],
        check=False,
        capture_output=True,
    )
    if tmp.exists():
        tmp.replace(path)
    # If pngquant didn't write the file, the original was already optimal —
    # leave it unchanged.


def _optimize_png_pillow(path: Path) -> None:
    image = Image.open(path)
    image.save(path, "png", optimize=True)


def optimize_site(site_dir: Path) -> None:
    """Optimize all PNG and JPG/JPEG images in the built site directory in-place.

    ``.ico`` files and other binary assets are left untouched.
    """
    for path in site_dir.rglob("*.jpg"):
        optimize_jpg(path)

    for path in site_dir.rglob("*.jpeg"):
        optimize_jpg(path)

    for path in site_dir.rglob("*.png"):
        optimize_png(path)
