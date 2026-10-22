"""Claude7 - SYSTEM-2011, a Windows 7 Home Premium computer from October 2011 in the Claude Timeline.

Importing the package wires the Timeline up: ClaudeCore's stubs (the stand-in `ollama`), the shared program folders
(ClaudeCore, ClaudeGames, ClaudeArchive, ClaudeApps), and ClaudeXP - whose period programs Claude7 runs inside its own
Aero windows through the compatibility layer in xpcompat.py. The host every shared program talks to is host7.py."""
import os
import sys
from pathlib import Path

_TIMELINE = Path(__file__).resolve().parent.parent.parent
_STUBS = str(_TIMELINE / "ClaudeCore" / "stubs")
if _STUBS not in sys.path:
    sys.path.insert(0, _STUBS)
if "ollama" in sys.modules and getattr(sys.modules["ollama"], "__version__", "") != "claudecore":
    del sys.modules["ollama"]

for _shared in ("ClaudeCore", "ClaudeGames", "ClaudeArchive", "ClaudeApps", "ClaudeXP"):
    _p = str(_TIMELINE / _shared)
    if (_TIMELINE / _shared).is_dir() and _p not in sys.path:
        sys.path.append(_p)

from claudecore import host as _host  # noqa: E402


def _host7():
    from .host7 import Host7
    return Host7()


_host.register_factory(_host7)

# Web pages (Hotmail, LiveJournal, Kiwix) render in light colours, as 2011 did, whatever the real PC is set to.
_LIGHT = "--blink-settings=preferredColorScheme=1"
if _LIGHT not in os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", ""):
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "") + " " + _LIGHT).strip()
