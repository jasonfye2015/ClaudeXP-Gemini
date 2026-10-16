"""ClaudeRPG: the standalone browser roguelike, in its ClaudeXP 'release state'.

The game is one HTML file in ClaudeGames/clauderpg/game/ (the newest 'ClaudeRPG v*.html' there is the one that
runs - drop a newer version in to update it). It plays in a Qt WebEngine view with its own permanent browser profile
in ClaudeGames/Saves/clauderpg (shared by every era), loaded straight from the file so the page's address (and so its localStorage saves) never
changes. Sound follows the computer's mute, mouse capture (the first-person view) is allowed, and the window opens
maximized. Saves made in a normal browser stay there; the game's own backup text can carry them across."""
import re

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from shiboken6 import isValid

from pathlib import Path

from claudecore import host

GAME_DIR = Path(__file__).resolve().parent / "game"
PROFILE_DIR = host.saves("clauderpg")
TITLE = "ClaudeRPG"


def rpg_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    shield = QPainterPath()                                         # a heater shield
    shield.moveTo(6, 6)
    shield.lineTo(26, 6)
    shield.lineTo(26, 16)
    shield.cubicTo(26, 23, 20, 27, 16, 30)
    shield.cubicTo(12, 27, 6, 23, 6, 16)
    shield.closeSubpath()
    g = QLinearGradient(6, 6, 26, 30)
    g.setColorAt(0, QColor("#3A6AD8"))
    g.setColorAt(1, QColor("#15306E"))
    p.setPen(QPen(QColor("#D8B040"), 2))
    p.setBrush(g)
    p.drawPath(shield)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#E8C858"))
    p.drawRect(QRectF(15, 9, 2, 17))                               # the shield's gold cross
    p.drawRect(QRectF(9, 14, 14, 2))
    blade = QPolygonF([QPointF(26.5, 1.5), QPointF(29.5, 2.5), QPointF(13, 19), QPointF(11, 17)])
    p.setPen(QPen(QColor("#505868"), 0.8))
    p.setBrush(QColor("#E8ECF4"))
    p.drawPolygon(blade)                                            # a sword across it
    p.setPen(QPen(QColor("#8A5A20"), 2.6, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(8.5, 18.5), QPointF(13.5, 23.5))             # crossguard
    p.setPen(QPen(QColor("#5A3A18"), 2.4, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(11, 21), QPointF(6.5, 25.5))                # grip
    p.setBrush(QColor("#E8C858"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(5.8, 26.2), 1.8, 1.8)                     # pommel
    p.end()
    return QIcon(pm)


def game_file():
    """The newest ClaudeRPG v*.html in Program Files/ClaudeRPG (None if it's missing)."""
    best = None
    for f in GAME_DIR.glob("ClaudeRPG v*.html"):
        m = re.search(r"v(\d+(?:\.\d+)*)", f.stem)
        key = tuple(int(x) for x in m.group(1).split(".")) if m else (0,)
        if best is None or key > best[0]:
            best = (key, f)
    return best[1] if best else None


_profile = None


def profile():
    """One permanent browser profile for the game (its saves live in data/clauderpg)."""
    global _profile
    if _profile is None:
        from PySide6.QtWebEngineCore import QWebEngineProfile
        from PySide6.QtWidgets import QApplication
        _profile = QWebEngineProfile("clauderpg", QApplication.instance())
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        _profile.setPersistentStoragePath(str(PROFILE_DIR / "storage"))
        _profile.setCachePath(str(PROFILE_DIR / "cache"))
    return _profile


class RPGWindow(QWidget):
    def __init__(self, desktop):
        super().__init__()
        from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
        from PySide6.QtWebEngineWidgets import QWebEngineView
        self.desktop = desktop
        self.frame = None
        self.closing = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        path = game_file()
        if path is None:
            note = QLabel("ClaudeRPG isn't installed.\n\nPut 'ClaudeRPG v<version>.html' in "
                          "Program Files\\ClaudeRPG and try again.")
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
        self.page.setBackgroundColor(QColor("black"))
        if hasattr(self.page, "permissionRequested"):                   # Qt 6.8+
            self.page.permissionRequested.connect(self._permission)
        elif hasattr(self.page, "featurePermissionRequested"):              # older Qt
            self.page.featurePermissionRequested.connect(self._feature)
        self.view.setPage(self.page)
        self.view.setContextMenuPolicy(Qt.NoContextMenu)
        lay.addWidget(self.view)
        self.view.setUrl(QUrl.fromLocalFile(str(path)))
        self.version = re.search(r"v[\d.]+", path.stem).group(0) if re.search(r"v[\d.]+", path.stem) else ""
        self.mute_timer = QTimer(self, interval=500, timeout=self._sync_mute)
        self.mute_timer.start()
        self._sync_mute()

    def _permission(self, permission):
        """Mouse capture (first-person view) and gamepads are fine; nothing else is asked for."""
        try:
            from PySide6.QtWebEngineCore import QWebEnginePermission
            if permission.permissionType() == QWebEnginePermission.PermissionType.MouseLock:
                permission.grant()
            else:
                permission.deny()
        except Exception:
            pass

    def _feature(self, origin, feature):
        from PySide6.QtWebEngineCore import QWebEnginePage
        ok = feature == QWebEnginePage.Feature.MouseLock
        self.page.setFeaturePermission(origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser if ok
                                       else QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)

    def _sync_mute(self):
        if self.view is not None and self.page.isAudioMuted() != host.muted():
            self.page.setAudioMuted(host.muted())

    def showEvent(self, event):
        super().showEvent(event)
        if self.view is not None:
            QTimer.singleShot(0, self.view.setFocus)                    # keys go straight to the game

    def closeEvent(self, event):
        """Let the game's page unload (it saves on the way out) before the window goes."""
        if self.view is None or self.closing:
            event.accept()
            return
        event.ignore()
        self.closing = True
        self.mute_timer.stop()
        self.view.setUrl(QUrl("about:blank"))
        QTimer.singleShot(400, lambda: self.frame.request_close() if self.frame and isValid(self.frame) else None)


_open = {}


def open_rpg(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = RPGWindow(desktop)
    win = host.window(desktop, TITLE, body, rpg_icon(), (980, 700))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    win.toggle_maximize()                                           # the game likes room
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win) and win.content.view is not None:
        win.content.view.setUrl(QUrl("about:blank"))
