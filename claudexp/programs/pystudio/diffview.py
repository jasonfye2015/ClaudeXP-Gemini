"""A before/after preview of a change, with the problems pyflakes finds in the new code."""
import difflib
import html

from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QListWidget, QTextBrowser, QVBoxLayout)


def diff_html(old, new, context=3):
    lines = list(difflib.unified_diff(old.splitlines(), new.splitlines(), "before", "after", lineterm="", n=context))
    if not lines:
        return "<p><i>No differences.</i></p>"
    out = []
    for ln in lines:
        text = html.escape(ln) or "&nbsp;"
        if ln.startswith("+++") or ln.startswith("---"):
            continue
        if ln.startswith("@@"):
            out.append(f'<div style="color:#808080;background:#EEF">{text}</div>')
        elif ln.startswith("+"):
            out.append(f'<div style="background:#D8F5D0">{text}</div>')
        elif ln.startswith("-"):
            out.append(f'<div style="background:#FAD4D4">{text}</div>')
        else:
            out.append(f"<div>{text}</div>")
    return '<pre style="font-family:Consolas;font-size:10pt">' + "".join(out) + "</pre>"


class DiffDialog(QDialog):
    """Shows what will change. `problems` is [(line, message)] for the new code."""

    def __init__(self, parent, title, old, new, problems=(), accept_text="Apply", prompt=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(640, 460)
        box = QVBoxLayout(self)
        if prompt:
            box.addWidget(QLabel(prompt))
        view = QTextBrowser()
        view.setHtml(diff_html(old, new))
        box.addWidget(view, 1)
        errors = [p for p in problems if p[1].startswith("Syntax error")]
        if problems:
            label = QLabel("<b>The new code has problems:</b>" if not errors else
                           "<b style='color:#B00000'>The new code has a syntax error and will not run:</b>")
            box.addWidget(label)
            lst = QListWidget()
            lst.setMaximumHeight(80)
            for line, message in problems[:30]:
                lst.addItem(f"Line {line}: {message}")
            box.addWidget(lst)
        else:
            ok = QLabel("Pyflakes found no problems in the new code.")
            ok.setStyleSheet("QLabel { color: #006000; }")
            box.addWidget(ok)
        buttons = QDialogButtonBox()
        buttons.addButton(accept_text, QDialogButtonBox.AcceptRole)
        buttons.addButton("Cancel", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        box.addWidget(buttons)

    @staticmethod
    def ask(parent, title, old, new, problems=(), accept_text="Apply", prompt=""):
        return DiffDialog(parent, title, old, new, problems, accept_text, prompt).exec() == QDialog.Accepted
