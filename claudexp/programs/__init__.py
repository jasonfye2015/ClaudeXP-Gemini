"""Registry of programs that can run inside ClaudeXP."""
from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle

from .. import network, sound
from ..paths import pixmap
from . import aim, irc, muck, navigator
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


def _my_computer(desktop):
    open_placeholder(desktop, "My Computer", std_icon(QStyle.SP_ComputerIcon),
                     "No drives installed yet.\n\nClaudeXP is still being assembled!")


def _connect(desktop):
    net = network.get(desktop)
    if net.connected:
        net._show_status()
    else:
        sound.play("navigate")
        net.connect()


PROGRAMS = [
    Program("notepad", "Notepad", "Write some text", lambda: std_icon(QStyle.SP_FileIcon), open_notepad),
    Program("mycomputer", "My Computer", "", lambda: std_icon(QStyle.SP_ComputerIcon), _my_computer),
    Program("aim", "ClaudeAIM", "Instant messenger", aim.aim_icon, aim.launch, aim.shutdown),
    Program("muck", "ClaudeMUCK", "PawPrints MUCK", muck.muck_icon, muck.launch, muck.shutdown),
    Program("irc", "ClaudeIRC", "Chat on FurNet", irc.irc_icon, irc.launch, irc.shutdown),
    Program("navigator", "Netscape Navigator", "Browse the Web", navigator.nav_icon, navigator.launch,
            navigator.shutdown),
    Program("connect", "Connect to the Internet", "", lambda: QIcon(pixmap("aol_icon.png")), _connect,
            lambda: network.disconnect(quiet=True)),
]


def get(key):
    return next(p for p in PROGRAMS if p.key == key)


def launch(desktop, key):
    get(key).run(desktop)


def shutdown_all():
    for prog in PROGRAMS:
        if prog.shutdown:
            prog.shutdown()
