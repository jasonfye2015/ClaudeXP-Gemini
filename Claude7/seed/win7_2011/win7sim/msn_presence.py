"""Lightweight MSN presence; timers advance only while the desktop is running."""

import random

from PySide6.QtCore import QObject, QTimer, Signal, QDateTime, QTimeZone

from .contacts import MSN_CONTACTS, SUPPLIED_PROFILES


class MSNPresence(QObject):
    changed = Signal(str, str)
    userChanged = Signal()
    userStatusChanged = Signal(str, str)

    def __init__(self, parent=None, rng=None, preferences=None, service=None):
        super().__init__(parent)
        self.rng = rng or random.Random()
        # Sign-in is always explicit at the start of a desktop session.
        self.user_status = "Offline"
        self.away_message = ""
        self.blocked = set()
        self.preferences = preferences
        self.service = service
        self.chatting = set()
        if preferences:
            self.blocked = set(preferences.data["blocked"])
            self.away_message = preferences.data["away_message"]
            if preferences.data["user_status"] != "Offline" and not preferences.read_only:
                preferences.data["user_status"] = "Offline"
                preferences.save()
        self.states = {}
        self.remaining = {}
        self.timer = QTimer(self)
        self.timer.setInterval(30_000)
        self.timer.timeout.connect(self.advance)
        for contact in MSN_CONTACTS:
            presence = self.metadata(contact.contact_id).get("presence", {})
            state = "Online" if self.rng.random() < presence.get("start_online_chance", .7) else "Offline"
            if self.sleeping(contact.contact_id):
                state = "Offline"
            self.states[contact.contact_id] = state
            self.remaining[contact.contact_id] = self.duration(contact.contact_id, state)
        self.timer.start()

    def metadata(self, contact_id):
        return SUPPLIED_PROFILES.get(contact_id, {}).get("metadata", {})

    def duration(self, contact_id, state):
        key = {"Online": "online_minutes", "Away": "away_minutes", "Offline": "offline_minutes"}.get(state, "online_minutes")
        bounds = self.metadata(contact_id).get("presence", {}).get(key, [10, 40])
        return self.rng.uniform(*bounds) * 60

    def state(self, contact_id):
        return "Blocked" if contact_id in self.blocked else self.states.get(contact_id, "Offline")

    def set_state(self, contact_id, state):
        if state not in ("Online", "Away", "Do not disturb", "Offline"):
            raise ValueError("Unknown MSN presence")
        self.states[contact_id] = state
        self.remaining[contact_id] = self.duration(contact_id, state)
        self.changed.emit(contact_id, self.state(contact_id))

    def set_user_status(self, state, message=""):
        if state not in ("Online", "Away", "Do not disturb", "Offline"):
            raise ValueError("Unknown MSN presence")
        previous_status, previous_message = self.user_status, self.away_message
        self.user_status, self.away_message = state, message
        if self.preferences:
            self.preferences.data.update(user_status=state, away_message=message)
            self.preferences.save()
        self.userChanged.emit()
        if (previous_status, previous_message) != (state, message):
            self.userStatusChanged.emit(previous_status, state)

    def toggle_block(self, contact_id):
        if contact_id in self.blocked:
            self.blocked.remove(contact_id)
        else:
            self.blocked.add(contact_id)
        if self.preferences:
            self.preferences.data["blocked"] = sorted(self.blocked)
            self.preferences.save()
        self.changed.emit(contact_id, self.state(contact_id))

    def advance(self):
        if self.service and self.service.background_work_paused:
            return
        for contact_id in tuple(self.states):
            if contact_id in self.chatting and self.metadata(contact_id).get(
                "presence", {}).get("stay_while_chatting", True):
                continue
            if self.sleeping(contact_id):
                if self.states[contact_id] != "Offline":
                    self.set_state(contact_id, "Offline")
                continue
            self.remaining[contact_id] -= 30
            if self.remaining[contact_id] > 0:
                continue
            state = self.states[contact_id]
            if state == "Offline":
                next_state = "Online"
            elif state == "Away":
                next_state = "Online"
            else:
                chance = self.metadata(contact_id).get("presence", {}).get("away_chance", .2)
                next_state = "Away" if self.rng.random() < chance else "Offline"
            self.set_state(contact_id, next_state)

    def sleeping(self, contact_id):
        metadata = self.metadata(contact_id)
        schedules = metadata.get("presence", {}).get("schedule", {})
        if not schedules:
            return False
        timezone = QTimeZone(metadata.get("timezone", "").encode())
        now = QDateTime.currentDateTime()
        if timezone.isValid():
            now = now.toTimeZone(timezone)
        schedule = schedules.get("weekend" if now.date().dayOfWeek() >= 6 else "weekday", {})
        if "wake" not in schedule or "sleep" not in schedule:
            return False
        def minutes(value):
            hour, minute = map(int, value.split(":"))
            return hour * 60 + minute
        wake = sum(map(minutes, schedule["wake"])) / 2
        sleep = sum(map(minutes, schedule["sleep"])) / 2
        current = now.time().hour() * 60 + now.time().minute()
        if sleep >= 1440:
            return sleep - 1440 <= current < wake
        return current < wake or current >= sleep

    def stop(self):
        self.timer.stop()
