"""A small local-only web viewer for MSN advertisements; no real network requests."""

from html import escape
from urllib.parse import urlsplit, urljoin

from PySide6.QtCore import QUrl, QByteArray, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextBrowser, QHBoxLayout, QPushButton

from . import config


class LocalWebView(QTextBrowser):
    """Allow local page assets only; Qt's rich-text view does not execute scripts."""
    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = root.resolve()

    def loadResource(self, kind, url):
        if url.scheme() not in ("", "file"):
            return QByteArray()
        try:
            path = self.document().baseUrl().resolved(url).toLocalFile()
            from pathlib import Path
            resource = Path(path).resolve()
            resource.relative_to(self.root)
            return QByteArray(resource.read_bytes())
        except (OSError, ValueError):
            return QByteArray()


class MSNBrowser(QWidget):
    networkTransferRequested = Signal(str, int, str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        self.address = QLineEdit()
        self.address.returnPressed.connect(lambda: self.navigate(self.address.text()))
        root.addWidget(self.address)
        self._history = []
        self._history_index = -1
        controls = QHBoxLayout()
        for text, callback in (("Back", lambda: self._step(-1)),
                               ("Forward", lambda: self._step(1)),
                               ("Refresh", lambda: self.navigate(self.address.text(), False))):
            button = QPushButton(text)
            button.clicked.connect(callback)
            controls.addWidget(button)
        root.addLayout(controls)
        self.page = LocalWebView(config.STORAGE_ROOT / "Web")
        self.page.setOpenLinks(False)
        self.page.setOpenExternalLinks(False)
        self.page.anchorClicked.connect(self._follow_link)
        root.addWidget(self.page)
        self.navigate(url)

    def _follow_link(self, url):
        if url.isLocalFile():
            from pathlib import Path
            try:
                local = Path(url.toLocalFile()).resolve().relative_to(
                    (config.STORAGE_ROOT / "Web").resolve()
                )
                if len(local.parts) < 2:
                    return
                self.navigate("http://" + local.parts[0] + "/" + "/".join(local.parts[1:]))
            except ValueError:
                return
        else:
            self.navigate(urljoin(self.address.text(), url.toString()))

    def _step(self, delta):
        position = self._history_index + delta
        if 0 <= position < len(self._history):
            self._history_index = position
            self.navigate(self._history[position], False)

    def navigate(self, url, record=True):
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            self.page.setPlainText("Enter a valid simulated website address.")
            return
        self.address.setText(url)
        self.networkTransferRequested.emit(
            "outgoing", len(url.encode("utf-8")) + 160, "Simulated web request"
        )
        if record:
            self._history = self._history[:self._history_index + 1] + [url]
            self._history_index = len(self._history) - 1
        web = config.STORAGE_ROOT / "Web"
        candidate = web / parts.hostname / (parts.path.lstrip("/") or "index.html")
        if candidate.suffix == "":
            candidate /= "index.html"
        try:
            resolved = candidate.resolve()
            resolved.relative_to(web.resolve())
            if resolved.is_file():
                self.page.document().setBaseUrl(QUrl.fromLocalFile(str(resolved.parent) + "/"))
                html = resolved.read_text(encoding="utf-8")
                self.page.setHtml(html)
                self.networkTransferRequested.emit(
                    "incoming", len(html.encode("utf-8")) + 128,
                    f"Web page from {parts.hostname}",
                )
                return
        except (OSError, UnicodeError, ValueError) as exc:
            self.page.setPlainText(f"Local page could not be opened: {exc}")
            return
        html = ("<h2>This page is not installed</h2><p>" + escape(url)
                + "</p><p>This browser stays inside the local simulation. "
                "No real internet request was made.</p>")
        self.page.setHtml(html)
        self.networkTransferRequested.emit(
            "incoming", len(html.encode("utf-8")) + 128,
            f"Local not-installed page for {parts.hostname}",
        )
