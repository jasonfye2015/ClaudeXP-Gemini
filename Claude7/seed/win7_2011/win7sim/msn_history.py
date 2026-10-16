"""Share histories between native MSN windows without sharing generation channels."""

import weakref
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox


class MSNHistorySession(QObject):
    changed = Signal()
    fields = (
        "_histories_by_profile", "_errors_by_profile", "_blocked_saves_by_profile",
        "_context_by_profile", "_additional_context", "_additional_context_errors",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.maps = None
        self.participants = []

    def attach(self, app):
        if self.maps is None:
            self.maps = {field: getattr(app, field) for field in self.fields}
        else:
            for field, value in self.maps.items():
                setattr(app, field, value)
            app._profile_id = None
            app._sync_profile()
        app.history_session = self
        self.participants.append(weakref.ref(app))
        self.changed.connect(app._refresh_shared_history)

    def other_windows_need_saving(self, current):
        for reference in self.participants:
            participant = reference()
            if participant is None or participant is current:
                continue
            try:
                if participant.client.is_busy or participant._unsaved_conversations:
                    return True
            except RuntimeError:
                continue  # The native widget was destroyed.
        return False


class MSNHistoryParticipant:
    def _refresh_shared_history(self):
        self._render_history()
        self._update_history_status()

    def _notify_history(self):
        session = getattr(self, "history_session", None)
        if session:
            session.changed.emit()

    def _save_history(self, *args, **kwargs):
        super()._save_history(*args, **kwargs)
        self._notify_history()

    def _can_change_saved_history(self):
        session = getattr(self, "history_session", None)
        if session and session.other_windows_need_saving(self):
            QMessageBox.warning(self, "Another conversation needs attention",
                "Wait for other replies to finish and save their messages before changing saved chats.")
            return False
        return True

    def _clear_history(self):
        if self._can_change_saved_history():
            super()._clear_history()
            self._notify_history()

    def _import_history(self):
        if self._can_change_saved_history():
            super()._import_history()
            self._notify_history()

    def _assign_legacy_history(self):
        if self._can_change_saved_history():
            super()._assign_legacy_history()
            self._notify_history()

    def _apply_additional_context(self, *args, **kwargs):
        result = super()._apply_additional_context(*args, **kwargs)
        self._notify_history()
        return result
