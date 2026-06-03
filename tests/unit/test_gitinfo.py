"""Unit tests for git-based last-modified date resolution."""

import datetime as dt
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from scripts.gitinfo import git_last_modified_date

pytestmark = pytest.mark.unit


def _completed(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["git"], returncode=0, stdout=stdout, stderr="")


def test_returns_date_from_git_output() -> None:
    with mock.patch("scripts.gitinfo.subprocess.run", return_value=_completed("2026-05-29\n")) as run:
        result = git_last_modified_date(Path("src/blog/posts/example.md"))
    assert result == dt.date(2026, 5, 29)
    run.assert_called_once()


def test_returns_none_when_output_empty() -> None:
    with mock.patch("scripts.gitinfo.subprocess.run", return_value=_completed("\n")):
        assert git_last_modified_date(Path("untracked.md")) is None


def test_returns_none_when_output_not_a_date() -> None:
    with mock.patch("scripts.gitinfo.subprocess.run", return_value=_completed("not-a-date")):
        assert git_last_modified_date(Path("weird.md")) is None


def test_returns_none_when_git_missing() -> None:
    with mock.patch("scripts.gitinfo.subprocess.run", side_effect=FileNotFoundError):
        assert git_last_modified_date(Path("any.md")) is None


def test_returns_none_when_git_fails() -> None:
    error = subprocess.CalledProcessError(returncode=128, cmd=["git"])
    with mock.patch("scripts.gitinfo.subprocess.run", side_effect=error):
        assert git_last_modified_date(Path("any.md")) is None
