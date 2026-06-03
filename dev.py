"""Development server with live reload.

Watches src/, templates/, assets/, and data/ for changes, rebuilds the site,
and triggers a browser refresh via Server-Sent Events.

Usage:
    uv run dev.py [--port 8000] [--no-minify] [--no-optimize]
"""

import argparse
import http.server
import queue
import socketserver
import threading
from pathlib import Path
from typing import Any

import watchfiles  # type: ignore[import-not-found]

import main as site
from scripts.constants import ASSETS_DIR, DATA_DIR, SITE_DIR, SRC_DIR, TEMPLATES_DIR

WATCH_EXTENSIONS = frozenset({".md", ".html", ".css", ".js", ".yml", ".yaml", ".json", ".txt", ".xml"})
WATCH_DIRS = [SRC_DIR, TEMPLATES_DIR, ASSETS_DIR, DATA_DIR]

_subscribers: list[queue.Queue[str]] = []
_lock = threading.Lock()

_LIVERELOAD_SCRIPT = b"""<script>
(function(){
  function connect(){
    var es = new EventSource("/__livereload__");
    es.onmessage = function() { window.location.reload(); };
    es.onerror = function() { es.close(); setTimeout(connect, 1000); };
  }
  connect();
})();
</script>"""


def _notify() -> None:
    with _lock:
        for q in list(_subscribers):
            try:
                q.put_nowait("reload")
            except queue.Full:
                pass


class _ThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class DevHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/__livereload__":
            self._sse()
            return
        path = self.translate_path(self.path)
        if path.endswith(".html") and Path(path).is_file():
            self._html(path)
            return
        super().do_GET()

    def _html(self, path: str) -> None:
        content = Path(path).read_bytes()
        if b"</body>" in content:
            content = content.replace(b"</body>", _LIVERELOAD_SCRIPT + b"</body>", 1)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _sse(self) -> None:
        q: queue.Queue[str] = queue.Queue(maxsize=10)
        with _lock:
            _subscribers.append(q)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=25)
                    self.wfile.write(f"data: {msg}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with _lock:
                try:
                    _subscribers.remove(q)
                except ValueError:
                    pass

    def log_message(self, fmt: str, *args: Any) -> None:
        if args and "/__livereload__" in str(args[0]):
            return
        super().log_message(fmt, *args)


def _watch(minify: bool, optimize: bool) -> None:

    def _filter(_change: Any, path: str) -> bool:
        return Path(path).suffix in WATCH_EXTENSIONS

    for _changes in watchfiles.watch(*WATCH_DIRS, watch_filter=_filter):
        print("\nChange detected - rebuilding...")
        try:
            site.build_site(minify=minify, optimize=optimize)
            print("Rebuild done.")
        except Exception as exc:
            print(f"Build error: {exc}")
        _notify()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-minify", action="store_true")
    parser.add_argument("--no-optimize", action="store_true")
    args = parser.parse_args()

    minify = not args.no_minify
    optimize = not args.no_optimize

    print("Building site...")
    site.build_site(minify=minify, optimize=optimize)

    threading.Thread(target=_watch, args=(minify, optimize), daemon=True).start()

    for port in range(args.port, args.port + 10):
        try:
            with _ThreadingServer(("127.0.0.1", port), DevHandler) as httpd:
                print(f"Serving at http://127.0.0.1:{port}  (live reload enabled)")
                print(f"Watching: {', '.join(str(d.relative_to(d.parent.parent)) for d in WATCH_DIRS)}")
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\nStopping.")
            break
        except OSError:
            continue


if __name__ == "__main__":
    main()
