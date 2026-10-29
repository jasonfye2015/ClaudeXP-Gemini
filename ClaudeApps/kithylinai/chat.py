"""The chat window's pieces: the art backdrop, the conversation view (white for you, light blue for Kithylin,
purple for the system) and the composer with bold and italic."""
import html
import random
import re
import time

from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPixmap, QShortcut, QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QTextBrowser, QToolButton, QVBoxLayout, QWidget

USER, KITHY, SYSTEM, MUTED = "#FFFFFF", "#9FD3FF", "#CDA4FF", "#B8B4C4"
ADULT_WORDS = ("porn", "nsfw", "adult", "yiff", "lewd", "explicit", "hyper", "nude", "xxx")


def adult_folders(settings, names):
    """Which of these art folders the slideshow leaves out: the ones chosen in Settings, or until a choice is made,
    the folders whose names say so (Kithy Porn, Kithy Porn Hyper...)."""
    chosen = settings["background"].get("adult_folders")
    if isinstance(chosen, list):
        return set(chosen) & set(names)
    return {n for n in names if any(w in n.lower() for w in ADULT_WORDS)}
FONT = "Segoe UI"


def md(text):
    """A little Markdown: **bold**, *italic*, `code`, and line breaks - as HTML."""
    s = html.escape(text or "")
    s = re.sub(r"`([^`\n]+)`", r"<code style='background:rgba(255,255,255,.12);padding:0 3px;border-radius:3px'>\1</code>", s)
    s = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<b>\1</b>", s, flags=re.S)
    s = re.sub(r"(?<![\w*])\*(?=\S)([^*\n]+?)(?<=\S)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"(?<![\w_])_(?=\S)([^_\n]+?)(?<=\S)_(?![\w_])", r"<i>\1</i>", s)
    return s.replace("\n", "<br>")


class Backdrop(QWidget):
    """Paints one of Kithylin's pictures behind whatever it holds, dimmed so the text reads."""

    def __init__(self):
        super().__init__()
        self._pix = QPixmap()
        self._dim = 0.58
        self._scaled = None
        self._scaled_for = None
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)

    def set_picture(self, path, dim=None):
        self._pix = QPixmap(str(path)) if path else QPixmap()
        if dim is not None:
            self._dim = dim
        self._scaled_for = None
        self.update()

    def set_dim(self, dim):
        self._dim = dim
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#141420"))
        if not self._pix.isNull():
            if self._scaled_for != self.size():
                self._scaled = self._pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self._scaled_for = self.size()
            x = (self.width() - self._scaled.width()) // 2
            y = (self.height() - self._scaled.height()) // 2
            p.drawPixmap(x, y, self._scaled)
            p.fillRect(self.rect(), QColor(10, 10, 20, int(255 * self._dim)))
        p.end()


class ChatView(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setObjectName("chatview")
        self.setOpenExternalLinks(False)
        self.setFrameShape(QTextBrowser.NoFrame)
        self.viewport().setAutoFillBackground(False)
        self.setStyleSheet("QTextBrowser#chatview { background: transparent; border: none; }")
        self.text_size = 11
        self.user_name = "You"
        self._stick = True          # follow new text to the bottom
        self._keep = 0              # else: where the reader was
        # the text is laid out after setHtml, a bit at a time: keep re-applying the scroll position as it grows
        self.verticalScrollBar().rangeChanged.connect(lambda *_: self._apply_scroll())

    def _apply_scroll(self):
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum() if self._stick else min(self._keep, sb.maximum()))

    def render(self, messages, streaming=False):
        """streaming=True: jump to the bottom whatever (you've just sent something). Otherwise follow the new text
        only if you were already at the bottom, and keep your place if you'd scrolled up to read."""
        sb = self.verticalScrollBar()
        self._stick = streaming or sb.value() >= sb.maximum() - 40
        self._keep = sb.value()
        parts = [f"<div style=\"font-family:'{FONT}'; font-size:{self.text_size}pt; color:{USER}\">"]
        for m in messages:
            stamp = time.strftime("%H:%M", time.localtime(m.get("time", time.time())))
            role = m["role"]
            if role == "system":
                body = md(m["content"])
                parts.append(f"<p style='margin:5px 0; color:{SYSTEM}'><span style='color:{MUTED};font-size:{self.text_size - 2}pt'>"
                             f"{stamp}</span> &nbsp;<i>{body}</i></p>")
                continue
            who = "Kithylin" if role == "assistant" else self.user_name
            colour = KITHY if role == "assistant" else USER
            body = md(m["content"])
            if m.get("streaming") and not m["content"]:
                body = "<span style='color:%s'>…</span>" % MUTED
            cursor = " <span style='color:%s'>▍</span>" % KITHY if m.get("streaming") and m["content"] else ""
            note = "(stopped)" if m.get("stopped") else "(cut where it started repeating itself)" if m.get("looped") else ""
            stopped = f" <span style='color:{MUTED}; font-size:{self.text_size - 2}pt'>{note}</span>" if note else ""
            parts.append(f"<p style='margin:7px 0; color:{colour}'><span style='color:{MUTED};font-size:{self.text_size - 2}pt'>"
                         f"{stamp}</span> &nbsp;<b>{html.escape(who)}:</b> {body}{cursor}{stopped}</p>")
        parts.append("</div>")
        self.setHtml("".join(parts))
        self._apply_scroll()
        QTimer.singleShot(0, self._apply_scroll)


class Composer(QPlainTextEdit):
    send = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("composer")
        self.setPlaceholderText("Say something to Kithylin...  (Enter sends, Shift+Enter for a new line, Ctrl+B bold, Ctrl+I italic)")
        self.setMaximumHeight(110)
        QShortcut(QKeySequence("Ctrl+B"), self, activated=lambda: self.wrap("**"))
        QShortcut(QKeySequence("Ctrl+I"), self, activated=lambda: self.wrap("*"))

    def wrap(self, mark):
        c = self.textCursor()
        if c.hasSelection():
            start, end = c.selectionStart(), c.selectionEnd()
            text = c.selectedText()
            c.insertText(f"{mark}{text}{mark}")
            c.setPosition(start + len(mark))
            c.setPosition(end + len(mark), QTextCursor.KeepAnchor)
        else:
            c.insertText(mark + mark)
            c.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(mark))
        self.setTextCursor(c)
        self.setFocus()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not (e.modifiers() & Qt.ShiftModifier):
            self.send.emit()
            return
        super().keyPressEvent(e)


class FormatBar(QWidget):
    """B and I buttons beside the composer."""

    def __init__(self, composer):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        for text, mark, tip in (("B", "**", "Bold (Ctrl+B)"), ("I", "*", "Italic (Ctrl+I)")):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            f = b.font()
            f.setBold(text == "B")
            f.setItalic(text == "I")
            b.setFont(f)
            b.clicked.connect(lambda _=False, m=mark: composer.wrap(m))
            lay.addWidget(b)
        lay.addStretch(1)


class Slideshow:
    """Picks the backdrop's picture from the gallery index, by the background settings."""

    def __init__(self, backdrop, art_dir, index, settings):
        self.backdrop, self.art, self.index, self.settings = backdrop, art_dir, index, settings
        self.timer = QTimer(backdrop)
        self.timer.timeout.connect(self.next)
        self.current = None

    def pool(self):
        bg = self.settings["background"]
        folders = self.index.get("folders", [])
        if bg["mode"] == "folder" and bg.get("folder"):
            folders = [f for f in folders if f["name"] == bg["folder"]]
        elif bg.get("skip_adult", True):
            adult = adult_folders(self.settings, [f["name"] for f in folders])
            folders = [f for f in folders if f["name"] not in adult]
        return [self.art / f["name"] / i["file"] for f in folders for i in f["items"] if i["kind"] == "image"]

    def apply(self):
        bg = self.settings["background"]
        self.timer.stop()
        if bg["mode"] == "none":
            self.backdrop.set_picture(None, bg["dim"])
            return
        if bg["mode"] == "picture" and bg.get("picture"):
            self.backdrop.set_picture(self.art / bg["picture"], bg["dim"])
            return
        self.next()
        self.timer.start(max(1, int(bg.get("minutes", 4))) * 60 * 1000)

    def next(self):
        pics = self.pool()
        if not pics:
            self.backdrop.set_picture(None, self.settings["background"]["dim"])
            return
        choice = random.choice(pics)
        if len(pics) > 1 and choice == self.current:
            choice = random.choice(pics)
        self.current = choice
        self.backdrop.set_picture(choice, self.settings["background"]["dim"])
