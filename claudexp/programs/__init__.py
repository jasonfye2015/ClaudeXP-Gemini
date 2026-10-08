"""Registry of programs that can run inside ClaudeXP."""
from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle

from .. import network, sound
from ..paths import pixmap
from . import aim, claudeai, irc, muck, navigator
from .notepad import open_notepad
from .placeholder import open_placeholder


def std_icon(which):
    return QApplication.style().standardIcon(which)


@dataclass
class Program:
    key: str
    name: str
    blurb: str
    icon: Callable[[], QIcon]
    run: Callable
    shutdown: Optional[Callable] = None   # called on Log Off / Turn Off
    group: str = ""                         # All Programs submenu, e.g. "Games" or "Accessories/System Tools"


def _my_computer(desktop):
    from .. import explorer
    explorer.launch(desktop)


def _connect(desktop):
    net = network.get(desktop)
    if net.connected:
        net._show_status()
    else:
        sound.play("navigate")
        net.connect()


def _windows_update(desktop):
    from .. import maintenance
    updates = maintenance.get().updates
    if updates.ready and updates.clock is None:
        updates.show_dialog()
    elif updates.clock is not None:
        desktop.balloon.dismiss()
        updates.tray.showMessage("Automatic Updates", updates.tray.toolTip().split("\n")[-1], None, 5000)
    elif network.is_connected():
        if not updates.start_download():
            open_placeholder(desktop, "Windows Update", QIcon(_update_icon()),
                             "Your computer is up to date.\n\nThere are no new updates for you right now.",
                             sound_event="info")
    else:
        network.connect(desktop, then=lambda: _windows_update(desktop))


def _update_icon():
    from ..maintenance.updates import shield_pixmap
    return shield_pixmap(32)


def _defrag_icon():
    from ..maintenance.defrag import icon_pixmap
    return QIcon(icon_pixmap(32))


def _defrag(desktop):
    from ..maintenance import defrag
    defrag.launch(desktop)


def _av_icon():
    from ..maintenance.antivirus import shield_icon
    return QIcon(shield_icon(32))


def _game(module, func):
    def run(desktop):
        import importlib
        getattr(importlib.import_module(f"..games.{module}", __package__), func)(desktop)
    return run


def _game_icon(kind, *args):
    def icon():
        from ..games import common
        return getattr(common, kind)(*args)
    return icon


def _antivirus(desktop):
    from .. import maintenance
    maintenance.get().antivirus.open()


PROGRAMS = [
    Program("notepad", "Notepad", "Write some text", lambda: std_icon(QStyle.SP_FileIcon), open_notepad,
            group="Accessories"),
    Program("mycomputer", "My Computer", "", lambda: std_icon(QStyle.SP_ComputerIcon), _my_computer),
    Program("aim", "ClaudeAIM", "Instant messenger", aim.aim_icon, aim.launch, aim.shutdown),
    Program("muck", "ClaudeMUCK", "PawPrints MUCK", muck.muck_icon, muck.launch, muck.shutdown),
    Program("irc", "ClaudeIRC", "Chat on FurNet", irc.irc_icon, irc.launch, irc.shutdown),
    Program("navigator", "Netscape Navigator", "Browse the Web", navigator.nav_icon, navigator.launch,
            navigator.shutdown),
    Program("claudeai", "ClaudeAI", "Chat with your local AI", claudeai.claudeai_icon, claudeai.launch,
            claudeai.shutdown),
    Program("winupdate", "Windows Update", "", lambda: QIcon(_update_icon()), _windows_update),
    Program("defrag", "Disk Defragmenter", "", _defrag_icon, _defrag, group="Accessories/System Tools"),
    Program("antivirus", "ClaudeShield AntiVirus", "", _av_icon, _antivirus),
    Program("connect", "Connect to the Internet", "", lambda: QIcon(pixmap("aol_icon.png")), _connect,
            lambda: network.disconnect(quiet=True)),
    Program("freecell", "FreeCell", "", _game_icon("card_icon", "H", "#D00000"), _game("freecell", "open_freecell"),
            group="Games"),
    Program("hearts", "Hearts", "", _game_icon("card_icon", "H", "#D00000"), _game("hearts", "open_hearts"),
            group="Games"),
    Program("minesweeper", "Minesweeper", "", _game_icon("mine_icon"), _game("minesweeper", "open_minesweeper"),
            group="Games"),
    Program("solitaire", "Solitaire", "", _game_icon("card_icon", "S"), _game("solitaire", "open_solitaire"),
            group="Games"),
    Program("spider", "Spider Solitaire", "", _game_icon("card_icon", "S"), _game("spider", "open_spider"),
            group="Games"),
]


def get(key):
    return next(p for p in PROGRAMS if p.key == key)


def launch(desktop, key):
    get(key).run(desktop)


def shutdown_all():
    for prog in PROGRAMS:
        if prog.shutdown:
            prog.shutdown()
