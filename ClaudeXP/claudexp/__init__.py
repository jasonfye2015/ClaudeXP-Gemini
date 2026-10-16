"""ClaudeXP. Importing the package puts claudexp/stubs first on sys.path, so `import ollama` anywhere (ClaudeAIM
included) gets ClaudeXP's own stand-in, backed by the bundled llama.cpp engine (see llm_server.py)."""
import sys
from pathlib import Path

_STUBS = str(Path(__file__).resolve().parent / "stubs")
if _STUBS not in sys.path:
    sys.path.insert(0, _STUBS)
if "ollama" in sys.modules and getattr(sys.modules["ollama"], "__version__", "") != "claudexp":
    del sys.modules["ollama"]          # the real package was imported first somehow: use ours from now on

# 2001 had no dark mode: every web page in ClaudeXP (Kiwix, the Furry Web, Hotmail, LiveJournal) renders in light
# colours even when the real PC is set to dark. Chromium reads this when the web engine first starts.
import os as _os

_LIGHT = "--blink-settings=preferredColorScheme=1"
if _LIGHT not in _os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", ""):
    _os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (_os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "") + " " + _LIGHT).strip()
