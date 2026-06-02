import datetime as dt
from dataclasses import dataclass, field
from email.utils import format_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from .constants import GITHUB_REPO, ROOT_DIR, SITE_URL


@dataclass(slots=True)
class Page:
    title: str
    description: str
    url: str
    template: str
    output_path: Path
    content_html: str = ""
    body_markdown: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    social_card_url: str = ""

    @property
    def absolute_url(self) -> str:
        return urljoin(f"{SITE_URL}/", self.url.lstrip("/"))


@dataclass(slots=True)
class Post:
    title: str
    description: str
    date: dt.date
    slug: str
    url: str
    output_path: Path
    content_html: str
    excerpt_html: str
    body_markdown: str
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    authors: list[str] = field(default_factory=list)
    author_profiles: list[dict[str, str]] = field(default_factory=list)
    read_time_minutes: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    source_path: Path | None = None
    social_card_url: str = ""

    @property
    def absolute_url(self) -> str:
        return urljoin(f"{SITE_URL}/", self.url.lstrip("/"))

    @property
    def github_view_url(self) -> str:
        if self.source_path is None:
            return ""
        rel = self.source_path.relative_to(ROOT_DIR).as_posix()
        return f"https://github.com/{GITHUB_REPO}/blob/main/{rel}"

    @property
    def github_edit_url(self) -> str:
        if self.source_path is None:
            return ""
        rel = self.source_path.relative_to(ROOT_DIR).as_posix()
        return f"https://github.com/{GITHUB_REPO}/edit/main/{rel}"

    @property
    def rss_date(self) -> str:
        return format_datetime(dt.datetime.combine(self.date, dt.time.min, tzinfo=dt.UTC))

    @property
    def read_time_label(self) -> str:
        minute_label = "minute" if self.read_time_minutes == 1 else "minutes"
        return f"{self.read_time_minutes} {minute_label} read"
