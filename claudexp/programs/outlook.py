"""Outlook Express 6 and the Windows Address Book. The Inbox is the living world's mailbox (buddies' emails,
the same mail Netscape WebMail shows); you can write to buddies, reply and forward, and they answer a few minutes
later (written by the model, in character). Mail written offline waits in the Outbox until Send/Recv. Folders:
Inbox, Outbox, Sent Items, Deleted Items, Drafts. The Address Book lists every buddy's email address."""
import re

from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QMenuBar, QPlainTextEdit, QPushButton, QSplitter, QStyle, QTextBrowser,
                               QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import clock, network, sound
from ..paths import DATA
from ..wm import XPWindow
from .notepad import MENU_STYLE
from .people import load_json, save_json

STORE = DATA / "outlook.json"
FOLDERS = [("inbox", "Inbox"), ("outbox", "Outbox"), ("sent", "Sent Items"), ("deleted", "Deleted Items"),
           ("drafts", "Drafts")]
STYLE = MENU_STYLE + """
QWidget#oe { background: #ECE9D8; }
QWidget#oebar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FDFDFB, stop:1 #E3E0D0);
                border-bottom: 1px solid #ACA899; }
QToolButton { border: 1px solid transparent; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
QToolButton:hover { border: 1px solid #ACA899; background: #FFFFFF; }
QTreeWidget, QTextBrowser { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; }
QLabel#paneTitle { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3A6EA5, stop:1 #8EB0DA);
                   color: white; font-family: Tahoma; font-size: 12px; font-weight: bold; padding: 3px 6px; }
QLabel#header { background: #ECE9D8; border: 1px solid #ACA899; padding: 4px 6px; font-family: Tahoma; font-size: 11px; }
QLabel#status { border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
QLineEdit, QPlainTextEdit { font-family: Arial; font-size: 13px; }
"""


def _life():
    from .. import life
    return life.get()


def _store():
    data = load_json(STORE, {})
    for key in ("outbox", "sent", "drafts"):
        data.setdefault(key, [])
    data.setdefault("next_id", 1)
    return data


def _now_text():
    now = clock.now()
    return f"{now.month}/{now.day}/{now.year} {clock.time_text(now)}"


def envelope_pixmap(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.scale(s, s)
    p.setPen(QPen(QColor("#806020"), 1))
    p.setBrush(QColor("#FFF6D0"))
    p.drawRect(QRectF(3.5, 9.5, 25, 17))
    path = QPainterPath()
    path.moveTo(3.5, 9.5)
    path.lineTo(16, 19)
    path.lineTo(28.5, 9.5)
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    p.end()
    return pm


def oe_icon():
    pm = envelope_pixmap(32)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#1C5FC4"), 3))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(14, 2, 16, 16), 30 * 16, 300 * 16)
    p.end()
    return QIcon(pm)


def book_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#203060"), 1))
    p.setBrush(QColor("#3A5FC0"))
    p.drawRoundedRect(QRectF(6.5, 3.5, 20, 25), 2, 2)
    p.setBrush(QColor("white"))
    p.drawRect(QRectF(10.5, 7.5, 12, 7))
    p.setBrush(QColor("#F0C080"))
    p.drawEllipse(QRectF(13, 17, 7, 7))
    p.end()
    return QIcon(pm)


def recipients(text):
    return [a.strip() for a in re.split(r"[;,]", text) if a.strip()]


def resolve_address(text):
    """'ArcticFox' or 'ArcticFox <arcticfox@aol.com>' or an address -> an email address."""
    from ..life import email_address
    m = re.search(r"<([^>]+)>", text)
    if m:
        return m.group(1).strip()
    if "@" in text:
        return text
    sim = _life()
    if sim is not None:
        for name in sim.buddies:
            if name.lower() == text.lower():
                return email_address(name)
    return text


def deliver(desktop, msg):
    """Hand a sent message to the world (each recipient)."""
    sim = _life()
    if sim is None:
        return
    for addr in recipients(msg["to"]):
        sim.receive_email(resolve_address(addr), msg["subject"], msg["body"])


# ---- composing ---------------------------------------------------------------------------------------------------

class Compose(QWidget):
    def __init__(self, oe, to="", subject="", body="", draft_id=None):
        super().__init__()
        self.oe = oe
        self.desktop = oe.desktop
        self.frame = None
        self.draft_id = draft_id
        self.sent = False
        self.setObjectName("oe")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        menu = QMenuBar()
        f = menu.addMenu("&File")
        f.addAction("&Send Message", self.send, QKeySequence("Alt+S"))
        f.addAction("Save", self.save_draft, QKeySequence("Ctrl+S"))
        f.addSeparator()
        f.addAction("&Close", lambda: self.frame.request_close())
        menu.addMenu("&Edit").addAction("Select &All", lambda: self.body.selectAll(), QKeySequence("Ctrl+A"))
        v.addWidget(menu)
        bar = QWidget()
        bar.setObjectName("oebar")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        bh = QHBoxLayout(bar)
        bh.setContentsMargins(4, 2, 4, 2)
        send = QToolButton()
        send.setText("Send")
        send.setIcon(QIcon(envelope_pixmap(24)))
        send.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        send.clicked.connect(self.send)
        bh.addWidget(send)
        addr = QToolButton()
        addr.setText("Addresses")
        addr.setIcon(book_icon())
        addr.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        addr.clicked.connect(self.pick_address)
        bh.addWidget(addr)
        bh.addStretch()
        v.addWidget(bar)
        grid = QGridLayout()
        grid.setContentsMargins(6, 6, 6, 4)
        self.to = QLineEdit(to)
        self.cc = QLineEdit()
        self.subject = QLineEdit(subject)
        for row, (label, edit) in enumerate((("To:", self.to), ("Cc:", self.cc), ("Subject:", self.subject))):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(edit, row, 1)
        v.addLayout(grid)
        self.body = QPlainTextEdit(body)
        v.addWidget(self.body, 1)
        self.subject.textChanged.connect(self._title)

    def _title(self):
        if self.frame is not None:
            self.frame.set_title(self.subject.text() or "New Message")

    def pick_address(self):
        def chosen(name, addr):
            current = self.to.text().strip()
            self.to.setText((current + "; " if current else "") + f"{name} <{addr}>")
        open_address_book(self.desktop, chosen)

    def message(self):
        to = "; ".join(x for x in (self.to.text().strip(), self.cc.text().strip()) if x)
        return {"to": to, "subject": self.subject.text().strip() or "(no subject)",
                "body": self.body.toPlainText(), "date": _now_text()}

    def send(self):
        from ..explorer.dialogs import msgbox
        msg = self.message()
        if not recipients(msg["to"]):
            return msgbox(self.desktop, "Send Mail", "There must be at least one name or distribution list in "
                          "the To, Cc, or Bcc box.", "error")
        store = _store()
        msg["id"] = store["next_id"]
        store["next_id"] += 1
        if self.draft_id is not None:
            store["drafts"] = [d for d in store["drafts"] if d["id"] != self.draft_id]
        if network.is_connected():
            deliver(self.desktop, msg)
            store["sent"].append(msg)
        else:
            store["outbox"].append(msg)
            msgbox(self.desktop, "Send Mail", "Your message will be placed in your Outbox and sent the next time "
                   "you choose Send/Recv.", "info")
        save_json(STORE, store)
        self.sent = True
        self.oe.refresh()
        self.desktop.close_window(self.frame)

    def save_draft(self):
        store = _store()
        msg = self.message()
        if self.draft_id is None:
            self.draft_id = store["next_id"]
            store["next_id"] += 1
        msg["id"] = self.draft_id
        store["drafts"] = [d for d in store["drafts"] if d["id"] != self.draft_id] + [msg]
        save_json(STORE, store)
        self.oe.refresh()


# ---- the main window ------------------------------------------------------------------------------------------------

class OutlookExpress(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.folder = "inbox"
        self.setObjectName("oe")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self.menu = QMenuBar()
        self.menu.triggered.connect(lambda _a: sound.play("menu"))
        v.addWidget(self.menu)
        v.addWidget(self._toolbar())
        split = QSplitter(Qt.Horizontal)
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(0)
        t = QLabel("Folders")
        t.setObjectName("paneTitle")
        lv.addWidget(t)
        self.folders = QTreeWidget()
        self.folders.setHeaderHidden(True)
        self.folders.currentItemChanged.connect(self._folder_changed)
        lv.addWidget(self.folders, 3)
        c = QLabel("Contacts")
        c.setObjectName("paneTitle")
        lv.addWidget(c)
        self.contacts = QTreeWidget()
        self.contacts.setHeaderHidden(True)
        self.contacts.setRootIsDecorated(False)
        self.contacts.itemDoubleClicked.connect(lambda item: self.compose(to=item.data(0, Qt.UserRole)))
        lv.addWidget(self.contacts, 2)
        split.addWidget(left)
        right = QSplitter(Qt.Vertical)
        self.list = QTreeWidget()
        self.list.setRootIsDecorated(False)
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.setHeaderLabels(["From", "Subject", "Received"])
        self.list.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.list.setColumnWidth(0, 150)
        self.list.currentItemChanged.connect(self._show_message)
        self.list.itemDoubleClicked.connect(lambda item: self.open_message(item))
        right.addWidget(self.list)
        pv = QWidget()
        pvl = QVBoxLayout(pv)
        pvl.setContentsMargins(0, 0, 0, 0)
        pvl.setSpacing(0)
        self.header = QLabel("")
        self.header.setObjectName("header")
        self.header.setTextFormat(Qt.RichText)
        pvl.addWidget(self.header)
        self.preview = QTextBrowser()
        pvl.addWidget(self.preview, 1)
        right.addWidget(pv)
        right.setSizes([220, 260])
        split.addWidget(right)
        split.setSizes([190, 560])
        v.addWidget(split, 1)
        self.status = QLabel("")
        self.status.setObjectName("status")
        v.addWidget(self.status)
        self._menus()
        sim = _life()
        if sim is not None:
            sim.mail_arrived.connect(self._mail_arrived)
        self.listener = lambda *_q: self.refresh()
        network.get(desktop).disconnect_listeners.append(self.listener)
        self.refresh()

    def _toolbar(self):
        bar = QWidget()
        bar.setObjectName("oebar")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        h = QHBoxLayout(bar)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(2)
        st = QApplication.style()
        buttons = [("Create Mail", QIcon(envelope_pixmap(24)), lambda: self.compose()),
                   ("Reply", st.standardIcon(QStyle.SP_ArrowBack), self.reply),
                   ("Reply All", st.standardIcon(QStyle.SP_ArrowBack), self.reply),
                   ("Forward", st.standardIcon(QStyle.SP_ArrowForward), self.forward),
                   ("Print", st.standardIcon(QStyle.SP_FileIcon), self.print_),
                   ("Delete", st.standardIcon(QStyle.SP_TrashIcon), self.delete),
                   ("Send/Recv", st.standardIcon(QStyle.SP_BrowserReload), self.send_recv),
                   ("Addresses", book_icon(), lambda: open_address_book(self.desktop,
                                                                        lambda n, a: self.compose(to=f"{n} <{a}>")))]
        for text, icon, slot in buttons:
            b = QToolButton()
            b.setText(text)
            b.setIcon(icon)
            b.setIconSize(QSize(24, 24))
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.clicked.connect(lambda _c=False, s=slot: s())
            h.addWidget(b)
        h.addStretch()
        return bar

    def _menus(self):
        m = self.menu
        f = m.addMenu("&File")
        new = f.addMenu("&New")
        new.addAction("&Mail Message", lambda: self.compose(), QKeySequence("Ctrl+N"))
        f.addSeparator()
        f.addAction("&Print...", self.print_, QKeySequence("Ctrl+P"))
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close())
        e = m.addMenu("&Edit")
        e.addAction("&Delete", self.delete, QKeySequence("Ctrl+D"))
        e.addAction("Mark as &Read", lambda: self._mark(True), QKeySequence("Ctrl+Q"))
        e.addAction("Mark as &Unread", lambda: self._mark(False))
        e.addAction("Empty 'Deleted Items' Folder", self.empty_deleted)
        msg = m.addMenu("&Message")
        msg.addAction("&New Message", lambda: self.compose(), QKeySequence("Ctrl+N"))
        msg.addAction("&Reply to Sender", self.reply, QKeySequence("Ctrl+R"))
        msg.addAction("&Forward", self.forward, QKeySequence("Ctrl+F"))
        tools = m.addMenu("&Tools")
        tools.addAction("&Send and Receive All", self.send_recv, QKeySequence("Ctrl+M"))
        tools.addAction("&Address Book...", lambda: open_address_book(self.desktop), QKeySequence("Ctrl+Shift+B"))
        m.addMenu("&Help").addAction("&About Outlook Express", lambda: self._message(
            "About Outlook Express", "Microsoft Outlook Express 6\nVersion 6.00.2600.0000"))

    # ---- data -------------------------------------------------------------------------------------------------
    def messages(self, folder):
        sim = _life()
        if folder in ("inbox", "deleted"):
            box = sim.mailbox.messages() if sim is not None else []
            return [dict(m, kind="in") for m in box if m.get("folder", "inbox") == folder][::-1]
        return [dict(m, kind=folder) for m in _store()[folder]][::-1]

    def refresh(self):
        if not isValid(self):
            return
        sim = _life()
        unread = len(sim.mailbox.unread()) if sim is not None else 0
        store = _store()
        current = self.folder
        self.folders.blockSignals(True)
        self.folders.clear()
        root = QTreeWidgetItem(["Outlook Express"])
        root.setIcon(0, oe_icon())
        local = QTreeWidgetItem(["Local Folders"])
        local.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        root.addChild(local)
        for key, label in FOLDERS:
            count = unread if key == "inbox" else len(store["outbox"]) if key == "outbox" else 0
            item = QTreeWidgetItem([f"{label} ({count})" if count else label])
            item.setData(0, Qt.UserRole, key)
            item.setIcon(0, QApplication.style().standardIcon(
                QStyle.SP_TrashIcon if key == "deleted" else QStyle.SP_DirIcon))
            if count:
                f = item.font(0)
                f.setBold(True)
                item.setFont(0, f)
            local.addChild(item)
            if key == current:
                self.folders.setCurrentItem(item)
        self.folders.addTopLevelItem(root)
        self.folders.expandAll()
        self.folders.blockSignals(False)
        self.contacts.clear()
        if sim is not None:
            from ..life import email_address
            for name in sorted(sim.buddies, key=str.lower):
                item = QTreeWidgetItem([name])
                item.setIcon(0, book_icon())
                item.setData(0, Qt.UserRole, f"{name} <{email_address(name)}>")
                self.contacts.addTopLevelItem(item)
        self._fill_list()
        online = "Working Online" if network.is_connected() else "Working Offline"
        msgs = self.messages(self.folder)
        unread_here = sum(1 for m in msgs if m["kind"] == "in" and not m.get("read"))
        self.status.setText(f"{len(msgs)} message(s), {unread_here} unread          {online}")

    def _fill_list(self):
        selected = self.list.currentItem().data(0, Qt.UserRole)["id"] if self.list.currentItem() else None
        self.list.blockSignals(True)
        self.list.clear()
        incoming = self.folder in ("inbox", "deleted")
        self.list.setHeaderLabels(["From" if incoming else "To", "Subject", "Received" if incoming else "Sent"])
        for m in self.messages(self.folder):
            who = m["from"] if m["kind"] == "in" else m["to"]
            item = QTreeWidgetItem([who, m["subject"], m["date"]])
            item.setData(0, Qt.UserRole, m)
            item.setIcon(0, QIcon(envelope_pixmap(16)))
            if m["kind"] == "in" and not m.get("read"):
                for col in range(3):
                    f = item.font(col)
                    f.setBold(True)
                    item.setFont(col, f)
            self.list.addTopLevelItem(item)
            if m["id"] == selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        if self.list.currentItem() is None:
            self.header.setText("")
            self.preview.clear()

    def _folder_changed(self, item, _prev):
        if item is not None and item.data(0, Qt.UserRole):
            self.folder = item.data(0, Qt.UserRole)
            self.refresh()

    def current(self):
        item = self.list.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def _show_message(self, item, _prev=None):
        if item is None:
            return
        m = item.data(0, Qt.UserRole)
        sim = _life()
        if m["kind"] == "in":
            me = sim.user_address() if sim is not None else ""
            self.header.setText(f"<b>From:</b> {m['from']} &lt;{m.get('addr', '')}&gt;&nbsp;&nbsp;&nbsp;"
                                f"<b>To:</b> {me}<br><b>Subject:</b> {m['subject']}")
            if not m.get("read") and sim is not None:
                sim.mailbox.mark_read(m["id"])
                QTimer.singleShot(0, self.refresh)
        else:
            self.header.setText(f"<b>To:</b> {m['to'].replace('<', '&lt;')}<br><b>Subject:</b> {m['subject']}")
        self.preview.setPlainText(m["body"])

    def open_message(self, item):
        m = item.data(0, Qt.UserRole)
        if m["kind"] == "drafts":
            self.compose(m["to"], m["subject"], m["body"], draft_id=m["id"])

    def _mark(self, read):
        m = self.current()
        sim = _life()
        if m and m["kind"] == "in" and sim is not None:
            sim.mailbox.mark_read(m["id"], read)
            self.refresh()

    def _mail_arrived(self):
        if isValid(self):
            self.refresh()

    # ---- actions --------------------------------------------------------------------------------------------------
    def compose(self, to="", subject="", body="", draft_id=None):
        body_w = Compose(self, to, subject, body, draft_id)
        win = XPWindow(self.desktop, subject or "New Message", body_w, QIcon(envelope_pixmap(16)), (560, 440))
        body_w.frame = win
        self.desktop.open_window(win)
        (body_w.body if to else body_w.to).setFocus()
        return win

    def _quote(self, m):
        sim = _life()
        me = sim.user_address() if sim is not None else ""
        quoted = "\n".join("> " + line for line in m["body"].splitlines())
        return (f"\n\n----- Original Message -----\nFrom: {m['from']} <{m.get('addr', '')}>\nTo: {me}\n"
                f"Sent: {m['date']}\nSubject: {m['subject']}\n\n{quoted}")

    def reply(self):
        m = self.current()
        if not m or m["kind"] != "in" or m["from"] == "Mail Delivery Subsystem":
            return
        subject = m["subject"] if m["subject"].lower().startswith("re:") else f"Re: {m['subject']}"
        win = self.compose(f"{m['from']} <{m['addr']}>", subject, self._quote(m))
        edit = win.content.body
        cursor = edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        edit.setTextCursor(cursor)

    def forward(self):
        m = self.current()
        if not m:
            return
        body = self._quote(m) if m["kind"] == "in" else "\n\n" + m["body"]
        self.compose("", f"Fw: {m['subject']}", body)

    def delete(self):
        m = self.current()
        if not m:
            return
        sim = _life()
        if m["kind"] == "in" and sim is not None:
            if self.folder == "deleted":
                self._message("Outlook Express", "Are you sure you want to permanently delete the selected "
                              "message(s)?", ("Yes", "No"),
                              lambda b: b == "Yes" and (sim.mailbox.purge(m["id"]), self.refresh()), "warning")
                return
            sim.mailbox.move(m["id"], "deleted")
        else:
            store = _store()
            store[m["kind"]] = [x for x in store[m["kind"]] if x["id"] != m["id"]]
            save_json(STORE, store)
        self.refresh()

    def empty_deleted(self):
        sim = _life()
        if sim is None:
            return

        def go(button):
            if button == "Yes":
                for m in sim.mailbox.messages():
                    if m.get("folder") == "deleted":
                        sim.mailbox.purge(m["id"])
                self.refresh()
        self._message("Outlook Express", "Are you sure you want to permanently delete all the messages in the "
                      "'Deleted Items' folder?", ("Yes", "No"), go, "warning")

    def send_recv(self):
        if not network.is_connected():
            network.connect(self.desktop, then=self.send_recv)
            return
        store = _store()
        for msg in store["outbox"]:
            deliver(self.desktop, msg)
            store["sent"].append(msg)
        sent = len(store["outbox"])
        store["outbox"] = []
        save_json(STORE, store)
        sim = _life()
        if sim is not None:
            sim._deliver_mail()
        self.status.setText(f"Sent {sent} message(s). Checking for new messages..." if sent else
                            "Checking for new messages...")
        QTimer.singleShot(1500, self.refresh)

    def print_(self):
        m = self.current()
        if not m:
            return
        from ..printing import print_text
        who = f"From: {m['from']}" if m["kind"] == "in" else f"To: {m['to']}"
        print_text(self.desktop, m["subject"], f"{who}\nDate: {m['date']}\nSubject: {m['subject']}\n\n{m['body']}")

    def _message(self, title, text, buttons=("OK",), on_button=None, icon="info"):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon, buttons, on_button)

    def closeEvent(self, event):
        sim = _life()
        if sim is not None:
            try:
                sim.mail_arrived.disconnect(self._mail_arrived)
            except (RuntimeError, TypeError):
                pass
        net = network.get(self.desktop)
        if self.listener in net.disconnect_listeners:
            net.disconnect_listeners.remove(self.listener)
        event.accept()


_open = {}


def open_outlook(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = OutlookExpress(desktop)
    win = XPWindow(desktop, "Inbox - Outlook Express", body, oe_icon(), (820, 560))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win


# ---- the Windows Address Book ----------------------------------------------------------------------------------------

def open_address_book(desktop, on_pick=None):
    """Every buddy and their email address. Double-click (or Select) to address a message."""
    from ..life import email_address
    sim = _life()
    body = QWidget()
    body.setObjectName("oe")
    body.setAttribute(Qt.WA_StyledBackground, True)
    body.setStyleSheet(STYLE)
    v = QVBoxLayout(body)
    v.setContentsMargins(6, 6, 6, 6)
    find = QLineEdit()
    find.setPlaceholderText("Type name or select from list")
    v.addWidget(find)
    tree = QTreeWidget()
    tree.setRootIsDecorated(False)
    tree.setHeaderLabels(["Name", "E-Mail Address", "Home Phone"])
    tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
    names = sorted(sim.buddies, key=str.lower) if sim is not None else []
    for name in names:
        item = QTreeWidgetItem([name, email_address(name), ""])
        item.setIcon(0, book_icon())
        tree.addTopLevelItem(item)
    find.textChanged.connect(lambda t: [tree.topLevelItem(i).setHidden(t.lower() not in tree.topLevelItem(i).text(0).lower())
                                        for i in range(tree.topLevelItemCount())])
    v.addWidget(tree, 1)
    row = QHBoxLayout()
    row.addStretch()
    pick = QPushButton("Select" if on_pick else "Send Mail")
    close = QPushButton("Close")
    for b in (pick, close):
        b.setFixedSize(80, 23)
        row.addWidget(b)
    v.addLayout(row)
    win = XPWindow(desktop, "Address Book - Main Identity" if on_pick is None else "Select Recipients", body,
                   book_icon(), (520, 380))

    def use(item=None):
        item = item or tree.currentItem()
        if item is None:
            return
        desktop.close_window(win)
        if on_pick is not None:
            on_pick(item.text(0), item.text(1))
        else:
            open_outlook(desktop).content.compose(f"{item.text(0)} <{item.text(1)}>")

    pick.clicked.connect(lambda: use())
    tree.itemDoubleClicked.connect(lambda item: use(item))
    close.clicked.connect(lambda: desktop.close_window(win))
    desktop.open_window(win)
    return win
