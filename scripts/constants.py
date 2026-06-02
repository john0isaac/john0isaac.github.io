import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
SITE_DIR = ROOT_DIR / "site"
TEMPLATES_DIR = ROOT_DIR / "templates"
ASSETS_DIR = ROOT_DIR / "assets"
VENDOR_DIR = ROOT_DIR / "vendor"

SITE_NAME = "John Aziz"
SITE_URL = "https://johnaziz.org"
GITHUB_REPO = "john0isaac/john0isaac.github.io"
AUTHOR = "John Aziz"
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
DATE_PREFIX_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)$")
EXCERPT_MARKER = "<!-- more -->"
MARKDOWN_EXTENSIONS = [
    "admonition",
    "attr_list",
    "fenced_code",
    "footnotes",
    "md_in_html",
    "tables",
    "toc",
]
BLOG_POSTS_PER_PAGE = 10
