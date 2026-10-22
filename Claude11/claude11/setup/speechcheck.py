"""The speech licences and the speak-and-listen test from ClaudeXP's Setup, run here as they are: the same file,
loaded under the XP name so its relative imports resolve (its answer is kept in Claude11's own data folder)."""
import importlib.util
import sys

from claude11.paths import XP_ROOT

_NAME = "claudexp.setup.speechcheck"
_SOURCE = XP_ROOT / "claudexp" / "setup" / "speechcheck.py"


def _load():
    existing = sys.modules.get(_NAME)
    if existing is not None and existing is not sys.modules.get(__name__) and getattr(existing, "accepted", None):
        return existing
    spec = importlib.util.spec_from_file_location(_NAME, _SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_NAME] = module
    spec.loader.exec_module(module)
    return module


_mod = _load()
globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})
