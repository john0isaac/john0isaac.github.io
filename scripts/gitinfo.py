"""Helpers for reading git metadata (e.g. last-modified dates) for source files."""

import datetime as dt
import subprocess
from pathlib import Path

from .constants import ROOT_DIR


def git_last_modified_date(path: Path) -> dt.date | None:
    """Return the date of the last git commit that touched ``path``.

    Returns ``None`` when git is unavailable, the file is untracked, or the
    command fails for any reason (e.g. building outside a git checkout).
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    stamp = result.stdout.strip()
    if not stamp:
        return None
    try:
        return dt.date.fromisoformat(stamp)
    except ValueError:
        return None
