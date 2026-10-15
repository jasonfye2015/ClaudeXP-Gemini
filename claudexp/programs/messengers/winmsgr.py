"""Windows Messenger 4.6, the messenger built into Windows XP - and famous for never leaving you alone.

It starts with Windows, sits in the notification area, and every so often pops up 'Click here to sign in'. Your
.NET Passport is your Hotmail address; the buddies are the same people as on MSN Messenger. It can be taken out in
Add or Remove Programs > Add/Remove Windows Components (as people did in 2001), or just told not to start with
Windows from its tray menu.
"""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ...paths import DATA
from ..people import load_json, save_json
from .core import AWAY, BUSY, OFFLINE, ONLINE
from .generic import Theme, make

SETTINGS = DATA / "windows_messenger.json"
NAG_MINUTES = (25, 70)            # how often it reminds you to sign in


def _passport(name):
    from ...life import email_address
    return email_address(name)


WINMSGR = Theme(
    key="winmsgr", title="Windows Messenger", version="4.6.0073", icon="wm_logo",
    status_icons={ONLINE: "msn_online", AWAY: "msn_away", BUSY: "msn_away", OFFLINE: "msn_offline"},
    handle=lambda c, sec: _passport(c.screen_name),
    my_handle=lambda me: _passport(me),
    statuses=[("Online", ONLINE), ("Busy", BUSY), ("Be Right Back", AWAY), ("Away", AWAY), ("On The Phone", BUSY),
              ("Out To Lunch", AWAY), ("Appear Offline", AWAY)],
    groups=[("Online", lambda b: b.presence != OFFLINE), ("Not Online", lambda b: b.presence == OFFLINE)],
    head_top="#FFFFFF", head_bottom="#D6E4F7", head_text="#1C3D7A", accent="#3A6EC8", page="#F3F7FD",
    subtitle=".NET Messenger Service", signin_title="Click here to sign in",
    signin_field=".NET Passport:", signin_button="Sign In",
    buttons=["Invite", "Send Files", "Voice", "Video", "Whiteboard", "Application Sharing"],
    footer=["Add a Contact", "Send a File"],
    me_color="#1C3D7A", them_color="#3A3A3A", line_style="name", main_size=(300, 480),
    message_sound="MSN_Messenger_Notification_Sound.mp3", signin_sound="MSN_Messenger_Notification_Sound.mp3",
    toast=("#FFFFFF", "#D6E4F7", "#3A6EC8", "#1C3D7A"),
)

_launch, _shutdown, winmsgr_icon, client = make(WINMSGR)
_nag = {"timer": None, "tray": None}


def launch(desktop):
    """Open Windows Messenger (its own tray icon replaces the sign-in nag's)."""
    _exit()
    _launch(desktop)


def settings():
    return {"start_with_windows": True, **load_json(SETTINGS, {})}


def _save(key, value):
    s = settings()
    s[key] = value
    save_json(SETTINGS, s)


def start_at_logon(desktop):
    """Windows Messenger starts with Windows, whether you like it or not: a tray icon and a sign-in nag."""
    from .. import installed
    if installed.is_removed("winmsgr") or not settings()["start_with_windows"]:
        return
    c = client(desktop)
    if c.network.signed_in:
        return
    from ...tray import TrayIcon
    if _nag["tray"] is None:
        tray = TrayIcon(desktop, winmsgr_icon(), desktop)
        tray.setToolTip("Windows Messenger - Not Signed In")
        menu = QMenu(desktop)
        menu.addAction("Open", lambda: launch(desktop))
        menu.addAction("Sign In...", lambda: launch(desktop))
        menu.addSeparator()
        start = menu.addAction("Run this program when Windows starts")
        start.setCheckable(True)
        start.setChecked(True)
        start.toggled.connect(lambda on: _save("start_with_windows", on))
        menu.addSeparator()
        menu.addAction("Exit", lambda: _exit())
        tray.setContextMenu(menu)
        tray.activated.connect(lambda r: launch(desktop) if r in (QSystemTrayIcon.Trigger,
                                                                  QSystemTrayIcon.DoubleClick) else None)
        tray.messageClicked.connect(lambda: launch(desktop))
        tray.show()
        _nag["tray"] = tray
    QTimer.singleShot(9000, lambda: _remind(desktop))


def _remind(desktop):
    import random
    tray = _nag["tray"]
    if tray is None:
        return
    c = client(desktop)
    if not c.network.signed_in and desktop.isVisible():
        tray.showMessage("Windows Messenger", "Click here to sign in.", None, 7000)
    t = _nag["timer"]
    if t is None:
        t = _nag["timer"] = QTimer(desktop)
        t.setSingleShot(True)
        t.timeout.connect(lambda: _remind(desktop))
    t.start(int(random.uniform(*NAG_MINUTES) * 60 * 1000))


def _exit():
    if _nag["timer"] is not None:
        _nag["timer"].stop()
    if _nag["tray"] is not None:
        _nag["tray"].hide()
        _nag["tray"].deleteLater()
        _nag["tray"] = None


def shutdown():
    _exit()
    _shutdown()
