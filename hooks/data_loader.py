"""MkDocs hook - injects external YAML data into page.meta for templates."""

import yaml
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def on_page_context(context, page, config, nav):
    """Load data from YAML files into page.meta so templates can access it."""
    if page.file.src_path == "projects.md":
        with open(DATA_DIR / "projects.yml") as f:
            page.meta["projects"] = yaml.safe_load(f)
    elif page.file.src_path == "talks.md":
        videos_path = DATA_DIR / "videos.yml"
        if videos_path.exists():
            with open(videos_path) as f:
                page.meta["videos"] = yaml.safe_load(f)
    return context
