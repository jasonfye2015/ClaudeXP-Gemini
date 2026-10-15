"""The pieces both messengers are built from: the buddy list tree, the conversation window and the little
'has just signed in' toasts. Each messenger dresses them in its own look (msn.py, yim.py)."""
import html
from datetime import datetime

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QTextBrowser, QTextEdit, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ... import sound
from . import art
from .core import AWAY, BUSY, OFFLINE, ONLINE

e = html.escape


class BuddyTree(QTreeWidget):
    """Groups of buddies. groups: [(title format, test)] e.g. [("Online ({n})", lambda b: b.presence != OFFLINE)]."""
    open_buddy = Signal(str)

    def __init__(self, network, groups, icons, style, label=None):
        super().__init__()
        self.network, self.groups, self.icons = network, groups, icons
        self.label = label or (lambda b: b.name)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setIndentation(14)
        self.setIconSize(QSize(18, 18))
        self.setStyleSheet(style)
        self.itemDoubleClicked.connect(self._double)
        self.expanded = {}
        network.presence_changed.connect(lambda _id: self.fill())
        self.fill()

    def fill(self):
        if not isValid(self):
            return
        for i in range(self.topLevelItemCount()):
            it = self.topLevelItem(i)
            self.expanded[it.data(0, Qt.UserRole + 1)] = it.isExpanded()
        self.clear()
        buddies = sorted(self.network.buddies.values(), key=lambda b: self.label(b).lower())
        for title, test in self.groups:
            members = [b for b in buddies if test(b)]
            head = QTreeWidgetItem([title.format(n=len(members))])
            head.setData(0, Qt.UserRole + 1, title)
            f = head.font(0)
            f.setBold(True)
            head.setFont(0, f)
            self.addTopLevelItem(head)
            for b in members:
                item = QTreeWidgetItem([self.label(b)])
                item.setIcon(0, art.icon(self.icons[b.presence], 18))
                item.setData(0, Qt.UserRole, b.contact.id)
                if b.presence == OFFLINE:
                    item.setForeground(0, QColor("#808080"))
                item.setToolTip(0, f"{b.name} <{b.handle}>")
                head.addChild(item)
            head.setExpanded(self.expanded.get(title, True))

    def _double(self, item, _col):
        bid = item.data(0, Qt.UserRole)
        if bid:
            self.open_buddy.emit(bid)


class Conversation(QWidget):
    """One buddy's IM window. skin: header(buddy) -> widget, line(entry, me, buddy) -> html, send_label, input_style,
    transcript_style, typing_text(buddy)."""

    def __init__(self, network, buddy, skin):
        super().__init__()
        self.network, self.buddy, self.skin = network, buddy, skin
        self.frame = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.setObjectName("convo")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(skin.window_style)
        lay.addWidget(skin.toolbar(self))
        lay.addWidget(skin.header(self, buddy))
        self.transcript = QTextBrowser()
        self.transcript.setOpenLinks(False)
        self.transcript.setStyleSheet(skin.transcript_style)
        self.transcript.setProperty("nospell", True)
        lay.addWidget(self.transcript, 1)
        fmt = skin.format_bar(self)
        if fmt is not None:
            lay.addWidget(fmt)
        row = QHBoxLayout()
        row.setContentsMargins(6, 4, 6, 6)
        self.input = QTextEdit()
        self.input.setAcceptRichText(False)
        self.input.setFixedHeight(64)
        self.input.setStyleSheet(skin.input_style)
        self.input.installEventFilter(self)
        send = QPushButton(skin.send_label)
        send.setFixedSize(skin.send_size)
        send.setStyleSheet(skin.send_style)
        send.clicked.connect(self.send)
        row.addWidget(self.input, 1)
        row.addWidget(send, 0, Qt.AlignTop)
        box = QWidget()
        box.setLayout(row)
        lay.addWidget(box)
        self.status = QLabel("")
        self.status.setStyleSheet(skin.status_style)
        lay.addWidget(self.status)
        network.message_added.connect(self._added)
        network.typing_changed.connect(self._typing)
        for entry in buddy.history[-60:]:
            self._append(entry)
        self._last_received()

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == event.Type.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter) \
                and not event.modifiers() & Qt.ShiftModifier:
            self.send()
            return True
        return False

    def send(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        sound.play("ding") if self.skin.send_sound else None
        self.network.send(self.buddy, text)

    def _added(self, bid, entry):
        if not isValid(self) or bid != self.buddy.contact.id:
            return
        self._append(entry)
        if entry["kind"] == "contact":
            self.buddy.unread = False
            self._last_received()

    def _append(self, entry):
        html_line = self.skin.line(entry, self.network.my_handle(), self.buddy)
        self.transcript.append(html_line)
        bar = self.transcript.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _typing(self, bid, on):
        if isValid(self) and bid == self.buddy.contact.id:
            self.status.setText(self.skin.typing_text(self.buddy) if on else self._received_text)

    def _last_received(self):
        last = next((m for m in reversed(self.buddy.history) if m["kind"] == "contact"), None)
        if last is None:
            self._received_text = ""
        else:
            try:
                t = datetime.fromisoformat(last["ts"])
                self._received_text = self.skin.received_text(t)
            except (ValueError, KeyError):
                self._received_text = ""
        self.status.setText(self._received_text)

    def focus_input(self):
        self.input.setFocus()


class Toast(QWidget):
    """The little window that slides up over the clock: 'KittyKat has just signed in.'"""
    clicked = Signal()

    def __init__(self, desktop, title, text, logo, colors):
        super().__init__(desktop)
        self.desktop, self.title, self.text, self.logo, self.colors = desktop, title, text, logo, colors
        self.setFixedSize(190, 110)
        self.setCursor(Qt.PointingHandCursor)
        area = desktop.work_area()
        self.target = QPoint(area.right() - self.width() - 6, area.bottom() - self.height() - 4)
        self.move(self.target.x(), area.bottom())
        self.show()
        self.raise_()
        self.step = 0
        self.timer = QTimer(self, interval=15, timeout=self._slide)
        self.timer.start()
        QTimer.singleShot(5500, self._close)

    def _slide(self):
        y = self.y() - 6
        if y <= self.target.y():
            y = self.target.y()
            self.timer.stop()
        self.move(self.target.x(), y)

    def _close(self):
        if isValid(self):
            self.hide()
            self.deleteLater()

    def mousePressEvent(self, event):
        self.clicked.emit()
        self._close()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        top, bottom, border, text = self.colors
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor(top))
        g.setColorAt(1, QColor(bottom))
        p.setBrush(g)
        p.setPen(QPen(QColor(border), 1))
        p.drawRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1))
        p.drawPixmap(8, 6, self.logo)
        p.setPen(QColor(text))
        f = QFont("Tahoma", 8)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(34, 6, self.width() - 40, 18), Qt.AlignVCenter | Qt.AlignLeft, self.title)
        p.setFont(QFont("Tahoma", 9))
        p.drawText(QRectF(10, 30, self.width() - 20, self.height() - 36), Qt.AlignCenter | Qt.TextWordWrap, self.text)


STATUS_WORDS = {ONLINE: "Online", AWAY: "Away", BUSY: "Busy", OFFLINE: "Offline"}
