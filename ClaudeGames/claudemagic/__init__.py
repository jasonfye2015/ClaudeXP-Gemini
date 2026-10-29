"""Claude and Magic: a first-person dungeon crawler ("blobber") in the line of Wizardry, Might and Magic, The Bard's
Tale and Eye of the Beholder. A party of four - Knight, Rogue, Cleric and Mage - moves as one through twenty floors
of stone, a square and a quarter-turn at a time (smoothly, in 3D), with an automap filling in as they go. Chests and
fallen monsters give weapons, armor, potions and gold; a ladder on every floor leads deeper. After floors 5, 10 and
15 there's a merchant's camp. The Lich King waits on floor 20. It's a roguelike: when the whole party falls, the run
is over and the next one starts afresh. The deepest runs go in the Hall of Fame.

The game is one HTML file in ClaudeGames/claudemagic/game/ (the newest 'Claude and Magic v*.html' there is the one
that runs), built from src/ by build.py: WebGL for the view, Web Audio for the sounds, nothing to ship. It plays in a
browser as it is; here it plays in a Qt WebEngine view with its own permanent browser profile in
ClaudeGames/Saves/claudemagic (shared by every era), loaded straight from the file so the page's address - and so
its localStorage saves - never changes. Sound follows the computer's mute. The old Python version's run.json and
hall_of_fame.json (the same Saves folder) are brought into the page the first time, then kept as *.imported.json."""
import json
import re
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from shiboken6 import isValid

from claudecore import host

TITLE = "Claude and Magic"
GAME_DIR = Path(__file__).resolve().parent / "game"
SAVES = host.saves("claudemagic")
PROFILE_DIR = SAVES
RUN_FILE = SAVES / "run.json"                   # (the old Python game's)
FAME_FILE = SAVES / "hall_of_fame.json"


def magic_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(QRectF(1, 1, 30, 30), QColor("#1A1410"))
    p.setBrush(QColor("#6A5A48"))
    p.setPen(Qt.NoPen)
    p.drawPolygon(QPolygonF([QPointF(1, 1), QPointF(10, 8), QPointF(10, 24), QPointF(1, 31)]))
    p.drawPolygon(QPolygonF([QPointF(31, 1), QPointF(22, 8), QPointF(22, 24), QPointF(31, 31)]))
    p.setBrush(QColor("#4A3E32"))
    p.drawRect(QRectF(10, 8, 12, 16))
    p.setPen(QPen(QColor("#E8E8F0"), 2))
    p.drawLine(QPointF(9, 26), QPointF(23, 6))                    # a sword
    p.setPen(QPen(QColor("#F0C040"), 2))
    p.drawLine(QPointF(10, 20), QPointF(16, 24))
    p.end()
    return QIcon(pm)


def game_file():
    """The newest Claude and Magic v*.html in game/ (None if it's missing)."""
    best = None
    for f in GAME_DIR.glob("Claude and Magic v*.html"):
        m = re.search(r"v(\d+(?:\.\d+)*)", f.stem)
        key = tuple(int(x) for x in m.group(1).split(".")) if m else (0,)
        if best is None or key > best[0]:
            best = (key, f)
    return best[1] if best else None


_profile = None


def profile():
    """One permanent browser profile for the game: its saves live in Saves/claudemagic/storage."""
    global _profile
    if _profile is None:
        from PySide6.QtWebEngineCore import QWebEngineProfile
        from PySide6.QtWidgets import QApplication
        _profile = QWebEngineProfile("claudemagic", QApplication.instance())
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        _profile.setPersistentStoragePath(str(PROFILE_DIR / "storage"))
        _profile.setCachePath(str(PROFILE_DIR / "cache"))
    return _profile


def old_saves():
    """What the Python version of the game left behind, if anything: {"run": ..., "fame": [...]}."""
    out = {}
    for key, path in (("run", RUN_FILE), ("fame", FAME_FILE)):
        try:
            out[key] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return out


def retire_old_saves():
    for path in (RUN_FILE, FAME_FILE):
        if path.exists():
            try:
                path.replace(path.with_name(path.stem + ".imported.json"))
            except OSError:
                pass


class MagicWindow(QWidget):
    def __init__(self, desktop):
        super().__init__()
        from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
        from PySide6.QtWebEngineWidgets import QWebEngineView
        self.desktop = desktop
        self.frame = None
        self.closing = False
        self.imported = None                 # what the page took from the old saves (None until it has been asked)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        path = game_file()
        if path is None:
            note = QLabel("Claude and Magic isn't built.\n\nRun  python build.py  in ClaudeGames\\claudemagic and try again.")
            note.setAlignment(Qt.AlignCenter)
            lay.addWidget(note)
            self.view = None
            return
        self.view = QWebEngineView(self)
        self.page = QWebEnginePage(profile(), self.view)
        s = self.page.settings()
        for attr, on in ((QWebEngineSettings.PlaybackRequiresUserGesture, False),
                         (QWebEngineSettings.LocalStorageEnabled, True),
                         (QWebEngineSettings.ShowScrollBars, False)):
            s.setAttribute(attr, on)
        self.page.setBackgroundColor(QColor("#18120C"))
        if hasattr(self.page, "permissionRequested"):                   # Qt 6.8+
            self.page.permissionRequested.connect(lambda permission: permission.deny())
        self.view.setPage(self.page)
        self.view.setContextMenuPolicy(Qt.NoContextMenu)
        lay.addWidget(self.view)
        self.view.loadFinished.connect(self._arrived)
        self.view.setUrl(QUrl.fromLocalFile(str(path)))
        self.version = re.search(r"v[\d.]+", path.stem).group(0) if re.search(r"v[\d.]+", path.stem) else ""
        self.mute_timer = QTimer(self, interval=500, timeout=self._sync_mute)
        self.mute_timer.start()
        self._sync_mute()

    def _arrived(self, ok):
        """The page is up: it learns the user's name (for the Hall of Fame), and takes the old game's saves once."""
        if not ok or self.closing:
            return
        name = host.user_name() or "Adventurer"
        self.page.runJavaScript(f"window.CM && (CM.playerName = {json.dumps(name)});")
        old = old_saves()
        if not old:
            self.imported = []
            return

        def took(result):
            try:
                self.imported = list(json.loads(result)) if isinstance(result, str) else []
            except (ValueError, TypeError):
                self.imported = []
            if self.imported:
                retire_old_saves()
        self.page.runJavaScript("(function(d){ return JSON.stringify(window.CM && CM.game ? CM.game.importOld(d) : []); })(%s)"
                                % json.dumps(old), took)

    def _sync_mute(self):
        if self.view is not None and self.page.isAudioMuted() != host.muted():
            self.page.setAudioMuted(host.muted())

    def showEvent(self, event):
        super().showEvent(event)
        if self.view is not None:
            QTimer.singleShot(0, self.view.setFocus)                    # keys go straight to the game

    def closeEvent(self, event):
        """Let the page unload (its saves are written as it goes) before the window goes."""
        if self.view is None or self.closing:
            event.accept()
            return
        event.ignore()
        self.closing = True
        self.mute_timer.stop()
        self.view.setUrl(QUrl("about:blank"))
        QTimer.singleShot(400, lambda: self.frame.request_close() if self.frame and isValid(self.frame) else None)


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = MagicWindow(desktop)
    win = host.window(desktop, TITLE, body, magic_icon(), (1000, 720))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    win.toggle_maximize()                                           # the dungeon likes room
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win) and win.content.view is not None:
        win.content.view.setUrl(QUrl("about:blank"))
