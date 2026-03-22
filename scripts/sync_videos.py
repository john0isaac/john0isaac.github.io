"""Fetch YouTube channel videos and write them into talks.md."""

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import yaml

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"
TALKS_MD_PATH = Path(__file__).resolve().parent.parent / "src" / "talks.md"
THUMBNAIL_URL = "https://img.youtube.com/vi/{video_id}/mqdefault.jpg"


def _fetch_json(url: str) -> dict:
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
    return playlists["uploads"]


def fetch_playlist_videos(
    api_key: str,
    playlist_id: str,
    max_results: int = 50,
) -> list[dict]:
    """Fetch videos from a playlist, handling pagination."""
    videos: list[dict] = []
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


def fetch_video_statistics(api_key: str, videos: list[dict]) -> None:
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


def write_talks_md(videos: list[dict], output_path: Path) -> None:
    """Write talks.md with video data as YAML front matter."""
    front_matter = yaml.dump(
        {"template": "talks.html", "videos": videos},
        default_flow_style=False,
        sort_keys=False,
    )
    content = f"---\n{front_matter}---\n\n"
    # Write video titles/descriptions as hidden markdown so MkDocs search indexes them
    for video in videos:
        content += f"## {video['title']} {{ #{video['id']} }}\n\n"
        if video.get("description"):
            # Escape # at start of lines to prevent markdown heading interpretation
            desc = video["description"].replace("\n#", "\n\\#")
            if desc.startswith("#"):
                desc = "\\" + desc
            content += f"{desc}\n\n"
    output_path.write_text(content)
    print(f"Wrote {len(videos)} videos to {output_path}")


def main() -> None:
    """Parse arguments, fetch videos, and write talks.md."""
    parser = argparse.ArgumentParser(
        description="Sync YouTube videos to talks.md",
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
        default=TALKS_MD_PATH,
        help="Output path for talks.md",
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

    write_talks_md(videos, args.output)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(override=True)
    main()
