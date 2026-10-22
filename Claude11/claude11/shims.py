"""Stand-ins for ClaudeXP modules that have no Windows 11 counterpart, with just the parts the period programs touch:
the XP visual styles (theme/themes: Windows 11's metrics instead), the Contact Persona Styles (ClaudeXP only - here the
residents are always the live code), Clippy (no Office Assistant in 2025), and XP's Log Off box."""
import types

from PySide6.QtCore import QObject, Signal

from . import wm

# ---- theme -------------------------------------------------------------------------------------------------------
MENU_CSS = """
QMenu { background: #F9F9F9; border: 1px solid #E0E0E0; border-radius: 8px; padding: 4px;
        font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 12px; color: #1A1A1A; }
QMenu::item { padding: 6px 28px 6px 12px; border-radius: 4px; margin: 1px 2px; background: transparent; }
QMenu::item:selected { background: #EAEAEA; color: #1A1A1A; }
QMenu::item:disabled { color: #9A9A9A; }
QMenu::separator { height: 1px; background: #E5E5E5; margin: 4px 8px; }
QMenu::icon { padding-left: 8px; }
"""


class _Notifier(QObject):
    changed = Signal()


class _MicaStyle:
    """What theme.current() answers with: Windows 11's frame metrics."""
    key = "mica"
    scheme = "light"
    border = wm.BORDER
    title_h = wm.TITLE_H
    sm_name = "#FFFFFF"
    sm_name_shadow = "#000000"
    sm_text = "#000000"
    sm_sub = "#6D6D6D"
    sm_hover = "#EAEAEA"
    sm_hover_text = "#000000"
    sm_footer_text = "#FFFFFF"

    def palette(self):
        return None

    def menu_css(self):
        return MENU_CSS

    def desktop_color(self):
        return "#000000"


_style = _MicaStyle()
theme = types.ModuleType("claudexp.theme")
theme.notifier = _Notifier()
theme.HACKED = ()
theme.DEFAULT = {"style": "mica", "scheme": "light", "font": "normal", "name": "Windows 11"}
theme.FONT_SIZES = [("normal", "Normal")]
theme.FONT_BUMP = {"normal": 0}
theme.reverted = False
theme.current = lambda: _style
theme.border = lambda: wm.BORDER
theme.title_h = lambda: wm.TITLE_H
theme.state = lambda: dict(theme.DEFAULT)
theme.set_state = lambda **kw: None
theme.make_style = lambda *a, **kw: _style
theme.refresh_window = lambda win: None
theme.shift_color = lambda color, scheme: color
theme.recolored = lambda name, scheme: None

# ---- themes ------------------------------------------------------------------------------------------------------
themes = types.ModuleType("claudexp.themes")
themes.install_files = lambda: None
themes.restore = lambda desktop: None
themes.with_please_wait = lambda desktop, fn: fn()
themes.THEMES = {}
themes.FILE_NAMES = {}
themes._fish = lambda *a, **kw: None

# ---- persona_style: ClaudeXP's frozen Contact Persona Styles don't apply here -----------------------------------
persona_style = types.ModuleType("claudexp.persona_style")
persona_style.DEV = "dev"
persona_style.DEFAULT = "dev"
persona_style.ENV = "CLAUDE_TIMELINE_PERSONA_STYLE"
persona_style.installed = lambda: "dev"
persona_style.frozen = lambda: False
persona_style.uses = lambda feature: True
persona_style.apply = lambda sid=None: []
persona_style.check = lambda sid=None: []
persona_style.restore_generated = lambda: 0
persona_style.name = lambda sid=None: "Development (latest changes)"
persona_style.available = lambda: [{"id": "dev", "name": "Development (latest changes)", "description": ""}]
persona_style.testing = lambda sid: None
persona_style.requested = lambda: None
persona_style.consume_request = lambda: None
persona_style.set_installed = lambda sid: None


# ---- clippy: there's no Office Assistant on Windows 11 -------------------------------------------------------------
class _HiddenWidget:
    """What Neko asks about Clippy: never on screen."""

    def isVisible(self):
        return False

    def geometry(self):
        from PySide6.QtCore import QRect
        return QRect()


class _NoClippy:
    widget = _HiddenWidget()
    balloon = _HiddenWidget()
    mood = "idle"

    def raise_all(self):
        pass

    def start(self):
        pass

    def notify(self, *a, **kw):
        pass


clippy = types.ModuleType("claudexp.clippy")
clippy.notify = lambda *a, **kw: None
clippy.install = lambda desktop: _NoClippy()
clippy.get = lambda: None
clippy.settings = lambda: {}
clippy.art = types.ModuleType("claudexp.clippy.art")
clippy.art.clippy_pixmap = lambda size=32: None
clippy.art.W, clippy.art.H = 124, 93
clippy.program = types.ModuleType("claudexp.clippy.program")
clippy.program.shutdown = lambda: None

# ---- logoff: Windows 11 logs off straight from the Start menu ------------------------------------------------------
logoff = types.ModuleType("claudexp.logoff")


def _ask(desktop):
    from . import sound
    sound.play("menu")
    desktop.hide_start_menu()
    desktop.logoff_requested.emit()


logoff.ask = _ask
