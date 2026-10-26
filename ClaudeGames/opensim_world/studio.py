"""Furry SL Persona Studio: who the 34 main residents are in Second Life (the Furry Hollow) - when they log on, where
they go, what they do there, how sociable they are, what they're open to in the adults' regions, and what they wear -
with galleries of the furry bodies and the clothing to dress them from.

The settings live in personas.json (see personas.py); looks are mirrored into wardrobe.json for the Tailor, and a
changed look is fitted by running the Tailor (a second viewer window for a couple of minutes per resident)."""
import json
import os
import subprocess
import sys

from PySide6.QtCore import QProcess, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
                               QScrollArea, QSlider, QSpinBox, QSplitter, QTabWidget, QTextEdit, QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore import host

from . import HERE, QUIET_REGIONS, REGIONS, catalog, dress, personas

LIVED_IN = [r[0] for r in REGIONS if r[0] not in QUIET_REGIONS]     # where residents go

_state = {"frame": None}
TIMEZONES = ["America/New_York", "America/Chicago", "America/Denver", "America/Phoenix", "America/Los_Angeles",
             "America/Vancouver", "America/Toronto", "America/Halifax", "Europe/London", "Europe/Dublin",
             "Europe/Amsterdam", "Europe/Berlin", "Europe/Stockholm", "Australia/Perth", "Australia/Brisbane",
             "Australia/Sydney", "Australia/Melbourne", "Pacific/Auckland"]


def studio_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#B388EB"))
    g.setColorAt(1, QColor("#6A3FA0"))
    p.setPen(QPen(QColor("#3E2466"), 1))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(3 * s, 2 * s, 26 * s, 28 * s), 3 * s, 3 * s)       # a wardrobe
    p.setPen(QPen(QColor("#3E2466"), 1))
    p.drawLine(int(16 * s), int(4 * s), int(16 * s), int(28 * s))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#FFFFFF"))
    for x, y in ((11, 12), (16, 10), (21, 12)):                          # a paw on the door
        p.drawEllipse(QRectF((x - 1.6) * s, (y - 1.6) * s, 3.2 * s, 3.2 * s))
    p.drawEllipse(QRectF(13 * s, 14 * s, 6 * s, 5 * s))
    p.setBrush(QColor("#F2D16B"))
    p.drawEllipse(QRectF(13.5 * s, 22 * s, 2 * s, 2 * s))
    p.drawEllipse(QRectF(16.5 * s, 22 * s, 2 * s, 2 * s))
    p.end()
    return QIcon(pm)


def _thumb(name):
    if not name:
        return None
    path = catalog.folder() / "thumbs" / name
    return QIcon(str(path)) if path.exists() else None


def _hours_text(hours):
    def t(h):
        return f"{int(h) % 24:02d}:{int(round((h % 1) * 60)):02d}"
    return ", ".join(f"{t(a)}-{t(b)}" for a, b in hours)


def _parse_hours(text):
    out = []
    for part in text.split(","):
        if "-" not in part:
            continue
        a, b = part.split("-", 1)
        try:
            def h(x):
                x = x.strip().replace(".", ":")
                hh, _, mm = x.partition(":")
                return (int(hh) + (int(mm) if mm else 0) / 60) % 24
            out.append([round(h(a), 2), round(h(b), 2)])
        except ValueError:
            continue
    return out or [[19, 23]]


class Gallery(QWidget):
    """Bodies, clothes or hair as a grid of pictures, with filters; double-click (or Use) picks one."""

    def __init__(self, section="bodies", on_pick=None):
        super().__init__()
        self.index = catalog.load()
        self.on_pick = on_pick or (lambda entry: None)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        self.section = QComboBox()
        self.section.addItems(["Bodies", "Clothes", "Hair"])
        self.section.setCurrentIndex(["bodies", "clothes", "hair"].index(section))
        self.layer = QComboBox()
        self.who = QComboBox()
        self.who.addItems(["anyone", "men", "women", "accessories"])
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")
        for w in (self.section, self.layer, self.who, self.search):
            row.addWidget(w)
        v.addLayout(row)
        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(96, 128))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setWordWrap(True)
        self.grid.setGridSize(QSize(118, 172))
        self.grid.setUniformItemSizes(True)
        self.grid.itemDoubleClicked.connect(lambda item: self.on_pick(item.data(Qt.UserRole)))
        v.addWidget(self.grid, 1)
        self.count = QLabel("")
        v.addWidget(self.count)
        self.section.currentIndexChanged.connect(self._layers)
        for w in (self.layer, self.who):
            w.currentIndexChanged.connect(self.refresh)
        self.search.textChanged.connect(self.refresh)
        self._layers()

    def _layers(self):
        sec = self.section.currentText().lower()
        self.layer.blockSignals(True)
        self.layer.clear()
        if sec == "bodies":
            self.layer.addItems(["all", "furry", "human", "male", "female"])
        elif sec == "hair":
            self.layer.addItems(["all"])
        else:
            self.layer.addItems(["all"] + sorted({c["layer"] for c in self.index.get("clothes", []) if c["layer"]}))
        self.layer.blockSignals(False)
        self.who.setVisible(sec == "clothes")
        self.refresh()

    def entries(self):
        sec = self.section.currentText().lower()
        f, who, q = self.layer.currentText(), self.who.currentText(), self.search.text().lower()
        out = []
        for e in self.index.get(sec, []):
            if sec == "bodies" and f != "all" and f not in (e["kind"], e["gender"]):
                continue
            if sec == "clothes" and f != "all" and e["layer"] != f:
                continue
            if sec == "clothes" and who != "anyone" and e["pack"] != who:
                continue
            text = " ".join([e.get("name", ""), e.get("folder", ""), e.get("pack", ""), e.get("kind", "")]).lower()
            if q and q not in text:
                continue
            out.append(e)
        return out

    def refresh(self):
        self.grid.clear()
        sec = self.section.currentText().lower()
        entries = self.entries()
        for e in entries[:600]:
            label = e["name"] if sec == "bodies" else f"{e['name']}\n({e['folder'].split('/')[-1]})"
            item = QListWidgetItem(label)
            icon = _thumb(e.get("thumb"))
            if icon is not None:
                item.setIcon(icon)
            item.setToolTip("\n".join(f"{k}: {v}" for k, v in e.items() if k not in ("thumb", "id") and v))
            item.setData(Qt.UserRole, dict(e, section=sec))
            self.grid.addItem(item)
        self.count.setText(f"{len(entries)} shown" + (" (first 600)" if len(entries) > 600 else "") +
                           ". Double-click one to use it for the selected resident.")


class PickDialog(QDialog):
    def __init__(self, parent, section, title):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(760, 560)
        self.picked = None
        v = QVBoxLayout(self)
        self.gallery = Gallery(section, self._pick)
        v.addWidget(self.gallery, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._ok)
        buttons.rejected.connect(self.reject)
        v.addWidget(buttons)

    def _pick(self, entry):
        self.picked = entry
        self.accept()

    def _ok(self):
        item = self.gallery.grid.currentItem()
        if item is not None:
            self.picked = item.data(Qt.UserRole)
            self.accept()


class _Checks(QListWidget):
    """A list of checkable names."""

    def __init__(self, names):
        super().__init__()
        for n in names:
            item = QListWidgetItem(n)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.addItem(item)
        self.setMaximumHeight(24 * min(len(names), 9) + 8)

    def set(self, chosen):
        for i in range(self.count()):
            self.item(i).setCheckState(Qt.Checked if self.item(i).text() in chosen else Qt.Unchecked)

    def get(self):
        return [self.item(i).text() for i in range(self.count()) if self.item(i).checkState() == Qt.Checked]


def _slider(lo, hi):
    s = QSlider(Qt.Horizontal)
    s.setRange(lo, hi)
    return s


class StudioBody(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.setStyleSheet("QWidget { font-family: 'Segoe UI'; font-size: 12px; }")
        self.names = self._cast()
        self.wardrobe = dress.wardrobe()
        self.data = personas.load_all()
        self.current = None
        self.proc = None
        split = QSplitter()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.addWidget(split, 1)
        # the residents
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.list = QListWidget()
        self.list.setIconSize(QSize(48, 72))
        index = catalog.load()
        for n in self.names:
            item = QListWidgetItem(n)
            icon = _thumb(index.get("residents", {}).get(dress.slug(n)))
            if icon is not None:
                item.setIcon(icon)
            self.list.addItem(item)
        self.list.currentTextChanged.connect(self._show)
        lv.addWidget(self.list, 1)
        self.online = QLabel("")
        self.online.setWordWrap(True)
        lv.addWidget(self.online)
        split.addWidget(left)
        # the settings
        self.tabs = QTabWidget()
        self.tabs.addTab(self._account_tab(), "Account")
        self.tabs.addTab(self._habits_tab(), "Habits")
        self.tabs.addTab(self._social_tab(), "Social")
        self.tabs.addTab(self._adult_tab(), "Adult")
        self.tabs.addTab(self._look_tab(), "Look")
        self.gallery = Gallery("bodies", self._use_from_gallery)
        self.tabs.addTab(self.gallery, "Gallery")
        split.addWidget(self.tabs)
        split.setSizes([200, 620])
        # the buttons
        row = QHBoxLayout()
        self.status = QLabel("")
        row.addWidget(self.status, 1)
        self.reset_btn = QPushButton("Reset to defaults")
        self.reset_btn.clicked.connect(self._reset)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save)
        self.fit_btn = QPushButton("Fit changed looks")
        self.fit_btn.setToolTip("Runs the Tailor: a second viewer tries each changed look on and saves it (a couple of "
                                "minutes per resident). The Furry Hollow must be closed first.")
        self.fit_btn.clicked.connect(self._fit)
        for b in (self.reset_btn, self.save_btn, self.fit_btn):
            row.addWidget(b)
        outer.addLayout(row)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(90)
        self.log.hide()
        outer.addWidget(self.log)
        self.clock = QTimer(self)
        self.clock.timeout.connect(self._who_is_on)
        self.clock.start(60000)
        if self.names:
            self.list.setCurrentRow(0)
        self._who_is_on()

    # ---- the cast ----
    def _cast(self):
        try:
            import residents
            return list(residents.names(2025, tier="main"))
        except Exception:
            return sorted(dress.wardrobe().get("picks", {}))

    def _resident(self, name):
        try:
            import residents
            return residents.load(name, 2025)
        except Exception:
            return None

    def persona(self, name):
        data = personas.get(name, self._resident(name), self.wardrobe)
        if name in self.data:                           # edits this session, saved or not
            data.update(self.data[name])
        return data

    # ---- tabs ----
    @staticmethod
    def _form():
        """A tab with a form at the top (not stretched down the whole tab)."""
        w = QWidget()
        v = QVBoxLayout(w)
        f = QFormLayout()
        v.addLayout(f)
        v.addStretch()
        return w, f

    def _account_tab(self):
        w, f = self._form()
        self.sl_name = QLabel("")
        self.display_name = QLineEdit()
        self.gender = QLabel("")
        self.about = QTextEdit()
        self.about.setMaximumHeight(70)
        self.partner = QLineEdit()
        self.groups = QLineEdit()
        self.maturity = QComboBox()
        self.maturity.addItems(personas.MATURITY)
        self.home = QComboBox()
        self.home.addItems(LIVED_IN)
        self.home.currentTextChanged.connect(self._parcels)
        self.parcel = QComboBox()
        self.days = QSpinBox()
        self.days.setRange(0, 7)
        self.hours = QLineEdit()
        self.hours.setPlaceholderText("19:30-23:00, 14:00-17:00  (their own local time)")
        self.session = QDoubleSpinBox()
        self.session.setRange(0.5, 12)
        self.session.setSingleStep(0.5)
        self.tz = QComboBox()
        self.tz.setEditable(True)
        self.tz.addItems(TIMEZONES)
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Anything else about how they are in Second Life; the residents are told this.")
        f.addRow("Second Life name", self.sl_name)
        f.addRow("Display name", self.display_name)
        f.addRow("Gender", self.gender)
        f.addRow("Profile (About)", self.about)
        f.addRow("Partner", self.partner)
        f.addRow("Groups", self.groups)
        f.addRow("Maturity rating", self.maturity)
        f.addRow("Home region", self.home)
        f.addRow("Home parcel", self.parcel)
        f.addRow("Days online a week", self.days)
        f.addRow("Typical hours", self.hours)
        f.addRow("Hours per session", self.session)
        f.addRow("Time zone", self.tz)
        f.addRow("Notes", self.notes)
        return w

    def _parcels(self, region):
        """The parcels of the chosen home region (from the world's land table), as the home-parcel choices."""
        current = self.parcel.currentText()
        self.parcel.blockSignals(True)
        self.parcel.clear()
        self.parcel.addItem("(anywhere)", None)
        for name, spot, area in personas.parcels(region):
            if area < 60000:
                self.parcel.addItem(f"{name}  ({int(area)} sq m)", spot)
        self.parcel.setCurrentText(current)
        self.parcel.blockSignals(False)

    def _habits_tab(self):
        w, f = self._form()
        self.usually = _Checks(personas.ACTIVITIES)
        self.sometimes = _Checks(personas.ACTIVITIES)
        self.favourites = _Checks(LIVED_IN)
        self.avoids = _Checks(LIVED_IN)
        f.addRow("Usually does", self.usually)
        f.addRow("Sometimes does", self.sometimes)
        f.addRow("Favourite regions", self.favourites)
        f.addRow("Avoids regions", self.avoids)
        note = QLabel("Activities decide where they go: " + "; ".join(
            f"{r}: {', '.join(a)}" for r, a in personas.REGION_ROLES.items()))
        note.setWordWrap(True)
        f.addRow(note)
        return w

    def _social_tab(self):
        w, f = self._form()
        self.crowds = _slider(-100, 100)
        self.chattiness = _slider(0, 100)
        self.im_over_local = _slider(0, 100)
        self.roleplay = QCheckBox("Engages in roleplay")
        self.rp_receptive = _slider(0, 100)
        self.invites_receptive = _slider(0, 100)
        self.initiates = _slider(0, 100)
        self.rp_style = QLineEdit()
        f.addRow("Avoids crowds ... seeks crowds", self.crowds)
        f.addRow("Chattiness", self.chattiness)
        f.addRow("Prefers IMs over local chat", self.im_over_local)
        f.addRow("", self.roleplay)
        f.addRow("Receptive to roleplay", self.rp_receptive)
        f.addRow("Receptive to invitations (sit, dance)", self.invites_receptive)
        f.addRow("Starts conversations", self.initiates)
        f.addRow("Roleplay style", self.rp_style)
        return w

    def _adult_tab(self):
        w, f = self._form()
        self.visits = QComboBox()
        self.visits.addItems(personas.ADULT_VISITS)
        self.engages = _Checks(personas.ADULT_ACTS)
        self.adult_with = QComboBox()
        self.adult_with.addItems(personas.ADULT_WITH)
        self.with_user = QCheckBox("Open to that with you")
        f.addRow(QLabel("The residents are all adults. This decides whether they go to the adults' regions "
                        "(Whitewood, Castle LoveGlo) and what they'll do there."))
        f.addRow("Visits adult regions", self.visits)
        f.addRow("Engages in", self.engages)
        f.addRow("With", self.adult_with)
        f.addRow("", self.with_user)
        return w

    def _look_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        top = QHBoxLayout()
        self.body_pic = QLabel()
        self.body_pic.setFixedSize(128, 224)
        self.body_pic.setFrameShape(QFrame.StyledPanel)
        self.body_pic.setAlignment(Qt.AlignCenter)
        top.addWidget(self.body_pic)
        col = QVBoxLayout()
        self.body_name = QLabel("")
        col.addWidget(self.body_name)
        b = QPushButton("Choose body...")
        b.clicked.connect(lambda: self._pick("bodies", "Choose a body"))
        col.addWidget(b)
        self.me_pic = QLabel()
        self.me_pic.setFixedSize(128, 224)
        self.me_pic.setFrameShape(QFrame.StyledPanel)
        self.me_pic.setAlignment(Qt.AlignCenter)
        col.addWidget(QLabel("As last fitted:"))
        col.addWidget(self.me_pic)
        col.addStretch()
        top.addLayout(col)
        clothes = QVBoxLayout()
        clothes.addWidget(QLabel("Clothes and accessories (worn over the body):"))
        self.clothes = QListWidget()
        self.clothes.setIconSize(QSize(40, 40))
        clothes.addWidget(self.clothes, 1)
        brow = QHBoxLayout()
        add = QPushButton("Add garment...")
        add.clicked.connect(lambda: self._pick("clothes", "Add a garment"))
        rem = QPushButton("Remove")
        rem.clicked.connect(self._remove_garment)
        brow.addWidget(add)
        brow.addWidget(rem)
        clothes.addLayout(brow)
        self.fitted = QLabel("")
        clothes.addWidget(self.fitted)
        top.addLayout(clothes, 1)
        v.addLayout(top)
        return w

    # ---- showing and collecting ----
    def _show(self, name):
        if self.current:
            self._collect()
        self.current = name
        if not name:
            return
        p = self.persona(name)
        self.sl_name.setText(p["sl_name"])
        self.display_name.setText(p.get("display_name", ""))
        self.gender.setText(p.get("gender", ""))
        self.about.setPlainText(p.get("about", ""))
        self.partner.setText(p.get("partner", ""))
        self.groups.setText(", ".join(p.get("groups", [])))
        self.maturity.setCurrentText(p.get("maturity", "Moderate"))
        self.home.setCurrentText(p["home"]["region"])
        self._parcels(p["home"]["region"])
        want = p["home"].get("parcel") or "(anywhere)"
        for i in range(self.parcel.count()):
            if self.parcel.itemText(i).split("  (")[0] == want:
                self.parcel.setCurrentIndex(i)
                break
        s = p["schedule"]
        self.days.setValue(int(s.get("days_per_week", 5)))
        self.hours.setText(_hours_text(s.get("hours", [[19, 23]])))
        self.session.setValue(float(s.get("session_hours", 2.5)))
        self.tz.setCurrentText(s.get("timezone", "America/New_York"))
        self.notes.setPlainText(p.get("notes", ""))
        self.usually.set(p.get("usually", []))
        self.sometimes.set(p.get("sometimes", []))
        self.favourites.set(p.get("favourite_regions", []))
        self.avoids.set(p.get("avoids_regions", []))
        so = p["social"]
        self.crowds.setValue(int(so.get("crowds", 0) * 100))
        for key, w in (("chattiness", self.chattiness), ("im_over_local", self.im_over_local),
                       ("rp_receptive", self.rp_receptive), ("invites_receptive", self.invites_receptive),
                       ("initiates", self.initiates)):
            w.setValue(int(so.get(key, 0.5) * 100))
        self.roleplay.setChecked(bool(so.get("roleplay", True)))
        self.rp_style.setText(so.get("rp_style", ""))
        a = p["adult"]
        self.visits.setCurrentText(a.get("visits", "never"))
        self.engages.set(a.get("engages", []))
        self.adult_with.setCurrentText(a.get("with", "friends"))
        self.with_user.setChecked(bool(a.get("with_user", False)))
        self._show_look(p)
        self.status.setText(f"{name}: " + ("online now" if personas.online(p, name) else "offline now") +
                            f", home {p['home']['region']}")

    def _show_look(self, p):
        look = p.get("look", {})
        index = catalog.load()
        body = next((b for b in index.get("bodies", []) if b["slug"] == look.get("body")), None)
        self.body_name.setText(body["name"] if body else (look.get("body") or "(none)"))
        icon = _thumb(body["thumb"]) if body else None
        self.body_pic.setPixmap(icon.pixmap(128, 224) if icon else QPixmap())
        me = _thumb(index.get("residents", {}).get(dress.slug(self.current)))
        self.me_pic.setPixmap(me.pixmap(128, 224) if me else QPixmap())
        self.clothes.clear()
        for folder, item in look.get("clothes", []):
            entry = next((c for c in index.get("clothes", []) if c["name"].lower() == item.lower() and
                          c["folder"].split("/")[-1].lower() == folder.lower()), None)
            li = QListWidgetItem(f"{item}  ({folder})")
            icon = _thumb(entry["thumb"]) if entry else None
            if icon:
                li.setIcon(icon)
            li.setData(Qt.UserRole, [folder, item])
            self.clothes.addItem(li)
        self.fitted.setText("" if look.get("fitted", True) else "Changed: not fitted yet (Save, then Fit changed looks).")

    def _collect(self):
        name = self.current
        p = self.persona(name)
        p["display_name"] = self.display_name.text().strip() or name
        p["about"] = self.about.toPlainText().strip()
        p["partner"] = self.partner.text().strip()
        p["groups"] = [g.strip() for g in self.groups.text().split(",") if g.strip()]
        p["maturity"] = self.maturity.currentText()
        p["home"]["region"] = self.home.currentText()
        lot = self.parcel.currentData()
        p["home"]["parcel"] = self.parcel.currentText().split("  (")[0] if lot else None
        p["home"]["spot"] = [round(lot[0], 1), round(lot[1], 1)] if lot else None
        p["schedule"].update(days_per_week=self.days.value(), hours=_parse_hours(self.hours.text()),
                             session_hours=self.session.value(), timezone=self.tz.currentText().strip())
        p["notes"] = self.notes.toPlainText().strip()
        p["usually"] = self.usually.get()
        p["sometimes"] = self.sometimes.get()
        p["favourite_regions"] = self.favourites.get()
        p["avoids_regions"] = self.avoids.get()
        p["social"].update(crowds=self.crowds.value() / 100, chattiness=self.chattiness.value() / 100,
                           im_over_local=self.im_over_local.value() / 100, roleplay=self.roleplay.isChecked(),
                           rp_receptive=self.rp_receptive.value() / 100,
                           invites_receptive=self.invites_receptive.value() / 100,
                           initiates=self.initiates.value() / 100, rp_style=self.rp_style.text().strip())
        p["adult"].update(visits=self.visits.currentText(), engages=self.engages.get(),
                          **{"with": self.adult_with.currentText()}, with_user=self.with_user.isChecked())
        p["look"]["clothes"] = [self.clothes.item(i).data(Qt.UserRole) for i in range(self.clothes.count())]
        self.data[name] = p
        return p

    # ---- the look ----
    def _pick(self, section, title):
        if not self.current:
            return
        dlg = PickDialog(self, section, title)
        if dlg.exec() == QDialog.Accepted and dlg.picked:
            self._use_from_gallery(dlg.picked)

    def _use_from_gallery(self, entry):
        if not self.current or not entry:
            return
        p = self._collect()
        if entry.get("section") == "bodies":
            p["look"]["body"] = entry["slug"]
        elif entry.get("section") == "clothes":
            pair = [entry["folder"].split("/")[-1], entry["name"]]
            if pair not in p["look"]["clothes"]:
                p["look"]["clothes"].append(pair)
        else:
            return
        p["look"]["fitted"] = False
        self.data[self.current] = p
        self._show_look(p)
        self.tabs.setCurrentIndex(4)

    def _remove_garment(self):
        row = self.clothes.currentRow()
        if row < 0:
            return
        p = self._collect()
        del p["look"]["clothes"][row]
        p["look"]["fitted"] = False
        self.data[self.current] = p
        self._show_look(p)

    # ---- saving, resetting, fitting ----
    def _save(self):
        if self.current:
            self._collect()
        personas.save_all(self.data)
        w = self.wardrobe
        for name, p in self.data.items():
            look = p.get("look", {})
            if look.get("body"):
                w.setdefault("picks", {})[name] = look["body"]
            w.setdefault("clothes", {})[name] = look.get("clothes", [])
        lines = ["{", f'  "about": {json.dumps(w.get("about", ""), ensure_ascii=False)},', '  "picks": {']
        picks, clothes = w.get("picks", {}), w.get("clothes", {})
        lines += [f'    {json.dumps(k)}: {json.dumps(v)}' + ("," if i < len(picks) - 1 else "")
                  for i, (k, v) in enumerate(picks.items())]
        lines += ["  },", '  "clothes": {']
        lines += [f'    {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}' + ("," if i < len(clothes) - 1 else "")
                  for i, (k, v) in enumerate(clothes.items())]
        lines += ["  }", "}"]
        (HERE / "wardrobe.json").write_text("\n".join(lines) + "\n", encoding="utf-8")
        pending = [n for n, p in self.data.items() if not p.get("look", {}).get("fitted", True)]
        if pending:
            try:                                        # the Tailor rebuilds the residents' folder next time
                from . import world_file
                data = json.loads(world_file().read_text(encoding="utf-8"))
                data.setdefault("tailor", {})["residents_pack"] = False
                world_file().write_text(json.dumps(data, indent=2), encoding="utf-8")
            except (OSError, ValueError):
                pass
        self.status.setText("Saved." + (f" {len(pending)} look(s) to fit." if pending else ""))

    def _reset(self):
        if not self.current:
            return
        self.data.pop(self.current, None)
        self.data[self.current] = personas.defaults(self.current, self._resident(self.current), dress.wardrobe())
        self._show(self.current)
        self.status.setText(f"{self.current}: back to the defaults (not saved yet).")

    def _fit(self):
        if self.proc is not None and self.proc.state() != QProcess.NotRunning:
            self.status.setText("The Tailor is already working.")
            return
        try:
            from . import program
            server = program._state.get("server")
            if server is not None and server.running():
                host.message(self.desktop, "Furry SL Persona Studio",
                             "Close the Furry Hollow first: the Tailor needs the world to itself for a few minutes.")
                return
        except Exception:
            pass
        self._save()
        pending = [n for n, p in self.data.items() if not p.get("look", {}).get("fitted", True)]
        if not pending:
            self.status.setText("Every look is fitted already.")
            return
        self.log.show()
        self.log.clear()
        self.proc = QProcess(self)
        env = self.proc.processEnvironment()
        env.insert("PYTHONPATH", os.pathsep.join([str(HERE.parent), str(HERE.parent.parent / "ClaudeCore"),
                                                  str(HERE.parent.parent / "ClaudeXP"), str(HERE.parent.parent)]))
        env.insert("PYTHONUNBUFFERED", "1")
        self.proc.setProcessEnvironment(env)
        self.proc.setWorkingDirectory(str(HERE.parent))
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyRead.connect(lambda: self.log.appendPlainText(
            bytes(self.proc.readAll()).decode("utf-8", "replace").rstrip()))
        self.proc.finished.connect(lambda code, _st: self._fitted(pending, code))
        self.proc.start(sys.executable, ["-m", "opensim_world.tailor", "residents", *pending, "120"])
        self.fit_btn.setEnabled(False)
        self.status.setText(f"Fitting {', '.join(pending)}... (a viewer window opens; a couple of minutes each)")

    def _fitted(self, names, code):
        self.fit_btn.setEnabled(True)
        if code == 0:
            for n in names:
                if n in self.data:
                    self.data[n].setdefault("look", {})["fitted"] = True
            personas.save_all(self.data)
            try:
                catalog.build(progress=lambda t: None)   # their new photos into the galleries
            except Exception:
                pass
            self.status.setText(f"Fitted {', '.join(names)}.")
            if self.current:
                self._show_look(self.persona(self.current))
        else:
            self.status.setText("The Tailor stopped early; see the log.")

    def _who_is_on(self):
        on = [n for n in self.names if personas.online(self.persona(n), n)]
        self.online.setText("Online now: " + (", ".join(on) if on else "nobody") + ".")

    def closeEvent(self, event):
        if self.current:
            self._collect()
        if self.proc is not None and self.proc.state() != QProcess.NotRunning:
            self.proc.kill()
        _state["frame"] = None
        event.accept()


def open_studio(desktop):
    frame = _state.get("frame")
    if frame is not None and isValid(frame):
        desktop.open_window(frame)
        return frame
    body = StudioBody(desktop)
    frame = host.window(desktop, "Furry SL Persona Studio", body, studio_icon(), (900, 620))
    body.frame = frame
    _state["frame"] = frame
    desktop.open_window(frame)
    return frame
