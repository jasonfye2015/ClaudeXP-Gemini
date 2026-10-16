"""Macromedia Flash Player 5, the standalone player (FlashPla.exe): opens .swf animations and plays them with
Ruffle (assets/engines/ruffle, a Flash Player emulator written in Rust and compiled to WebAssembly) inside a Qt
WebEngine view. A tiny web server on 127.0.0.1 hands the page Ruffle and the one movie it was asked for; nothing
else on the disk is reachable, and the movie can't reach the Internet.

The window sizes itself to the movie's stage, like the real player. View has 100% / Show All / Zoom / Full Screen,
Control has Play, Rewind and Mute, and Quality picks Ruffle's render quality."""
import hashlib
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote

from PySide6.QtCore import QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QIcon, QKeySequence, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QMenuBar, QStackedWidget, QVBoxLayout, QWidget
from shiboken6 import isValid

from .. import sound
from ..paths import ROOT
from .. import theme
from ..wm import XPWindow
from .notepad import MENU_STYLE

RUFFLE = ROOT / "assets" / "engines" / "ruffle"
TITLE = "Macromedia Flash Player 5"
MENU_H = 20


def flash_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#7A0000"), 1))
    p.setBrush(QColor("#D8161C"))
    p.drawRoundedRect(QRectF(2.5, 2.5, 27, 27), 6, 6)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 60))
    p.drawRoundedRect(QRectF(4, 4, 24, 11), 5, 5)
    f = QPainterPath()                                       # the swooping white 'f'
    f.moveTo(22.5, 7.5)
    f.cubicTo(17, 6.5, 14.5, 9, 13.8, 14)
    f.lineTo(12.6, 21)
    f.cubicTo(12, 24.5, 10.5, 25.5, 8, 25)
    p.setPen(QPen(QColor("white"), 3.2, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawPath(f)
    p.drawLine(10, 15, 19, 15)
    p.end()
    return QIcon(pm)


# ---- the local server ---------------------------------------------------------------------------------------------

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; height: 100%; overflow: hidden; background: #FFFFFF; }
#stage, ruffle-player { width: 100%; height: 100%; display: block; }
</style><script>
window.RufflePlayer = window.RufflePlayer || {};
window.RufflePlayer.config = { autoplay: "on", unmuteOverlay: "hidden", splashScreen: false, letterbox: "on",
  openUrlMode: "deny", allowNetworking: "internal", showSwfDownload: false, warnOnUnsupportedContent: false,
  contextMenu: "rightClickOnly", logLevel: "error", backgroundColor: null, publicPath: "/ruffle/",
  polyfills: false, autoplayUnmute: true };
</script><script src="/ruffle/ruffle.js"></script></head><body><div id="stage"></div><script>
const fp = { player: null, url: null, opts: {} };
function api() { const p = fp.player; return p ? (p.ruffle ? p.ruffle() : p) : null; }
function report(kind, extra) { console.log("FP:" + JSON.stringify(Object.assign({ kind: kind }, extra || {}))); }
fp.load = function (url, opts) {
  fp.url = url; fp.opts = opts || {};
  const stage = document.getElementById("stage");
  stage.innerHTML = "";
  const ruffle = window.RufflePlayer.newest();
  const p = ruffle.createPlayer();
  fp.player = p;
  stage.appendChild(p);
  p.addEventListener("loadedmetadata", function () {
    const m = api().metadata || p.metadata || {};
    report("meta", { width: m.width, height: m.height, frames: m.numFrames, fps: m.frameRate, version: m.swfVersion,
                     background: m.backgroundColor });
  });
  p.addEventListener("loadeddata", function () { report("loaded"); });
  const cfg = Object.assign({ url: url }, fp.opts);
  try { api().load(cfg).catch(function (e) { report("error", { message: String(e) }); }); }
  catch (e) { report("error", { message: String(e) }); }
  fp.setVolume(fp.opts.volume === undefined ? 1 : fp.opts.volume);
};
fp.toggle = function () {
  const a = api(); if (!a) return false;
  if (a.isPlaying) { (a.suspend || a.pause).call(a); } else { (a.resume || a.play).call(a); }
  return a.isPlaying;
};
fp.pause = function () { const a = api(); if (a && a.isPlaying) (a.suspend || a.pause).call(a); };
fp.resume = function () { const a = api(); if (a && !a.isPlaying) (a.resume || a.play).call(a); };
fp.playing = function () { const a = api(); return !!(a && a.isPlaying); };
fp.rewind = function () { if (fp.url) fp.load(fp.url, fp.opts); };
fp.setVolume = function (v) { fp.opts.volume = v; const a = api(); if (a) { try { a.volume = v; } catch (e) {} } };
fp.clear = function () { document.getElementById("stage").innerHTML = ""; fp.player = null; fp.url = null; };
</script></body></html>"""


class _Server:
    """Serves Ruffle, the player page, and only the movies the player has been handed (by token)."""

    def __init__(self):
        self.movies = {}
        self.ruffle_files = {p.name for p in RUFFLE.iterdir() if p.is_file()} if RUFFLE.is_dir() else set()
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                parts = unquote(self.path.split("?", 1)[0]).strip("/").split("/")
                if parts == ["player.html"]:
                    return self._send(PAGE.encode("utf-8"), "text/html; charset=utf-8")
                if len(parts) == 2 and parts[0] == "ruffle" and parts[1] in server.ruffle_files:
                    return self._file(RUFFLE / parts[1])
                if len(parts) >= 2 and parts[0] == "swf" and parts[1] in server.movies:
                    return self._file(server.movies[parts[1]])
                self.send_error(404)

            def _file(self, path):
                try:
                    data = Path(path).read_bytes()
                except OSError:
                    return self.send_error(404)
                ext = Path(path).suffix.lower()
                kind = {".wasm": "application/wasm", ".js": "text/javascript", ".swf": "application/x-shockwave-flash"
                        }.get(ext) or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                self._send(data, kind)

            def _send(self, data, kind):
                self.send_response(200)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    self.wfile.write(data)
                except OSError:
                    pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True, name="flash-server").start()

    def base(self):
        return f"http://127.0.0.1:{self.port}"

    def movie_url(self, path):
        path = Path(path)
        token = hashlib.sha1(str(path).encode("utf-8", "replace")).hexdigest()[:20]
        self.movies[token] = path
        return f"{self.base()}/swf/{token}/{quote(path.name)}"


_server = None


def server():
    global _server
    if _server is None:
        _server = _Server()
    return _server


# ---- the window ---------------------------------------------------------------------------------------------------

def _page_class():
    from PySide6.QtWebEngineCore import QWebEnginePage

    class Page(QWebEnginePage):
        def __init__(self, profile, owner):
            super().__init__(profile, owner)
            self.owner = owner

        def javaScriptConsoleMessage(self, level, message, line, source):
            if message.startswith("FP:"):
                try:
                    self.owner.page_event(json.loads(message[3:]))
                except ValueError:
                    pass

        def acceptNavigationRequest(self, url, kind, main_frame):       # getURL() and links go nowhere
            return url.host() == "127.0.0.1"

        def createWindow(self, kind):
            return None
    return Page


class FlashPlayer(QWidget):
    def __init__(self, desktop):
        super().__init__()
        from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
        from PySide6.QtWebEngineWidgets import QWebEngineView
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.meta = {}
        self.muted = False
        self.quality = "high"
        self.zoom = 1.0
        self.ready = False
        self.pending = None
        self.setObjectName("flash")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(MENU_STYLE + "QWidget#flash { background: white; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.menu = QMenuBar()
        self.menu.setFixedHeight(MENU_H)
        self.menu.triggered.connect(lambda _a: sound.play("menu"))
        lay.addWidget(self.menu)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.blank = QLabel()
        self.blank.setStyleSheet("background: white;")
        self.stack.addWidget(self.blank)
        self.profile = QWebEngineProfile(self)                # off the record: nothing is kept on disk
        self.view = QWebEngineView(self)
        self.page = _page_class()(self.profile, self)
        s = self.page.settings()
        s.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        s.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        s.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        self.page.setBackgroundColor(QColor("white"))
        self.view.setPage(self.page)
        self.view.setContextMenuPolicy(Qt.NoContextMenu)
        self.page.loadFinished.connect(self._page_ready)
        self.stack.addWidget(self.view)
        self._menus()
        self.view.setUrl(QUrl(server().base() + "/player.html"))

    # ---- menus -------------------------------------------------------------------------------------------------
    def _menus(self):
        m = self.menu
        f = m.addMenu("&File")
        f.addAction("&Open...", self.open_dialog, QKeySequence("Ctrl+O"))
        f.addAction("&Close", self.close_movie, QKeySequence("Ctrl+W"))
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close() if self.frame else None, QKeySequence("Ctrl+Q"))
        v = m.addMenu("&View")
        v.addAction("Zoom &In", lambda: self.set_zoom(self.zoom * 1.25), QKeySequence("Ctrl+="))
        v.addAction("Zoom &Out", lambda: self.set_zoom(self.zoom / 1.25), QKeySequence("Ctrl+-"))
        v.addSeparator()
        v.addAction("&100%", self.actual_size, QKeySequence("Ctrl+1"))
        v.addAction("&Show All", self.show_all, QKeySequence("Ctrl+3"))
        quality = v.addMenu("&Quality")
        group = QActionGroup(self)
        for label, value in (("&Low", "low"), ("&Medium", "medium"), ("&High", "high")):
            act = QAction(label, self, checkable=True, checked=value == self.quality)
            act.triggered.connect(lambda _c=False, value=value: self.set_quality(value))
            group.addAction(act)
            quality.addAction(act)
        v.addSeparator()
        v.addAction("&Full Screen", self.full_screen, QKeySequence("Ctrl+F"))
        c = m.addMenu("&Control")
        self.play_act = c.addAction("&Play", self.toggle_play, QKeySequence("Return"))
        c.addAction("&Rewind", self.rewind, QKeySequence("Ctrl+R"))
        c.addSeparator()
        self.mute_act = QAction("&Mute Sounds", self, checkable=True, checked=self.muted)
        self.mute_act.toggled.connect(self._set_mute)
        c.addAction(self.mute_act)
        m.addMenu("&Help").addAction(f"&About {TITLE}...", self.about)

    # ---- the page ----------------------------------------------------------------------------------------------
    def _page_ready(self, ok):
        self.ready = ok
        if ok and self.pending is not None:
            path, self.pending = self.pending, None
            self.open(path)

    def page_event(self, ev):
        kind = ev.get("kind")
        if kind == "meta":
            self.meta = ev
            self._fit_to_movie()
        elif kind == "error":
            from ..explorer.dialogs import msgbox
            msgbox(self.desktop, TITLE, f"This movie couldn't be played:\n\n{self.path.name if self.path else ''}",
                   "error")
        self._update_play_label()

    def _options(self):
        return {"autoplay": "on", "quality": self.quality, "scale": "showAll", "letterbox": "on",
                "volume": 0 if (self.muted or sound.is_muted()) else 1}

    def open(self, path):
        path = Path(path)
        self.path = path
        self.meta = {}
        if not self.ready:
            self.pending = path
            self._titles()
            return
        url = server().movie_url(path)
        opts = dict(self._options(), url=url)
        self.page.runJavaScript(f"fp.load({json.dumps(url)}, {json.dumps(opts)});")
        self.stack.setCurrentWidget(self.view)
        self._titles()

    def _titles(self):
        if self.frame is not None:
            self.frame.set_title(f"{self.path.name} - {TITLE}" if self.path else TITLE)

    def close_movie(self):
        self.path = None
        self.meta = {}
        self.page.runJavaScript("fp.clear();")
        self.stack.setCurrentWidget(self.blank)
        self._titles()

    def _js_opts(self):
        """Re-load the movie with new options (Ruffle reads scale/quality at load time)."""
        if self.path is not None:
            self.open(self.path)

    def toggle_play(self):
        self.page.runJavaScript("fp.toggle();", 0, lambda playing: self._update_play_label(playing))

    def _update_play_label(self, playing=None):
        if playing is None:
            self.page.runJavaScript("fp.playing();", 0, lambda on: self._update_play_label(bool(on)))
            return
        self.play_act.setText("&Stop" if playing else "&Play")

    def rewind(self):
        self.page.runJavaScript("fp.rewind();")

    def _set_mute(self, on):
        self.muted = on
        self.page.runJavaScript(f"fp.setVolume({0 if (on or sound.is_muted()) else 1});")

    def set_quality(self, value):
        self.quality = value
        self._js_opts()

    def actual_size(self):
        self.zoom = 1.0
        self._fit_to_movie()

    def show_all(self):
        """Fit the whole stage into the window as it is (the movie always scales with the window)."""
        if self.frame is not None and not self.frame.maximized:
            self._fit_to_movie()

    def set_zoom(self, z):
        self.zoom = max(0.25, min(4.0, z))
        self._fit_to_movie()

    def full_screen(self):
        if self.frame is not None:
            self.frame.toggle_maximize()

    def _fit_to_movie(self):
        """Size the window around the movie's stage (in twips-converted pixels), like FlashPla.exe does."""
        if self.frame is None or self.frame.maximized:
            return
        w, h = self.meta.get("width") or 0, self.meta.get("height") or 0
        if not w or not h:
            return
        area = self.desktop.work_area()
        chrome_w, chrome_h = 2 * theme.border(), theme.title_h() + theme.border() + MENU_H
        zoom = min(self.zoom, (area.width() - chrome_w) / w, (area.height() - chrome_h) / h)
        self.frame.resize(max(240, int(w * zoom) + chrome_w), max(160, int(h * zoom) + chrome_h))
        g = self.frame.geometry()
        if not area.contains(g):
            self.frame.move(max(area.left(), min(g.left(), area.right() - g.width())),
                            max(area.top(), min(g.top(), area.bottom() - g.height())))

    def open_dialog(self):
        from .opendialog import open_dialog
        open_dialog(self.desktop, "Open", {".swf"}, self.open, flash_icon(),
                    self.path.parent if self.path else None)

    def about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, f"About {TITLE}", f"{TITLE}\nVersion 5,0,30,0\n\nCopyright (c) 1996-2001 Macromedia, "
               "Inc.\n\nPlayback by Ruffle, the Flash Player emulator\n(MIT / Apache-2.0, ruffle.rs).", "info")

    def hideEvent(self, event):
        self.page.runJavaScript("fp.pause();")
        super().hideEvent(event)

    def showEvent(self, event):
        if self.path is not None:
            self.page.runJavaScript("fp.resume();")
        super().showEvent(event)

    def closeEvent(self, event):
        self.page.runJavaScript("fp.clear();")
        self.view.setUrl(QUrl("about:blank"))
        event.accept()


_open = {}


def open_flash(desktop, path=None):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = FlashPlayer(desktop)
        win = XPWindow(desktop, TITLE, body, flash_icon(), (560, 440))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    if path is not None:
        win.content.open(path)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.page.runJavaScript("fp.clear();")
