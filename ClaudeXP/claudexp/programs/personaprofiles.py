"""Fur Persona Profiles: the Contact Persona Styles side by side - how each style makes the residents (their AIM
personas, profiles and typing voices), every prompt template and prompt-building function, and how each style did
in the realism test. Pick any two styles to compare; what changed is highlighted."""
import difflib
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QProcess, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QSplitter,
                               QTabWidget, QTextBrowser, QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import persona_style, persona_profiles_data as data
from ..paths import ROOT
from ..wm import XPWindow

_open = {}
CHANGED = "#C0261A"
OLD_BG, NEW_BG = "#FFD7D5", "#CDEFD0"
SECTIONS = [("persona", "Persona"), ("profile", "Profile")]
SCORES = [("overall", "Overall"), ("style", "Types like real AIM"), ("failures", "No failures"),
          ("distinct", "Distinct from each other"), ("repetition", "Not repetitive")]


def profiles_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32.0
    for dx, fill in ((7, "#E8EEF8"), (0, "#FFFFFF")):  # two cards, one behind the other
        p.setPen(QPen(QColor("#4A5A7A"), max(1.0, s)))
        p.setBrush(QColor(fill))
        p.drawRoundedRect(QRectF((2 + dx) * s, (4 + dx * 0.6) * s, 21 * s, 22 * s), 2 * s, 2 * s)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2F6FD0"))
    p.drawRect(QRectF(3 * s, 5 * s, 19 * s, 4 * s))
    p.setBrush(QColor("#B5651D"))                        # a paw print
    p.drawEllipse(QRectF(7 * s, 17 * s, 9 * s, 6.5 * s))
    for x, y in ((5, 14), (8.5, 11.5), (13, 11.5), (16.5, 14)):
        p.drawEllipse(QRectF(x * s, y * s, 3 * s, 3.5 * s))
    p.end()
    return QIcon(pm)


# ---- showing differences -----------------------------------------------------------------------------------
def _text(value):
    if value is None:
        return ""
    return value if isinstance(value, str) else json.dumps(value, indent=1, ensure_ascii=False)


def diff_html(a, b):
    """Both texts as HTML, with what was taken out marked on the left and what was put in marked on the right."""
    ta, tb = re.split(r"(\s+)", a), re.split(r"(\s+)", b)
    left, right = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
        old, new = html.escape("".join(ta[i1:i2])), html.escape("".join(tb[j1:j2]))
        if op == "equal":
            left.append(old)
            right.append(new)
            continue
        if old:
            left.append(f'<span style="background:{OLD_BG}">{old}</span>')
        if new:
            right.append(f'<span style="background:{NEW_BG}">{new}</span>')
    return "".join(left), "".join(right)


def side_by_side(title, a, b, names, mono=False):
    a, b = _text(a), _text(b)
    left, right = diff_html(a, b) if a != b else (html.escape(a), html.escape(b))
    font = "font-family:'Lucida Console','Courier New',monospace; font-size:8pt;" if mono else ""
    flag = f' <span style="color:{CHANGED}">(changed)</span>' if a != b else ' <span style="color:#777">(the same)</span>'
    empty = '<i style="color:#888">(none)</i>'
    return (f'<h3 style="margin:10px 0 4px 0">{html.escape(title)}{flag}</h3>'
            '<table width="100%" cellspacing="0" cellpadding="6" border="1" style="border-color:#C9D3E3">'
            f'<tr><th width="50%" bgcolor="#E8EEF8" align="left">{html.escape(names[0])}</th>'
            f'<th width="50%" bgcolor="#E8EEF8" align="left">{html.escape(names[1])}</th></tr>'
            f'<tr><td valign="top" style="white-space:pre-wrap; {font}">{left or empty}</td>'
            f'<td valign="top" style="white-space:pre-wrap; {font}">{right or empty}</td></tr></table>')


def voice_text(v):
    if not v:
        return ""
    h = v.get("habits", {})
    return (f"{v['archetype']}: {v['label']}\n"
            f"Greetings: {', '.join(v.get('greetings') or []) or '-'}\n"
            f"Emoticons: {' '.join(v.get('emoticons') or []) or '-'}\n"
            f"Says: {', '.join(v.get('shorthand') or []) or '-'}\n"
            f"About {h.get('words', '?')} words an IM; lowercase {h.get('lowercase', 0):.0%}, full stops "
            f"{h.get('end_punct', 0):.0%}, emoticons {h.get('emoticon', 0):.0%}, exclamations "
            f"{h.get('exclaim', 0):.0%}, questions {h.get('question', 0):.0%}\n\n{v.get('note', '')}")


def _pieces(view):
    """[(module, name, {"kind", "value"})] of a style's prompting."""
    return [(m, n, v) for m, entry in (view or {}).get("prompting", {}).items() for n, v in entry.items()]


class PersonaProfiles(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.views = {}                                  # style id -> view (or None while it's being worked out)
        self.process = None
        self.styles = persona_style.available()

        self.a, self.b = QComboBox(), QComboBox()
        for combo in (self.a, self.b):
            for s in self.styles:
                combo.addItem(s["name"], s["id"])
        ids = [s["id"] for s in self.styles]
        self.a.setCurrentIndex(max(0, len(ids) - 2))     # the newest frozen style against Development
        self.b.setCurrentIndex(len(ids) - 1)
        installed = QLabel(f"This computer: <b>{html.escape(persona_style.name())}</b>")
        installed.setToolTip("Chosen when the computer was set up (the launcher's Load and Format)")
        top = QHBoxLayout()
        top.addWidget(QLabel("Compare"))
        top.addWidget(self.a, 1)
        top.addWidget(QLabel("with"))
        top.addWidget(self.b, 1)
        top.addSpacing(12)
        top.addWidget(installed)

        self.tabs = QTabWidget()
        self.overview = QTextBrowser()
        self.overview.setOpenExternalLinks(False)
        self.tabs.addTab(self.overview, "Overview")
        self.people = QListWidget()
        self.people.currentRowChanged.connect(lambda _r: self._show_person())
        self.person = QTextBrowser()
        self.tabs.addTab(self._split(self.people, self.person), "Residents")
        self.prompt_list = QListWidget()
        self.prompt_list.currentRowChanged.connect(lambda _r: self._show_piece())
        self.piece = QTextBrowser()
        self.tabs.addTab(self._split(self.prompt_list, self.piece), "Prompting")
        self.eval_list = QListWidget()
        self.eval_list.currentRowChanged.connect(lambda _r: self._show_eval())
        self.eval_view = QTextBrowser()
        self.tabs.addTab(self._split(self.eval_list, self.eval_view), "Realism Tests")
        self.status = QLabel()

        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addWidget(self.tabs, 1)
        root.addWidget(self.status)
        self._fill_evals()
        for combo in (self.a, self.b):
            combo.currentIndexChanged.connect(self._styles_changed)
        self._styles_changed()

    @staticmethod
    def _split(left, right):
        split = QSplitter(Qt.Horizontal)
        left.setMinimumWidth(150)
        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        split.setSizes([190, 700])
        return split

    # ---- loading ---------------------------------------------------------------------------------------------
    def _ids(self):
        return self.a.currentData(), self.b.currentData()

    def _names(self):
        return self.a.currentText(), self.b.currentText()

    def _styles_changed(self, *_):
        for sid in self._ids():
            if sid not in self.views:
                self._load(sid)
        self._refresh()

    def _load(self, sid):
        if sid != persona_style.DEV:
            self.views[sid] = data.frozen_view(sid)
            return
        self.views[sid] = None                           # worked out in a process of its own (see persona_profiles_data)
        out = Path(tempfile.gettempdir()) / f"claudexp-persona-dev-{os.getpid()}.json"
        proc = QProcess(self)
        proc.setWorkingDirectory(str(ROOT))
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.finished.connect(lambda code, _status: self._dev_ready(proc, out, code))
        proc.start(sys.executable, ["-m", "claudexp.persona_profiles_data", persona_style.DEV, str(out)])
        self.process = proc

    def _dev_ready(self, proc, out, code):
        if not isValid(self):
            return
        try:
            self.views[persona_style.DEV] = json.loads(out.read_text(encoding="utf-8"))
            out.unlink()
        except (OSError, ValueError):
            err = bytes(proc.readAll()).decode("utf-8", "replace").strip().splitlines()
            self.views[persona_style.DEV] = {"error": err[-1] if err else f"exit code {code}"}
        self._refresh()

    def _ready(self):
        va, vb = (self.views.get(s) for s in self._ids())
        return va, vb

    # ---- showing ---------------------------------------------------------------------------------------------
    def _refresh(self):
        va, vb = self._ready()
        if va is None or vb is None:
            self.status.setText("Working out the Development style from the live code and Residents...")
            self.overview.setHtml("<p><i>Working out the Development style...</i></p>")
            self.people.clear()
            self.prompt_list.clear()
            self.person.clear()
            self.piece.clear()
            return
        for v in (va, vb):
            if v.get("error"):
                self.status.setText(f"Couldn't work out the Development style: {v['error']}")
        self._fill_people(va, vb)
        self._fill_pieces(va, vb)
        self._show_overview(va, vb)
        if not any(v.get("error") for v in (va, vb)):
            self.status.setText("Red: only in the left style.  Green: only in the right style.")

    def _person_changed(self, va, vb, name):
        ca, cb = va["contacts"].get(name) or {}, vb["contacts"].get(name) or {}
        return (any(_text(ca.get(k)) != _text(cb.get(k)) for k, _t in SECTIONS)
                or va["prompts"].get(name) != vb["prompts"].get(name)
                or (va.get("voices") or {}).get(name) != (vb.get("voices") or {}).get(name))

    def _fill_people(self, va, vb):
        keep = self.people.currentItem().data(Qt.UserRole) if self.people.currentItem() else None
        self.people.blockSignals(True)
        self.people.clear()
        for name in sorted(set(va["contacts"]) | set(vb["contacts"]), key=str.lower):
            changed = self._person_changed(va, vb, name)
            item = QListWidgetItem(("• " if changed else "   ") + name)
            item.setData(Qt.UserRole, name)
            if changed:
                item.setForeground(QColor(CHANGED))
            self.people.addItem(item)
            if name == keep:
                self.people.setCurrentItem(item)
        self.people.blockSignals(False)
        if self.people.currentRow() < 0 and self.people.count():
            self.people.setCurrentRow(0)
        self._show_person()

    def _fill_pieces(self, va, vb):
        keep = self.prompt_list.currentItem().data(Qt.UserRole) if self.prompt_list.currentItem() else None
        pa = {(m, n): v for m, n, v in _pieces(va)}
        pb = {(m, n): v for m, n, v in _pieces(vb)}
        self.prompt_list.blockSignals(True)
        self.prompt_list.clear()
        for key in list(pa) + [k for k in pb if k not in pa]:
            changed = _text((pa.get(key) or {}).get("value")) != _text((pb.get(key) or {}).get("value"))
            item = QListWidgetItem(("• " if changed else "   ") + f"{key[1]}   ({key[0]})")
            item.setData(Qt.UserRole, key)
            item.setToolTip(f"{key[0]}.{key[1]}")
            if changed:
                item.setForeground(QColor(CHANGED))
            self.prompt_list.addItem(item)
            if key == keep:
                self.prompt_list.setCurrentItem(item)
        self.prompt_list.blockSignals(False)
        if self.prompt_list.currentRow() < 0 and self.prompt_list.count():
            self.prompt_list.setCurrentRow(0)
        self._show_piece()

    def _show_overview(self, va, vb):
        names = self._names()
        evals = data.latest_evals()
        people = set(va["contacts"]) | set(vb["contacts"])
        changed_people = sum(self._person_changed(va, vb, n) for n in people)
        pa = {(m, n): v for m, n, v in _pieces(va)}
        pb = {(m, n): v for m, n, v in _pieces(vb)}
        changed_pieces = sum(_text((pa.get(k) or {}).get("value")) != _text((pb.get(k) or {}).get("value"))
                             for k in set(pa) | set(pb))
        cells = []
        for v in (va, vb):
            m = v.get("meta") or {}
            feats = ", ".join(m.get("features") or []) or "none (as first recorded)"
            cells.append(f"<b>{html.escape(m.get('name', v['id']))}</b><br>{html.escape(m.get('description', ''))}"
                         f"<br><br>Made: {html.escape(m.get('created', 'now - it is the live code'))}"
                         f"<br>Residents on AIM: {len(v['contacts'])}"
                         f"<br>Prompt pieces: {len(_pieces(v))}<br>Added features: {html.escape(feats)}")
        rows = "".join(f'<tr><td>{label}</td>' + "".join(
            f'<td align="right">{(evals.get(v["id"]) or {}).get("scores", {}).get(key, "-")}</td>' for v in (va, vb))
            + "</tr>" for key, label in SCORES)
        typing = ""
        ga = (evals.get(va["id"]) or {}).get("typing", {})
        gb = (evals.get(vb["id"]) or {}).get("typing", {})
        if ga or gb:
            real = (ga or gb).get("real_aim", {})
            for f, goal in real.items():
                def show(t, f=f):
                    x = (t.get("got") or {}).get(f)
                    return "-" if x is None else (f"{x:.1f}" if f == "avg_words" else f"{x:.0%}")
                label = "words per message" if f == "avg_words" else f.replace("_", " ")
                real_x = f"{goal:.1f}" if f == "avg_words" else f"{goal:.0%}"
                typing += f"<tr><td>{label}</td><td align='right'>{show(ga)}</td><td align='right'>{show(gb)}</td>" \
                          f"<td align='right'><i>{real_x}</i></td></tr>"
        table = 'cellspacing="0" cellpadding="5" border="1" style="border-color:#C9D3E3"'
        head = "".join(f'<th bgcolor="#E8EEF8">{html.escape(n)}</th>' for n in names)
        self.overview.setHtml(
            "<h2>Contact Persona Styles</h2>"
            "<p>A style is chosen when the computer is set up (the launcher's <b>Load and Format</b>) and stays until "
            "the next format. A frozen style keeps the residents and every prompt word for word, so later changes "
            "only reach the Development style.</p>"
            f'<table width="100%" {table}><tr>{head}</tr><tr>'
            + "".join(f'<td valign="top" width="50%">{c}</td>' for c in cells) + "</tr></table>"
            f"<p><b>{changed_people}</b> of {len(people)} residents and <b>{changed_pieces}</b> prompt pieces differ "
            "between them (see the Residents and Prompting tabs).</p>"
            f"<h3>Realism test (newest run of each)</h3><table {table}><tr><th></th>{head}</tr>{rows}</table>"
            + (f"<h3>How they type</h3><table {table}><tr><th></th>{head}<th bgcolor='#E8EEF8'>Real AIM chat</th>"
               f"</tr>{typing}</table>" if typing else "<p><i>No realism tests yet.</i></p>"))

    def _show_person(self):
        va, vb = self._ready()
        item = self.people.currentItem()
        if not item or va is None or vb is None:
            self.person.clear()
            return
        name = item.data(Qt.UserRole)
        names = self._names()
        ca, cb = va["contacts"].get(name) or {}, vb["contacts"].get(name) or {}
        parts = [f"<h2>{html.escape(name)}</h2>"]
        for key, title in SECTIONS:
            parts.append(side_by_side(title, ca.get(key), cb.get(key), names))
        parts.append(side_by_side("Typing voice", voice_text((va.get("voices") or {}).get(name)),
                                  voice_text((vb.get("voices") or {}).get(name)), names))
        settings = {k: v for k, v in ca.items() if k not in ("persona", "profile")}
        settings_b = {k: v for k, v in cb.items() if k not in ("persona", "profile")}
        parts.append(side_by_side("AIM settings", settings, settings_b, names, mono=True))
        parts.append(side_by_side("AIM system prompt (a sample: Monday 15 October 2001, 7:30 PM, before any chats)",
                                  va["prompts"].get(name), vb["prompts"].get(name), names))
        self.person.setHtml("".join(parts))

    def _show_piece(self):
        va, vb = self._ready()
        item = self.prompt_list.currentItem()
        if not item or va is None or vb is None:
            self.piece.clear()
            return
        mod, name = item.data(Qt.UserRole)
        get = lambda v: (((v.get("prompting") or {}).get(mod) or {}).get(name) or {}).get("value")
        kind = "module (recorded whole)" if name == "<module>" else "template" if name.split(".")[-1].isupper() else "function"
        self.piece.setHtml(f"<h2>{html.escape(name)}</h2><p style='color:#555'>{html.escape(mod)} - a prompt {kind}"
                           "</p>" + side_by_side("Word for word", get(va), get(vb), self._names(), mono=True))

    # ---- realism tests ---------------------------------------------------------------------------------------
    def _fill_evals(self):
        self.eval_list.clear()
        for f in sorted((persona_style.styles_dir() / "evals").glob("*.md"), reverse=True):
            item = QListWidgetItem(f.stem)
            item.setData(Qt.UserRole, str(f))
            self.eval_list.addItem(item)
        if self.eval_list.count():
            self.eval_list.setCurrentRow(0)

    def _show_eval(self):
        item = self.eval_list.currentItem()
        if not item:
            self.eval_view.clear()
            return
        try:
            self.eval_view.setMarkdown(Path(item.data(Qt.UserRole)).read_text(encoding="utf-8"))
        except OSError as exc:
            self.eval_view.setPlainText(str(exc))

    def shutdown(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()


def open_profiles(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = PersonaProfiles(desktop)
        win = XPWindow(desktop, "Fur Persona Profiles", body, profiles_icon(16), (940, 640))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win
