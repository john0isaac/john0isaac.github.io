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
AUTHOR_JOB_TITLE = "Senior AI Software Engineer"
AUTHOR_BIO = (
    "John Aziz is a Senior AI Software Engineer and former Microsoft MVP building "
    "production-grade AI systems, open-source projects, and cloud-native architectures on Azure."
)
AUTHOR_IMAGE = "/images/John-Headshot.jpg"
TWITTER_HANDLE = "@john00isaac"
SAME_AS_LINKS = [
    "https://github.com/john0isaac",
    "https://linkedin.com/in/john0isaac",
    "https://youtube.com/@john0isaac",
    "https://x.com/john00isaac",
]
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
