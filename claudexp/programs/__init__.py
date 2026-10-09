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
    listed: bool = True                     # shown in All Programs (Task Manager isn't, like XP)


def _my_computer(desktop):
    from .. import explorer
    explorer.launch(desktop)


FURRY = "Furry Stuff"

# Desktop shortcuts to the user's own archive folders on E: (Local Storage): key -> (label, folder name prefix).
FOLDER_SHORTCUTS = {"mediaarchive": ("Furry Media Archive", "furry media archive"),
                    "tvmovies": ("TV and Movies", "tv and movies")}


def archive_folder(key):
    """The E: folder a folder shortcut points at, or None if the user hasn't put one there."""
    from ..explorer.vfs import local_storage
    prefix = FOLDER_SHORTCUTS[key][1]
    return next((d for d in sorted(local_storage().iterdir()) if d.is_dir() and d.name.lower().startswith(prefix)),
                None)


def _open_folder_shortcut(key):
    def run(desktop):
        from .. import explorer
        folder = archive_folder(key)
        if folder is None:
            from ..explorer.dialogs import msgbox
            msgbox(desktop, "Problem with Shortcut", "The drive or network connection that the shortcut "
                   f"'{FOLDER_SHORTCUTS[key][0]}' refers to is unavailable.", "error")
            return
        explorer.launch(desktop, folder)
    return run


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


def _lazy(module, func):
    """A program's launcher (or icon) that imports its module only when first used."""
    def call(*args):
        import importlib
        name = module if module.startswith(".") else "." + module
        return getattr(importlib.import_module(name, __package__), func)(*args)
    return call


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
    Program("outlook", "Outlook Express", "E-mail", _lazy("outlook", "oe_icon"), _lazy("outlook", "open_outlook")),
    Program("wab", "Address Book", "", _lazy("outlook", "book_icon"), _lazy("outlook", "open_address_book"),
            group="Accessories"),
    Program("wmp", "Windows Media Player", "Play music and sounds", _lazy("wmp", "wmp_icon"), _lazy("wmp", "open_wmp"),
            _lazy("wmp", "shutdown")),
    Program("winupdate", "Windows Update", "", lambda: QIcon(_update_icon()), _windows_update),
    Program("calc", "Calculator", "", _lazy("calc", "calc_icon"), _lazy("calc", "open_calc"), group="Accessories"),
    Program("wordpad", "WordPad", "", _lazy("wordpad", "wordpad_icon"), _lazy("wordpad", "open_wordpad"),
            group="Accessories"),
    Program("paint", "Paint", "", _lazy("paint", "paint_icon"), _lazy("paint", "open_paint"), group="Accessories"),
    Program("cmd", "Command Prompt", "", _lazy("cmd", "cmd_icon"), _lazy("cmd", "open_cmd"), group="Accessories"),
    Program("taskmgr", "Windows Task Manager", "", _lazy("taskmgr", "taskmgr_icon"), _lazy("taskmgr", "open_taskmgr"),
            listed=False),
    Program("charmap", "Character Map", "", _lazy("charmap", "charmap_icon"), _lazy("charmap", "open_charmap"),
            group="Accessories/System Tools"),
    Program("cleanmgr", "Disk Cleanup", "", _lazy("cleanmgr", "cleanup_icon"), _lazy("cleanmgr", "open_cleanup"),
            group="Accessories/System Tools"),
    Program("msinfo", "System Information", "", _lazy("msinfo", "msinfo_icon"), _lazy("msinfo", "open_msinfo"),
            group="Accessories/System Tools"),
    Program("tour", "Tour Windows XP", "", _lazy("tour", "tour_icon"), _lazy("tour", "open_tour"), group="Accessories"),
    Program("search", "Search", "", _lazy("search", "search_icon"), _lazy("search", "open_search"), listed=False),
    Program("helpctr", "Help and Support", "", _lazy("helpctr", "help_icon"), _lazy("helpctr", "open_help"),
            listed=False),
    Program("sysrestore", "System Restore", "", _lazy("sysrestore", "restore_icon"), _lazy("sysrestore", "open_wizard"),
            group="Accessories/System Tools"),
    Program("sndrec", "Sound Recorder", "", _lazy("sndrec", "sndrec_icon"), _lazy("sndrec", "open_sndrec"),
            group="Accessories/Entertainment"),
    # Start > Programs > Furry Stuff: the furry programs and the archive folders on E:
    Program("tv", "FurTV 2000", "Watch TV", _lazy(".tv.tuner", "tv_icon"), _lazy(".tv.tuner", "open_tv"),
            _lazy(".tv.tuner", "shutdown"), group=FURRY),
    Program("comix", "FurComix Reader", "Read comics", _lazy(".comix.reader", "comix_icon"),
            _lazy(".comix.reader", "open_comix"), group=FURRY),
    Program("folio", "FurFolio Reader", "Browse art portfolios", _lazy(".folio.gallery", "folio_icon"),
            _lazy(".folio.gallery", "open_folio"), group=FURRY),
    Program("stories", "FurStory Reader", "Read stories", _lazy(".folio.stories", "story_icon"),
            _lazy(".folio.stories", "open_stories"), group=FURRY),
    Program("cdviewer", "Fur CD Viewer", "Browse art CDs and DVDs", _lazy(".folio.cdviewer", "cd_icon"),
            _lazy(".folio.cdviewer", "open_cdviewer"), _lazy(".folio.cdviewer", "shutdown"), group=FURRY),
    Program("furcon", "Furry Con CD Viewer", "Convention recap discs", _lazy(".folio.furcon", "con_icon"),
            _lazy(".folio.furcon", "open_furcon"), _lazy(".folio.furcon", "shutdown"), group=FURRY),
    *[Program(key, label, "", lambda: std_icon(QStyle.SP_DirIcon), _open_folder_shortcut(key), group=FURRY)
      for key, (label, _prefix) in FOLDER_SHORTCUTS.items()],
    Program("nes", "NES Emulator", "Play NES games", _lazy(".nes.fceu", "nes_icon"), _lazy(".nes.fceu", "open_nes"),
            _lazy(".nes.fceu", "shutdown"), group="Games"),
    Program("tvguide", "TV Guide", "", _lazy(".tv.tuner", "tv_icon"), _lazy(".tv.guide", "open_guide"), listed=False),
    Program("defrag", "Disk Defragmenter", "", _defrag_icon, _defrag, group="Accessories/System Tools"),
    Program("antivirus", "ClaudeShield AntiVirus", "", _av_icon, _antivirus),
    Program("connect", "Connect to the Internet", "", lambda: QIcon(pixmap("aol_icon.png")), _connect,
            lambda: network.disconnect(quiet=True)),
    Program("freecell", "FreeCell", "", _game_icon("card_icon", "H", "#D00000"), _game("freecell", "open_freecell"),
            group="Games"),
    Program("hearts", "Hearts", "", _game_icon("card_icon", "H", "#D00000"), _game("hearts", "open_hearts"),
            group="Games"),
    Program("ibackgammon", "Internet Backgammon", "", _lazy("..games.ibackgammon", "backgammon_icon"),
            _lazy("..games.ibackgammon", "open_internet_backgammon"), group="Games"),
    Program("icheckers", "Internet Checkers", "", _lazy("..games.icheckers", "checkers_icon"),
            _lazy("..games.icheckers", "open_internet_checkers"), group="Games"),
    Program("ihearts", "Internet Hearts", "", _game_icon("card_icon", "H", "#D00000"),
            _lazy("..games.ihearts", "open_internet_hearts"), group="Games"),
    Program("ireversi", "Internet Reversi", "", _lazy("..games.ireversi", "reversi_icon"),
            _lazy("..games.ireversi", "open_internet_reversi"), group="Games"),
    Program("ispades", "Internet Spades", "", _game_icon("card_icon", "S"),
            _lazy("..games.ispades", "open_internet_spades"), group="Games"),
    Program("minesweeper", "Minesweeper", "", _game_icon("mine_icon"), _game("minesweeper", "open_minesweeper"),
            group="Games"),
    Program("pinball", "Pinball", "", _lazy("..games.pinball", "pinball_icon"), _lazy("..games.pinball", "open_pinball"),
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
