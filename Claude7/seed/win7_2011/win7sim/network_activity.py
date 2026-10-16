"""Visual simulation of packet activity over a representative 2011 DSL line."""

from __future__ import annotations

import time

from PySide6.QtCore import QPoint, QSize, QTimer, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QToolButton


class DSLNetworkTrayButton(QToolButton):
    """Taskbar indicator for simulated uploads and downloads; never throttles work."""

    DOWNLOAD_BITS_PER_SECOND = 3_000_000
    UPLOAD_BITS_PER_SECOND = 512_000
    MIN_VISIBLE_TRANSFER_SECONDS = 0.18
    BLINK_INTERVAL_MS = 120

    _DIRECTION_LABELS = {
        "outgoing": "Sending",
        "incoming": "Receiving",
    }
    _DIRECTION_COLORS = {
        "outgoing": "#3bd16b",
        "incoming": "#f04a4a",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("networkActivityTray")
        self.setAccessibleName("Simulated DSL network activity")
        self.setFixedSize(32, 30)
        self.setIconSize(QSize(26, 26))
        self._connection_state = "connected"
        self._events = []
        self._direction_end = {"outgoing": 0.0, "incoming": 0.0}
        self._blink_on = True
        self._last_transfer = None

        self.activity_timer = QTimer(self)
        self.activity_timer.setInterval(self.BLINK_INTERVAL_MS)
        self.activity_timer.timeout.connect(self._tick)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._refresh()

    @staticmethod
    def _state_name(state):
        return getattr(state, "value", state)

    @property
    def connected(self):
        return self._connection_state in ("connected", "slowdown")

    def set_connection_state(self, state, _status_text=""):
        self._connection_state = self._state_name(state)
        if not self.connected:
            self._events.clear()
            self._direction_end = {"outgoing": 0.0, "incoming": 0.0}
            self.activity_timer.stop()
            self._blink_on = False
        self._refresh()

    def effective_rate(self, direction):
        if direction not in self._DIRECTION_LABELS:
            raise ValueError("Network transfer direction must be outgoing or incoming.")
        base = (
            self.UPLOAD_BITS_PER_SECOND
            if direction == "outgoing"
            else self.DOWNLOAD_BITS_PER_SECOND
        )
        return base // 2 if self._connection_state == "slowdown" else base

    def estimated_transfer_seconds(self, direction, payload_bytes):
        if payload_bytes < 0:
            raise ValueError("Transfer size cannot be negative.")
        return payload_bytes * 8 / self.effective_rate(direction)

    def report_transfer(self, direction, payload_bytes, description=""):
        """Show a transfer at DSL speed; return its estimated payload time in seconds."""
        duration = self.estimated_transfer_seconds(direction, payload_bytes)
        if payload_bytes == 0 or not self.connected:
            return duration

        now = time.monotonic()
        visible_duration = max(duration, self.MIN_VISIBLE_TRANSFER_SECONDS)
        start = max(now, self._direction_end[direction])
        end = start + visible_duration
        event = {
            "direction": direction,
            "bytes": int(payload_bytes),
            "description": str(description or "Network data"),
            "duration": duration,
            "start": start,
            "end": end,
            "rate": self.effective_rate(direction),
        }
        self._events.append(event)
        self._direction_end[direction] = end
        self._last_transfer = event
        self._blink_on = True
        if not self.activity_timer.isActive():
            self.activity_timer.start()
        self._refresh()
        return duration

    def _tick(self):
        now = time.monotonic()
        self._events = [event for event in self._events if event["end"] > now]
        if not self._events:
            self.activity_timer.stop()
            self._blink_on = False
        else:
            self._blink_on = not self._blink_on
        self._refresh()

    def stop_activity(self):
        self._events.clear()
        self._direction_end = {"outgoing": 0.0, "incoming": 0.0}
        self.activity_timer.stop()
        self._blink_on = False
        self._refresh()

    @staticmethod
    def _format_rate(bits_per_second):
        if bits_per_second >= 1_000_000:
            return f"{bits_per_second / 1_000_000:g} Mbps"
        return f"{bits_per_second / 1_000:g} kbps"

    @staticmethod
    def _format_size(byte_count):
        if byte_count >= 1024:
            return f"{byte_count / 1024:.1f} KiB"
        return f"{byte_count} bytes"

    def _refresh(self):
        pixmap = QPixmap(26, 26)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QPen(QColor("#263a48"), 1.2))
        painter.setBrush(QColor("#536b7b"))
        painter.drawRoundedRect(3, 3, 20, 16, 2, 2)
        painter.setBrush(QColor("#b9d2e1"))
        painter.drawRoundedRect(5, 5, 16, 12, 1, 1)
        painter.setBrush(QColor("#536b7b"))
        painter.drawRect(10, 19, 6, 3)
        painter.drawRoundedRect(7, 22, 12, 2, 1, 1)

        active_directions = set()
        now = time.monotonic()
        if self._blink_on:
            active_directions = {
                event["direction"] for event in self._events
                if event["start"] <= now < event["end"]
            }
        for direction, x, points in (
            ("outgoing", 9, (QPoint(9, 14), QPoint(9, 7), QPoint(6, 10), QPoint(9, 7), QPoint(12, 10))),
            ("incoming", 17, (QPoint(17, 7), QPoint(17, 14), QPoint(14, 11), QPoint(17, 14), QPoint(20, 11))),
        ):
            active = direction in active_directions and self.connected
            color = QColor(self._DIRECTION_COLORS[direction] if active else "#647580")
            painter.setPen(QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(points[0], points[1])
            painter.drawLine(points[1], points[2])
            painter.drawLine(points[1], points[3])
            painter.drawLine(points[3], points[4])

        if not self.connected:
            painter.setPen(QPen(QColor("#d32929"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(4, 4, 22, 20)
            painter.drawLine(22, 4, 4, 20)
        painter.end()
        self.setIcon(QIcon(pixmap))

        down_rate = self.effective_rate("incoming")
        up_rate = self.effective_rate("outgoing")
        status = {
            "connected": "Connected",
            "slowdown": "Slow response — reduced simulated speed",
            "disconnected": "Disconnected",
            "maintenance": "Service maintenance",
        }.get(self._connection_state, "Connection status unknown")
        tooltip = (
            f"Simulated 2011 DSL — {status}\n"
            f"Download: {self._format_rate(down_rate)} · "
            f"Upload: {self._format_rate(up_rate)}\n"
            "Green = sending · Red = receiving.\n"
            "Transfer estimates affect this indicator only; they do not delay the app."
        )
        if self._events:
            active = [event for event in self._events if event["start"] <= now < event["end"]]
            queued = [event for event in self._events if event["start"] > now]
            event = active[0] if active else self._events[0]

            def event_summary(item, prefix):
                estimate_ms = item["duration"] * 1000
                rate = self._format_rate(item["rate"])
                return (
                    f"\n{prefix}{self._DIRECTION_LABELS[item['direction']]} "
                    f"{self._format_size(item['bytes'])} — {item['description']}; "
                    f"about {estimate_ms:.1f} ms of payload time at {rate}."
                )

            tooltip += event_summary(event, "")
            concurrent = next(
                (item for item in active[1:] if item["direction"] != event["direction"]),
                None,
            )
            if concurrent:
                tooltip += event_summary(concurrent, "Also: ")
            elif queued:
                tooltip += event_summary(queued[0], "Next: ")
        elif self._last_transfer:
            event = self._last_transfer
            tooltip += (
                f"\nLast: {self._DIRECTION_LABELS[event['direction']]} "
                f"{self._format_size(event['bytes'])} — {event['description']}."
            )
        self.setToolTip(tooltip)
