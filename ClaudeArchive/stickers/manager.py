"""Sticker Manager: look through the sticker packs in Local Storage/Sticker Packs and give each sticker an emoji and
a few words of meaning - which is all a resident ever sees of it.

The shelf shows every pack with how much of it is done; a pack opens as a wall of its stickers, each wearing its
emoji. Pick one to see it (animated ones play) and choose an emoji from the palette (or type one) and what it means;
Save moves on to the next. 'Suggest with AI' asks this computer's picture-reading language model to fill in every
sticker in the pack that has no emoji yet; its guesses wear a dashed outline until they're saved or accepted."""
import re
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QImageReader, QMovie, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget,
                               QListWidgetItem, QPushButton, QStackedWidget, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from comix.reader import Loader
from claudecore import host

from . import library

TILE = 112
PALETTE = ("😀 😄 😁 😂 🤣 😊 😍 🥰 😘 😜 😎 🤔 😏 😴 😢 😭 😡 😱 😳 🥺 😇 🤗 🙄 😬 🤤 😈 💀 😮 😤 🤪 "
           "👋 👍 👎 👏 🙏 💪 ❤️ 💔 💕 🔥 ✨ 🎉 💤 💦 🍕 ☕ 🐾 🐺 🦊 🐶 🐱 🎁 ❓ ❗ 🤷 🫡 😋 🥳 🤯 😻").split()
EMOJI_FONT = "Segoe UI Emoji"
PROMPT = ("This picture is a chat sticker. Answer on ONE line: the single emoji that best matches it, then ' | ', then "
          "2 to 5 lowercase words saying what someone means by sending it. Example: 😊 | happy tail wag")


def stickers_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#B0A080"), 1))
    p.setBrush(QColor("#FFFFFF"))
    p.drawRoundedRect(QRectF(2.5, 4.5, 22, 22), 5, 5)
    p.setBrush(QColor("#FFE070"))
    p.drawRoundedRect(QRectF(8.5, 8.5, 21, 21), 5, 5)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#D8261C"))
    for x, y, r in ((19, 21, 3.2), (14.4, 16.6, 1.6), (17.4, 14.4, 1.6), (20.6, 14.4, 1.6), (23.6, 16.6, 1.6)):
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.end()
    return QIcon(pm)


def _thumb(path, size=TILE - 12):
    reader = QImageReader(str(path))
    full = reader.size()
    if full.isValid():
        reader.setScaledSize(full.scaled(size, size, Qt.KeepAspectRatio))
    img = reader.read()
    return img


def _png_bytes(path, size=320):
    img = _thumb(path, size)
    if img.isNull():
        return None
    flat = QImage(img.size(), QImage.Format_RGB32)
    flat.fill(Qt.white)
    p = QPainter(flat)
    p.drawImage(0, 0, img)
    p.end()
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.WriteOnly)
    flat.save(buf, "PNG")
    return bytes(data)


def parse_suggestion(text):
    """'😊 | happy tail wag' -> ('😊', 'happy tail wag'), forgiving of extra words around it."""
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    left, _bar, right = line.partition("|")
    emoji = next((tok for tok in left.split() if not re.search(r"[A-Za-z0-9]", tok)), "")
    if not emoji:
        found = re.search(r"[^\w\s|,.:;'\"!?()\-]+", line)
        emoji = found.group(0) if found else ""
    meaning = re.sub(r"[^\w\s'\-]", "", right).strip().lower()
    return emoji[:8], " ".join(meaning.split()[:6])


def _tile(img, info, size=TILE):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    card = QRectF(3, 3, size - 6, size - 6)
    suggested = bool(info and info.get("suggested"))
    p.setPen(QPen(QColor("#E0A020"), 2, Qt.DashLine) if suggested else QPen(QColor("#C8C4B8"), 1))
    p.setBrush(QColor("white"))
    p.drawRoundedRect(card, 10, 10)
    if img is not None and not img.isNull():
        p.drawImage(QRectF(card.center().x() - img.width() / 2, card.center().y() - img.height() / 2,
                           img.width(), img.height()), img)
    badge = QRectF(size - 36, size - 36, 32, 32)
    p.setPen(QPen(QColor("#B0A890"), 1))
    p.setBrush(QColor(255, 255, 255, 235))
    p.drawEllipse(badge)
    if info and info.get("emoji"):
        f = QFont(EMOJI_FONT)
        f.setPixelSize(18)
        p.setFont(f)
        p.setPen(QColor("black"))
        p.drawText(badge, Qt.AlignCenter, info["emoji"])
    else:
        p.setPen(QColor("#A0A0A0"))
        p.setFont(QFont("Tahoma", 12, QFont.Bold))
        p.drawText(badge, Qt.AlignCenter, "?")
    p.end()
    return pm


class StickerManager(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.data = library.load()
        self.pack = None
        self.files = []
        self.index = -1
        self.thumbs = {}
        self.ai_queue, self.ai_job, self.ai_total = [], None, 0
        self.loader = Loader(self, threads=3)
        self.loader.loaded.connect(self._thumb_loaded)
        self.setStyleSheet("QLabel#title { font: bold 13px Tahoma; color: #203060; }"
                           "QListWidget { background: #F4F2EC; border: none; font: 11px Tahoma; }"
                           "QListWidget::item:selected { background: rgba(49,106,197,60); color: black; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet("QWidget#bar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFB,"
                          " stop:1 #E3E0D2); border-bottom: 1px solid #A0A0A0; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(6, 4, 6, 4)
        self.back = QPushButton("◄ All Packs")
        self.back.clicked.connect(self.show_shelf)
        row.addWidget(self.back)
        self.title = QLabel()
        self.title.setObjectName("title")
        row.addWidget(self.title, 1)
        self.suggest_btn = QPushButton("Suggest with AI")
        self.suggest_btn.clicked.connect(self.toggle_suggest)
        row.addWidget(self.suggest_btn)
        self.accept_btn = QPushButton("Accept suggestions")
        self.accept_btn.clicked.connect(self.accept_suggestions)
        row.addWidget(self.accept_btn)
        lay.addWidget(bar)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.shelf = self._grid(TILE + 40, TILE + 46)
        self.shelf.itemActivated.connect(lambda item: self.open_pack(item.data(Qt.UserRole)))
        self.stack.addWidget(self.shelf)
        page = QWidget()
        prow = QHBoxLayout(page)
        prow.setContentsMargins(0, 0, 0, 0)
        self.wall = self._grid(TILE + 10, TILE + 10)
        self.wall.currentRowChanged.connect(self.select)
        prow.addWidget(self.wall, 1)
        prow.addWidget(self._editor())
        self.stack.addWidget(page)
        self.status = QLabel()
        self.status.setStyleSheet("font: 11px Tahoma; padding: 2px 6px; background: #ECE9D8; border-top: 1px solid #A0A0A0;")
        lay.addWidget(self.status)
        self.show_shelf()

    def _grid(self, w, h):
        g = QListWidget()
        g.setViewMode(QListView.IconMode)
        g.setIconSize(QSize(TILE, TILE))
        g.setGridSize(QSize(w, h))
        g.setResizeMode(QListView.Adjust)
        g.setMovement(QListView.Static)
        g.setUniformItemSizes(True)
        g.setWordWrap(True)
        g.setSelectionMode(QAbstractItemView.SingleSelection)
        return g

    def _editor(self):
        panel = QWidget()
        panel.setFixedWidth(290)
        panel.setObjectName("editor")
        panel.setAttribute(Qt.WA_StyledBackground)
        panel.setStyleSheet("QWidget#editor { background: #ECE9D8; border-left: 1px solid #A0A0A0; }"
                            "QToolButton { font: 17px 'Segoe UI Emoji'; border: 1px solid transparent; border-radius: 3px; }"
                            "QToolButton:hover { border-color: #7F9DB9; background: white; }"
                            "QLabel { font: 11px Tahoma; } QLineEdit { font: 12px Tahoma; padding: 2px; }")
        col = QVBoxLayout(panel)
        self.preview = QLabel()
        self.preview.setFixedSize(270, 200)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("background: white; border: 1px solid #C0BCA8;")
        col.addWidget(self.preview)
        self.name = QLabel()
        col.addWidget(self.name)
        grid = QGridLayout()
        grid.setSpacing(1)
        for i, emoji in enumerate(PALETTE):
            b = QToolButton()
            b.setText(emoji)
            b.setFixedSize(28, 28)
            b.clicked.connect(lambda _c=False, e=emoji: self.emoji.setText(e))
            grid.addWidget(b, i // 9, i % 9)
        col.addLayout(grid)
        form = QGridLayout()
        form.addWidget(QLabel("Emoji:"), 0, 0)
        self.emoji = QLineEdit()
        self.emoji.setMaxLength(8)
        self.emoji.setStyleSheet("font: 18px 'Segoe UI Emoji';")
        form.addWidget(self.emoji, 0, 1)
        form.addWidget(QLabel("Meaning:"), 1, 0)
        self.meaning = QLineEdit()
        self.meaning.setPlaceholderText("e.g. happy tail wag")
        self.meaning.returnPressed.connect(self.save_current)
        form.addWidget(self.meaning, 1, 1)
        col.addLayout(form)
        buttons = QHBoxLayout()
        for text, slot in (("◄", lambda: self.step(-1)), ("Save", self.save_current), ("Clear", self.clear_current),
                           ("►", lambda: self.step(1))):
            b = QPushButton(text)
            b.clicked.connect(slot)
            buttons.addWidget(b)
        col.addLayout(buttons)
        col.addStretch(1)
        self.movie = None
        return panel

    # ---- the shelf ---------------------------------------------------------------------------------------------
    def show_shelf(self):
        self._stop_ai()
        self.pack = None
        self.loader.clear()
        self.data = library.load()
        self.shelf.clear()
        packs = library.packs()
        for folder in packs:
            files = library.stickers(folder)
            done = len(library.assigned(self.data, folder.name))
            item = QListWidgetItem(f"{folder.name}\n{done} of {len(files)} assigned")
            item.setData(Qt.UserRole, folder)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.shelf.addItem(item)
            if files:
                key = f"cover:{files[0]}"
                self.loader.request(key, lambda f=files[0]: _thumb(f))
                self.thumbs[key] = item
            item.setIcon(QIcon(_tile(None, None)))
        self.stack.setCurrentWidget(self.shelf)
        self.back.setEnabled(False)
        self.suggest_btn.setEnabled(False)
        self.accept_btn.setEnabled(False)
        self.title.setText("Sticker Packs")
        self.status.setText(f"{len(packs)} packs.  Open one to give its stickers emojis." if packs else
                            "Put sticker packs (a folder each) in 'Sticker Packs' on drive E: (Local Storage).")

    def _thumb_loaded(self, key, img):
        target = self.thumbs.get(key)
        if isinstance(target, QListWidgetItem):
            try:
                target.setIcon(QIcon(_tile(img, {"emoji": ""} if key.startswith("cover:") else None)))
            except RuntimeError:
                pass
            self.thumbs[key] = img
            return
        self.thumbs[key] = img
        if self.pack is not None and key.startswith("sticker:"):
            name = key.split(":", 1)[1]
            for i, f in enumerate(self.files):
                if f.name == name:
                    self._paint(i)

    # ---- a pack ------------------------------------------------------------------------------------------------
    def open_pack(self, folder):
        self.pack = folder
        self.files = library.stickers(folder)
        self.thumbs = {k: v for k, v in self.thumbs.items() if isinstance(v, QImage)}
        self.wall.clear()
        for i, f in enumerate(self.files):
            item = QListWidgetItem()
            self.wall.addItem(item)
            key = f"sticker:{f.name}"
            if key not in self.thumbs:
                self.loader.request(key, lambda path=f: _thumb(path))
            self._paint(i)
        self.stack.setCurrentIndex(1)
        self.back.setEnabled(True)
        self.suggest_btn.setEnabled(True)
        self._refresh_title()
        if self.files:
            self.wall.setCurrentRow(0)

    def _info(self, f):
        return self.data["packs"].get(self.pack.name, {}).get(f.name)

    def _paint(self, i):
        item = self.wall.item(i)
        if item is None:
            return
        f = self.files[i]
        info = self._info(f)
        item.setIcon(QIcon(_tile(self.thumbs.get(f"sticker:{f.name}"), info)))
        item.setToolTip(f"{info['emoji']}  {info.get('meaning', '')}" if info and info.get("emoji") else "No emoji yet")

    def _refresh_title(self):
        pack = self.data["packs"].get(self.pack.name, {})
        done = sum(1 for f in self.files if pack.get(f.name, {}).get("emoji"))
        guesses = sum(1 for f in self.files if pack.get(f.name, {}).get("suggested"))
        self.title.setText(f"{self.pack.name}  -  {done} of {len(self.files)} assigned"
                           + (f", {guesses} suggested by AI (dashed)" if guesses else ""))
        self.accept_btn.setEnabled(bool(guesses))

    def select(self, i):
        if not (0 <= i < len(self.files)):
            return
        self.index = i
        f = self.files[i]
        if self.movie is not None:
            self.movie.stop()
        self.movie = QMovie(str(f))
        if self.movie.isValid():
            size = QImageReader(str(f)).size()
            if size.isValid():
                self.movie.setScaledSize(size.scaled(260, 190, Qt.KeepAspectRatio))
            self.preview.setMovie(self.movie)
            self.movie.start()
        else:
            self.preview.setPixmap(QPixmap(str(f)).scaled(260, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        info = self._info(f) or {}
        self.name.setText(f"{f.name}" + ("   (AI suggestion)" if info.get("suggested") else ""))
        self.emoji.setText(info.get("emoji", ""))
        self.meaning.setText(info.get("meaning", ""))
        self.meaning.setFocus()

    def step(self, way):
        if self.files:
            self.wall.setCurrentRow((self.index + way) % len(self.files))

    def _store(self, f, emoji, meaning, suggested=False):
        pack = self.data["packs"].setdefault(self.pack.name, {})
        if emoji:
            pack[f.name] = {"emoji": emoji, "meaning": meaning, "suggested": suggested}
        else:
            pack.pop(f.name, None)
        library.save(self.data)

    def save_current(self):
        if not (0 <= self.index < len(self.files)):
            return
        emoji = self.emoji.text().strip()
        self._store(self.files[self.index], emoji, " ".join(self.meaning.text().split()))
        self._paint(self.index)
        self._refresh_title()
        if emoji:
            self.step(1)

    def clear_current(self):
        if 0 <= self.index < len(self.files):
            self._store(self.files[self.index], "", "")
            self.emoji.clear()
            self.meaning.clear()
            self._paint(self.index)
            self._refresh_title()

    def accept_suggestions(self):
        pack = self.data["packs"].get(self.pack.name, {})
        for info in pack.values():
            info["suggested"] = False
        library.save(self.data)
        for i in range(len(self.files)):
            self._paint(i)
        self._refresh_title()
        self.status.setText("All the AI's suggestions in this pack are accepted.")

    # ---- Suggest with AI ---------------------------------------------------------------------------------------
    def toggle_suggest(self):
        if self.ai_job is not None or self.ai_queue:
            self._stop_ai()
            self.status.setText("Stopped suggesting.")
            return
        try:
            from claudecore.ai import ai_models
            model = ai_models.vision_model()
            seeing = ai_models.get(model).vision
        except Exception:
            model, seeing = None, False
        if not model or not seeing:
            host.message(self.desktop, "Sticker Manager", "Suggest with AI needs a language model that can see "
                         "pictures (one with an mmproj file in E:\\LLM Models).", "warning")
            return
        self.ai_model = model
        self.ai_queue = [i for i, f in enumerate(self.files) if not (self._info(f) or {}).get("emoji")]
        self.ai_total = len(self.ai_queue)
        if not self.ai_queue:
            self.status.setText("Every sticker in this pack already has an emoji.")
            return
        self.suggest_btn.setText("Stop suggesting")
        self._next_suggestion()

    def _next_suggestion(self):
        if not self.ai_queue or self.pack is None:
            self._stop_ai()
            self.status.setText(f"Suggested emojis for {self.ai_total} sticker{'' if self.ai_total == 1 else 's'}. "
                                "Look them over, then Save each or Accept suggestions.")
            return
        i = self.ai_queue.pop(0)
        f = self.files[i]
        png = _png_bytes(f)
        if png is None:
            self._next_suggestion()
            return
        done = self.ai_total - len(self.ai_queue)
        self.status.setText(f"Suggesting {done} of {self.ai_total}: {f.name}...")
        from claudecore.ai import broker
        pack_name = self.pack.name
        self.ai_job = broker.get().chat(self.ai_model, [{"role": "user", "content": PROMPT, "images": [png]}],
                                        {"temperature": 0.3, "num_predict": 40},
                                        lambda text, err, f=f, i=i, p=pack_name: self._suggested(f, i, p, text, err),
                                        priority=broker.FOREGROUND)

    def _suggested(self, f, i, pack_name, text, err):
        self.ai_job = None
        if not isValid(self) or self.suggest_btn.text() != "Stop suggesting":     # (stopped meanwhile)
            return
        if err:
            self._stop_ai()
            self.status.setText(f"The language model couldn't help: {err}")
            return
        emoji, meaning = parse_suggestion(text)
        if emoji and self.pack is not None and self.pack.name == pack_name:
            if not (self._info(f) or {}).get("emoji"):              # (the user may have done this one meanwhile)
                self._store(f, emoji, meaning, suggested=True)
                self._paint(i)
                if i == self.index:
                    self.select(i)
                self._refresh_title()
        if self.ai_queue or self.ai_job is None:
            self._next_suggestion()

    def _stop_ai(self):
        self.ai_queue = []
        if self.ai_job is not None:
            try:
                self.ai_job.stop()
            except Exception:
                pass
            self.ai_job = None
        self.suggest_btn.setText("Suggest with AI")

    def closeEvent(self, event):
        self._stop_ai()
        self.loader.clear()
        if self.movie is not None:
            self.movie.stop()
        super().closeEvent(event)


_open = {}


def open_stickers(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = StickerManager(desktop)
        win = host.window(desktop, "Sticker Manager", body, stickers_icon(), (900, 620))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content._stop_ai()
