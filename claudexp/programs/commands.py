"""What Start > Run and the Command Prompt understand: program names (notepad, calc, winmine...),
folders and files on the virtual drives, and web addresses."""
from pathlib import Path

from .. import programs

# command name -> ClaudeXP program key
NAMES = {
    "notepad": "notepad", "calc": "calc", "cmd": "cmd", "command": "cmd", "taskmgr": "taskmgr",
    "explorer": "mycomputer", "winmine": "minesweeper", "freecell": "freecell", "sol": "solitaire",
    "spider": "spider", "mshearts": "hearts", "dfrg.msc": "defrag", "dfrgntfs": "defrag", "wupdmgr": "winupdate",
    "netscape": "navigator", "claudeaim": "aim", "aim": "aim", "claudeirc": "irc", "mirc32": "irc", "mirc": "irc",
    "bckgzm": "ibackgammon", "hrtzzm": "ihearts", "shvlzm": "ispades", "chkrzm": "icheckers", "rvsezm": "ireversi", "wmplayer": "wmp", "mplayer2": "wmp", "mspaint": "paint", "pbrush": "paint", "claudemuck": "muck", "claudeai": "claudeai", "claudeshield": "antivirus", "isignup": "connect",
}


def _special(name):
    """Control Panel bits that aren't in the program list."""
    from .. import controlpanel
    return {"control": controlpanel.control_panel, "desk.cpl": controlpanel.display_properties,
            "nusrmgr.cpl": controlpanel.user_accounts}.get(name)


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
        return lambda: navigator.launch(desktop, url)
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
