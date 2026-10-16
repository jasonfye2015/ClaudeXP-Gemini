"""Serves the ZIM books to Kiwix's web view from 127.0.0.1: http://127.0.0.1:<port>/<book>/<path>.

<book> is the file name without .zim. For new-style ZIMs the path is the content path ('Albert_Einstein',
'_assets_/...'); for old ones it keeps the namespace ('A/Albert_Einstein', 'I/x.png'), so the books' own relative
links work either way. Redirect entries become HTTP redirects.
"""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote, urlparse

from . import library
from .zim import ZimFile

_server = None
_lock = threading.Lock()
_open = {}


def book(book_id):
    """The open ZimFile for a book id, or None."""
    with _lock:
        z = _open.get(book_id)
        if z is None:
            path = library.folder() / f"{book_id}.zim"
            if not path.is_file():
                return None
            z = _open[book_id] = ZimFile(path)
        return z


def close_all():
    with _lock:
        for z in _open.values():
            try:
                z.close()
            except Exception:
                pass
        _open.clear()


def forget(book_id):
    with _lock:
        z = _open.pop(book_id, None)
    if z is not None:
        z.close()


def entry_path(z, entry):
    """How an entry is addressed under /<book>/."""
    return entry.url if z.new_namespaces and entry.namespace == "C" else entry.path


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parts = urlparse(self.path)
        book_id, _, rest = parts.path.lstrip("/").partition("/")
        book_id, rest = unquote(book_id), unquote(rest)
        z = book(book_id)
        if z is None:
            return self._send(404, b"<h1>Book not found</h1>", "text/html")
        try:
            if not rest:
                main = z.resolve(z.main_entry())
                if main is None:
                    return self._send(404, b"<h1>This book has no main page</h1>", "text/html")
                return self._redirect(f"/{quote(book_id)}/{quote(entry_path(z, main))}")
            e = z.get(rest)
            if e is None:
                return self._send(404, f"<h1>Not found</h1><p>{rest} isn't in this book.</p>".encode(), "text/html")
            if e.is_redirect:
                target = z.resolve(e)
                return self._redirect(f"/{quote(book_id)}/{quote(entry_path(z, target))}")
            data = z.content(e) or b""
            self._send(200, data, e.mime or "application/octet-stream")
        except Exception as ex:                        # a damaged entry shouldn't stop the server
            self._send(500, f"<h1>Error</h1><p>{ex}</p>".encode(), "text/html")

    def _redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send(self, status, body, ctype):
        try:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "max-age=3600")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionError, OSError):
            pass


def port():
    global _server
    with _lock:
        if _server is None:
            _server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
            _server.daemon_threads = True
            threading.Thread(target=_server.serve_forever, name="kiwix", daemon=True).start()
        return _server.server_address[1]


def url_for(book_id, path=""):
    return f"http://127.0.0.1:{port()}/{quote(book_id)}/{quote(path)}"


def is_local(url):
    p = urlparse(url)
    return p.hostname == "127.0.0.1" and _server is not None and p.port == _server.server_address[1]
