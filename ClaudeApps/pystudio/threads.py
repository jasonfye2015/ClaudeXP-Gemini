"""Background threads that can't take the program down with them.

A QThread let go of while it still runs aborts the whole program ("QThread: Destroyed while thread is still
running") - the AI Helper's window closed mid-answer, say, with the model still reading the prompt. Kept threads are
held here from start until they've really finished, whoever lets go of them first."""
from PySide6.QtCore import QThread

_running = set()


class Kept(QThread):
    def start(self, *args):
        _running.add(self)
        self.finished.connect(self._release)
        super().start(*args)

    def _release(self):
        _running.discard(self)
