"""Registry of programs that can run inside ClaudeXP."""
from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle

from .. import network, sound
from ..paths import pixmap
import claudeai

from . import aim, irc, muck, navigator
from . import neko
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
DOOM_GAMES = [("doom", "Doom", "Rip and tear"), ("doom2", "Doom II", "Hell on Earth"),
              ("wolf3d", "Wolfenstein 3D", "Escape from Castle Wolfenstein")]
EMULATORS = [("nes", "NES Emulator", "Play NES games"), ("snes", "SNES Emulator", "Play Super NES games"),
             ("gb", "Game Boy Emulator", "Play Game Boy games"),
             ("gbc", "Game Boy Color Emulator", "Play Game Boy Color games"),
             ("gba", "Game Boy Advance Emulator", "Play Game Boy Advance games"),
             ("gen", "Genesis Emulator", "Play Sega Genesis and 32X games"),
             ("sms", "Master System Emulator", "Play Sega Master System games"),
             ("gg", "Game Gear Emulator", "Play Sega Game Gear games"),
             ("n64", "N64 Emulator", "Play Nintendo 64 games"),
             ("apple2", "Apple ][ Emulator", "Boot Apple ][ disks")]

# Desktop shortcuts to the user's own archive folders on E: (Local Storage): key -> (label, folder name prefix).
FOLDER_SHORTCUTS = {"mediaarchive": ("Furry Media Archive", "furry media archive"),
                    "tvmovies": ("TV and Movies", "tv and movies"),
                    "miscimages": ("Misc Personal Image Folders", "misc personal image folders"),
                    "personaldocs": ("Personal Text and Documents", "personal text"),
                    "localprojects": ("Local Projects", "projects/local projects")}
SHORTCUT_GROUPS = {"localprojects": "Projects"}        # the rest are in Furry Stuff


def archive_folder(key):
    """The E: folder a folder shortcut points at, or None if the user hasn't put one there."""
    from ..explorer.vfs import local_storage
    folder = local_storage()
    for prefix in FOLDER_SHORTCUTS[key][1].split("/"):       # ('projects/local projects': a folder inside one)
        try:
            folder = next((d for d in sorted(folder.iterdir()) if d.is_dir() and d.name.lower().startswith(prefix)),
                          None)
        except OSError:
            folder = None
        if folder is None:
            return None
    return folder


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


def _connect(desktop, kind="aol"):
    net = network.get(desktop)
    if net.connected:
        net._show_status()
    else:
        sound.play("navigate")
        net.connect(kind=kind)


def _connect_dsl(desktop):
    _connect(desktop, "dsl")


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


def _shared(module, func):
    """A program from the Claude Timeline's shared folders (ClaudeGames, ClaudeArchive, ClaudeApps), imported on first use."""
    def call(*args):
        import importlib
        return getattr(importlib.import_module(module), func)(*args)
    return call


def _project_icon(key):
    return lambda: __import__("projects").icon(key)


def _project_launch(key):
    """One of the Projects (ClaudeApps/projects): its own program, in its own window."""
    return lambda desktop: __import__("projects").launch(desktop, key)


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
    Program("aim", "ClaudeAIM", "Instant messenger", aim.aim_icon, aim.launch, aim.shutdown, group="Social Programs"),
    Program("muck", "ClaudeMUCK", "PawPrints MUCK", muck.muck_icon, muck.launch, muck.shutdown,
            group="Social Programs"),
    Program("msn", "MSN Messenger", "Chat with your buddies on MSN", _lazy(".messengers.msn", "msn_icon"),
            _lazy(".messengers.msn", "launch"), _lazy(".messengers.msn", "shutdown"), group="Social Programs"),
    Program("yim", "Yahoo! Messenger", "Chat with your friends on Yahoo!", _lazy(".messengers.yim", "yim_icon"),
            _lazy(".messengers.yim", "launch"), _lazy(".messengers.yim", "shutdown"), group="Social Programs"),
    Program("icq", "ICQ", "I Seek You", _lazy(".messengers.others", "icq_icon"),
            _lazy(".messengers.others", "launch_icq"), _lazy(".messengers.others", "shutdown_icq"),
            group="Social Programs"),
    Program("trillian", "Trillian", "Every network in one window", _lazy(".messengers.others", "trillian_icon"),
            _lazy(".messengers.others", "launch_trillian"), _lazy(".messengers.others", "shutdown_trillian"),
            group="Social Programs"),
    Program("skype", "Skype", "Free Internet calls and chat", _lazy(".messengers.others", "skype_icon"),
            _lazy(".messengers.others", "launch_skype"), _lazy(".messengers.others", "shutdown_skype"),
            group="Social Programs"),
    Program("kik", "Kik", "Chat like on a phone", _lazy(".messengers.others", "kik_icon"),
            _lazy(".messengers.others", "launch_kik"), _lazy(".messengers.others", "shutdown_kik"),
            group="Social Programs"),
    Program("telegram", "Telegram", "Fast, secure messaging - with stickers", _lazy(".messengers.telegram", "telegram_icon"),
            _lazy(".messengers.telegram", "launch"), _lazy(".messengers.telegram", "shutdown"), group="Social Programs"),
    Program("discord", "Discord", "Your friends, The Den, and what you're playing", _lazy(".messengers.discord", "discord_icon"),
            _lazy(".messengers.discord", "launch"), _lazy(".messengers.discord", "shutdown"), group="Social Programs"),
    Program("irc", "ClaudeIRC", "Chat on FurNet", irc.irc_icon, irc.launch, irc.shutdown, group="Social Programs"),
    Program("claudeggle", "Claudeggle", "Aim, shoot, clear the orange pegs", _shared("claudeggle", "peggle_icon"),
            _shared("claudeggle", "launch"), _shared("claudeggle", "shutdown"), group="Games"),
    Program("claudemmings", "Claudemmings", "Guide the lemmings home - the twelve Fun levels, with the original music",
            _shared("claudemmings", "claudemmings_icon"), _shared("claudemmings", "launch"),
            _shared("claudemmings", "shutdown"), group="Games"),
    Program("backup", "Backup Utility", "Back up and restore your saves, computers' data and profile",
            _shared("claudecore.backup_ui", "backup_icon"), _shared("claudecore.backup_ui", "launch"),
            group="Accessories/System Tools"),
    Program("claudualties", "Claudualties Unknown", "Descend the caves for the cargo and keep the Expie alive",
            _shared("claudualties", "claudualties_icon"), _shared("claudualties", "launch"),
            _shared("claudualties", "shutdown"), group="Games"),
    Program("fractals", "Claude Fractal Generator", "Mandelbrot, Julia and friends, Fractint style",
            _shared("fractals", "fractal_icon"), _shared("fractals", "open_fractals"),
            _shared("fractals", "shutdown"), group="Games"),
    Program("terrain", "Claude Terrain Generator", "Fractal landscapes, VistaPro style", _shared("terrain", "terrain_icon"),
            _shared("terrain", "open_terrain"), group="Games"),
    Program("claudemagic", "Claude and Magic", "Twenty floors down, the Lich King waits", _shared("claudemagic", "magic_icon"),
            _shared("claudemagic", "launch"), _shared("claudemagic", "shutdown"), group="Games"),
    Program("claudelife", "Claude Life", "Conway's Game of Life - draw, stamp and watch it grow",
            _shared("claudelife", "life_icon"), _shared("claudelife", "launch"), _shared("claudelife", "shutdown"),
            group="Games"),
    Program("claudeshelter", "Claude Shelter", "Run an underground vault: dwellers, rooms, raiders and the wasteland",
            _shared("claudeshelter", "shelter_icon"), _shared("claudeshelter", "launch"),
            _shared("claudeshelter", "shutdown"), group="Games"),
    Program("claudeout", "Claudeout 4", "Out of Vault 111 and down into the old neighbourhood, two parts, in 3D",
            _shared("claudeout", "out_icon"), _shared("claudeout", "launch"), _shared("claudeout", "shutdown"),
            group="Games"),
    Program("claudepit", "ClaudePit", "A slot machine, a debt, and a trapdoor - pay up or fall",
            _shared("claudepit", "pit_icon"), _shared("claudepit", "launch"), _shared("claudepit", "shutdown"),
            group="Games"),
    Program("claudeatro", "Claudeatro", "Poker hands, chips x mult, and jokers that break the rules",
            _shared("claudeatro", "atro_icon"), _shared("claudeatro", "launch"), _shared("claudeatro", "shutdown"),
            group="Games"),
    Program("claudescryption", "Claudescryption", "Leshy deals - a card game of sacrifice in a cabin in the woods",
            _shared("claudescryption", "scry_icon"), _shared("claudescryption", "launch"),
            _shared("claudescryption", "shutdown"), group="Games"),
    Program("claudeita", "Claudeita", "Wands, spells and a world that falls apart - descend to the Unmaker",
            _shared("claudeita", "claudeita_icon"), _shared("claudeita", "launch"), _shared("claudeita", "shutdown"),
            group="Games"),
    Program("claudeaquarium", "Claude Aquarium", "A living fish tank - windowed, full screen or a desktop pet",
            _shared("claudeaquarium", "aquarium_icon"), _shared("claudeaquarium", "launch"),
            _shared("claudeaquarium", "shutdown"), group="Games"),
    Program("claudeincremental", "Claude Incremental", "From answering questions to converting the galaxy",
            _shared("claudeincremental", "incremental_icon"), _shared("claudeincremental", "launch"),
            _shared("claudeincremental", "shutdown"), group="Games"),
    Program("claudeanoid", "Claudeanoid", "Break all the blocks - 40 rounds", _shared("claudeanoid", "claudeanoid_icon"),
            _shared("claudeanoid", "launch"), _shared("claudeanoid", "shutdown"), group="Games"),
    Program("claudejeweled", "Claudejeweled", "Swap gems, line up three", _shared("claudejeweled", "jeweled_icon"),
            _shared("claudejeweled", "launch"), _shared("claudejeweled", "shutdown"), group="Games"),
    Program("scorched", "Scorched Claude", "Tanks, nukes and very angry physics", _shared("scorched", "scorched_icon"),
            _shared("scorched", "launch"), _shared("scorched", "shutdown"), group="Games"),
    Program("claudecity", "ClaudeCity", "Build a city from dust to Megalopolis", _shared("claudecity", "city_icon"),
            _shared("claudecity", "launch"), _shared("claudecity", "shutdown"), group="Games"),
    Program("claudeablo", "Claudeablo", "Fifty levels down, the Lord of Terror waits", _shared("claudeablo", "ablo_icon"),
            _shared("claudeablo", "launch"), _shared("claudeablo", "shutdown"), group="Games"),
    Program("claudequest", "ClaudeQuest", "The pack is calling", _shared("claudequest", "quest_icon"),
            _shared("claudequest", "launch"), _shared("claudequest", "shutdown"), group="Games"),
    Program("secondlife", "Second Life", "Your world. Your imagination. A 3D world of furry avatars",
            _lazy(".secondlife", "sl_icon"), _lazy(".secondlife", "launch"), _lazy(".secondlife", "shutdown"),
            group="Social Programs"),
    Program("hollow", "Furry Hollow", "Second Life on your own PC (OpenSimulator), with the residents in it",
            _shared("opensim_world.program", "hollow_icon"), _shared("opensim_world.program", "open_world"),
            _shared("opensim_world.program", "shutdown"), group="Social Programs"),
    Program("furcadia", "Claudecadia", "Let your imagination soar: a furry graphical chat world", _lazy(".furcadia", "furc_icon"),
            _lazy(".furcadia", "launch"), _lazy(".furcadia", "shutdown"), group="Social Programs"),
    Program("claudecraft", "ClaudeCraft", "Build anything, block by block", _shared("claudecraft", "craft_icon"),
            _shared("claudecraft", "launch"), _shared("claudecraft", "shutdown"), group="Games"),
    Program("kiwix", "Kiwix Wiki Reader", "Wikipedia, offline", _lazy(".kiwix", "kiwix_icon"), _lazy(".kiwix", "launch"),
            _lazy(".kiwix", "shutdown"), group="Kiwix"),
    Program("realplayer", "RealPlayer", "Play audio and video", _lazy("players", "real_icon"),
            _lazy("players", "open_realplayer"), _lazy("players", "shutdown_realplayer"), group="Real"),
    Program("quicktime", "QuickTime Player", "Play movies", _lazy("players", "qt_icon"),
            _lazy("players", "open_quicktime"), _lazy("players", "shutdown_quicktime"), group="QuickTime"),
    Program("moviemaker", "Windows Movie Maker", "Make home movies", _lazy("moviemaker", "mm_icon"),
            _lazy("moviemaker", "open_moviemaker"), _lazy("moviemaker", "shutdown"), group="Accessories"),
    Program("winmsgr", "Windows Messenger", "Instant messages with .NET Passport",
            _lazy(".messengers.winmsgr", "winmsgr_icon"), _lazy(".messengers.winmsgr", "launch"),
            _lazy(".messengers.winmsgr", "shutdown"), group="Social Programs"),
    Program("activate", "Activate Windows", "", _lazy("..xpnags", "activation_icon"),
            _lazy("..xpnags", "launch_activation"), group="Accessories/System Tools"),
    Program("arp", "Add or Remove Programs", "", _lazy("arp", "arp_qicon"), _lazy("arp", "open_arp"), listed=False),
    Program("livejournal", "LiveJournal", "Your friends' online journals",
            _lazy(".navigator.sites.livejournal", "lj_icon"), _lazy(".navigator.sites.livejournal", "open_livejournal"),
            group="Social Programs"),
    Program("hotmail", "MSN Hotmail", "Free web-based e-mail", _lazy("..mailtray", "hotmail_icon"),
            _lazy("..mailtray", "open_hotmail"), group="Social Programs"),
    Program("iexplore", "Internet Explorer", "Browse the Web", _lazy(".navigator.iexplore", "ie_icon"),
            _lazy(".navigator.iexplore", "launch"), _lazy(".navigator.iexplore", "shutdown")),
    Program("navigator", "Netscape Navigator", "Browse the Web", navigator.nav_icon, navigator.launch,
            navigator.shutdown, group="Social Programs"),
    Program("claudeai", "ClaudeAI", "Chat with your local AI", claudeai.claudeai_icon, claudeai.launch,
            claudeai.shutdown),
    Program("kithylinai", "Kithylin AI", "Chat with Kithylin the Angelic Husky, played by your own fine-tuned models",
            _shared("kithylinai", "kithylin_icon"), _shared("kithylinai", "launch"), _shared("kithylinai", "shutdown")),
    Program("manual", "Claude Timeline Manual", "How the three computers, the archive, the games and Kithylin fit together",
            _shared("manual", "manual_icon"), _shared("manual", "launch")),
    Program("outlook", "Outlook Express", "E-mail", _lazy("outlook", "oe_icon"), _lazy("outlook", "open_outlook")),
    Program("wab", "Address Book", "", _lazy("outlook", "book_icon"), _lazy("outlook", "open_address_book"),
            group="Accessories"),
    Program("wmp", "Windows Media Player", "Play music and sounds", _lazy("wmp", "wmp_icon"), _lazy("wmp", "open_wmp"),
            _lazy("wmp", "shutdown")),
    Program("winupdate", "Windows Update", "", lambda: QIcon(_update_icon()), _windows_update),
    Program("calc", "Calculator", "", _lazy("calc", "calc_icon"), _lazy("calc", "open_calc"), group="Accessories"),
    Program("wordpad", "WordPad", "", _lazy("wordpad", "wordpad_icon"), _lazy("wordpad", "open_wordpad"),
            group="Accessories"),
    Program("gemini_word", "Gemini Word", "Create and format documents",
            _lazy("gemini_word", "gemini_word_icon"), _lazy("gemini_word", "open_gemini_word"),
            group="Gemini Office"),
    Program("gemini_excel", "Gemini Excel", "Create spreadsheets and workbooks",
            _lazy("gemini_excel", "gemini_excel_icon"), _lazy("gemini_excel", "open_gemini_excel"),
            group="Gemini Office"),
    Program("gemini_powerpoint", "Gemini PowerPoint", "Create and present slide shows",
            _lazy("gemini_powerpoint", "gemini_powerpoint_icon"),
            _lazy("gemini_powerpoint", "open_gemini_powerpoint"), group="Gemini Office"),
    Program("gemini_outlook", "Gemini Outlook", "Mail, calendar, tasks, and contacts",
            _lazy("gemini_outlook", "gemini_outlook_icon"),
            _lazy("gemini_outlook", "open_gemini_outlook"), group="Gemini Office"),
    Program("gemini_access", "Gemini Access", "Create and manage databases",
            _lazy("gemini_access", "gemini_access_icon"),
            _lazy("gemini_access", "open_gemini_access"), group="Gemini Office"),
    Program("gemini_publisher", "Gemini Publisher", "Design flyers and page-layout publications",
            _lazy("gemini_publisher", "gemini_publisher_icon"),
            _lazy("gemini_publisher", "open_gemini_publisher"), group="Gemini Office"),
    Program("gemini_photo", "Gemini Photo", "Edit and retouch pictures",
            _lazy("gemini_photo", "gemini_photo_icon"),
            _lazy("gemini_photo", "open_gemini_photo"), group="GeminiAdobe"),
    Program("gemini_draw", "Gemini Draw", "Create and edit vector illustrations",
            _lazy("gemini_draw", "gemini_draw_icon"),
            _lazy("gemini_draw", "open_gemini_draw"), group="GeminiAdobe"),
    Program("gemini_acrobat", "Gemini Acrobat", "View and print PDF documents",
            _lazy("gemini_acrobat", "gemini_acrobat_icon"),
            _lazy("gemini_acrobat", "open_gemini_acrobat"), group="GeminiAdobe"),
    Program("gemini_distiller", "Gemini Distiller", "Create PDF files from documents and images",
            _lazy("gemini_distiller", "gemini_distiller_icon"),
            _lazy("gemini_distiller", "open_gemini_distiller"), group="GeminiAdobe"),
    Program("paint", "Paint", "", _lazy("paint", "paint_icon"), _lazy("paint", "open_paint"), group="Accessories"),
    Program("imagecreator", "Copilot Image Creator", "Generate images locally",
            _shared("imagegen", "imagegen_icon"), _shared("imagegen", "open_imagegen"),
            _shared("imagegen", "shutdown"), group="Accessories"),
    Program("copilotvoice", "Copilot Voice", "Talk with your local AI using speech",
            _shared("copilot_voice", "voice_icon"), _shared("copilot_voice", "open_copilot_voice"),
            _shared("copilot_voice", "shutdown"), group="Accessories"),
    Program("copilotai", "CopilotAI", "Chat with local models using text or voice",
            _shared("copilotai", "copilotai_icon"), _shared("copilotai", "launch"),
            _shared("copilotai", "shutdown"), group="Accessories"),
    Program("copilotwidgets", "Copilot Widgets", "Clock, calendar, weather, TV guide and more",
            _lazy("copilot_widgets", "widgets_icon"), _lazy("copilot_widgets", "launch"),
            _lazy("copilot_widgets", "shutdown"), group="Accessories"),
    Program("pystudio", "Copilot Python Studio", "Write and run Python programs offline",
            _shared("pystudio", "studio_icon"), _shared("pystudio", "launch"),
            _shared("pystudio", "shutdown"), group="Accessories"),
    Program("cmd", "Command Prompt", "", _lazy("cmd", "cmd_icon"), _lazy("cmd", "open_cmd"), group="Accessories"),
    Program("taskmgr", "Windows Task Manager", "", _lazy("taskmgr", "taskmgr_icon"), _lazy("taskmgr", "open_taskmgr"),
            listed=False),
    Program("charmap", "Character Map", "", _lazy("charmap", "charmap_icon"), _lazy("charmap", "open_charmap"),
            group="Accessories/System Tools"),
    Program("cleanmgr", "Disk Cleanup", "", _lazy("cleanmgr", "cleanup_icon"), _lazy("cleanmgr", "open_cleanup"),
            group="Accessories/System Tools"),
    Program("msinfo", "System Information", "", _lazy("msinfo", "msinfo_icon"), _lazy("msinfo", "open_msinfo"),
            group="Accessories/System Tools"),
    Program("clippy", "Office Assistant", "Clippy, at your service", _lazy("..clippy.program", "clippy_icon"),
            _lazy("..clippy.program", "summon"), _lazy("..clippy.program", "shutdown"), group="Accessories"),
    Program("neko", "Copilot Neko", "The Classic Desktop Cat", neko.neko_icon, neko.launch, neko.shutdown,
            group="Accessories"),
    Program("tour", "Tour Windows XP", "", _lazy("tour", "tour_icon"), _lazy("tour", "open_tour"), group="Accessories"),
    Program("search", "Search", "", _lazy("search", "search_icon"), _lazy("search", "open_search"), listed=False),
    Program("helpctr", "Help and Support", "", _lazy("helpctr", "help_icon"), _lazy("helpctr", "open_help"),
            listed=False),
    Program("msconfig", "System Configuration Utility", "", _lazy("msconfig", "msconfig_icon"),
            _lazy("msconfig", "open_msconfig"), listed=False),
    Program("sysrestore", "System Restore", "", _lazy("sysrestore", "restore_icon"), _lazy("sysrestore", "open_wizard"),
            group="Accessories/System Tools"),
    Program("sndvol", "Volume Control", "", _lazy("..volume", "volume_icon"), _lazy("..volume", "open_volume_control"),
            group="Accessories/Entertainment"),
    Program("sndrec", "Sound Recorder", "", _lazy("sndrec", "sndrec_icon"), _lazy("sndrec", "open_sndrec"),
            group="Accessories/Entertainment"),
    Program("flash", "Macromedia Flash Player", "Play Shockwave Flash movies", _lazy("flash", "flash_icon"),
            _lazy("flash", "open_flash"), _lazy("flash", "shutdown"), group="Accessories/Entertainment"),
    Program("stylexp", "StyleXP", "Visual styles for Windows XP", _lazy("stylexp", "stylexp_icon"),
            _lazy("stylexp", "open_stylexp"), group="StyleXP"),
    Program("torrent", "ClaudeTorrent", "Download with BitTorrent", _lazy("torrent", "torrent_icon"),
            _lazy("torrent", "open_torrent"), _lazy("torrent", "shutdown"), group="ClaudeTorrent"),
    Program("nero", "Nero Burning ROM", "CD and DVD burning software",
            _lazy("utility_icons", "nero_icon"), _lazy("nero", "open_nero"), group="Nero"),
    Program("alcohol120", "Alcohol 120%", "CD/DVD burning and emulation",
            _lazy("utility_icons", "alcohol_icon"), _lazy("alcohol", "open_alcohol"), group="Alcohol 120%"),
    Program("adaware", "Ad-aware", "Find and remove spyware", _lazy("..maintenance.adaware", "aa_icon"),
            _lazy("..maintenance.adaware", "launch"), group="Lavasoft Ad-aware 5.6"),
    Program("winrar", "WinRAR", "Archive manager",
            _lazy("utility_icons", "winrar_icon"), _lazy("winrar", "open_winrar"), group="WinRAR"),
    Program("winzip", "WinZip", "The Zip File Utility",
            _lazy("utility_icons", "winzip_icon"), _lazy("winzip", "open_winzip"), group="WinZip"),
    Program("claudeamp", "ClaudeAmp", "It really whips the llama's ass", _lazy("amp", "amp_icon"),
            _lazy("amp", "open_amp"), _lazy("amp", "shutdown"), group="ClaudeAmp"),
    Program("tv", "ClaudeTV", "Watch TV", _shared("claudetv.tuner", "tv_icon"), _shared("claudetv.tuner", "open_tv"),
            _shared("claudetv.tuner", "shutdown")),
    # Start > Programs > Furry Stuff: the furry programs and the archive folders on E:
    Program("comix", "FurComix Reader", "Read comics", _shared("comix.reader", "comix_icon"),
            _shared("comix.reader", "open_comix"), group=FURRY),
    Program("folio", "FurFolio Reader", "Browse art portfolios", _shared("folio.gallery", "folio_icon"),
            _shared("folio.gallery", "open_folio"), group=FURRY),
    Program("stories", "FurStory Reader", "Read stories", _shared("folio.stories", "story_icon"),
            _shared("folio.stories", "open_stories"), group=FURRY),
    Program("cdviewer", "Fur CD Viewer", "Browse art CDs and DVDs", _shared("folio.cdviewer", "cd_icon"),
            _shared("folio.cdviewer", "open_cdviewer"), _shared("folio.cdviewer", "shutdown"), group=FURRY),
    Program("furcon", "Furry Con CD Viewer", "Convention recap discs", _shared("folio.furcon", "con_icon"),
            _shared("folio.furcon", "open_furcon"), _shared("folio.furcon", "shutdown"), group=FURRY),
    Program("furdir", "The Fur Directory", "Who's who among the residents", _lazy("furdir", "dir_icon"),
            _lazy("furdir", "open_furdir"), group=FURRY),
    Program("furlog", "Furry Log", "A diary of everything the language model does", _lazy("furrylog", "furlog_icon"),
            _lazy("furrylog", "open_furlog"), group=FURRY),
    Program("furlocator", "Furry Proximity Locator", "A world map with a pin where each Fur Directory resident lives",
            _lazy("furlocator", "locator_icon"), _lazy("furlocator", "open_furlocator"), group=FURRY),
    Program("slstudio", "Furry SL Persona Studio", "Who the residents are in Second Life: their hours, homes, habits "
            "and looks", _shared("opensim_world.studio", "studio_icon"), _shared("opensim_world.studio", "open_studio"),
            group=FURRY),
    Program("furvideo", "Furry Video Browser", "Browse the video archive", _shared("folio.videos", "video_icon"),
            _shared("folio.videos", "open_videos"), _shared("folio.videos", "shutdown"), group=FURRY),
    Program("photos", "Personal Image Gallery", "Browse your own pictures and videos",
            _shared("folio.photos", "photos_icon"), _shared("folio.photos", "open_photos"),
            _shared("folio.photos", "shutdown"), group=FURRY),
    Program("miscfurry", "Misc Furry Image Viewer", "Browse the numbered albums of assorted furry pictures",
            _shared("folio.miscfurry", "misc_icon"), _shared("folio.miscfurry", "open_miscfurry"),
            _shared("folio.miscfurry", "shutdown"), group=FURRY),
    Program("documents", "Personal Document Gallery", "Browse your own texts and documents",
            _shared("folio.documents", "docs_icon"), _shared("folio.documents", "open_documents"),
            _shared("folio.documents", "shutdown"), group=FURRY),
    Program("camroll", "Camera Roll Archive", "Every camera roll photo and video, by year and month",
            _shared("folio.camroll", "camroll_icon"), _shared("folio.camroll", "open_camroll"),
            _shared("folio.camroll", "shutdown"), group=FURRY),
    Program("others", "Other's Files Archive Viewer", "Files saved from other people, by name",
            _shared("folio.others", "others_icon"), _shared("folio.others", "open_others"),
            _shared("folio.others", "shutdown"), group=FURRY),
    Program("stickers", "Sticker Manager", "Give each sticker an emoji and a meaning", _shared("stickers.manager", "stickers_icon"),
            _shared("stickers.manager", "open_stickers"), _shared("stickers.manager", "shutdown"), group=FURRY),
    Program("furcoder", "FurCoder", "Encode and decode Furry Codes and YIFF Codes", _shared("furcoder", "furcoder_icon"),
            _shared("furcoder", "launch"), group=FURRY),
    Program("personaprofiles", "Fur Persona Profiles", "The Contact Persona Styles side by side: residents, prompts, tests",
            _lazy("personaprofiles", "profiles_icon"), _lazy("personaprofiles", "open_profiles"), group=FURRY),
    Program("chatlogs", "Furry Chat Logs", "Years of chat logs by service, account and buddy",
            _shared("chatlogs.viewer", "chat_icon"), _shared("chatlogs.viewer", "open_chatlogs"),
            _shared("chatlogs.viewer", "shutdown"), group=FURRY),
    *[Program(key, label, "", lambda: std_icon(QStyle.SP_DirIcon), _open_folder_shortcut(key),
              group=SHORTCUT_GROUPS.get(key, FURRY)) for key, (label, _prefix) in FOLDER_SHORTCUTS.items()],
    # Start > Programs > Projects: the user's own programs (E:\Projects), and Python Studio's Local Projects
    *[Program(key, name, blurb, _project_icon(key), _project_launch(key), group="Projects")
      for key, (name, blurb, _rel, _how, _llm) in __import__("projects").PROJECTS.items()],
    # Start > Programs > Games: the id/Raven shooters (Doom-engine ones run on PrBoom, Heretic/Hexen on Chocolate)
    *[Program(key, name, blurb, _shared("emulators.emulator", f"{key}_icon"), _shared("emulators.emulator", f"open_{key}"),
              _shared("emulators.emulator", f"shutdown_{key}"), group="Games") for key, name, blurb in DOOM_GAMES],
    Program("rpg", "ClaudeRPG", "A cozy, endless dungeon adventure", _shared("clauderpg", "rpg_icon"),
            _shared("clauderpg", "open_rpg"), _shared("clauderpg", "shutdown"), group="Games"),
    Program("heretic", "Heretic", "Raven's dark fantasy shooter", _shared("doom.native", "heretic_icon"),
            _shared("doom.native", "open_heretic"), _shared("doom.native", "shutdown_heretic"), group="Games"),
    Program("hexen", "Hexen", "Beyond Heretic", _shared("doom.native", "hexen_icon"),
            _shared("doom.native", "open_hexen"), _shared("doom.native", "shutdown_hexen"), group="Games"),
    # Start > Programs > Games > Game Emulation
    *[Program(key, name, blurb, _shared("emulators.emulator", f"{key}_icon"), _shared("emulators.emulator", f"open_{key}"),
              _shared("emulators.emulator", f"shutdown_{key}"), group="Games/Game Emulation") for key, name, blurb in EMULATORS],
    Program("tvguide", "TV Guide", "", _shared("claudetv.tuner", "tv_icon"), _shared("claudetv.guide", "open_guide"), listed=False),
    Program("defrag", "Disk Defragmenter", "", _defrag_icon, _defrag, group="Accessories/System Tools"),
    Program("antivirus", "ClaudeShield AntiVirus", "", _av_icon, _antivirus),
    Program("connect", "Connect to the Internet", "", lambda: QIcon(pixmap("aol_icon.png")), _connect,
            lambda: network.disconnect(quiet=True)),
    Program("dsl", "DSL Broadband", "Always-on, high-speed Internet", lambda: network.dsl_icon(), _connect_dsl,
            lambda: network.disconnect(quiet=True)),
    Program("freecell", "FreeCell", "", _game_icon("card_icon", "H", "#D00000"), _game("freecell", "open_freecell"),
            group="Games/Windows Games"),
    Program("hearts", "Hearts", "", _game_icon("card_icon", "H", "#D00000"), _game("hearts", "open_hearts"),
            group="Games/Windows Games"),
    Program("ibackgammon", "Internet Backgammon", "", _lazy("..games.ibackgammon", "backgammon_icon"),
            _lazy("..games.ibackgammon", "open_internet_backgammon"), group="Games/Windows Games"),
    Program("icheckers", "Internet Checkers", "", _lazy("..games.icheckers", "checkers_icon"),
            _lazy("..games.icheckers", "open_internet_checkers"), group="Games/Windows Games"),
    Program("ihearts", "Internet Hearts", "", _game_icon("card_icon", "H", "#D00000"),
            _lazy("..games.ihearts", "open_internet_hearts"), group="Games/Windows Games"),
    Program("ireversi", "Internet Reversi", "", _lazy("..games.ireversi", "reversi_icon"),
            _lazy("..games.ireversi", "open_internet_reversi"), group="Games/Windows Games"),
    Program("ispades", "Internet Spades", "", _game_icon("card_icon", "S"),
            _lazy("..games.ispades", "open_internet_spades"), group="Games/Windows Games"),
    Program("blockfall", "Blockfall", "Falling blocks", _lazy("..games.blockfall", "blockfall_icon"),
            _game("blockfall", "open_blockfall"), group="Games/Windows Games"),
    Program("golf", "Golf", "Golf solitaire", _lazy("..games.peaks", "golf_icon"), _game("peaks", "open_golf"),
            group="Games/Windows Games"),
    Program("rodent", "Rodent's Revenge", "Trap the cats", _lazy("..games.rodent", "rodent_icon"),
            _game("rodent", "open_rodent"), group="Games/Windows Games"),
    Program("taipei", "Taipei", "Mahjong solitaire", _lazy("..games.taipei", "taipei_icon"),
            _game("taipei", "open_taipei"), group="Games/Windows Games"),
    Program("tripeaks", "TriPeaks", "TriPeaks solitaire", _lazy("..games.peaks", "tripeaks_icon"),
            _game("peaks", "open_tripeaks"), group="Games/Windows Games"),
    Program("jezzball", "JezzBall", "Trap the atoms", _lazy("..games.jezzball", "jezzball_icon"),
            _game("jezzball", "open_jezzball"), group="Games/Windows Games"),
    Program("skifree", "SkiFree", "Ski the endless mountain", _lazy("..games.skifree", "skifree_icon"),
            _game("skifree", "open_skifree"), group="Games/Windows Games"),
    Program("minesweeper", "Minesweeper", "", _game_icon("mine_icon"), _game("minesweeper", "open_minesweeper"),
            group="Games/Windows Games"),
    Program("pinball", "Pinball", "", _lazy("..games.pinball", "pinball_icon"), _lazy("..games.pinball", "open_pinball"),
            group="Games/Windows Games"),
    Program("solitaire", "Solitaire", "", _game_icon("card_icon", "S"), _game("solitaire", "open_solitaire"),
            group="Games/Windows Games"),
    Program("spider", "Spider Solitaire", "", _game_icon("card_icon", "S"), _game("spider", "open_spider"),
            group="Games/Windows Games"),
]


def get(key):
    return next(p for p in PROGRAMS if p.key == key)


MFU_SLOTS = 7
PINNED = ("iexplore",)          # XP's pinned 'Internet' spot
recent = ["aim", "irc", "muck", "claudeai", "connect", "notepad", "mycomputer"]


def launch(desktop, key):
    program = get(key)
    from . import installed
    if installed.is_removed(key):
        from ..explorer.dialogs import msgbox
        msgbox(desktop, program.name, f"{program.name} is not installed.\n\nTo use it again, reinstall it from "
               "Control Panel > Add or Remove Programs > Add New Programs.", "warning")
        return
    installed.record(key)
    if program.listed and key not in PINNED:
        if key in recent:
            recent.remove(key)
        recent.insert(0, key)
        del recent[MFU_SLOTS:]
    program.run(desktop)


def shutdown_all():
    for prog in PROGRAMS:
        if prog.shutdown:
            prog.shutdown()
