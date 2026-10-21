"""The encoder/decoder for both codes, as one widget: the launcher's profile and the eras' Fur Codes program use it.

CodesEditor(furcode, yiffcode) has a tab per code. Each tab has the code itself (type or paste one), the encoder (every
category as a menu, with its sub-options, species and flags) and the decoder (the code in words). Typing a code fills
the encoder in; changing the encoder rewrites the code. codes() -> {"furcode", "yiffcode"}; `changed` fires on edits.
It takes its colours from wherever it's shown."""
import html

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QScrollArea, QSplitter, QTabWidget, QTextBrowser,
                               QVBoxLayout, QWidget)

from . import furcode, yiffcode
from .furcode_tables import CATEGORY_NAMES, SPECIES_BY_CATEGORY, TABLES

LEAVE_OUT = "(leave out)"


def _combo(items, width=None):
    """items: [(data, text)]."""
    box = QComboBox()
    for data, text in items:
        box.addItem(text, data)
    if width:
        box.setMinimumWidth(width)
    return box


def _set(box, data):
    i = box.findData(data)
    box.setCurrentIndex(i if i >= 0 else 0)


def decoded_html(rows):
    out, side = [], None
    for s, name, words in rows:
        if s != side:
            side = s
            out.append(f"<tr><td colspan='2'><br><b>{html.escape(s)}</b></td></tr>")
        out.append(f"<tr><td style='padding-right:12px; white-space:nowrap'>{html.escape(name)}</td>"
                   f"<td>{html.escape(words)}</td></tr>")
    return "<table cellspacing='2'>" + "".join(out) + "</table>" if out else "<i>Type or paste a code.</i>"


class _CodeTab(QWidget):
    changed = Signal()

    def __init__(self, title, placeholder):
        super().__init__()
        self._busy = False
        col = QVBoxLayout(self)
        col.setContentsMargins(6, 6, 6, 6)
        row = QHBoxLayout()
        row.addWidget(QLabel(title))
        self.line = QLineEdit()
        self.line.setPlaceholderText(placeholder)
        self.line.textEdited.connect(self._typed)
        row.addWidget(self.line, 1)
        clear = QPushButton("Clear")
        clear.clicked.connect(lambda: self.set_code(""))
        row.addWidget(clear)
        col.addLayout(row)
        split = QSplitter(Qt.Horizontal)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.form_host = QWidget()
        scroll.setWidget(self.form_host)
        split.addWidget(scroll)
        self.words = QTextBrowser()
        self.words.setOpenLinks(False)
        split.addWidget(self.words)
        split.setSizes([560, 380])
        col.addWidget(split, 1)
        self.timer = QTimer(self, singleShot=True, interval=350, timeout=self._read_line)

    def _typed(self, _text):
        self.timer.start()

    def _read_line(self):
        self._busy = True
        try:
            self.fill(self.line.text().strip())
        finally:
            self._busy = False
        self._show_words()
        self.changed.emit()

    def _form_changed(self, *_):
        if self._busy:
            return
        self.line.setText(self.build())
        self._show_words()
        self.changed.emit()

    def set_code(self, code):
        self.line.setText(code or "")
        self._read_line()

    def code(self):
        return self.line.text().strip()

    def _show_words(self):
        code = self.code()
        try:
            rows = self.describe(code) if code else []
        except Exception:
            rows = [("?", "Not understood", code)]
        self.words.setHtml(decoded_html(rows))

    def _watch(self, *widgets):
        for w in widgets:
            if isinstance(w, QComboBox):
                w.currentIndexChanged.connect(self._form_changed)
            elif isinstance(w, QCheckBox):
                w.toggled.connect(self._form_changed)
            elif isinstance(w, QLineEdit):
                w.editingFinished.connect(self._form_changed)


# ---- Furry Code ------------------------------------------------------------------------------------------------
class FurCodeTab(_CodeTab):
    SUB_LETTERS = {"D": "m", "M": "tls", "V": "m", "c": "bhlmw", "i": "wf", "j": "sd", "m": "ail"}

    def __init__(self):
        super().__init__("Furry Code 2.0", "FCG3rs A- C+++ ... Smb smb")
        self.describe = furcode.describe
        form = QVBoxLayout(self.form_host)
        # the fursona
        box = QGroupBox("Fursona")
        f = QFormLayout(box)
        self.cat = _combo([("", LEAVE_OUT)] + [(c, n) for c, n in CATEGORY_NAMES.items()] +
                          [("custom", "Custom..."), ("F?", "? Unsure"), ("F!", "! None"), ("F#", "# Private")], 220)
        self.cat.currentIndexChanged.connect(self._fill_species)
        f.addRow("Species group", self.cat)
        self.species = QComboBox()
        f.addRow("Species", self.species)
        self.custom = QLineEdit()
        self.custom.setPlaceholderText("Custom species (e.g. Moon jellyfish)")
        f.addRow("Custom", self.custom)
        mods = QGridLayout()
        self.mods = {}
        for i, (letter, name) in enumerate(TABLES["modifiers"].items()):
            cb = QCheckBox(name)
            self.mods[letter] = cb
            mods.addWidget(cb, i // 3, i % 3)
        f.addRow("Modifiers", mods)
        self.scale = _combo([("", LEAVE_OUT)] + [(k, f"{k} - {v}") for k, v in TABLES["scale"].items()])
        f.addRow("Human-animal", self.scale)
        rel = QGridLayout()
        self.rel = {}
        for i, (letter, name) in enumerate(TABLES["relationship"].items()):
            cb = QCheckBox(name)
            self.rel[letter] = cb
            rel.addWidget(cb, i // 3, i % 3)
        f.addRow("You and them", rel)
        form.addWidget(box)
        self._watch(self.cat, self.species, self.custom, self.scale, *self.mods.values(), *self.rel.values())
        # the categories
        self.levels, self.subs = {}, {}
        for title, cats in (("Furry side", furcode.FURRY), ("Real life", None)):
            box = QGroupBox(title)
            f = QFormLayout(box)
            if cats is None:
                self.job = _combo([("", LEAVE_OUT)] + [(k, v) for k, v in TABLES["realLife"].items()], 200)
                self.trained = QCheckBox("Trained, but no job")
                row = QHBoxLayout()
                row.addWidget(self.job, 1)
                row.addWidget(self.trained)
                f.addRow("Job (RL)", row)
                self.age = _combo([("", LEAVE_OUT)] + [(k[1:], v) for k, v in TABLES["age"].items()])
                f.addRow("Age (a)", self.age)
                self._watch(self.job, self.trained, self.age)
                cats = furcode.OFFLINE
            for letter, name, table in cats:
                lv = _combo([(None, LEAVE_OUT)] + [(k[len(letter):], v) for k, v in TABLES[table].items()], 200)
                self.levels[letter] = lv
                row = QHBoxLayout()
                row.addWidget(lv, 1)
                self.subs[letter] = {}
                for ch in self.SUB_LETTERS.get(letter, ""):
                    cb = QCheckBox(furcode.SUBS.get(letter, {}).get(ch, ch))
                    self.subs[letter][ch] = cb
                    row.addWidget(cb)
                    self._watch(cb)
                f.addRow(f"{name} ({letter})", row)
                self._watch(lv)
            if title == "Furry side":
                self.S = self._gender_row(f, "Fursona gender (S)")
            else:
                self.s = self._gender_row(f, "Your gender (s)")
            form.addWidget(box)
        form.addStretch(1)
        self._fill_species()

    def _gender_row(self, f, label):
        g = _combo([("", LEAVE_OUT)] + [(k, v.title()) for k, v in furcode.GENDERS.items()])
        s = _combo([("", "-")] + [(k, v.title()) for k, v in furcode.SEXUALITIES.items()])
        row = QHBoxLayout()
        row.addWidget(g, 1)
        row.addWidget(s, 1)
        f.addRow(label, row)
        self._watch(g, s)
        return g, s

    def _fill_species(self, *_):
        cat = self.cat.currentData() or ""
        self.species.blockSignals(True)
        self.species.clear()
        if cat in CATEGORY_NAMES:
            self.species.addItem("(any)", cat)
            for code, name in SPECIES_BY_CATEGORY.get(cat, {}).items():
                self.species.addItem(name, code)
        self.species.blockSignals(False)
        self.species.setEnabled(cat in CATEGORY_NAMES)
        self.custom.setEnabled(cat == "custom")

    def fill(self, code):
        p = furcode.parts(code)
        f = (p["fursonas"] or [None])[0]
        if f is None:
            _set(self.cat, "")
        elif f["species"].startswith("F["):
            _set(self.cat, "custom")
            self.custom.setText(f["species"][2:-1])
        elif f["species"] in ("F?", "F!", "F#"):
            _set(self.cat, f["species"])
        else:
            cat = next((c for c, sp in SPECIES_BY_CATEGORY.items() if f["species"] in sp), f["species"])
            _set(self.cat, cat if cat in CATEGORY_NAMES else "FG")
            self._fill_species()
            _set(self.species, f["species"])
        for letter, cb in self.mods.items():
            cb.setChecked(bool(f) and letter in f["mods"])
        _set(self.scale, (f or {}).get("scale", ""))
        for letter, cb in self.rel.items():
            cb.setChecked(bool(f) and letter in f["rel"])
        for letter, box in self.levels.items():
            lv = p["levels"].get(letter)
            _set(box, None if lv is None else lv["level"])
            for ch, cb in self.subs[letter].items():
                cb.setChecked(bool(lv) and ch in lv.get("subs", ""))
        job = p["job"] or {}
        _set(self.job, job.get("code", ""))
        self.trained.setChecked(bool(job.get("trained")))
        _set(self.age, (p["age"] or {}).get("level", ""))
        for key, (g, s) in (("S", self.S), ("s", self.s)):
            _set(g, (p[key] or {}).get("gender", ""))
            _set(s, (p[key] or {}).get("sexuality", ""))

    def build(self):
        p = {"fursonas": [], "levels": {}, "job": None, "age": None, "S": None, "s": None, "other": []}
        cat = self.cat.currentData() or ""
        if cat:
            species = f"F[{self.custom.text().strip() or 'custom'}]" if cat == "custom" else \
                cat if cat in ("F?", "F!", "F#") else (self.species.currentData() or cat)
            p["fursonas"].append({"species": species, "mods": "".join(k for k, cb in self.mods.items() if cb.isChecked()),
                                  "scale": self.scale.currentData() or "",
                                  "rel": "".join(k for k, cb in self.rel.items() if cb.isChecked())})
        for letter, box in self.levels.items():
            if box.currentData() is not None:
                p["levels"][letter] = {"level": box.currentData(), "custom": "",
                                       "subs": "".join(ch for ch, cb in self.subs[letter].items() if cb.isChecked())}
        if self.job.currentData():
            p["job"] = {"code": self.job.currentData(), "trained": self.trained.isChecked(), "custom": ""}
        if self.age.currentIndex() > 0:
            p["age"] = {"level": self.age.currentData()}
        for key, (g, s) in (("S", self.S), ("s", self.s)):
            if g.currentData():
                p[key] = {"gender": g.currentData(), "sexuality": s.currentData() or "", "custom": ""}
        return furcode.encode(p)


# ---- YIFF Code ---------------------------------------------------------------------------------------------------
class YiffCodeTab(_CodeTab):
    def __init__(self):
        super().__init__("YIFF Code 3.0", "YIFF 3.0 M kinsey-5 ... WIXXX:2,10,31")
        self.describe = yiffcode.describe
        form = QVBoxLayout(self.form_host)
        box = QGroupBox("You")
        f = QFormLayout(box)
        self.gender = _combo([(k, v) for k, v in yiffcode.GENDERS.items()])
        self.orient = _combo([(k, v) for k, v in yiffcode.ORIENTATIONS.items()])
        f.addRow("Gender", self.gender)
        f.addRow("Orientation", self.orient)
        form.addWidget(box)
        self._watch(self.gender, self.orient)
        self.cats = {}
        for letter, name in yiffcode.CATEGORIES.items():
            box = QGroupBox(f"{letter} - {name}")
            f = QFormLayout(box)
            q = _combo([("Ns", "(leave out)")] + [(k, v) for k, v in yiffcode.QUALIFIERS.items() if k != "Ns"] +
                       list(yiffcode.SPECIAL_QUALIFIERS.get(letter, {}).items()))
            f.addRow("Answer", q)
            mods = QHBoxLayout()
            mod_boxes = {}
            for m, words in yiffcode.MODIFIERS.get(letter, {}).items():
                cb = QCheckBox(words)
                mod_boxes[m] = cb
                mods.addWidget(cb)
            mods.addStretch(1)
            f.addRow("Only / style", mods)
            oe = _combo([("", "(as above)")] + list(yiffcode.EXCEPTIONS.items()))
            f.addRow("Orientation here", oe)
            species = QLineEdit()
            species.setPlaceholderText("e.g. fox_wolf (equally), fox-wolf (in order), fox- (then anything)")
            if letter != "H":
                f.addRow("Species", species)
            self.cats[letter] = (q, mod_boxes, oe, species)
            self._watch(q, oe, species, *mod_boxes.values())
            form.addWidget(box)
        box = QGroupBox("WIXXX interests")
        grid = QGridLayout(box)
        self.flags = {}
        for i, (n, name) in enumerate(yiffcode.WIXXX.items()):
            cb = QCheckBox(f"{n} {name}")
            if n in yiffcode.OFF_LIMITS_FLAGS:
                cb.setToolTip("Allowed in your own code, but nobody here will ever play along with it.")
            self.flags[n] = cb
            grid.addWidget(cb, i // 3, i % 3)
            self._watch(cb)
        self.custom_flags = QLineEdit()
        self.custom_flags.setPlaceholderText("Custom interests, comma separated")
        grid.addWidget(self.custom_flags, len(self.flags) // 3 + 1, 0, 1, 3)
        self._watch(self.custom_flags)
        form.addWidget(box)
        form.addStretch(1)

    def fill(self, code):
        p = yiffcode.parts(code)
        _set(self.gender, p["gender"] or "M")
        _set(self.orient, p["orientation"])
        for letter, (q, mods, oe, species) in self.cats.items():
            c = p["categories"].get(letter) or {}
            _set(q, c.get("q", "Ns"))
            for m, cb in mods.items():
                cb.setChecked(m in c.get("mods", []))
            _set(oe, c.get("oe", ""))
            species.setText(c.get("species", ""))
        for n, cb in self.flags.items():
            cb.setChecked(n in p["wixxx"])
        self.custom_flags.setText(", ".join(p["custom"]))

    def build(self):
        cats = {}
        for letter, (q, mods, oe, species) in self.cats.items():
            cats[letter] = {"q": q.currentData(), "mods": [m for m, cb in mods.items() if cb.isChecked()],
                            "oe": oe.currentData() or "", "species": species.text().strip().strip("*")}
        p = {"version": "3.0", "gender": self.gender.currentData(), "orientation": self.orient.currentData(),
             "categories": cats, "wixxx": [n for n, cb in self.flags.items() if cb.isChecked()],
             "custom": [c.strip() for c in self.custom_flags.text().split(",") if c.strip()]}
        return yiffcode.encode(p)


class CodesEditor(QWidget):
    changed = Signal()

    def __init__(self, furcode_text="", yiffcode_text=""):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.fur = FurCodeTab()
        self.yiff = YiffCodeTab()
        self.tabs.addTab(self.fur, "Furry Code")
        self.tabs.addTab(self.yiff, "YIFF Code")
        lay.addWidget(self.tabs)
        self.fur.set_code(furcode_text)
        self.yiff.set_code(yiffcode_text)
        self.fur.changed.connect(self.changed)
        self.yiff.changed.connect(self.changed)

    def set_codes(self, codes):
        self.fur.set_code((codes or {}).get("furcode", ""))
        self.yiff.set_code((codes or {}).get("yiffcode", ""))

    def codes(self):
        return {"furcode": self.fur.code(), "yiffcode": self.yiff.code()}
