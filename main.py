"""Macros module - loads external YAML data for use in Markdown pages."""

import yaml
from pathlib import Path


def define_env(env):
    """Load data files and expose them as Jinja2 variables in Markdown."""
    data_dir = Path(env.project_dir) / "data"

    projects_path = data_dir / "projects.yml"
    if projects_path.exists():
        with open(projects_path) as f:
            env.variables["projects"] = yaml.safe_load(f)

    videos_path = data_dir / "videos.yml"
    if videos_path.exists():
        with open(videos_path) as f:
            env.variables["videos"] = yaml.safe_load(f)
