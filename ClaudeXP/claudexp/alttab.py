"""Alt+Tab: XP's task switcher - a box of window icons, the chosen one framed, its title underneath.

The real Windows handles Alt+Tab itself, before any program sees it, so while ClaudeXP is fullscreen and in front a
low-level keyboard hook catches Alt+Tab (and Alt+Shift+Tab, and Esc to cancel) for the XP desktop instead. In a
window, or when ClaudeXP isn't in front, Alt+Tab goes to the real Windows as usual. The hook is only installed while
ClaudeXP is the active program.
"""
import ctypes
import os

if os.name == "nt":                 # Windows' own types: the keyboard hook is Windows-only (a Mac has its own Alt+Tab)
    from ctypes import wintypes
else:
    wintypes = None

from PySide6.QtCore import QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QApplication, QStyle, QWidget

from . import sound

CELL, ICON, COLS = 43, 32, 7


class AltTab(QWidget):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.wins = []
        self.index = 0
        self.hide()

    def _order(self):
        """Most recently used first: the windows on screen top-down, then the minimized ones."""
        d = self.desktop
        shown = [w for w in reversed(d.windows) if w.on_taskbar and w.isVisible()]
        hidden = [w for w in reversed(d.windows) if w.on_taskbar and not w.isVisible()]
        return shown + hidden

    def tab(self, backwards=False):
        if not self.isVisible():
            self.wins = self._order()
            if not self.wins:
                return
            n = len(self.wins)
            self.index = (n - 1 if backwards else 1) % n
            self.desktop.hide_start_menu()
            self._place()
            self.show()
            self.raise_()
        else:
            self.wins = [w for w in self.wins if w in self.desktop.windows]
            if not self.wins:
                self.cancel()
                return
            self.index = (self.index + (-1 if backwards else 1)) % len(self.wins)
        self.update()

    def commit(self):
        if not self.isVisible():
            return
        self.hide()
        if 0 <= self.index < len(self.wins):
            win = self.wins[self.index]
            if win in self.desktop.windows:
                if not win.isVisible():
                    sound.play("restore")
                self.desktop.activate(win)
                self.desktop.taskbar.update()

    def cancel(self):
        self.hide()

    def _place(self):
        n = len(self.wins)
        cols = min(COLS, n)
        rows = (n + COLS - 1) // COLS
        w = max(260, cols * CELL + 28)
        h = rows * CELL + 70
        self.resize(w, h)
        self.move((self.desktop.width() - w) // 2, (self.desktop.height() - h) // 2)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor("#FFFFFF"))
        g.setColorAt(1, QColor("#E4EAF6"))
        p.setPen(QPen(QColor("#3A6EA5"), 2))
        p.setBrush(g)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 6, 6)
        n = len(self.wins)
        cols = min(COLS, n)
        x0 = (w - cols * CELL) // 2
        fallback = QApplication.style().standardIcon(QStyle.SP_DesktopIcon)
        for i, win in enumerate(self.wins):
            r, c = divmod(i, COLS)
            cell = QRect(x0 + c * CELL, 14 + r * CELL, CELL, CELL)
            if i == self.index:
                p.setPen(QPen(QColor("#316AC5"), 2))
                p.setBrush(QColor(49, 106, 197, 40))
                p.drawRoundedRect(QRectF(cell).adjusted(1, 1, -1, -1), 4, 4)
            icon = win.icon if not win.icon.isNull() else fallback
            p.drawPixmap(cell.x() + (CELL - ICON) // 2, cell.y() + (CELL - ICON) // 2, icon.pixmap(ICON, ICON))
        # the chosen window's title in a sunken box
        box = QRect(12, h - 42, w - 24, 26)
        p.setPen(QPen(QColor("#7F9DB9"), 1))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRect(box)
        p.setPen(QColor("#000000"))
        f = QFont("Tahoma", 8, QFont.Bold)
        p.setFont(f)
        title = self.wins[self.index].title if self.wins else ""
        p.drawText(box.adjusted(6, 0, -6, 0), Qt.AlignVCenter | Qt.AlignHCenter,
                   QFontMetrics(f).elidedText(title, Qt.ElideRight, box.width() - 12))
        p.end()


# ---- the keyboard hook (Windows only) ------------------------------------------------------------------------------

WH_KEYBOARD_LL, HC_ACTION = 13, 0
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x100, 0x101, 0x104, 0x105
VK_TAB, VK_SHIFT, VK_ESCAPE, VK_MENU, VK_LMENU, VK_RMENU = 0x09, 0x10, 0x1B, 0x12, 0xA4, 0xA5
LLKHF_ALTDOWN, LLKHF_INJECTED = 0x20, 0x10
VK_MASK = 0xFF                 # a key that does nothing: stops a lone Alt release from opening a menu


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", ctypes.c_uint32), ("scanCode", ctypes.c_uint32), ("flags", ctypes.c_uint32),
                ("time", ctypes.c_uint32), ("dwExtraInfo", ctypes.c_size_t)]       # DWORDs


class KeyHook:
    def __init__(self, main, switcher):
        self.main, self.switcher = main, switcher
        self.hook = None
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        LRESULT = ctypes.c_ssize_t
        self.Proc = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        u = self.user32
        u.SetWindowsHookExW.argtypes = [ctypes.c_int, self.Proc, wintypes.HINSTANCE, wintypes.DWORD]
        u.SetWindowsHookExW.restype = wintypes.HHOOK
        u.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        u.CallNextHookEx.restype = LRESULT
        u.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        u.GetForegroundWindow.restype = wintypes.HWND
        u.GetAsyncKeyState.argtypes = [ctypes.c_int]
        u.GetAsyncKeyState.restype = ctypes.c_short
        u.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_size_t]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        self.module = kernel32.GetModuleHandleW(None)
        self.callback = self.Proc(self._proc)          # kept alive as long as the hook

    def install(self):
        if self.hook is None:
            self.hook = self.user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.callback, self.module, 0)

    def uninstall(self):
        if self.hook:
            self.user32.UnhookWindowsHookEx(self.hook)
        self.hook = None
        self.switcher.cancel()

    def _ours(self):
        """Is the XP desktop fullscreen and in front?"""
        m = self.main
        try:
            if not m.isFullScreen() or m.stack.currentWidget() is not m.desktop:
                return False
            return int(self.user32.GetForegroundWindow() or 0) == int(m.winId())
        except RuntimeError:
            return False

    def _proc(self, code, wparam, lparam):
        try:
            if code == HC_ACTION:
                kb = KBDLLHOOKSTRUCT.from_address(lparam)
                vk, down = kb.vkCode, wparam in (WM_KEYDOWN, WM_SYSKEYDOWN)
                alt = bool(kb.flags & LLKHF_ALTDOWN)
                showing = self.switcher.isVisible()
                if vk == VK_TAB and alt and not kb.flags & LLKHF_INJECTED and (showing or self._ours()):
                    if down:
                        back = bool(self.user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
                        if not showing:
                            self.user32.keybd_event(VK_MASK, 0, 0, 0)
                            self.user32.keybd_event(VK_MASK, 0, 2, 0)
                        QTimer.singleShot(0, lambda: self.switcher.tab(back))
                    return 1
                if showing and vk in (VK_MENU, VK_LMENU, VK_RMENU) and not down:
                    QTimer.singleShot(0, self.switcher.commit)
                elif showing and vk == VK_ESCAPE:
                    if down:
                        QTimer.singleShot(0, self.switcher.cancel)
                    return 1
        except Exception:
            pass
        return self.user32.CallNextHookEx(None, code, wparam, lparam)


def install(main):
    """Give the XP desktop its Alt+Tab (main is ClaudeXP's main window)."""
    switcher = AltTab(main.desktop)
    if os.name != "nt":
        return switcher
    try:
        hook = KeyHook(main, switcher)
    except Exception:
        return switcher
    app = QApplication.instance()

    def state(st):
        if st == Qt.ApplicationActive:
            hook.install()
        else:
            hook.uninstall()
    app.applicationStateChanged.connect(state)
    app.aboutToQuit.connect(hook.uninstall)
    if app.applicationState() == Qt.ApplicationActive:
        hook.install()
    switcher.hook = hook
    return switcher
