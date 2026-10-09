"""The channel lineup, shared by the tuner and the TV Guide. Scanning the archive happens once, off the UI thread."""
import threading

from PySide6.QtCore import QObject, Signal

from . import library, schedule

_state = {"channels": None, "loading": False, "waiting": []}


class _Notifier(QObject):
    done = Signal(object)


_notifier = None


def base():
    from ...explorer.vfs import local_storage
    return local_storage()


def get(callback):
    """callback(channels) now if the lineup is ready, otherwise once the archive has been scanned."""
    global _notifier
    if _state["channels"] is not None:
        callback(_state["channels"])
        return
    _state["waiting"].append(callback)
    if _state["loading"]:
        return
    _state["loading"] = True
    if _notifier is None:
        _notifier = _Notifier()
        _notifier.done.connect(_finished)

    def work():
        try:
            items = library.scan(base())
        except Exception:                # an unreadable archive just means nothing is on
            items = []
        _notifier.done.emit(schedule.build_channels(items))
    threading.Thread(target=work, name="tv-scan", daemon=True).start()


def _finished(channels):
    _state["channels"], _state["loading"] = channels, False
    waiting, _state["waiting"] = _state["waiting"], []
    for cb in waiting:
        try:
            cb(channels)
        except RuntimeError:             # that window was closed while we scanned
            pass


def ready():
    return _state["channels"]


def rescan(callback):
    _state["channels"] = None
    get(callback)
