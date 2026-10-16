"""The Buddy List (list.png)."""
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QFontMetrics, QPalette
from PySide6.QtWidgets import (QMenuBar, QStyle, QStyledItemDelegate, QStyleOptionViewItem,
                               QTreeWidget, QTreeWidgetItem)

from .. import host
from ..engine import Presence
from .common import ImageWindow

DOOR, NOTE, AWAY = "\U0001F6AA", "\U0001F4DD", "❗"
ID_ROLE = Qt.UserRole
BADGE_ROLE = Qt.UserRole + 1   # status emoji shown before the name
BADGE_FONT = QFont("Segoe UI Emoji", 11)


class BuddyDelegate(QStyledItemDelegate):
    """Draws a buddy's status emoji in full-size color, then their name."""

    def paint(self, painter, option, index):
        badges = index.data(BADGE_ROLE)
        if not badges:
            super().paint(painter, option, index)
            return
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        name = opt.text
        opt.text = ""
        widget = opt.widget
        widget.style().drawControl(QStyle.CE_ItemViewItem, opt, painter, widget)
        rect = widget.style().subElementRect(QStyle.SE_ItemViewItemText, opt, widget)
        painter.save()
        painter.setFont(BADGE_FONT)
        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, badges)
        rect.setLeft(rect.left() + QFontMetrics(BADGE_FONT).horizontalAdvance(badges) + 3)
        painter.setFont(opt.font)
        if opt.state & QStyle.State_Selected:
            painter.setPen(opt.palette.color(QPalette.HighlightedText))
        else:
            painter.setPen(index.data(Qt.ForegroundRole).color() if index.data(Qt.ForegroundRole)
                           else opt.palette.color(QPalette.Text))
        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, name)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(size.width() + 60, max(size.height(), QFontMetrics(BADGE_FONT).height() + 2))


class BuddyListWindow(ImageWindow):
    open_im = Signal(str)
    away_requested = Signal()
    icon_requested = Signal()
    setup_requested = Signal()
    help_requested = Signal()
    exit_requested = Signal()
    close_requested = Signal()   # the user closed the window (X): app decides tray vs exit

    def __init__(self, settings, world):
        super().__init__("list.png", "Buddy List")
        self.settings, self.world = settings, world

        menu_bar = QMenuBar(self)
        menu_bar.setGeometry(0, 0, self.width(), 22)
        file_menu = menu_bar.addMenu("&File")
        for text, signal in [("Set Away Status...", self.away_requested),
                             ("Set Buddy Icon...", self.icon_requested),
                             ("Setup...", self.setup_requested)]:
            action = QAction(text, self)
            action.triggered.connect(signal)
            file_menu.addAction(action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_requested)
        file_menu.addAction(exit_action)
        help_menu = menu_bar.addMenu("&Help")
        guide_action = QAction("&Guide", self)
        guide_action.triggered.connect(self.help_requested)
        help_menu.addAction(guide_action)

        self.tree = QTreeWidget(self)
        self.tree.setGeometry(10, 124, 195, 297)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(12)
        self.tree.setRootIsDecorated(True)
        self.tree.setFrameShape(QTreeWidget.NoFrame)
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setStyleSheet("QTreeWidget { background: white; font: 9pt 'Arial'; }")
        self.tree.itemClicked.connect(self._clicked)
        self.tree.setItemDelegate(BuddyDelegate(self.tree))

        bold = QFont("Arial", 9, QFont.Bold)
        self.online_group = QTreeWidgetItem(["Buddies"])
        self.offline_group = QTreeWidgetItem(["Offline"])
        for group in (self.online_group, self.offline_group):
            group.setFont(0, bold)
            self.tree.addTopLevelItem(group)
            group.setExpanded(True)

        self.items = {}
        for b in world.buddies.values():
            item = QTreeWidgetItem()
            item.setData(0, ID_ROLE, b.id)
            self.items[b.id] = item
            self.offline_group.addChild(item)
            self._style(b.id)
        self._regroup()

        world.presence_changed.connect(self._presence_changed)
        world.unread_changed.connect(self._style)
        world.user_away_changed.connect(self._update_title)
        self._update_title()

        screen = host.available_geometry(self)
        self.move(screen.right() - self.width() - 40, screen.top() + 60)

    def _update_title(self, *_):
        title = f"{self.settings['screen_name']}'s Buddy List"
        self.setWindowTitle(f"*Away* {title}" if self.world.user_away else title)

    def _style(self, buddy_id):
        b = self.world.buddies[buddy_id]
        item = self.items[buddy_id]
        badges = ""
        if b.door:
            badges += DOOR
        if b.history.unread:
            badges += NOTE
        if b.presence == Presence.AWAY:
            badges += AWAY
        item.setText(0, b.name)
        item.setData(0, BADGE_ROLE, badges)
        item.setToolTip(0, "Message waiting!" if b.history.unread else "")
        font = QFont("Arial", 9)
        font.setItalic(b.presence == Presence.OFFLINE)
        item.setFont(0, font)
        item.setForeground(0, QColor("#808080" if b.presence == Presence.OFFLINE else "#000000"))

    def _presence_changed(self, buddy_id):
        self._style(buddy_id)
        self._regroup()

    def _regroup(self):
        """Put each buddy under the right group, alphabetically, and update counts."""
        total = len(self.items)
        online, offline = [], []
        for bid, item in self.items.items():
            b = self.world.buddies[bid]
            (offline if b.presence == Presence.OFFLINE else online).append((b.name.lower(), item))
        for group, members in ((self.online_group, online), (self.offline_group, offline)):
            members.sort(key=lambda m: m[0])
            for _, item in members:
                parent = item.parent()
                if parent is not None:
                    parent.removeChild(item)
            for _, item in members:
                group.addChild(item)
        self.online_group.setText(0, f"Buddies ({len(online)}/{total})")
        self.offline_group.setText(0, f"Offline ({len(offline)}/{total})")

    def _clicked(self, item, _column):
        buddy_id = item.data(0, ID_ROLE)
        if buddy_id:
            self.open_im.emit(buddy_id)

    def closeEvent(self, event):
        if host.user_closed(self, event):  # the user clicked X
            event.ignore()
            self.close_requested.emit()
        else:
            event.accept()
