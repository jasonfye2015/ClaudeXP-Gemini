"""Instant Message window (IM.png), one per contact."""
import html
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QImage, QImageReader, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QMenuBar,
                               QTextBrowser, QTextEdit, QVBoxLayout, QWidget)

from .. import host, paths, timefmt
from ..engine import Presence
from .common import GREY, ImageButton, icon_pixmap
from .gallery import GalleryWindow
from .guide import show_guide
from .picture import PictureViewer

CONTACT_COLOR = "#ff0000"
USER_COLOR = "#0000ff"
THUMB_W, THUMB_H = 160, 80  # inline picture size; click for full size
SENT_MAX = 1024             # pictures you send are saved at most this big

# Window layout, matching the original IM.png skin.
DEFAULT_W, DEFAULT_H = 435, 293
MIN_W, MIN_H = 360, 260
ICON_COL = 68               # left column holding the two buddy icons
BOX_GAP = 35                # space between the conversation and the typing box
INPUT_H = 60
BAR_H = 55
# White boxes with the classic sunken edge: thick black top/left, thin dark bottom/right.
BOX_STYLE = ("background: white; font: 10pt 'Arial'; border-top: 2px solid #000000; "
             "border-left: 2px solid #000000; border-right: 1px solid #21211f; "
             "border-bottom: 1px solid #21211f;")
INPUT_STYLE = ("background: white; font: 10pt 'Arial'; border-top: 2px solid #000000; "
               "border-left: 2px solid #000000; border-right: none; border-bottom: none;")
PANEL_STYLE = ("QFrame#panel { border-top: 1px solid #848484; border-left: 1px solid #848484; "
               "border-right: 1px solid #ffffff; border-bottom: 1px solid #ffffff; }")


def _panel(width=None):
    """One etched section of the bottom bar."""
    frame = QFrame()
    frame.setObjectName("panel")
    frame.setStyleSheet(PANEL_STYLE)
    if width:
        frame.setFixedWidth(width)
    return frame


def save_sent_picture(source, buddy_id):
    """Copy a dropped/pasted picture into data/sent/<buddy>/. Returns its path relative to data/."""
    img = QImage(source) if isinstance(source, str) else QImage(source)
    if img.isNull():
        return None
    if img.width() > SENT_MAX or img.height() > SENT_MAX:
        img = img.scaled(SENT_MAX, SENT_MAX, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    flat = QImage(img.size(), QImage.Format_RGB32)  # JPG has no transparency: put it on white
    flat.fill(Qt.white)
    painter = QPainter(flat)
    painter.drawImage(0, 0, img)
    painter.end()
    folder = paths.DATA / "sent" / buddy_id
    folder.mkdir(parents=True, exist_ok=True)
    stem = datetime.now().strftime("%Y%m%d-%H%M%S")
    name, n = f"{stem}.jpg", 1
    while (folder / name).exists():
        n += 1
        name = f"{stem}-{n}.jpg"
    flat.save(str(folder / name), "JPG", 90)
    return f"sent/{buddy_id}/{name}"


class InputBox(QTextEdit):
    submitted = Signal()
    picture_dropped = Signal(object)  # a file path, or a QImage from the clipboard

    @staticmethod
    def _picture_in(mime):
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in paths.ICON_EXTS:
                    return url.toLocalFile()
        if mime.hasImage():
            return mime.imageData()
        return None

    def canInsertFromMimeData(self, mime):
        return self._picture_in(mime) is not None or super().canInsertFromMimeData(mime)

    def insertFromMimeData(self, mime):
        picture = self._picture_in(mime)
        if picture is not None:
            self.picture_dropped.emit(picture)
        else:
            super().insertFromMimeData(mime)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers() & Qt.ShiftModifier:
            self.submitted.emit()
            return
        super().keyPressEvent(event)


class IMWindow(host.HostedWindow, QWidget):
    closed = Signal(str)

    def __init__(self, settings, world, buddy_id):
        buddy = world.buddies[buddy_id]
        super().__init__(None, Qt.Window)
        self.setWindowTitle(f"{buddy.name} - Instant Message")
        self.settings, self.world, self.buddy = settings, world, buddy
        self.typing = False
        self.downloading = False
        self.gallery = None
        self.viewers = []

        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(GREY))
        self.setPalette(pal)
        self.setAutoFillBackground(True)
        self.setMinimumSize(MIN_W, MIN_H)
        w, h = settings["im_size"] or (DEFAULT_W, DEFAULT_H)
        self.resize(max(w, MIN_W), max(h, MIN_H))

        # --- menus ------------------------------------------------------------
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("&File")
        gallery_action = QAction("&Gallery...", self)
        gallery_action.triggered.connect(self._show_gallery)
        file_menu.addAction(gallery_action)
        file_menu.addSeparator()
        close_action = QAction("&Close", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        help_menu = menu_bar.addMenu("&Help")
        guide_action = QAction("&Guide", self)
        guide_action.triggered.connect(lambda: show_guide("im"))
        help_menu.addAction(guide_action)

        # --- conversation and typing boxes ----------------------------------------
        self.log = QTextBrowser()
        self.log.setFrameShape(QTextBrowser.NoFrame)
        self.log.setOpenExternalLinks(False)
        self.log.setOpenLinks(False)
        self.log.anchorClicked.connect(self._link_clicked)
        self.log.setStyleSheet(f"QTextBrowser {{ {BOX_STYLE} }}")
        self.log.setMinimumHeight(60)

        self.input = InputBox()
        self.input.setFrameShape(QTextEdit.NoFrame)
        self.input.setAcceptRichText(False)
        self.input.setStyleSheet(f"QTextEdit {{ {INPUT_STYLE} }}")
        self.input.setFixedHeight(INPUT_H)
        self.input.submitted.connect(self._send)
        self.input.picture_dropped.connect(self._send_picture)
        self.input.setToolTip("Type a message, or drag a picture here to send it")

        self.their_icon = QLabel()
        self.their_icon.setFixedSize(48, 48)
        self.their_icon.setAlignment(Qt.AlignCenter)
        self.their_icon.setPixmap(icon_pixmap(paths.resolve_icon(self.buddy.contact.icon)))

        self.my_icon = QLabel()
        self.my_icon.setFixedSize(48, 48)
        self.my_icon.setAlignment(Qt.AlignCenter)
        self.refresh_user_icon()

        # --- bottom bar: [Get Info] [status] [Send + memory meter] ------------------
        self.info_btn = ImageButton("button_getinfo.jpg", None, "Get Info")
        self.info_btn.clicked.connect(self._get_info)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: #404040; border: none;")

        self.send_btn = ImageButton("button_send.jpg", None, "Send")
        self.send_btn.clicked.connect(self._send)

        self.context = QLabel()
        self.context.setFixedSize(52, 10)

        info_panel = _panel(75)
        QVBoxLayout(info_panel).addWidget(self.info_btn, 0, Qt.AlignCenter)
        status_panel = _panel()
        status_layout = QVBoxLayout(status_panel)
        status_layout.setContentsMargins(4, 2, 4, 2)
        status_layout.addWidget(self.status)
        send_panel = _panel(57)
        send_layout = QVBoxLayout(send_panel)
        send_layout.setContentsMargins(1, 2, 1, 2)
        send_layout.setSpacing(3)
        send_layout.addWidget(self.send_btn, 0, Qt.AlignHCenter)
        send_layout.addWidget(self.context, 0, Qt.AlignHCenter)

        bar = QWidget()
        bar.setFixedHeight(BAR_H)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        bar_layout.addWidget(info_panel)
        bar_layout.addWidget(status_panel, 1)
        bar_layout.addWidget(send_panel)

        # --- put it together, like IM.png: a 68px icon column, then the boxes -----------
        etch = QFrame()
        etch.setFrameShape(QFrame.HLine)
        etch.setFrameShadow(QFrame.Sunken)

        grid = QGridLayout()
        grid.setContentsMargins(0, 8, 10, 2)
        grid.setHorizontalSpacing(2)
        grid.setVerticalSpacing(0)
        grid.setColumnMinimumWidth(0, ICON_COL)
        grid.addWidget(self.their_icon, 0, 0, Qt.AlignCenter)
        grid.addWidget(self.log, 0, 1)
        grid.setRowMinimumHeight(1, BOX_GAP)
        grid.addWidget(self.my_icon, 2, 0, Qt.AlignCenter)
        grid.addWidget(self.input, 2, 1)
        grid.setRowMinimumHeight(3, 8)
        grid.addWidget(bar, 4, 1)
        grid.setRowStretch(0, 1)    # extra height goes to the conversation
        grid.setColumnStretch(1, 1)  # extra width goes to the boxes

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setMenuBar(menu_bar)
        root.addWidget(etch)
        root.addLayout(grid, 1)

        for entry in self.buddy.history.messages:
            self._append(entry)
        self._update_context()
        self._update_status()

        world.message_added.connect(self._message_added)
        world.presence_changed.connect(self._presence_changed)
        world.typing_changed.connect(self._typing_changed)
        world.downloading_changed.connect(self._downloading_changed)

    # ----- display ------------------------------------------------------------

    def refresh_user_icon(self):
        self.my_icon.setPixmap(icon_pixmap(paths.resolve_icon(self.settings["buddy_icon"])))

    def _line(self, name, color, ts, text, tz=None):
        body = html.escape(text).replace("\n", "<br>")
        return (f'<span style="color:{color}; font-weight:bold;">{html.escape(name)}</span> '
                f'<span style="color:{color}; font-size:8pt;">({timefmt.stamp(ts, tz)})</span>: {body}')

    def _append(self, entry):
        kind, ts, text = entry["kind"], entry["ts"], entry["text"]
        me = self.settings["screen_name"]
        them = self.buddy.name
        tz = self.buddy.contact.timezone  # their messages show their local time
        if kind == "user":
            line = self._line(me, USER_COLOR, ts, text)
            if entry.get("image"):
                line += self._picture_html("u", entry["image"])
        elif kind == "contact":
            line = self._line(them, CONTACT_COLOR, ts, text, tz)
            if entry.get("image"):
                line += self._picture_html("c", entry["image"])
        elif kind == "auto":
            line = self._line(f"Auto response from {me}", USER_COLOR, ts, text)
        elif kind == "contact_auto":
            line = self._line(f"Auto response from {them}", CONTACT_COLOR, ts, text, tz)
        else:
            line = f'<span style="color:#808080; font-style:italic;">{html.escape(text)}</span>'
        self.log.append(line)
        bar = self.log.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _picture_path(self, who, name):
        """who: 'c' = from the contact's picture folder, 'u' = one the user sent (under data/)."""
        if who == "u":
            path = paths.DATA / name
        else:
            pics = self.buddy.contact.pictures
            path = pics.path(name) if pics else None
        return path if path and path.exists() else None

    def _picture_html(self, who, name):
        path = self._picture_path(who, name)
        if not path:
            return f'<br><i style="color:#808080;">[picture: {html.escape(name)} is missing]</i>'
        size = QImageReader(str(path)).size()
        scale = min(THUMB_W / max(size.width(), 1), THUMB_H / max(size.height(), 1), 1.0)
        w, h = max(int(size.width() * scale), 1), max(int(size.height() * scale), 1)
        src = QUrl.fromLocalFile(str(path)).toString()
        return (f'<br><a href="pic:{who}:{html.escape(name)}"><img src="{src}" width="{w}" height="{h}" '
                f'title="Click to view full size"></a>')

    def _link_clicked(self, url):
        link = url.toString()
        if link.startswith("pic:"):
            who, _, name = link[4:].partition(":")
            path = self._picture_path(who, name)
            if path:
                title = "Picture you sent" if who == "u" else f"Picture from {self.buddy.name}"
                viewer = PictureViewer(str(path), title, self)
                self.viewers.append(viewer)
                viewer.destroyed.connect(lambda *_: self.viewers.remove(viewer) if viewer in self.viewers else None)
                viewer.show()

    def _update_context(self):
        pct = self.world.context_fraction(self.buddy.id) * 100
        step = min(100, int(pct // 10) * 10)
        self.context.setPixmap(QPixmap(paths.image(f"context_{step:02d}.jpg")))
        self.context.setToolTip("Conversation memory" +
                                (" is full: the oldest messages are being forgotten."
                                 if pct >= 100 else f": about {int(pct)}% used."))

    def _update_status(self):
        b = self.buddy
        if self.downloading:
            text = f"{b.name} is downloading image..."
        elif self.typing:
            text = f"{b.name} is typing..."
        elif b.presence == Presence.OFFLINE:
            text = f"{b.name} is offline."
        elif b.presence == Presence.AWAY:
            text = f"{b.name} is away."
        else:
            text = ""
        self.status.setText(text)

    # ----- world events -----------------------------------------------------------

    def _message_added(self, buddy_id, entry):
        if buddy_id == self.buddy.id:
            self._append(entry)
            self._update_context()
            if entry["kind"] == "contact" and not self._seen():
                host.alert(self)  # flash on the taskbar, like AIM

    def _presence_changed(self, buddy_id):
        if buddy_id == self.buddy.id:
            self._update_status()

    def _typing_changed(self, buddy_id, typing):
        if buddy_id == self.buddy.id:
            self.typing = typing
            self._update_status()

    def _downloading_changed(self, buddy_id, downloading):
        if buddy_id == self.buddy.id:
            self.downloading = downloading
            self._update_status()

    # ----- actions ------------------------------------------------------------------

    def _send_picture(self, source):
        rel = save_sent_picture(source, self.buddy.id)
        if not rel:
            host.information(self, "Instant Message", "That picture couldn't be opened.")
            return
        self.world.user_send_image(self.buddy.id, rel)

    def _send(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.world.user_send(self.buddy.id, text)
        self.input.clear()

    def _show_gallery(self):
        if self.gallery is None:
            self.gallery = GalleryWindow(self.settings, self.world, self.buddy.id, self)
            self.gallery.destroyed.connect(lambda *_: setattr(self, "gallery", None))
        host.present(self.gallery)

    def _get_info(self):
        c = self.buddy.contact
        info = c.profile or f"{c.screen_name} hasn't written a profile yet."
        if c.timezone:
            info += f"\n\nLocal time: {timefmt.clock_text(c.timezone)}"
        host.information(self, f"Buddy Info: {c.screen_name}", info)

    def showEvent(self, event):
        super().showEvent(event)
        self.input.setFocus()
        self._report_seen()

    def _seen(self):
        return host.is_active(self)

    def _report_seen(self):
        self.world.set_window_seen(self.buddy.id, self._seen())

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.ActivationChange, QEvent.WindowStateChange):
            self._report_seen()

    def closeEvent(self, event):
        self.settings.set("im_size", [self.width(), self.height()])  # next IM opens this size
        self.input.clear()
        self.world.set_window_seen(self.buddy.id, False)
        self.closed.emit(self.buddy.id)
        event.accept()
