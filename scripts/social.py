"""Social card generator: produces 1200x630 PNG cards for all pages and posts."""

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import Page, Post

CARD_WIDTH = 1200
CARD_HEIGHT = 630
_BG_COLOR = "#0d1117"
_ACCENT_COLOR = "#3b82f6"
_TITLE_COLOR = "#ffffff"
_MUTED_COLOR = "#8b949e"


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Split *text* into lines that each fit within *max_width* pixels."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current: list[str] = []
    current_width = 0.0
    space_width = draw.textlength(" ", font=font)
    for word in words:
        word_width = draw.textlength(word, font=font)
        gap = space_width if current else 0.0
        if current and current_width + gap + word_width > max_width:
            lines.append(" ".join(current))
            current = [word]
            current_width = word_width
        else:
            current.append(word)
            current_width += gap + word_width
    if current:
        lines.append(" ".join(current))
    return lines


def _compute_hash(title: str, description: str, site_name: str) -> str:
    data = f"{title}|{description}|{site_name}"
    return hashlib.sha1(data.encode()).hexdigest()  # noqa: S324 - not security-sensitive


def _generate_card_image(
    title: str,
    description: str,
    site_name: str,
    logo_img: Image.Image,
    fonts_dir: Path,
) -> Image.Image:
    image = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), _BG_COLOR)
    draw = ImageDraw.Draw(image)

    # Accent bar at the bottom
    draw.rectangle([(0, CARD_HEIGHT - 8), (CARD_WIDTH, CARD_HEIGHT)], fill=_ACCENT_COLOR)

    # Logo - top-right corner
    image.paste(logo_img, (1072, 48), logo_img if logo_img.mode == "RGBA" else None)

    # Fonts
    font_bold = ImageFont.truetype(str(fonts_dir / "Roboto-Bold.ttf"), 56)
    font_regular_lg = ImageFont.truetype(str(fonts_dir / "Roboto-Regular.ttf"), 30)
    font_regular_sm = ImageFont.truetype(str(fonts_dir / "Roboto-Regular.ttf"), 26)

    # Site name
    draw.text((48, 60), site_name, font=font_regular_sm, fill=_MUTED_COLOR)

    # Title - up to 3 lines
    title_lines = _wrap_text(draw, title, font_bold, max_width=1104)[:3]
    y = 160
    for line in title_lines:
        draw.text((48, y), line, font=font_bold, fill=_TITLE_COLOR)
        y += 70  # ~56pt + leading

    # Description - up to 2 lines
    if description:
        desc_lines = _wrap_text(draw, description, font_regular_lg, max_width=960)[:2]
        y = 490
        for line in desc_lines:
            draw.text((48, y), line, font=font_regular_lg, fill=_MUTED_COLOR)
            y += 44

    return image


def generate_social_card(
    title: str,
    description: str,
    site_name: str,
    logo_path: Path,
    dest_path: Path,
    fonts_dir: Path,
    cache_dir: Path,
) -> None:
    """Generate a single social card PNG at *dest_path*, using the cache when possible."""
    card_hash = _compute_hash(title, description, site_name)
    manifest_path = cache_dir / "manifest.json"
    cache_cards_dir = cache_dir / "cards"
    cache_key = dest_path.name

    manifest: dict[str, str] = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            manifest = {}

    cached_png = cache_cards_dir / cache_key
    if manifest.get(cache_key) == card_hash and cached_png.is_file():
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cached_png, dest_path)
        return

    logo_img = Image.open(logo_path).convert("RGBA").resize((80, 80), Image.Resampling.LANCZOS)
    image = _generate_card_image(title, description, site_name, logo_img, fonts_dir)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest_path, format="PNG", optimize=True)

    cache_cards_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dest_path, cached_png)

    manifest[cache_key] = card_hash
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def generate_social_cards(
    posts: list[Post],
    pages: list[Page],
    site_dir: Path,
    site_name: str,
    logo_path: Path,
    fonts_dir: Path,
    cache_dir: Path,
) -> None:
    """Generate social card PNGs for all pages and posts into *site_dir/assets/social/*."""
    for page in pages:
        if not page.social_card_url:
            continue
        dest_path = site_dir / page.social_card_url.lstrip("/")
        generate_social_card(
            title=page.title,
            description=page.description,
            site_name=site_name,
            logo_path=logo_path,
            dest_path=dest_path,
            fonts_dir=fonts_dir,
            cache_dir=cache_dir,
        )
    for post in posts:
        if not post.social_card_url:
            continue
        dest_path = site_dir / post.social_card_url.lstrip("/")
        generate_social_card(
            title=post.title,
            description=post.description,
            site_name=site_name,
            logo_path=logo_path,
            dest_path=dest_path,
            fonts_dir=fonts_dir,
            cache_dir=cache_dir,
        )
