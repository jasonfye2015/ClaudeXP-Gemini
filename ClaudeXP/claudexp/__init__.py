"""ClaudeXP. Importing the package puts the Claude Timeline's ClaudeCore/stubs first on sys.path, so `import ollama`
anywhere (ClaudeAIM included) gets the Timeline's own stand-in, backed by its llama.cpp engine (claudecore/ai)."""
import sys
from pathlib import Path

_STUBS = str(Path(__file__).resolve().parent.parent.parent / "ClaudeCore" / "stubs")
if _STUBS not in sys.path:
    sys.path.insert(0, _STUBS)
if "ollama" in sys.modules and getattr(sys.modules["ollama"], "__version__", "") != "claudecore":
    del sys.modules["ollama"]          # the real package was imported first somehow: use ours from now on

# The Claude Timeline's shared folders (beside ClaudeXP): ClaudeCore, and the programs every era shares.
_TIMELINE = Path(__file__).resolve().parent.parent.parent
for _shared in ("ClaudeCore", "ClaudeGames", "ClaudeArchive", "ClaudeApps"):
    _p = str(_TIMELINE / _shared)
    if (_TIMELINE / _shared).is_dir() and _p not in sys.path:
        sys.path.append(_p)
try:
    from claudecore import host as _host

    def _xp_host():
        from .xphost import XPHost
        return XPHost()
    _host.register_factory(_xp_host)
except ImportError:
    pass                               # no Timeline around this ClaudeXP

# 2001 had no dark mode: every web page in ClaudeXP (Kiwix, the Furry Web, Hotmail, LiveJournal) renders in light
# colours even when the real PC is set to dark. Chromium reads this when the web engine first starts.
import os as _os

_LIGHT = "--blink-settings=preferredColorScheme=1"
if _LIGHT not in _os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", ""):
    _os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (_os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "") + " " + _LIGHT).strip()
