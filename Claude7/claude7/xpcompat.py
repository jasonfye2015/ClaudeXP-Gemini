"""The compatibility layer: ClaudeXP's period programs, run inside Claude7.

ClaudeXP's code and artwork stay in ClaudeXP/. What changes is what sits around it:
  - claudexp.paths.DATA points at Claude7/data before any XP module reads it, so everything the programs save
    (journals, mail, settings, drive C:) lands on this computer.
  - the modules that are Windows itself are swapped for Claude7's - sound, clock, wm (XPWindow -> AeroWindow),
    user, network, tray, display, volume, the visual styles, the dialogs, the drive (vfs), Setup, the Control
    Panel, the desktop icons: sys.modules carries Claude7's module under the XP name, so a program's
    `from ..wm import XPWindow` finds glass.
  - ClaudeAIM (XP's program) reads this computer's contacts and chats (Claude7/Program Files/ClaudeAIM), in 2011.
  - the Program Files constants (where the IRC and MUCK regulars, the Fur Directory's cards and the browsers' data
    live) are redirected to Claude7/Program Files as each module loads (an import hook).
  - '2001' becomes '2011' in the prompt constants the programs feed the language model.
"""
import importlib.abc
import importlib.machinery
import sys
import types

from . import paths

XP_PROGRAM_FILES = paths.XP_ROOT / "Program Files"
PF = paths.PROGRAM_FILES
YEAR_SWAPS = (("2001", "2011"), ("Windows XP", "Windows 7"))
_installed = False
_years_done = set()
_aliases = {}


# ---- the Program Files redirections --------------------------------------------------------------------------------
def _patch_furdir(m):
    m.DIR = PF / "The Fur Directory"
    m.RECORDS = m.DIR / "residents"
    m.AIM_DIR = PF / "ClaudeAIM"
    m.IRC_DIR = PF / "ClaudeIRC"
    m.MUCK_DIR = PF / "ClaudeMUCK" / "world"
    m.JOURNALS = paths.DATA / "journals"
    m.DISCLAIMER = m.DISCLAIMER.replace("ClaudeXP", "Claude7")


def _patch_furnet(m):
    m.IRC_DIR = PF / "ClaudeIRC"
    m.DATA_DIR = m.IRC_DIR / "data"
    m.QUERY_DIR = m.DATA_DIR / "queries"


def _patch_muck(m):
    m.MUCK_DIR = PF / "ClaudeMUCK"
    m.WORLD_DIR = m.MUCK_DIR / "world"
    m.DATA_DIR = m.MUCK_DIR / "data"
    m.PLAYER_FILE = m.DATA_DIR / "player.json"
    m.DESCS_FILE = m.DATA_DIR / "descriptions.json"


def _patch_web(m):
    m.ROOT = paths.ROOT                          # the regulars it reads at call time come from this computer
    m.DATA_DIR = PF / "Netscape" / "data"        # (sites.json stays with the program, in ClaudeXP)
    m.CACHE_DIR = m.DATA_DIR / "cache"
    from . import web2011
    web2011.patch_web(m)


def _patch_hotmail(m):
    from . import web2011
    web2011.patch_hotmail(m)


def _patch_mailtray(m):
    m.MAIL_NAME = "Windows Live Hotmail"


def _patch_antivirus(m):
    m.NAME = "ClaudeShield AntiVirus 2012"                      # (XP's is "ClaudeShield AntiVirus 2002")


def _patch_furaffinity(m):
    from . import web2011
    web2011.patch_furaffinity(m)


def _patch_iexplore(m):
    m.FAVORITES_FILE = PF / "Internet Explorer" / "favorites.json"
    from . import xpfaces
    xpfaces.patch_iexplore_favorites(m)


def _patch_msn(m):
    from .programs import wlm
    wlm.install(m)


def _patch_others(m):
    from . import xpfaces
    xpfaces.patch_messengers(m)


def _patch_yim(m):
    from . import xpfaces
    xpfaces.patch_yim(m)


def _patch_outlook(m):
    from . import xpfaces
    xpfaces.patch_outlook(m)


def _patch_lj(m):
    from . import xpfaces
    xpfaces.patch_lj(m)


def _patch_sites(m):
    from . import xpfaces
    xpfaces.patch_sites(m)


def _patch_llm_loading(m):
    from . import xpfaces
    xpfaces.patch_llm_loading(m)


def _patch_secondlife(m):
    m.FURDIR = PF / "The Fur Directory" / "residents"
    m.AIM_DIR = PF / "ClaudeAIM"


def _patch_messengers_core(m):
    import json

    def codes_for(b):
        try:
            rec = json.loads((PF / "The Fur Directory" / "residents" / f"{b.contact.id}.json")
                             .read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        c = rec.get("codes") or {}
        return {"furcode": c.get("furcode", ""), "yiffcode": c.get("yiffcode", "") if c.get("yiff_public") else ""}
    m.codes_for = codes_for


def _patch_mail_extras(m):
    from . import xpfaces
    xpfaces.patch_mail_extras(m)


def _patch_life(m):
    """The life simulation's cast: the regulars from this computer's Program Files."""
    from claudexp.programs.people import load_json
    Person, minutes = m.Person, m._minutes

    def people(self):
        if self._people is None:
            people = {name: Person(name, c.persona, None, c) for name, c in self.buddies.items()}
            for path, key in ((PF / "ClaudeIRC" / "regulars.json", "nick"),
                              (PF / "ClaudeMUCK" / "world" / "regulars.json", "name")):
                for r in load_json(path, {}).get("regulars", []):
                    name = r.get(key)
                    if not name or not r.get("persona") or name in people:
                        continue
                    hours = r.get("hours") or []
                    span = tuple(minutes(h) for h in hours[:2]) if len(hours) >= 2 else None
                    people[name] = Person(name, r["persona"], span if span and None not in span else None, None)
            self._people = people
        return self._people
    m.LifeSim.people = property(people)


PATCHES = {
    "claudexp.programs.furdir": _patch_furdir,
    "claudexp.programs.irc.furnet": _patch_furnet,
    "claudexp.programs.muck.world": _patch_muck,
    "claudexp.programs.navigator.web": _patch_web,
    "claudexp.programs.navigator.iexplore": _patch_iexplore,
    "claudexp.programs.navigator.sites": _patch_sites,
    "claudexp.programs.navigator.sites.hotmail": _patch_hotmail,
    "claudexp.mailtray": _patch_mailtray,
    "claudexp.maintenance.antivirus": _patch_antivirus,
    "claudexp.programs.messengers.msn": _patch_msn,
    "claudexp.programs.messengers.others": _patch_others,
    "claudexp.programs.messengers.yim": _patch_yim,
    "claudexp.programs.outlook": _patch_outlook,
    "claudexp.life.lj": _patch_lj,
    "claudexp.llm_loading": _patch_llm_loading,
    "claudexp.programs.navigator.sites.furaffinity": _patch_furaffinity,
    "claudexp.programs.secondlife.residents": _patch_secondlife,
    "claudexp.programs.messengers.core": _patch_messengers_core,
    "claudexp.life": _patch_life,
    "claudexp.life.mail_extras": _patch_mail_extras,
}


class _PatchingLoader(importlib.abc.Loader):
    """Runs the module as usual, then Claude7's patch for it."""

    def __init__(self, inner, patch):
        self.inner, self.patch = inner, patch

    def create_module(self, spec):
        return self.inner.create_module(spec) if hasattr(self.inner, "create_module") else None

    def exec_module(self, module):
        self.inner.exec_module(module)
        if self.patch is not None:
            try:
                self.patch(module)
            except Exception as exc:                # a patch that no longer fits the XP code: say so, carry on
                if sys.stderr is not None:
                    sys.stderr.write(f"Claude7: could not patch {module.__name__}: {exc}\n")
        patch_years(module)

    def __getattr__(self, name):                    # get_filename, is_package, get_source... from the real loader
        return getattr(self.inner, name)


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith("claudexp."):
            return None
        patch = PATCHES.get(fullname)
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.loader is None:
            return None
        spec.loader = _PatchingLoader(spec.loader, patch)
        return spec


# ---- '2001' -> '2011' ----------------------------------------------------------------------------------------------
def _swap(value):
    if isinstance(value, str):
        out = value
        for old, new in YEAR_SWAPS:
            out = out.replace(old, new)
        return out
    if isinstance(value, (list, tuple)) and value and all(isinstance(v, str) for v in value):
        return type(value)(_swap(v) for v in value)
    if isinstance(value, dict) and value and all(isinstance(v, str) for v in value.values()):
        return {k: _swap(v) for k, v in value.items()}
    return value


def patch_years(module=None):
    """Swap the years in the UPPERCASE string constants of every loaded XP module (the prompts the programs feed the
    language model, the dates and the names they show). Each module is done once."""
    if module is not None:
        mods = [module]
    else:
        mods = [m for n, m in list(sys.modules.items())
                if n.startswith("claudexp.") and isinstance(m, types.ModuleType) and n not in _years_done]
    for m in mods:
        if m.__name__ in _years_done or m.__name__.startswith("claude7"):
            continue
        _years_done.add(m.__name__)
        for key, value in list(vars(m).items()):
            if key.startswith("_") or not key.isupper():
                continue
            new = _swap(value)
            if new is not value and new != value:
                setattr(m, key, new)
    _fix_parent_attrs()


def _fix_parent_attrs():
    """Make sure each alias is also an attribute of its parent package (for `from . import vfs`)."""
    for name, module in _aliases.items():
        parent, _, child = name.rpartition(".")
        pkg = sys.modules.get(parent)
        if pkg is not None and getattr(pkg, child, None) is not module:
            try:
                setattr(pkg, child, module)
            except Exception:
                pass


def _alias(name, module):
    _aliases[name] = module
    sys.modules[name] = module
    parent, _, child = name.rpartition(".")
    if parent in sys.modules:
        setattr(sys.modules[parent], child, module)


# ---- installing ----------------------------------------------------------------------------------------------------
def install():
    global _installed
    if _installed:
        return
    _installed = True
    import claudexp                                            # noqa: F401  (registers XP's host: ours goes back)
    from claudecore import host
    from . import _host7
    host.register_factory(_host7)
    import claudexp.paths as xp_paths
    xp_paths.DATA = paths.DATA
    # ClaudeAIM: XP's program, with this computer's contacts and chats, in 2011
    aim_dir = str(XP_PROGRAM_FILES / "ClaudeAIM")
    if aim_dir not in sys.path:
        sys.path.insert(0, aim_dir)
    from claudeaim import paths as aim_paths, timefmt
    aim_paths.CONTACTS = PF / "ClaudeAIM" / "contacts"
    aim_paths.DATA = PF / "ClaudeAIM" / "data"
    aim_paths.HISTORY = aim_paths.DATA / "history"
    timefmt.YEAR = 2011
    # Claude7's modules under ClaudeXP's names
    from . import (clock, desktop, dialogs, display, icons, network, placeholder, setup, shims, sound, startmenu,
                   taskbar, tray, user, vfs, volume, wm)
    from . import controlpanel
    for name, module in {
        "claudexp.sound": sound, "claudexp.clock": clock, "claudexp.wm": wm, "claudexp.user": user,
        "claudexp.network": network, "claudexp.tray": tray, "claudexp.display": display, "claudexp.volume": volume,
        "claudexp.theme": shims.theme, "claudexp.themes": shims.themes, "claudexp.persona_style": shims.persona_style,
        "claudexp.clippy": shims.clippy, "claudexp.clippy.art": shims.clippy.art,
        "claudexp.clippy.program": shims.clippy.program, "claudexp.logoff": shims.logoff,
        "claudexp.controlpanel": controlpanel, "claudexp.setup": setup, "claudexp.desktop_icons": icons,
        "claudexp.taskbar": taskbar, "claudexp.startmenu": startmenu, "claudexp.desktop": desktop,
        "claudexp.explorer.vfs": vfs, "claudexp.explorer.dialogs": dialogs,
        "claudexp.programs.placeholder": placeholder,
    }.items():
        _alias(name, module)
    if not any(isinstance(f, _Finder) for f in sys.meta_path):
        sys.meta_path.insert(0, _Finder())
    patch_years()


def program_files_ready():
    """Claude7's Program Files folders, so the programs find somewhere to save even before the residents sync."""
    import shutil
    for sub in ("ClaudeAIM/contacts", "ClaudeAIM/data/history", "ClaudeIRC/data", "ClaudeMUCK/world",
                "ClaudeMUCK/data", "The Fur Directory/residents", "Netscape/data/cache", "Internet Explorer"):
        (PF / sub).mkdir(parents=True, exist_ok=True)
    for name, text in (("ClaudeIRC/regulars.json", '{"regulars": []}\n'),
                       ("ClaudeMUCK/world/regulars.json", '{"regulars": []}\n')):
        path = PF / name
        if not path.exists():
            path.write_text(text, encoding="utf-8")
    # the IRC network and the MUCK map are part of the programs: copied from XP once
    for rel in ("ClaudeIRC/network.json", "ClaudeMUCK/world/map.json", "ClaudeIRC/data/settings.json",
                "The Fur Directory/README.txt"):
        src, dst = XP_PROGRAM_FILES / rel, PF / rel
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
