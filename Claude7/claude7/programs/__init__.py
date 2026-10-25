"""Claude7's programs: ClaudeXP's registry (the shared games, archive tools and apps, and the period programs
bridged through xpcompat), rearranged for 2011 - the 2001-only things gone, the Windows Live names, the Windows 7
accessories added - and installed into claudexp.programs so every program that asks the registry sees it.

    from claudexp import programs
    programs.launch(desktop, "stickynotes")
"""
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtCore import QRectF, Qt
from PySide6.QtWidgets import QApplication, QStyle

from claudexp import programs as xp
from claudexp.programs import FOLDER_SHORTCUTS, Program, archive_folder, installed  # noqa: F401

from .. import wm, xpcompat
from ..paths import icon as asset_icon

# gone by 2011 (or ClaudeXP's own): Netscape, Windows Messenger, activation, the XP tour, StyleXP, Clippy, dial-up
DROPPED = {"navigator", "winmsgr", "activate", "tour", "stylexp", "clippy", "connect", "dsl", "search", "helpctr", "autopilot",
           "personaprofiles"}
RENAMED = {"backup": ("Backup and Restore", "Back up and restore your saves, computers' data and profile"),
           "msn": ("Windows Live Messenger", "Chat with your contacts on Windows Live"),
           "hotmail": ("Windows Live Hotmail", "Free web-based e-mail"),
           "outlook": ("Windows Live Mail", "E-mail"),
           "moviemaker": ("Windows Live Movie Maker", "Make home movies"),
           "mycomputer": ("Computer", ""), "wab": ("Windows Contacts", ""),
           "arp": ("Programs and Features", ""), "sndvol": ("Volume Mixer", ""),
           "flash": ("Adobe Flash Player", "Play Flash movies"),
           "iexplore": ("Internet Explorer", "Browse the Web"),
           "wmp": ("Windows Media Player", "Play music and video"),
           "aim": ("AIM", "Instant messenger"),
           "antivirus": ("ClaudeShield AntiVirus", ""), "adaware": ("Ad-Aware Free", "Find and remove spyware")}
REGROUPED = {"backup": "Maintenance", "msn": "Windows Live", "hotmail": "Windows Live", "outlook": "Windows Live", "moviemaker": "Windows Live",
             "livejournal": "Social Programs", "sndvol": "Accessories", "sndrec": "Accessories",
             "flash": "Adobe", "adaware": "Lavasoft", "neko": "Accessories", "copilotwidgets": "Accessories",
             "winupdate": "", "defrag": "Accessories/System Tools", "sysrestore": "Accessories/System Tools"}
MFU_SLOTS = 10
PINNED = ()
recent = xp.recent


def std_icon(which):
    return QApplication.style().standardIcon(which)


# ---- the Windows 7 accessories' icons --------------------------------------------------------------------------------
def note_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#FFF7A8"))
    g.setColorAt(1, QColor("#F2D95C"))
    p.setPen(QPen(QColor("#C9AE2E"), 1))
    p.setBrush(g)
    p.drawRect(QRectF(3 * s, 3 * s, 26 * s, 26 * s))
    p.setPen(QPen(QColor("#9E8A28"), 1.2 * s))
    for y in (11, 16, 21):
        p.drawLine(QRectF(8 * s, y * s, 0, 0).topLeft(), QRectF(23 * s, y * s, 0, 0).topLeft())
    p.end()
    return QIcon(pm)


def scissors_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#3A6EA5"), 2.4 * s))
    p.drawLine(QRectF(9 * s, 9 * s, 0, 0).topLeft(), QRectF(26 * s, 24 * s, 0, 0).topLeft())
    p.drawLine(QRectF(26 * s, 9 * s, 0, 0).topLeft(), QRectF(9 * s, 24 * s, 0, 0).topLeft())
    p.setPen(QPen(QColor("#C0392B"), 2 * s))
    p.setBrush(QColor("#F6D1CB"))
    p.drawEllipse(QRectF(3 * s, 20 * s, 9 * s, 9 * s))
    p.drawEllipse(QRectF(20 * s, 20 * s, 9 * s, 9 * s))
    p.end()
    return QIcon(pm)


def gadget_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#6EC1F5"))
    g.setColorAt(1, QColor("#1F6FB8"))
    p.setPen(QPen(QColor("#0E4A80"), 1))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(4 * s, 4 * s, 24 * s, 24 * s), 4 * s, 4 * s)
    p.setPen(QPen(QColor("white"), 2 * s))
    p.drawEllipse(QRectF(10 * s, 10 * s, 12 * s, 12 * s))
    p.drawLine(QRectF(16 * s, 16 * s, 0, 0).topLeft(), QRectF(16 * s, 11.5 * s, 0, 0).topLeft())
    p.drawLine(QRectF(16 * s, 16 * s, 0, 0).topLeft(), QRectF(19 * s, 16 * s, 0, 0).topLeft())
    p.end()
    return QIcon(pm)


def help_icon():
    ic = asset_icon("Help.ico")
    return ic if not ic.isNull() else std_icon(QStyle.SP_MessageBoxQuestion)


def _lazy(module, func):
    def call(*args):
        import importlib
        return getattr(importlib.import_module(module, __package__), func)(*args)
    return call


def _network(desktop):
    from .. import network
    network.get(desktop)._show_status()


def _control_panel(desktop):
    from ..controlpanel import control_panel
    control_panel(desktop)


def _network_icon():
    from ..network import network_icon
    return network_icon()


def _firefox_icon():
    from .browsers import firefox_icon
    return firefox_icon()


def _chess_icon():
    from .chess import chess_icon
    return chess_icon()


SEVEN = [
    Program("stickynotes", "Sticky Notes", "Notes on your desktop", note_icon, _lazy(".stickynotes", "launch"),
            _lazy(".stickynotes", "shutdown"), group="Accessories"),
    Program("snipping", "Snipping Tool", "Capture a piece of the screen", scissors_icon, _lazy(".snipping", "launch"),
            _lazy(".snipping", "shutdown"), group="Accessories"),
    Program("gadgets", "Desktop Gadget Gallery", "Clock, calendar, weather and more on the desktop", gadget_icon,
            _lazy(".gadgets", "open_gallery"), _lazy(".gadgets", "shutdown")),
    Program("helpctr", "Help and Support", "", help_icon, _lazy(".helpctr", "open_help"), listed=False),
    Program("controlpanel", "Control Panel", "", lambda: std_icon(QStyle.SP_DesktopIcon), _control_panel, listed=False),
    Program("network", "Network and Sharing Center", "", _network_icon, _network, listed=False),
    Program("firefox", "Mozilla Firefox", "Browse the Web", _firefox_icon, _lazy(".browsers", "launch_firefox"),
            _lazy(".browsers", "shutdown_firefox"), group="Mozilla Firefox"),
    Program("chess", "Chess Titans", "Chess against the computer on a wooden board", _chess_icon,
            _lazy(".chess", "open_chess"), group="Games/Windows Games"),
]


def _build():
    out = []
    for p in xp.PROGRAMS:
        if p.key in DROPPED:
            continue
        name, blurb = RENAMED.get(p.key, (p.name, p.blurb))
        group = REGROUPED.get(p.key, p.group)
        if group == "Accessories/Entertainment":
            group = "Accessories"
        run, shutdown = p.run, p.shutdown
        if p.key == "iexplore":                       # Internet Explorer 9's chrome on the same engine
            run, shutdown = _lazy(".browsers", "launch_ie"), _lazy(".browsers", "shutdown_ie")
        out.append(Program(p.key, name, blurb, p.icon, run, shutdown, group, p.listed))
    return out + SEVEN


PROGRAMS = _build()


def get(key):
    return next(p for p in PROGRAMS if p.key == key)


def launch(desktop, key):
    program = get(key)
    if installed.is_removed(key):
        from ..dialogs import msgbox
        msgbox(desktop, program.name, f"{program.name} is not installed.\n\nTo use it again, reinstall it from "
               "Control Panel > Programs and Features.", "warning")
        return
    installed.record(key)
    if program.listed and key not in PINNED:
        if key in recent:
            recent.remove(key)
        recent.insert(0, key)
        del recent[MFU_SLOTS:]
    wm.launching = key
    try:
        program.run(desktop)
    finally:
        wm.launching = None
    xpcompat.patch_years()


def shutdown_all():
    for prog in PROGRAMS:
        if prog.shutdown:
            try:
                prog.shutdown()
            except Exception:
                pass


# ---- install into claudexp.programs: everyone who asks the registry gets Claude7's ------------------------------------
from .browsers import install as _install_browsers  # noqa: E402
from ..explorer7 import install as _install_explorer  # noqa: E402
_install_browsers()
_install_explorer()
xp.PROGRAMS[:] = PROGRAMS
xp.PINNED = PINNED
xp.MFU_SLOTS = MFU_SLOTS
xp.launch = launch
xp.shutdown_all = shutdown_all
recent[:] = ["stickynotes", "snipping", "calc", "paint", "aim", "wmp", "solitaire", "claudeai", "msn", "iexplore"]
