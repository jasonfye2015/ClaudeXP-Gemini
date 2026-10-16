"""Idle handling, screen-saver animations, and Windows-style preferences."""

from __future__ import annotations

from collections import deque
from math import cos, pi, sin
from random import Random
import time

from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .config import (
    DEFAULT_SCREEN_SAVER_SETTINGS,
    SCREEN_SAVER_TIMEOUTS,
    SCREEN_SAVER_TYPES,
    load_screen_saver_settings,
    save_screen_saver_settings,
)

SAVER_LABELS = {"bubbles": "Bubbles", "mystify": "Mystify"}
TIMEOUT_LABELS = (
    ("Never", 0),
    ("1 minute", 60),
    ("5 minutes", 300),
    ("10 minutes", 600),
    ("15 minutes", 900),
    ("30 minutes", 1800),
)


class IdleScreenSaverController(QObject):
    """Launch a full-screen saver after inactivity and dismiss it on user input."""

    activeChanged = Signal(bool)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.application = QApplication.instance()
        if self.application is None:
            raise RuntimeError("A QApplication is required for screen savers.")
        self.settings_error: str | None = None
        try:
            self.settings = load_screen_saver_settings()
        except (OSError, ValueError) as exc:
            self.settings = DEFAULT_SCREEN_SAVER_SETTINGS.copy()
            self.settings_error = str(exc)
        self._active = False
        self._session_stopped = False
        self._activation_cursor = QCursor.pos()
        self._overlay: ScreenSaverOverlay | None = None
        self.idle_timer = QTimer(self)
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self._start_idle_saver)
        self.application.installEventFilter(self)
        self._arm_idle_timer()

    @property
    def active(self) -> bool:
        return self._active

    def apply_settings(self, saver: str, timeout_seconds: int) -> None:
        settings = {"saver": saver, "timeout_seconds": timeout_seconds}
        if (
            not isinstance(saver, str)
            or saver not in SCREEN_SAVER_TYPES
            or type(timeout_seconds) is not int
            or timeout_seconds not in SCREEN_SAVER_TIMEOUTS
        ):
            raise ValueError("Choose a listed screen saver and idle wait time.")
        save_screen_saver_settings(settings)
        self.settings = settings
        self.settings_error = None
        self._arm_idle_timer()

    def preview(self, saver: str | None = None) -> None:
        selected = saver or str(self.settings["saver"])
        if selected not in SCREEN_SAVER_TYPES:
            raise ValueError("The selected screen saver is not available.")
        self._show_saver(selected, preview=True)

    def stop_session(self) -> None:
        self._session_stopped = True
        self.idle_timer.stop()
        self.application.removeEventFilter(self)
        if self._overlay is not None:
            self._overlay.stop_animation()
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
        if self._active:
            self.activeChanged.emit(False)
        self._active = False

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 - Qt event name
        event_type = event.type()
        activity_types = {
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonDblClick,
            QEvent.Type.KeyPress,
            QEvent.Type.Wheel,
            QEvent.Type.TouchBegin,
            QEvent.Type.TabletPress,
        }
        if event_type not in activity_types or self._session_stopped:
            return False

        if self._active:
            if event_type == QEvent.Type.MouseMove:
                if (QCursor.pos() - self._activation_cursor).manhattanLength() < 4:
                    return False
            self._dismiss_saver()
            return True

        self._arm_idle_timer()
        return False

    def _arm_idle_timer(self) -> None:
        self.idle_timer.stop()
        timeout = int(self.settings["timeout_seconds"])
        if not self._session_stopped and self.settings_error is None and timeout:
            self.idle_timer.start(timeout * 1000)

    def _start_idle_saver(self) -> None:
        if not self.settings_error:
            self._show_saver(str(self.settings["saver"]), preview=False)

    def _show_saver(self, saver: str, *, preview: bool) -> None:
        if self._active or self._session_stopped:
            return
        self.idle_timer.stop()
        self._active = True
        self._activation_cursor = QCursor.pos()
        parent = self.parent()
        self._overlay = ScreenSaverOverlay(
            saver, parent if isinstance(parent, QWidget) else None
        )
        self.activeChanged.emit(True)
        self._overlay.showFullScreen()
        self._overlay.raise_()
        self._overlay.activateWindow()
        self._overlay.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def _dismiss_saver(self) -> None:
        if not self._active:
            return
        self._active = False
        overlay = self._overlay
        self._overlay = None
        self.activeChanged.emit(False)
        if overlay is not None:
            overlay.stop_animation()
            overlay.hide()
            overlay.deleteLater()
        self._arm_idle_timer()


class ScreenSaverOverlay(QWidget):
    """A frameless full-screen host for the built-in Bubbles and Mystify savers."""

    def __init__(self, saver: str, parent: QWidget | None = None):
        super().__init__(
            parent,
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        if saver not in SCREEN_SAVER_TYPES:
            raise ValueError("The selected screen saver is not available.")
        self.saver = saver
        self.setObjectName("screenSaverOverlay")
        self.setWindowTitle(f"{SAVER_LABELS[saver]} Screen Saver")
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self._rng = Random(time.time_ns())
        self._last_tick = time.monotonic()
        self._colors = (
            QColor("#49c6f4"),
            QColor("#9c82ff"),
            QColor("#4ee0bd"),
            QColor("#ff7889"),
            QColor("#ffd16e"),
        )
        self._bubbles = self._make_bubbles()
        self._shapes = self._make_shapes()
        self._trails = [deque(maxlen=12) for _ in self._shapes]
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    def stop_animation(self) -> None:
        self._timer.stop()

    def _make_bubbles(self) -> list[dict[str, float | int]]:
        bubbles = []
        for index in range(24):
            bubbles.append(
                {
                    "x": self._rng.uniform(0.04, 0.96),
                    "y": self._rng.uniform(0.04, 0.96),
                    "vx": self._rng.uniform(-0.16, 0.16),
                    "vy": self._rng.uniform(-0.13, 0.13),
                    "radius": self._rng.uniform(0.022, 0.075),
                    "color": index % len(self._colors),
                }
            )
        return bubbles

    def _make_shapes(self) -> list[list[list[float]]]:
        shapes = []
        for shape_index in range(4):
            center_x = self._rng.uniform(0.25, 0.75)
            center_y = self._rng.uniform(0.25, 0.75)
            radius = self._rng.uniform(0.13, 0.34)
            count = 5
            shape = []
            for vertex in range(count):
                angle = 2 * pi * vertex / count
                shape.append(
                    [
                        max(0.03, min(0.97, center_x + radius * self._rng.uniform(0.7, 1.1) * cos(angle))),
                        max(0.03, min(0.97, center_y + radius * self._rng.uniform(0.7, 1.1) * sin(angle))),
                        self._rng.uniform(-0.24, 0.24),
                        self._rng.uniform(-0.22, 0.22),
                    ]
                )
            shapes.append(shape)
        return shapes

    def _advance(self) -> None:
        now = time.monotonic()
        elapsed = min(0.08, now - self._last_tick)
        self._last_tick = now
        if self.saver == "bubbles":
            for bubble in self._bubbles:
                bubble["x"] = float(bubble["x"]) + float(bubble["vx"]) * elapsed
                bubble["y"] = float(bubble["y"]) + float(bubble["vy"]) * elapsed
                radius = float(bubble["radius"])
                for coordinate, velocity, edge in (
                    ("x", "vx", radius),
                    ("y", "vy", radius),
                ):
                    value = float(bubble[coordinate])
                    if value < edge or value > 1 - edge:
                        bubble[coordinate] = max(edge, min(1 - edge, value))
                        bubble[velocity] = -float(bubble[velocity])
        else:
            for shape_index, shape in enumerate(self._shapes):
                for point in shape:
                    point[0] += point[2] * elapsed
                    point[1] += point[3] * elapsed
                    if point[0] < 0.02 or point[0] > 0.98:
                        point[0] = max(0.02, min(0.98, point[0]))
                        point[2] = -point[2]
                    if point[1] < 0.02 or point[1] > 0.98:
                        point[1] = max(0.02, min(0.98, point[1]))
                        point[3] = -point[3]
                self._trails[shape_index].append(
                    [(point[0], point[1]) for point in shape]
                )
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt event name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        background = QLinearGradient(0, 0, self.width(), self.height())
        background.setColorAt(0, QColor("#030914"))
        background.setColorAt(0.55, QColor("#102338"))
        background.setColorAt(1, QColor("#030914"))
        painter.fillRect(self.rect(), QBrush(background))
        if self.saver == "bubbles":
            self._paint_bubbles(painter)
        else:
            self._paint_mystify(painter)

    def _paint_bubbles(self, painter: QPainter) -> None:
        extent = min(self.width(), self.height())
        for bubble in self._bubbles:
            x = float(bubble["x"]) * self.width()
            y = float(bubble["y"]) * self.height()
            radius = float(bubble["radius"]) * extent
            center = QPointF(x, y)
            gradient = QRadialGradient(
                QPointF(x - radius * 0.32, y - radius * 0.35),
                radius * 1.6,
            )
            color = QColor(self._colors[int(bubble["color"])])
            center_color = QColor("#ffffff")
            center_color.setAlpha(105)
            color.setAlpha(85)
            edge_color = QColor(color)
            edge_color.setAlpha(18)
            gradient.setColorAt(0.0, center_color)
            gradient.setColorAt(0.3, color)
            gradient.setColorAt(1.0, edge_color)
            painter.setBrush(gradient)
            outline = QColor(self._colors[int(bubble["color"])])
            outline.setAlpha(175)
            painter.setPen(QPen(outline, max(1.0, radius * 0.035)))
            painter.drawEllipse(QRectF(x - radius, y - radius, radius * 2, radius * 2))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 120))
            painter.drawEllipse(
                QRectF(
                    x - radius * 0.48,
                    y - radius * 0.53,
                    radius * 0.25,
                    radius * 0.12,
                )
            )

    def _paint_mystify(self, painter: QPainter) -> None:
        width = max(1, self.width())
        height = max(1, self.height())
        for shape_index, trail in enumerate(self._trails):
            base = self._colors[shape_index]
            snapshots = list(trail)
            for trail_index, points in enumerate(snapshots):
                opacity = int(20 + 190 * (trail_index + 1) / max(1, len(snapshots)))
                color = QColor(base)
                color.setAlpha(opacity)
                painter.setPen(QPen(color, 1.0 + 1.1 * trail_index / 12))
                path = QPainterPath()
                first_x, first_y = points[0]
                path.moveTo(first_x * width, first_y * height)
                for x, y in points[1:]:
                    path.lineTo(x * width, y * height)
                path.closeSubpath()
                painter.drawPath(path)


class ScreenSaverSettingsPage(QWidget):
    """Selection, idle wait, preview, and explicit save controls."""

    def __init__(self, controller: IdleScreenSaverController, parent=None):
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)
        explanation = QLabel(
            "Choose a screen saver and how long Windows must be idle before it "
            "starts. Move the mouse or press a key to return to the desktop."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        form = QFormLayout()
        self.saver_combo = QComboBox()
        self.saver_combo.setObjectName("screenSaverChoice")
        for saver_id, label in SAVER_LABELS.items():
            self.saver_combo.addItem(label, saver_id)
        self.wait_combo = QComboBox()
        self.wait_combo.setObjectName("screenSaverWait")
        for label, seconds in TIMEOUT_LABELS:
            self.wait_combo.addItem(label, seconds)
        form.addRow("Screen saver:", self.saver_combo)
        form.addRow("Wait:", self.wait_combo)
        layout.addLayout(form)

        controls = QHBoxLayout()
        self.preview_button = QPushButton("Preview")
        self.preview_button.setObjectName("screenSaverPreview")
        self.apply_button = QPushButton("Apply")
        self.apply_button.setObjectName("screenSaverApply")
        controls.addWidget(self.preview_button)
        controls.addWidget(self.apply_button)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.status_label = QLabel()
        self.status_label.setObjectName("screenSaverStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        self.preview_button.clicked.connect(self._preview)
        self.apply_button.clicked.connect(self._apply)
        self._load_current_settings()

    def _load_current_settings(self) -> None:
        saver = self.controller.settings["saver"]
        timeout = self.controller.settings["timeout_seconds"]
        self.saver_combo.setCurrentIndex(max(0, self.saver_combo.findData(saver)))
        self.wait_combo.setCurrentIndex(max(0, self.wait_combo.findData(timeout)))
        if self.controller.settings_error:
            self.status_label.setText(
                "Saved screen-saver settings could not be read. Defaults are shown; "
                "choose valid options and select Apply to repair them. "
                + self.controller.settings_error
            )
        else:
            self.status_label.setText("Current screen-saver settings are loaded.")

    def _preview(self) -> None:
        self.controller.preview(self.saver_combo.currentData())

    def _apply(self) -> None:
        try:
            self.controller.apply_settings(
                str(self.saver_combo.currentData()),
                int(self.wait_combo.currentData()),
            )
        except (OSError, ValueError) as exc:
            self.status_label.setText(f"Could not save screen-saver settings: {exc}")
            return
        timeout = int(self.wait_combo.currentData())
        wait = "never" if timeout == 0 else f"after {timeout // 60} minute(s)"
        self.status_label.setText(
            f"{self.saver_combo.currentText()} will start {wait} of inactivity."
        )
