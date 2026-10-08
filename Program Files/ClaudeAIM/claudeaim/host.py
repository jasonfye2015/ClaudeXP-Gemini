"""Lets ClaudeAIM run inside a host desktop (ClaudeXP) instead of as real windows.

ClaudeXP calls install() with its host object before starting ClaudeAIM. Without a
host, every function here falls back to plain Qt behaviour, so ClaudeAIM still runs
on its own.
"""
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

_host = None


def install(host):
    global _host
    _host = host


def hosted():
    return _host is not None


class HostedWindow:
    """Mixin for top-level windows: inside a host, the first show() moves the window onto its desktop."""

    def setVisible(self, visible):
        if visible and _host is not None and self.isWindow():
            _host.adopt(self)
        super().setVisible(visible)


def available_geometry(widget):
    """The area windows can use: the host's desktop, or the real screen."""
    if _host:
        return _host.work_area()
    return widget.screen().availableGeometry()


def present(widget):
    """Show a window, un-minimize it, and bring it to the front."""
    widget.show()
    if _host:
        _host.activate(widget)
        return
    if widget.isMinimized():
        widget.showNormal()
    widget.raise_()
    widget.activateWindow()


def is_active(widget):
    """True if the user is looking at this window right now."""
    if _host:
        return _host.is_active(widget)
    return widget.isVisible() and widget.isActiveWindow() and not widget.isMinimized()


def alert(widget):
    """Flash the window's taskbar button."""
    if _host:
        _host.alert(widget)
    else:
        QApplication.alert(widget)


def user_closed(widget, event):
    """True if a close came from the user clicking the window's X."""
    return event.spontaneous() or getattr(widget, "_host_user_close", False)


def muted():
    return bool(_host and _host.muted())


def tray_available():
    return True if _host else QSystemTrayIcon.isSystemTrayAvailable()


def tray_icon(icon, parent):
    """A tray icon with the QSystemTrayIcon interface: the host's tray, or the real one."""
    return _host.tray_icon(icon, parent) if _host else QSystemTrayIcon(icon, parent)


def hide_all_windows():
    if _host:
        _host.hide_all()
    else:
        for w in QApplication.topLevelWidgets():
            w.hide()


def exit_app():
    """Leave ClaudeAIM: close the program inside the host, or quit the real app."""
    if _host:
        _host.app_exited()
    else:
        # exit() rather than quit(): Qt 6's quit() first asks every window to close.
        QApplication.instance().exit(0)


def restart_app():
    """Start ClaudeAIM over (after Reset All). Returns False if the caller should do it itself."""
    if _host:
        _host.app_restart()
        return True
    return False


# ----- message boxes ---------------------------------------------------------------

class MessageBox(HostedWindow, QMessageBox):
    pass


def _box(icon, parent, title, text, buttons, default):
    box = MessageBox(icon, title, text, buttons, parent)
    if default != QMessageBox.NoButton:
        box.setDefaultButton(default)
    box.exec()
    answer = box.standardButton(box.clickedButton())
    box.deleteLater()
    return answer


def information(parent, title, text, buttons=QMessageBox.Ok, default=QMessageBox.NoButton):
    return _box(QMessageBox.Information, parent, title, text, buttons, default)


def warning(parent, title, text, buttons=QMessageBox.Ok, default=QMessageBox.NoButton):
    return _box(QMessageBox.Warning, parent, title, text, buttons, default)
