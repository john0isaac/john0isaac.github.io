"""Fetch YouTube channel videos and write them into data/videos.yml."""

import argparse
import io
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import yaml
from PIL import Image

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"
REPO_ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DATA_PATH = REPO_ROOT / "data" / "videos.yml"
THUMBNAILS_DIR = REPO_ROOT / "assets" / "img" / "talks"
THUMBNAILS_URL_PREFIX = "/assets/img/talks"
THUMBNAIL_URL = "https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
# Best quality first; maxresdefault (1280x720) is missing for some videos.
THUMBNAIL_SIZES = ("maxresdefault", "sddefault", "hqdefault", "mqdefault")
THUMBNAIL_WEBP_QUALITY = 82
# Pre-resized widths for srcset; browsers downscaling 1280px into a small card make text jagged.
THUMBNAIL_WIDTHS = (400, 800)


def _fetch_json(url: str) -> Any:
    """Fetch a URL and return the parsed JSON response."""
    with urlopen(Request(url)) as resp:  # noqa: S310
        return json.loads(resp.read())


def fetch_uploads_playlist_id(api_key: str, channel_handle: str) -> str:
    """Return the uploads playlist ID for a channel handle."""
    handle = channel_handle.lstrip("@")
    url = f"{YOUTUBE_API_URL}/channels?forHandle={handle}&part=contentDetails&key={api_key}"
    data = _fetch_json(url)
    items = data.get("items", [])
    if not items:
        raise SystemExit(f"No channel found for handle @{handle}")

    playlists = items[0]["contentDetails"]["relatedPlaylists"]
    return str(playlists["uploads"])


def fetch_playlist_videos(
    api_key: str,
    playlist_id: str,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """Fetch videos from a playlist, handling pagination."""
    videos: list[dict[str, Any]] = []
    page_token = ""

    while len(videos) < max_results:
        batch_size = min(max_results - len(videos), 50)
        url = (
            f"{YOUTUBE_API_URL}/playlistItems"
            f"?playlistId={playlist_id}"
            f"&part=snippet"
            f"&maxResults={batch_size}"
            f"&key={api_key}"
        )
        if page_token:
            url += f"&pageToken={page_token}"

        data = _fetch_json(url)

        for item in data.get("items", []):
            snippet = item["snippet"]
            video_id = snippet["resourceId"]["videoId"]
            description = snippet.get("description", "")
            videos.append(
                {
                    "id": video_id,
                    "title": snippet["title"],
                    "description": description,
                    "published": snippet["publishedAt"][:10],
                    "thumbnail": THUMBNAIL_URL.format(video_id=video_id),
                }
            )

        page_token = data.get("nextPageToken", "")
        if not page_token:
            break

    return videos


def fetch_video_statistics(api_key: str, videos: list[dict[str, Any]]) -> None:
    """Fetch view counts for videos and add them in-place."""
    # The videos endpoint accepts up to 50 IDs per request
    for i in range(0, len(videos), 50):
        batch = videos[i : i + 50]
        ids = ",".join(v["id"] for v in batch)
        url = f"{YOUTUBE_API_URL}/videos?id={ids}&part=statistics&key={api_key}"
        data = _fetch_json(url)
        stats_map = {item["id"]: item["statistics"] for item in data.get("items", [])}
        for video in batch:
            stats = stats_map.get(video["id"], {})
            video["views"] = int(stats.get("viewCount", 0))


def download_best_thumbnail(video_id: str) -> bytes:
    """Return the highest-resolution thumbnail YouTube has for a video."""
    for size in THUMBNAIL_SIZES:
        url = f"https://img.youtube.com/vi/{video_id}/{size}.jpg"
        try:
            with urlopen(Request(url)) as resp:  # noqa: S310
                return bytes(resp.read())
        except HTTPError as error:
            if error.code != 404:
                raise
    raise RuntimeError(f"No thumbnail available for video {video_id}")


def thumbnail_variants(data: bytes) -> dict[str, bytes]:
    """Crop to 16:9 (the 4:3 fallbacks are letterboxed) and encode WebP variants.

    Returns filename suffixes ("" for full size, "-400" etc.) mapped to WebP bytes.
    """
    with Image.open(io.BytesIO(data)) as image:
        rgb = image.convert("RGB")
    width, height = rgb.size
    target_height = round(width * 9 / 16)
    if target_height < height:
        top = (height - target_height) // 2
        rgb = rgb.crop((0, top, width, top + target_height))

    variants: dict[str, bytes] = {}
    sizes = [(f"-{w}", w) for w in THUMBNAIL_WIDTHS] + [("", rgb.width)]
    for suffix, target_width in sizes:
        target_width = min(target_width, rgb.width)
        resized = rgb.resize((target_width, round(target_width * 9 / 16)), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        resized.save(out, "WEBP", quality=THUMBNAIL_WEBP_QUALITY, method=6)
        variants[suffix] = out.getvalue()
    return variants


def localize_thumbnails(videos: list[dict[str, Any]], thumbnails_dir: Path) -> None:
    """Download thumbnails so the site serves them itself instead of loading from YouTube.

    Thumbnails already on disk are reused, and images for videos that are gone are removed.
    """
    thumbnails_dir.mkdir(parents=True, exist_ok=True)
    wanted: set[str] = set()
    for video in videos:
        names = {suffix: f"{video['id']}{suffix}.webp" for suffix in ["", *(f"-{w}" for w in THUMBNAIL_WIDTHS)]}
        wanted.update(names.values())
        if not all((thumbnails_dir / name).exists() for name in names.values()):
            for suffix, payload in thumbnail_variants(download_best_thumbnail(video["id"])).items():
                (thumbnails_dir / names[suffix]).write_bytes(payload)
        video["thumbnail"] = f"{THUMBNAILS_URL_PREFIX}/{names['']}"
    for stale in thumbnails_dir.iterdir():
        if stale.is_file() and stale.name not in wanted:
            stale.unlink()


def write_videos_data(videos: list[dict[str, Any]], data_path: Path) -> None:
    """Write video data as a standalone YAML file."""
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_path, "w") as f:
        yaml.dump(videos, f, default_flow_style=False, sort_keys=False)
    print(f"Wrote {len(videos)} videos to {data_path}")


def main() -> None:
    """Parse arguments, fetch videos, and write data/videos.yml."""
    parser = argparse.ArgumentParser(
        description="Sync YouTube videos to data/videos.yml",
    )
    parser.add_argument(
        "--channel",
        default="@john0isaac",
        help="YouTube channel handle (default: @john0isaac)",
    )
    parser.add_argument(
        "--playlists",
        nargs="*",
        default=["PLIflvZbgDJt2a6sT3PCBj-qfsCZSJiHbw"],
        help="Additional playlist IDs to include",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of videos to fetch (default: 50)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=VIDEOS_DATA_PATH,
        help="Output path for videos data YAML",
    )
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise SystemExit("YOUTUBE_API_KEY environment variable is required")

    print(f"Fetching uploads for {args.channel}...")
    uploads_id = fetch_uploads_playlist_id(api_key, args.channel)
    videos = fetch_playlist_videos(api_key, uploads_id, args.max_results)
    seen_ids = {v["id"] for v in videos}

    for pl_id in args.playlists or []:
        print(f"Fetching playlist {pl_id}...")
        for video in fetch_playlist_videos(api_key, pl_id, args.max_results):
            if video["id"] not in seen_ids:
                seen_ids.add(video["id"])
                videos.append(video)

    videos.sort(key=lambda v: v["published"], reverse=True)

    print("Fetching video statistics...")
    fetch_video_statistics(api_key, videos)

    print("Downloading thumbnails...")
    localize_thumbnails(videos, THUMBNAILS_DIR)

    write_videos_data(videos, args.output)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(override=True)
    main()
