"""Shared pytest fixtures for the static-site test suite."""

import datetime as dt
import functools
import http.server
import socketserver
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

import main


@pytest.fixture
def make_markdown(tmp_path: Path):
    """Factory that writes a markdown file (optionally with front matter)."""

    def _make(filename: str, body: str, front_matter: str | None = None) -> Path:
        if front_matter is not None:
            content = f"---\n{front_matter}\n---\n{body}"
        else:
            content = body
        path = tmp_path / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    return _make


def _make_post(
    *,
    title: str = "Sample",
    slug: str = "sample",
    date: dt.date | None = None,
    updated: dt.date | None = None,
    tags: list[str] | None = None,
    categories: list[str] | None = None,
    authors: list[str] | None = None,
    description: str = "A sample post.",
) -> main.Post:
    """Build a lightweight ``Post`` for unit tests without touching disk."""
    return main.Post(
        title=title,
        description=description,
        date=date or dt.date(2024, 1, 1),
        slug=slug,
        url=f"/blog/{slug}/",
        output_path=Path(f"site/blog/{slug}/index.html"),
        content_html=f"<p>{title}</p>",
        excerpt_html=f"<p>{title}</p>",
        body_markdown=title,
        categories=categories or [],
        tags=tags or [],
        authors=authors or [],
        updated=updated,
    )


@pytest.fixture
def post_factory():
    """Expose the post builder to tests."""
    return _make_post


@pytest.fixture(scope="session")
def built_site(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Build the real site once into a temp dir and yield the output path.

    The module-level ``SITE_DIR`` is redirected so the repository's ``site/``
    directory is never touched by the test run.
    """
    output_dir = tmp_path_factory.mktemp("site")
    original = main.SITE_DIR
    main.SITE_DIR = output_dir
    try:
        main.build_site()
        yield output_dir
    finally:
        main.SITE_DIR = original


@pytest.fixture(scope="session")
def live_server(built_site: Path) -> Iterator[str]:
    """Serve the built site on a background thread and yield its base URL."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(built_site))

    class QuietServer(socketserver.TCPServer):
        allow_reuse_address = True

        def handle_error(self, request, client_address):  # noqa: D401, ANN001
            """Silence noisy disconnect tracebacks during teardown."""

    httpd = QuietServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
