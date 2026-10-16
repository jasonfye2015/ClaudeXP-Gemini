"""Spell check for every place the user types a message or document.

One application-wide event filter (`install`) gives each editable multi-line text box (QPlainTextEdit / QTextEdit)
a red wavy underline under misspelled words and a right-click menu with suggestions, "Add to Dictionary" and
"Ignore All". Read-only views are skipped, and a program can opt a box out with `edit.setProperty("nospell", True)`.
It runs completely offline (pyspellchecker's English word list); if the package is missing, nothing happens.
Words you add are kept in data/spell_custom.txt and the on/off switch in data/spellcheck.json."""
import json
import re
import weakref

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QAction, QColor, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QTextEdit

from .paths import DATA

SETTINGS_FILE = DATA / "spellcheck.json"
CUSTOM_FILE = DATA / "spell_custom.txt"
WORD = re.compile(r"[A-Za-z]+(?:['\u2019][A-Za-z]+)*")
MAX_BLOCK = 4000             # a line longer than this is left alone, to keep typing smooth

_speller = None              # False once we know the package is not there
_enabled = None
_custom = None
_ignored = set()             # "Ignore All" lasts until ClaudeXP closes
_highlighters = weakref.WeakSet()
_filter = None


def _load_speller():
    global _speller
    if _speller is None:
        try:
            from spellchecker import SpellChecker
            _speller = SpellChecker()
            _speller.word_frequency.load_words(custom_words())
        except Exception:
            _speller = False
    return _speller


def custom_words():
    global _custom
    if _custom is None:
        try:
            _custom = {w.strip().lower() for w in CUSTOM_FILE.read_text(encoding="utf-8").splitlines() if w.strip()}
        except OSError:
            _custom = set()
    return _custom


def enabled():
    global _enabled
    if _enabled is None:
        try:
            _enabled = bool(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")).get("enabled", True))
        except (OSError, ValueError, AttributeError):
            _enabled = True
    return _enabled


def set_enabled(on):
    global _enabled
    _enabled = bool(on)
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps({"enabled": _enabled}), encoding="utf-8")
    except OSError:
        pass
    for h in list(_highlighters):
        h.rehighlight()


def add_word(word):
    words = custom_words()
    word = word.lower()
    if word in words:
        return
    words.add(word)
    try:
        CUSTOM_FILE.parent.mkdir(parents=True, exist_ok=True)
        CUSTOM_FILE.write_text("\n".join(sorted(words)) + "\n", encoding="utf-8")
    except OSError:
        pass
    speller = _load_speller()
    if speller:
        speller.word_frequency.load_words([word])
    _refresh_all()


def ignore_word(word):
    _ignored.add(word.lower())
    _refresh_all()


def _refresh_all():
    for h in list(_highlighters):
        h.rehighlight()


def misspelled(word):
    """True when `word` is not English (as far as we can tell). Names, acronyms and code-like words pass."""
    if len(word) < 2 or word.isupper():
        return False
    low = word.lower().replace("\u2019", "'")
    if low.endswith("'s"):
        low = low[:-2]
    if not low or low in _ignored or low in custom_words():
        return False
    speller = _load_speller()
    return bool(speller) and bool(speller.unknown([low]))


def suggestions(word, limit=6):
    speller = _load_speller()
    if not speller:
        return []
    low = word.lower().replace("\u2019", "'")
    found = speller.candidates(low) or set()
    found.discard(low)
    freq = speller.word_frequency
    best = sorted(found, key=lambda w: -freq[w])[:limit]
    if word[:1].isupper():
        best = [w[:1].upper() + w[1:] for w in best]
    return best


class Highlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.fmt = QTextCharFormat()
        self.fmt.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        self.fmt.setUnderlineColor(QColor("#E02020"))
        _highlighters.add(self)

    def highlightBlock(self, text):
        if not enabled() or len(text) > MAX_BLOCK:
            return
        for m in WORD.finditer(text):
            # skip words glued to digits, underscores, slashes or dots (file names, URLs, identifiers)
            a, b = m.start(), m.end()
            before = text[a - 1] if a else " "
            after = text[b] if b < len(text) else " "
            if before in "_/\\.@:#" or before.isdigit() or after in "_/\\@:" or after.isdigit() or \
                    (after == "." and b + 1 < len(text) and text[b + 1].isalnum()):
                continue
            if misspelled(m.group()):
                self.setFormat(a, b - a, self.fmt)


class _Filter(QObject):
    def eventFilter(self, obj, event):
        kind = event.type()
        if kind == QEvent.Show:
            if isinstance(obj, (QPlainTextEdit, QTextEdit)):
                self._attach(obj)
        elif kind == QEvent.ContextMenu and isinstance(obj, (QPlainTextEdit, QTextEdit)) \
                and obj.property("_spell") is not None:
            return self._menu(obj, event)
        return False

    @staticmethod
    def _attach(edit):
        doc = edit.document()
        if edit.isReadOnly() or edit.property("nospell") or not _load_speller():
            return
        if edit.property("_spell") is doc:
            return
        edit.setProperty("_spell", doc)
        edit._spell_highlighter = Highlighter(doc)

    @staticmethod
    def _menu(edit, event):
        if event.reason() == event.Reason.Mouse:
            cursor = edit.cursorForPosition(edit.viewport().mapFromGlobal(event.globalPos()))
        else:
            cursor = edit.textCursor()
        menu = edit.createStandardContextMenu()
        first = menu.actions()[0] if menu.actions() else None
        word = ""
        if enabled() and not edit.isReadOnly():
            probe = QTextCursor(cursor)
            probe.select(QTextCursor.WordUnderCursor)
            word = probe.selectedText().strip("'\u2019")
            if word and WORD.fullmatch(word) and misspelled(word):
                span = QTextCursor(probe)
                actions = []
                for s in suggestions(word) or []:
                    act = QAction(s, menu)
                    act.triggered.connect(lambda _=False, c=QTextCursor(span), s=s: c.insertText(s))
                    actions.append(act)
                if not actions:
                    none = QAction("(no suggestions)", menu)
                    none.setEnabled(False)
                    actions.append(none)
                add = QAction("Add to Dictionary", menu)
                add.triggered.connect(lambda _=False, w=word: add_word(w))
                ign = QAction("Ignore All", menu)
                ign.triggered.connect(lambda _=False, w=word: ignore_word(w))
                actions += [add, ign]
                for act in actions:
                    menu.insertAction(first, act)
                menu.insertSeparator(first)
        toggle = QAction("Check Spelling as I Type", menu)
        toggle.setCheckable(True)
        toggle.setChecked(enabled())
        toggle.triggered.connect(set_enabled)
        menu.addSeparator()
        menu.addAction(toggle)
        menu.exec(event.globalPos())
        return True


def install(app=None):
    """Turn spell check on for the whole application (call once, after the QApplication exists)."""
    global _filter
    if _filter is not None:
        return
    app = app or QApplication.instance()
    _filter = _Filter(app)
    app.installEventFilter(_filter)
