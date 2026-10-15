"""The furry web: real websites from the user's archive (E:\\Furry Media Archive...\\Website Rips), served offline at
their own addresses in Netscape.

Each site is a Site: the HTML rips (YiffStar, SexyFur, Club Stripes, Jay Naylor's sketch blogs) are served as they
were saved; the image-only rips (FurAffinity, Housepets!, Hardblush) get their pages built here from the pictures.
A tiny web server on 127.0.0.1 hands everything to Netscape's web engine; nothing ever goes to the real Internet.
URLs: Netscape shows http://www.furaffinity.net/view/12/ and the engine loads
http://127.0.0.1:<port>/www.furaffinity.net/view/12/ (see local_url() / logical_url())."""
import html
import mimetypes
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

RIPS_FOLDER = "Website Rips"


class Response:
    def __init__(self, body, ctype="text/html; charset=utf-8", status=200, headers=None):
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        self.ctype, self.status, self.headers = ctype, status, headers or {}


def redirect(location):
    return Response(b"", status=302, headers={"Location": location})


class Site:
    """One website. host: its canonical host ('www.furaffinity.net'); aliases: other names that reach it;
    folder: its folder under Website Rips."""
    host = ""
    aliases = ()
    title = ""
    blurb = ""                  # one line for the Netcenter home page
    folder = ""

    def root(self):
        base = rips_root()
        if base is None:
            return None
        want = self.folder.lower()
        return next((d for d in base.iterdir() if d.is_dir() and d.name.lower() == want), None)

    def installed(self):
        return self.root() is not None

    def handle(self, path, query):
        """path: '/view/12/' (decoded); query: the raw query string. -> Response or None for 'not found'."""
        return None


def file_response(path):
    path = Path(path)
    if not path.is_file():
        return None
    ctype = mimetypes.guess_type(path.name)[0] or ""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if ctype.startswith("text/html") or not ctype.startswith(("image/", "audio/", "video/", "text/css",
                                                              "application/x-shockwave-flash", "application/zip")):
        # saved .php/.asp pages, 'page.php@id=3' and the like are web pages too
        if ctype.startswith("text/html") or data[:2048].lstrip()[:1] == b"<" or b"<html" in data[:4096].lower():
            ctype = "text/html"       # the rips declare their own encodings (or none: the browser guesses)
        elif not ctype:
            ctype = "application/octet-stream"
    return Response(data, ctype)


# ---- the archive ------------------------------------------------------------------------------------------------

def rips_root():
    """E:\\<Furry Media Archive...>\\Website Rips, or None if the archive isn't installed."""
    from ... import archive_folder
    try:
        media = archive_folder("mediaarchive")
    except OSError:
        return None
    if media is None:
        return None
    return next((d for d in media.iterdir() if d.is_dir() and d.name.lower() == RIPS_FOLDER.lower()), None)


_sites = None


def sites():
    global _sites
    if _sites is None:
        from . import comics, furaffinity, rips
        _sites = [furaffinity.FurAffinity(), comics.HousePets(), comics.Hardblush(), comics.JayNaylor(),
                  rips.YiffStar(), rips.SexyFur(), rips.ClubStripes()]
    return _sites


def _bare(host):
    host = (host or "").lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def site_for(url_or_host):
    """The Site an address belongs to (installed or not), or None for the rest of the web."""
    host = urlparse(url_or_host).netloc if "://" in url_or_host else url_or_host
    bare = _bare(host)
    for s in sites():
        if bare == _bare(s.host) or bare in (_bare(a) for a in s.aliases):
            return s
    return None


# ---- pages every site can show ---------------------------------------------------------------------------------

def not_found_page(url, missing_site=None):
    """The 2001 Apache '404 Not Found', or, for a site whose rip isn't installed, the host not answering."""
    host = urlparse(url).netloc or url
    path = urlparse(url).path or "/"
    if missing_site is not None:
        return f"""<html><head><title>404 Not Found</title></head><body bgcolor="#FFFFFF">
<h1>Not Found</h1>
<p>The requested URL {html.escape(path)} was not found on this server.</p>
<p>The site <b>{html.escape(host)}</b> isn't on this computer yet: its pages come from the
<b>Website Rips</b> folder of the Furry Media Archive on drive E:. Copy the archive to E: and try again.</p>
<hr><address>Apache/1.3.20 Server at {html.escape(host)} Port 80</address></body></html>"""
    return f"""<html><head><title>404 Not Found</title></head><body bgcolor="#FFFFFF">
<h1>Not Found</h1>
<p>The requested URL {html.escape(path)} was not found on this server.</p>
<p>Additionally, a 404 Not Found error was encountered while trying to use an ErrorDocument to handle the
request.</p>
<hr><address>Apache/1.3.20 Server at {html.escape(host)} Port 80</address></body></html>"""


# ---- the local web server ----------------------------------------------------------------------------------------

_server = None
_lock = threading.Lock()


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parts = urlparse(self.path)
        segments = parts.path.lstrip("/").split("/", 1)
        site = site_for(segments[0]) if segments and segments[0] else None
        if site is None:
            # an absolute-path link ('/images/x.gif') lost its host: take it from the page it came from
            ref = urlparse(self.headers.get("Referer", ""))
            ref_host = ref.path.lstrip("/").split("/", 1)[0]
            if site_for(ref_host) is not None:
                self._send(redirect(f"/{ref_host}{self.path}"))
                return
            self._send(Response(not_found_page("http://" + self.path.lstrip("/")), status=404))
            return
        path = "/" + (unquote(segments[1], errors="replace") if len(segments) > 1 else "")
        try:
            resp = site.handle(path, parts.query) if site.installed() else None
            if isinstance(resp, str):                           # a built page
                resp = Response(resp)
        except Exception as e:                                  # a broken page shouldn't take the server down
            resp = Response(f"<html><body><h1>500 Internal Server Error</h1><p>{html.escape(str(e))}</p></body>"
                            "</html>", status=500)
        if resp is None:
            url = f"http://{site.host}{path}"
            resp = Response(not_found_page(url, None if site.installed() else site), status=404)
        if resp.ctype.startswith("text/html"):
            # '/view/12/' on the site means '/www.furaffinity.net/view/12/' here
            resp.body = re.sub(rb"""((?:href|src|action|background)\s*=\s*["']?)/(?!/)""",
                               rb"\1/" + site.host.encode() + b"/", resp.body, flags=re.I)
        if resp.headers.get("Location", "").startswith("/"):
            resp.headers["Location"] = f"/{site.host}{resp.headers['Location']}"
        self._send(resp)

    def _send(self, resp):
        try:
            self.send_response(resp.status)
            self.send_header("Content-Type", resp.ctype)
            self.send_header("Content-Length", str(len(resp.body)))
            self.send_header("Cache-Control", "no-store" if resp.ctype.startswith("text/html") else "max-age=3600")
            for k, v in resp.headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.body)
        except (ConnectionError, OSError):
            pass


def port():
    """Start the server the first time it's needed; -> its port."""
    global _server
    with _lock:
        if _server is None:
            _server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
            _server.daemon_threads = True
            threading.Thread(target=_server.serve_forever, name="furry-web", daemon=True).start()
        return _server.server_address[1]


def local_url(url):
    """http://www.furaffinity.net/view/12/?x -> http://127.0.0.1:<port>/www.furaffinity.net/view/12/?x"""
    p = urlparse(url)
    site = site_for(url)
    host = site.host if site else p.netloc
    path = quote(unquote(p.path or "/"), safe="/:@!$&'()*+,;=~-._")
    return f"http://127.0.0.1:{port()}/{host}{path}" + (f"?{p.query}" if p.query else "")


def logical_url(url):
    """The other way round; anything that isn't ours comes back unchanged."""
    p = urlparse(url)
    if p.hostname != "127.0.0.1" or _server is None or p.port != _server.server_address[1]:
        return url
    host, _, rest = p.path.lstrip("/").partition("/")
    return f"http://{host}/{unquote(rest, errors='replace')}" + (f"?{p.query}" if p.query else "")


def is_local(url):
    p = urlparse(url)
    return p.hostname == "127.0.0.1" and _server is not None and p.port == _server.server_address[1]
