"""One copy at a time, for the programs that run on their own (the launcher's APPS, Kithylin AI): the copy that's
running listens, and a second start - from APPS, a shortcut, anywhere - asks it to come forward (out of the
notification area, or from behind other windows, or minimised) and stops there. The launcher asks the same way
before it starts one, and asks whether one is running before it boots a computer that shares its files.

The listening point is a local socket (a named pipe on Windows) named for the program, this Timeline folder and
this user - so two copies of the Timeline, or two people on one PC, never meet. The tests' scratch data folder
(CLAUDE_STANDALONE_DATA) is part of the name too, so a test never reaches a copy that's really running."""
import getpass
import hashlib
import os
import sys
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
SHOW = b"show\n"


def name(key):
    try:
        user = getpass.getuser()
    except Exception:
        user = ""
    place = os.environ.get("CLAUDE_STANDALONE_DATA") or str(TIMELINE)
    tag = hashlib.sha1(f"{place.lower()}|{user}".encode("utf-8")).hexdigest()[:10]
    return f"claude-timeline-{key}-{tag}"


def _connect(key, timeout):
    from PySide6.QtNetwork import QLocalSocket
    sock = QLocalSocket()
    sock.connectToServer(name(key))
    return sock if sock.waitForConnected(timeout) else None


def running(key, timeout=300):
    """Is a copy of this program running (and listening)?"""
    sock = _connect(key, timeout)
    if sock is None:
        return False
    sock.disconnectFromServer()
    return True


def ask_to_show(key, timeout=600):
    """If a copy of this program is running, ask it to come forward. True if it was there to ask."""
    sock = _connect(key, timeout)
    if sock is None:
        return False
    if sys.platform == "win32":             # (Windows only lets the program in front - this one, the user just
        try:                                # started it - bring another's window forward: it lets it)
            import ctypes
            ctypes.windll.user32.AllowSetForegroundWindow(-1)
        except Exception:
            pass
    sock.write(SHOW)
    sent = sock.waitForBytesWritten(timeout)
    sock.disconnectFromServer()
    return sent


def listen(key, show, parent=None):
    """This copy is the one that runs: listen for later starts, and show() when one asks. Returns the server (keep
    it while the program runs), or None if the name couldn't be taken."""
    from PySide6.QtNetwork import QLocalServer
    server = QLocalServer(parent)
    QLocalServer.removeServer(name(key))     # (one that crashed can leave its name behind - on a Mac)
    if not server.listen(name(key)):
        return None

    def arrived():
        while server.hasPendingConnections():
            conn = server.nextPendingConnection()
            conn.disconnected.connect(conn.deleteLater)

            def read(conn=conn):
                if bytes(conn.readAll()).startswith(SHOW.strip()):
                    show()
            conn.readyRead.connect(read)
            if conn.bytesAvailable():
                read()
    server.newConnection.connect(arrived)
    return server


def come_forward(win, content=None):
    """A window asked for by a second start: out of the notification area (the program's show_again, if it has
    one), up from minimised, and in front."""
    if content is not None and hasattr(content, "show_again"):
        content.show_again()
        return
    win.showNormal() if win.isMinimized() else win.show()
    win.raise_()
    win.activateWindow()
