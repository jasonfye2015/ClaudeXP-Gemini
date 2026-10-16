"""What Start > Run and the Command Prompt understand: program names (notepad, calc, winmine...),
folders and files on the virtual drives, and web addresses."""
from pathlib import Path

from .. import programs

# command name -> ClaudeXP program key
NAMES = {
    "notepad": "notepad", "calc": "calc", "cmd": "cmd", "command": "cmd", "taskmgr": "taskmgr",
    "explorer": "mycomputer", "winmine": "minesweeper", "freecell": "freecell", "sol": "solitaire",
    "spider": "spider", "mshearts": "hearts", "dfrg.msc": "defrag", "dfrgntfs": "defrag", "wupdmgr": "winupdate",
    "netscape": "navigator", "iexplore": "iexplore", "claudeaim": "aim", "aim": "aim", "claudeirc": "irc", "mirc32": "irc", "mirc": "irc",
    "claudemuck": "muck", "claudeai": "claudeai", "claudeshield": "antivirus", "msmsgs": "winmsgr", "realplay": "realplayer", "kiwix": "kiwix", "claudecraft": "claudecraft", "minecraft": "claudecraft", "claudecadia": "furcadia", "claudequest": "claudequest", "claudeablo": "claudeablo", "claudecity": "claudecity", "simcity": "claudecity", "scorched": "scorched", "scorch": "scorched", "scorchedearth": "scorched", "diablo": "claudeablo", "wolfquest": "claudequest", "furcadia": "furcadia", "furc": "furcadia", "kiwix-desktop": "kiwix", "quicktimeplayer": "quicktime", "moviemk": "moviemaker", "msoobe": "activate", "appwiz.cpl": "arp", "ad-aware": "adaware", "adaware": "adaware", "isignup": "connect",
    "mspaint": "paint", "pbrush": "paint", "wordpad": "wordpad", "write": "wordpad",
    "charmap": "charmap", "cleanmgr": "cleanmgr", "msinfo32": "msinfo", "sndrec32": "sndrec", "sndvol32": "sndvol", "sndvol": "sndvol", "rstrui": "sysrestore", "msconfig": "msconfig", "helpctr": "helpctr",
    "tourstart": "tour", "claudetv": "tv", "furtv": "tv", "furcomix": "comix", "furfolio": "folio", "furstory": "stories", "furcd": "cdviewer", "furcon": "furcon", "furvideo": "furvideo", "stylexp": "stylexp", "claudetorrent": "torrent", "furdir": "furdir", "clauderpg": "rpg", "bittorrent": "torrent", "flashpla": "flash", "flash": "flash", "claudeamp": "claudeamp", "winamp": "claudeamp", "fceu": "nes", "fceultra": "nes", "snes9x": "snes", "gambatte": "gb",
    "gambatte_gbc": "gbc", "mgba": "gba", "picodrive": "gen", "gpgx": "sms", "gearsystem": "gg", "applewin": "apple2", "mupen64plus": "n64", "project64": "n64", "msnmsgr": "msn", "msmsgs": "msn",
    "ypager": "yim", "yahoomessenger": "yim", "icq": "icq", "trillian": "trillian", "skype": "skype", "kik": "kik",
    "doom": "doom", "doom2": "doom2", "wolf3d": "wolf3d", "heretic": "heretic", "hexen": "hexen",
    "ski": "skifree", "skifree": "skifree", "jezzball": "jezzball",
    "taipei": "taipei", "rodent": "rodent", "blockfall": "blockfall", "tripeaks": "tripeaks", "golf": "golf", "tvguide": "tvguide",
    "clippy": "clippy", "clippit": "clippy",
    "pinball": "pinball", "wmplayer": "wmp", "mplayer2": "wmp", "msimn": "outlook", "wab": "wab",
    "bckgzm": "ibackgammon", "hrtzzm": "ihearts", "shvlzm": "ispades", "chkrzm": "icheckers", "rvsezm": "ireversi",
}


def _special(name):
    """Control Panel bits that aren't in the program list."""
    from .. import controlpanel
    return {"control": controlpanel.control_panel, "desk.cpl": controlpanel.display_properties,
            "nusrmgr.cpl": controlpanel.user_accounts, "aimodels.cpl": controlpanel._ai_models}.get(name)


def resolve(desktop, text, cwd=None):
    """Return a function that opens what `text` names, or None if Windows 'cannot find' it."""
    from ..explorer import vfs
    text = text.strip().strip('"')
    if not text:
        return None
    low = text.lower()
    if low.startswith(("http://", "https://", "www.")):
        from . import navigator
        url = text if "://" in text else "http://" + text
        return lambda: navigator.open_url(desktop, url)
    name = low[:-4] if low.endswith(".exe") else low
    if name == "explorer":
        from .taskmgr import explorer_running, start_explorer
        if not explorer_running(desktop):
            return lambda: start_explorer(desktop)       # after Task Manager ended explorer.exe
    if name in NAMES and any(p.key == NAMES[name] for p in programs.PROGRAMS):
        return lambda: programs.launch(desktop, NAMES[name])
    special = _special(name)
    if special:
        return lambda: special(desktop)
    # a path: absolute (C:\...) or relative to the Command Prompt's folder
    real = vfs.to_real(text) if len(text) >= 2 and text[1] == ":" else (Path(cwd) / text if cwd else None)
    if real is not None and real.exists():
        from .. import explorer
        from ..explorer.viewers import open_file
        if real.is_dir():
            return lambda: explorer.launch(desktop, real)
        return lambda: open_file(desktop, real)
    return None
