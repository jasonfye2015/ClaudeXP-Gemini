"""Light and dark: Windows 11's two modes for the shell (Settings > Personalization > Colors > Choose your mode).

The taskbar, the Start menu, the flyouts, the window frames, the Widgets board, the toasts, Alt+Tab, the menus and
the Settings app ask here for their colours instead of knowing them; the period programs' own windows stay light, as
old programs do on a dark Windows 11, under a dark title bar."""
from PySide6.QtGui import QColor

# what a light-mode colour becomes in dark mode (for the style sheets, which are written in light-mode colours)
QSS_DARK = [("#1A1A1A", "#FFFFFF"), ("#5C5C5C", "#C5C5C5"), ("rgba(0, 0, 0, ", "rgba(255, 255, 255, "),
            ("rgba(255, 255, 255, 220)", "rgba(255, 255, 255, 24)"), ("rgba(255, 255, 255, 235)", "rgba(255, 255, 255, 30)"),
            ("rgba(255, 255, 255, 200)", "rgba(255, 255, 255, 20)"), ("#F9F9F9", "#2C2C2C"), ("#FBFBFB", "#2B2B2B"),
            ("#F6F6F6", "#333333"), ("#F3F3F3", "#202020"), ("#F0F0F0", "#353535"), ("#EAEAEA", "#3F3F3F"),
            ("#E9E9E9", "#3F3F3F"), ("#E5E5E5", "#3A3A3A"), ("#E0E0E0", "#3A3A3A"), ("#D0D0D0", "#4A4A4A"),
            ("#E6F0FB", "#1F3A57"), ("#9A9A9A", "#7A7A7A"), ("#8A8A8A", "#9A9A9A"), ("#767676", "#A0A0A0"),
            ("background: white", "background: #2B2B2B"), ("background: #FFFFFF", "background: #2B2B2B")]


def dark():
    try:
        from . import display
        return display.get().data.get("theme") == "dark"
    except Exception:
        return False


def text():
    return QColor("#FFFFFF") if dark() else QColor("#1A1A1A")


def text2():
    return QColor("#C5C5C5") if dark() else QColor("#5C5C5C")


def hover(alpha):
    """The translucent overlay for hover, selection, hairlines: black on light, white on dark."""
    return QColor(255, 255, 255, alpha) if dark() else QColor(0, 0, 0, alpha)


def field(alpha):
    """A lighter surface on the panel (the search pill, tiles that are off, small buttons)."""
    return QColor(255, 255, 255, max(14, int(alpha * 0.12))) if dark() else QColor(255, 255, 255, alpha)


def card(alpha=255):
    """A card or toast: white in light mode, dark grey in dark."""
    return QColor(43, 43, 43, alpha) if dark() else QColor(255, 255, 255, alpha)


def base():
    """Mica's base colour: the light grey or the near-black."""
    return QColor("#202020") if dark() else QColor("#F3F3F3")


def base_alpha(alpha):
    c = QColor(base())
    c.setAlpha(alpha)
    return c


def qss(css):
    """A style sheet written for light mode, in the current mode."""
    if not dark():
        return css
    for old, new in QSS_DARK:
        css = css.replace(old, new)
    return css


def refresh(desktop):
    """After the mode changed: the menus, every shell surface, every window frame."""
    from . import shims
    if not hasattr(shims, "MENU_CSS_LIGHT"):
        shims.MENU_CSS_LIGHT = shims.MENU_CSS
    shims.MENU_CSS = qss(shims.MENU_CSS_LIGHT)
    try:
        desktop.display._cache.clear()
    except Exception:
        pass
    desktop.update()
    desktop.taskbar.update()
    for f in desktop.taskbar.flyout_widgets():
        f.update()
    desktop.start_menu.place()
    desktop.start_menu.update()
    for w in desktop.windows:
        w.update()
    board = getattr(desktop.widgets, "board", None)
    if board is not None:
        board.update()
        for c in desktop.widgets.live():
            c.update()
