"""Claude11's programs: ClaudeXP's registry (the shared games, archive tools and apps, and the period programs
bridged through xpcompat), rearranged for 2025 - the services that have closed since gone (AIM, MSN Messenger,
Yahoo! Messenger, ICQ, Skype), the 2025 names (Microsoft Edge, Outlook, Clipchamp, Media Player), Windows 11's own
additions - and installed into claudexp.programs so every program that asks the registry sees it.

    from claudexp import programs
    programs.launch(desktop, "settings")
"""
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtWidgets import QApplication, QStyle

from claudexp import programs as xp
from claudexp.programs import FOLDER_SHORTCUTS, Program, archive_folder, installed  # noqa: F401

from .. import wm, xpcompat
from ..paths import icon as asset_icon

# gone by October 2025 (or ClaudeXP's own): AIM (2017), MSN/Windows Live Messenger (2013), Yahoo! Messenger (2018),
# ICQ (June 2024), Skype (May 2025), QuickTime for Windows (2016), Ad-Aware, the MSN Gaming Zone games (2019),
# Netscape, Windows Messenger, activation, the XP tour, StyleXP, Clippy, dial-up, XP's Help
DROPPED = {"navigator", "winmsgr", "activate", "tour", "stylexp", "clippy", "connect", "dsl", "search", "helpctr",
           "personaprofiles", "aim", "msn", "yim", "icq", "skype", "quicktime", "adaware",
           "ibackgammon", "icheckers", "ihearts", "ireversi", "ispades"}
RENAMED = {"backup": ("Windows Backup", "Back up and restore your saves, computers' data and profile"),
           "iexplore": ("Microsoft Edge", "Browse the web"),
           "hotmail": ("Outlook.com", "Your mail on the web"),
           "outlook": ("Outlook", "Mail and calendar"),
           "moviemaker": ("Clipchamp", "Make videos"),
           "mycomputer": ("File Explorer", ""), "wab": ("People", "Your contacts"),
           "arp": ("Installed apps", ""), "sndvol": ("Volume mixer", ""), "sndrec": ("Sound Recorder", ""),
           "flash": ("Ruffle Flash Player", "Play Flash movies (the Flash emulator)"),
           "wmp": ("Media Player", "Play music and video"),
           "taskmgr": ("Task Manager", ""), "cmd": ("Terminal", "Command Prompt in Windows Terminal"),
           "msconfig": ("System Configuration", ""), "defrag": ("Defragment and Optimize Drives", ""),
           "antivirus": ("ClaudeShield Antivirus", ""), "winupdate": ("Windows Update", ""),
           "trillian": ("Trillian", "Instant messaging for people and teams"), "kik": ("Kik", "Kik Messenger"),
           "pinball": ("3D Pinball Space Cadet", "The classic, still around"),
           "solitaire": ("Solitaire", "Microsoft Solitaire Collection"),
           "spider": ("Spider", "Microsoft Solitaire Collection"), "freecell": ("FreeCell", "Microsoft Solitaire Collection"),
           "tripeaks": ("TriPeaks", "Microsoft Solitaire Collection"), "minesweeper": ("Microsoft Minesweeper", ""),
           "livejournal": ("LiveJournal", "Journals, still going")}
REGROUPED = {"backup": "Windows Tools", "livejournal": "Social Programs", "hotmail": "Social Programs", "outlook": "", "wab": "", "moviemaker": "",
             "sndvol": "Windows Tools", "sndrec": "", "flash": "Ruffle", "neko": "", "copilotwidgets": "Copilot",
             "copilotai": "Copilot", "copilotvoice": "Copilot", "imagecreator": "Copilot", "pystudio": "Copilot",
             "winupdate": "", "defrag": "Windows Tools", "sysrestore": "Windows Tools", "charmap": "Windows Tools",
             "cleanmgr": "Windows Tools", "msinfo": "Windows Tools", "cmd": "Windows Tools",
             "solitaire": "Games/Solitaire & Casual Games", "spider": "Games/Solitaire & Casual Games",
             "freecell": "Games/Solitaire & Casual Games", "tripeaks": "Games/Solitaire & Casual Games",
             "minesweeper": "Games/Solitaire & Casual Games", "hearts": "Games/Classic Games", "golf": "Games/Classic Games",
             "blockfall": "Games/Classic Games", "rodent": "Games/Classic Games", "taipei": "Games/Classic Games",
             "jezzball": "Games/Classic Games", "skifree": "Games/Classic Games", "pinball": "Games/Classic Games"}
MFU_SLOTS = 10
PINNED = ()
recent = xp.recent


def std_icon(which):
    return QApplication.style().standardIcon(which)


# ---- Windows 11's own icons ---------------------------------------------------------------------------------------
def _pm(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    return pm, p, size / 32


def note_icon(size=32):
    pm, p, s = _pm(size)
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#FFF7A8"))
    g.setColorAt(1, QColor("#F5D95B"))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(QRectF(3 * s, 3 * s, 26 * s, 26 * s), 4 * s, 4 * s)
    p.setBrush(QColor("#E0C14A"))
    path = QPainterPath()
    path.moveTo(29 * s, 19 * s)
    path.lineTo(19 * s, 29 * s)
    path.lineTo(19 * s, 23 * s)
    path.quadTo(19 * s, 19 * s, 23 * s, 19 * s)
    path.closeSubpath()
    p.drawPath(path)
    p.setPen(QPen(QColor("#9E8A28"), 1.4 * s))
    for y in (11, 16):
        p.drawLine(QPointF(8 * s, y * s), QPointF(22 * s, y * s))
    p.end()
    return QIcon(pm)


def scissors_icon(size=32):
    pm, p, s = _pm(size)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#E7EFF8"))
    p.drawRoundedRect(QRectF(2 * s, 2 * s, 28 * s, 28 * s), 7 * s, 7 * s)
    p.setPen(QPen(QColor("#2B5FA8"), 2.2 * s))
    p.drawLine(QPointF(10 * s, 9 * s), QPointF(24 * s, 22 * s))
    p.drawLine(QPointF(22 * s, 9 * s), QPointF(8 * s, 22 * s))
    p.setPen(QPen(QColor("#C0392B"), 2 * s))
    p.setBrush(QColor("#F6D1CB"))
    p.drawEllipse(QRectF(4 * s, 19 * s, 8 * s, 8 * s))
    p.drawEllipse(QRectF(20 * s, 19 * s, 8 * s, 8 * s))
    p.end()
    return QIcon(pm)


def widget_icon(size=32):
    pm, p, s = _pm(size)
    colours = ("#4CC2FF", "#0067C0", "#FFB900", "#10893E")
    for i, colour in enumerate(colours):
        x, y = 3 + (i % 2) * 14, 3 + (i // 2) * 14
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(colour))
        p.drawRoundedRect(QRectF(x * s, y * s, 12 * s, 12 * s), 3 * s, 3 * s)
    p.end()
    return QIcon(pm)


def tips_icon(size=32):
    pm, p, s = _pm(size)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#FFB900"))
    p.drawEllipse(QRectF(8 * s, 3 * s, 16 * s, 16 * s))
    p.setBrush(QColor("#F0A000"))
    p.drawRect(QRectF(12 * s, 17 * s, 8 * s, 6 * s))
    p.setBrush(QColor("#6D6D6D"))
    p.drawRoundedRect(QRectF(12 * s, 23 * s, 8 * s, 3 * s), 1.5 * s, 1.5 * s)
    p.drawRoundedRect(QRectF(13 * s, 27 * s, 6 * s, 2 * s), 1 * s, 1 * s)
    p.end()
    return QIcon(pm)


def settings_icon(size=32):
    pm, p, s = _pm(size)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#4A5A6A"))
    from math import cos, radians, sin
    c = 16 * s
    for i in range(8):
        a = radians(i * 45)
        p.drawRoundedRect(QRectF(c + cos(a) * 11 * s - 3 * s, c + sin(a) * 11 * s - 3 * s, 6 * s, 6 * s), 1.5 * s,
                          1.5 * s)
    p.drawEllipse(QPointF(c, c), 10 * s, 10 * s)
    p.setBrush(QColor("#E7EFF8"))
    p.drawEllipse(QPointF(c, c), 4.5 * s, 4.5 * s)
    p.end()
    return QIcon(pm)


def help_icon():
    return tips_icon()


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


ELEVEN = [
    Program("stickynotes", "Sticky Notes", "Notes on your desktop", note_icon, _lazy(".stickynotes", "launch"),
            _lazy(".stickynotes", "shutdown")),
    Program("snipping", "Snipping Tool", "Capture a piece of the screen", scissors_icon, _lazy(".snipping", "launch"),
            _lazy(".snipping", "shutdown")),
    Program("widgets", "Widgets", "Weather, your calendar and inbox, the TV Guide and more on the Widgets board",
            widget_icon, _lazy(".widgets", "open_gallery"), _lazy(".widgets", "shutdown")),
    Program("helpctr", "Tips", "Get to know Windows 11 and this computer", tips_icon, _lazy(".helpctr", "open_help")),
    Program("settings", "Settings", "System, personalization, accounts, updates", settings_icon,
            _lazy("..settings", "open_settings")),
    Program("controlpanel", "Control Panel", "", lambda: std_icon(QStyle.SP_DesktopIcon), _control_panel,
            group="Windows Tools"),
    Program("network", "Network and Internet", "", _network_icon, _network, listed=False),
    Program("firefox", "Mozilla Firefox", "Browse the web", _firefox_icon, _lazy(".browsers", "launch_firefox"),
            _lazy(".browsers", "shutdown_firefox")),
]


def _build():
    out = []
    for p in xp.PROGRAMS:
        if p.key in DROPPED:
            continue
        name, blurb = RENAMED.get(p.key, (p.name, p.blurb))
        group = REGROUPED.get(p.key, p.group)
        if group == "Accessories/Entertainment":
            group = ""
        elif group == "Accessories/System Tools":
            group = "Windows Tools"
        elif group == "Accessories":
            group = ""
        run, shutdown = p.run, p.shutdown
        if p.key == "iexplore":                       # Microsoft Edge's chrome on the same engine
            run, shutdown = _lazy(".browsers", "launch_ie"), _lazy(".browsers", "shutdown_ie")
        out.append(Program(p.key, name, blurb, p.icon, run, shutdown, group, p.listed))
    return out + ELEVEN


PROGRAMS = _build()


def get(key):
    return next(p for p in PROGRAMS if p.key == key)


def launch(desktop, key):
    program = get(key)
    if installed.is_removed(key):
        from ..dialogs import msgbox
        msgbox(desktop, program.name, f"{program.name} is not installed.\n\nTo use it again, reinstall it from "
               "Settings > Apps > Installed apps.", "warning")
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


# ---- install into claudexp.programs: everyone who asks the registry gets Claude11's ----------------------------------
from .browsers import install as _install_browsers  # noqa: E402
from ..explorer11 import install as _install_explorer  # noqa: E402
_install_browsers()
_install_explorer()
xp.PROGRAMS[:] = PROGRAMS
xp.PINNED = PINNED
xp.MFU_SLOTS = MFU_SLOTS
xp.launch = launch
xp.shutdown_all = shutdown_all
recent[:] = ["iexplore", "outlook", "mycomputer", "wmp", "claudeai", "telegram", "discord", "snipping", "notepad",
             "settings"]
