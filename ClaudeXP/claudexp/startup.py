"""What starts with Windows, as the System Configuration Utility (msconfig) sees and changes it.

The Startup tab's items are real: an unchecked item isn't started at log on. Of the BOOT.INI switches,
/NOGUIBOOT (no boot logo, just black) and /SOS (driver names on the boot screen) are real; the rest are kept so
the tab looks right. Everything lives in data/msconfig.json.
"""
from .paths import DATA
from .programs.people import load_json, save_json

FILE = DATA / "msconfig.json"
RUN = r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
RUN_USER = r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
COMMON_STARTUP = "Common Startup"

# key: (Startup Item, Command, Location)
ITEMS = {
    "llm": ("llama-server", r'"C:\Program Files\ClaudeXP\LLM\llama-server.exe" --preload', RUN),
    "realsched": ("realsched", r"C:\Program Files\Real\RealPlayer\realplay.exe SYSTEMBOOTHIDEPLAYER", RUN),
    "qttask": ("qttask", r'"C:\Program Files\QuickTime\qttask.exe" -atboottime', RUN),
    "msmsgs": ("msmsgs", r'"C:\Program Files\Messenger\msmsgs.exe" /background', RUN_USER),
    "claudeai": ("ClaudeAI", r'"C:\Program Files\ClaudeAI\ClaudeAI.exe" /tray', RUN_USER),
    "torrent": ("ClaudeTorrent", r'"C:\Program Files\ClaudeTorrent\ClaudeTorrent.exe" /minimized', RUN_USER),
    "widgets": ("Copilot Widgets", r'"C:\Program Files\Copilot\widgets.exe" /startup', RUN_USER),
    "neko": ("Copilot Neko", r"C:\Program Files\Copilot\neko.exe", COMMON_STARTUP),
    "doggo": ("Doggo", r"C:\Program Files\Doggo\doggo.exe", COMMON_STARTUP),
    "deskmario": ("Desktop Mario", r"C:\Program Files\Desktop Mario\deskmario.exe", COMMON_STARTUP),
    "osa": ("Office Startup", r"C:\PROGRA~1\GEMINI~1\Office\OSA.EXE -b -l", COMMON_STARTUP),
}
BOOT_FLAGS = ["SAFEBOOT", "NOGUIBOOT", "BOOTLOG", "BASEVIDEO", "SOS"]
DEFAULTS = {"off": [], "boot": [], "safeboot": "MINIMAL", "timeout": 30, "services_off": [],
            "system_ini": True, "win_ini": True, "nag_off": False}


def load():
    data = dict(DEFAULTS)
    saved = load_json(FILE, {})
    if isinstance(saved, dict):
        data.update(saved)
    return data


def save(data):
    save_json(FILE, data)


def enabled(key):
    """Should this startup item run at log on?"""
    return key not in load()["off"]


def boot_flag(flag):
    return flag in load()["boot"]


def mode(data=None):
    """'normal', 'diagnostic' or 'selective', as the General tab shows it."""
    data = data or load()
    off = set(data["off"])
    if not off and not data["boot"] and not data["services_off"] and data["system_ini"] and data["win_ini"]:
        return "normal"
    if off >= set(ITEMS) and data["services_off"]:
        return "diagnostic"
    return "selective"
