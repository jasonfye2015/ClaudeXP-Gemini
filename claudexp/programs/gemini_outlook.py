"""Gemini Outlook: mail, calendar, tasks, and contacts for ClaudeXP."""
from PySide6.QtCore import QDate, QTime, Qt, QTimer
from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QDateEdit, QFormLayout, QHBoxLayout, QLabel, QHeaderView,
                               QLineEdit, QListWidget, QListWidgetItem, QMenuBar, QPushButton, QSplitter,
                               QTabWidget, QTextBrowser, QTimeEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
                               QWidget)
from shiboken6 import isValid

from .. import clock, network, sound
from ..paths import DATA
from ..wm import XPWindow
from . import outlook
from .notepad import MENU_STYLE
from .outlook import Compose, _life, _store, book_icon
from .people import load_json, save_json

STORE = DATA / "gemini_outlook.json"
STYLE = MENU_STYLE + """
QWidget#geminiOutlook { background: #ECE9D8; }
QWidget#geminiBar { background: #ECE9D8; border-bottom: 1px solid #ACA899; }
QTreeWidget, QTableWidget, QTextBrowser, QListWidget { background: white; border: 1px solid #7F9DB9;
                                                       font-family: Tahoma; font-size: 11px; }
QHeaderView::section { background: #E7E8EA; border: 1px solid #C5C5C5; padding: 3px; }
QLabel#geminiTitle { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3A6EA5, stop:1 #8EB0DA);
                     color: white; font-family: Tahoma; font-size: 12px; font-weight: bold; padding: 4px 6px; }
QLabel#geminiStatus { border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
QLineEdit, QDateEdit, QTimeEdit { background: white; font-family: Arial; font-size: 12px; }
"""
FOLDERS = [("inbox", "Inbox"), ("outbox", "Outbox"), ("sent", "Sent Items"),
           ("drafts", "Drafts"), ("deleted", "Deleted Items")]


def _data():
    data = load_json(STORE, {})
    data.setdefault("events", [])
    data.setdefault("tasks", [])
    data.setdefault("contacts", [])
    data.setdefault("next_id", 1)
    return data


def gemini_outlook_icon():
    from .office_icons import office_icon
    icon = office_icon("outlook")
    if not icon.isNull():
        return icon
    from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
    from PySide6.QtCore import QRectF

    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#344E6D"), 1))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(QRectF(3.5, 5.5, 25, 21), 2, 2)
    painter.setPen(QPen(QColor("#4876A8"), 2))
    painter.drawLine(5, 8, 16, 17)
    painter.drawLine(16, 17, 27, 8)
    painter.setPen(QPen(QColor("#184B78"), 1))
    painter.setBrush(QColor("#F5C451"))
    painter.drawEllipse(QRectF(18, 18, 13, 13))
    painter.drawText(QRectF(18, 18, 13, 13), Qt.AlignCenter, "G")
    painter.end()
    return QIcon(pixmap)


class ContactDialog(QWidget):
    def __init__(self, owner, contact=None):
        super().__init__()
        self.owner = owner
        self.contact = contact
        self.original_name = contact.get("name", "") if contact else None
        self.frame = None
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(contact.get("name", "") if contact else "")
        self.email = QLineEdit(contact.get("email", "") if contact else "")
        self.phone = QLineEdit(contact.get("phone", "") if contact else "")
        form.addRow("Name:", self.name)
        form.addRow("E-mail:", self.email)
        form.addRow("Phone:", self.phone)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        buttons.addStretch()
        save = QPushButton("&Save")
        cancel = QPushButton("Cancel")
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        save.clicked.connect(self.save)
        cancel.clicked.connect(self.close_dialog)

    def save(self):
        name, email = self.name.text().strip(), self.email.text().strip()
        if not name or (email and ("@" not in email or any(ch.isspace() for ch in email))):
            return self.owner._message("Gemini Outlook", "Enter a contact name and a valid e-mail address.",
                                       "warning")
        data = _data()
        contacts = data["contacts"]
        if any(c.get("name") != self.original_name and
               c.get("name", "").casefold() == name.casefold() for c in contacts):
            return self.owner._message("Gemini Outlook", "A contact with that name already exists.", "warning")
        record = {"name": name, "email": email, "phone": self.phone.text().strip()}
        if self.contact is None:
            contacts.append(record)
        else:
            existing = next((c for c in contacts if c.get("name") == self.original_name), None)
            if existing is None:
                return self.owner._message("Gemini Outlook", "That contact no longer exists.", "warning")
            existing.update(record)
        save_json(STORE, data)
        self.owner.refresh_contacts()
        self.close_dialog()

    def close_dialog(self):
        if self.frame is not None:
            self.owner.desktop.close_window(self.frame)


class GeminiOutlook(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.folder = "inbox"
        self.setObjectName("geminiOutlook")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._menu())
        self.tabs = QTabWidget()
        self.tabs.addTab(self._mail_tab(), "Mail")
        self.tabs.addTab(self._calendar_tab(), "Calendar")
        self.tabs.addTab(self._tasks_tab(), "Tasks")
        self.tabs.addTab(self._contacts_tab(), "Contacts")
        root.addWidget(self.tabs, 1)
        self.status = QLabel()
        self.status.setObjectName("geminiStatus")
        root.addWidget(self.status)

        self._sim = _life()
        if self._sim is not None:
            self._sim.mail_arrived.connect(self._mail_arrived)
        self._disconnect_listener = lambda *_args: self.refresh_mail()
        network.get(desktop).disconnect_listeners.append(self._disconnect_listener)
        self.refresh_all()

    def _menu(self):
        menu = QMenuBar()
        menu.triggered.connect(lambda _action: sound.play("menu"))
        file_menu = menu.addMenu("&File")
        file_menu.addAction("&New", self.new_item, QKeySequence("Ctrl+N"))
        file_menu.addAction("&Save", self.save, QKeySequence("Ctrl+S"))
        file_menu.addAction("&Print...", self.print_current, QKeySequence("Ctrl+P"))
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close())
        actions = menu.addMenu("&Actions")
        actions.addAction("&New E-mail", self.compose, QKeySequence("Ctrl+Shift+M"))
        actions.addAction("&Send/Receive", self.send_receive, QKeySequence("Ctrl+M"))
        actions.addAction("New &Appointment", self.add_event)
        actions.addAction("New &Task", self.add_task)
        actions.addAction("New &Contact", self.add_contact)
        help_menu = menu.addMenu("&Help")
        help_menu.addAction("&About Gemini Outlook", self.about)
        return menu

    def _mail_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        bar = QWidget()
        bar.setObjectName("geminiBar")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(3, 2, 3, 2)
        for label, callback in (("New E-mail", self.compose), ("Reply", self.reply),
                                ("Forward", self.forward), ("Delete", self.delete_mail),
                                ("Send/Receive", self.send_receive)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            bar_layout.addWidget(button)
        bar_layout.addStretch()
        layout.addWidget(bar)
        split = QSplitter(Qt.Horizontal)
        self.mail_folders = QTreeWidget()
        self.mail_folders.setHeaderHidden(True)
        self.mail_folders.currentItemChanged.connect(self._folder_changed)
        split.addWidget(self.mail_folders)
        right = QSplitter(Qt.Vertical)
        self.mail_list = QTreeWidget()
        self.mail_list.setRootIsDecorated(False)
        self.mail_list.setHeaderLabels(["From / To", "Subject", "Date"])
        self.mail_list.setColumnWidth(0, 150)
        self.mail_list.currentItemChanged.connect(self._show_mail)
        self.mail_list.itemDoubleClicked.connect(self._open_mail)
        right.addWidget(self.mail_list)
        preview = QWidget()
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.mail_header = QLabel()
        self.mail_header.setObjectName("geminiTitle")
        preview_layout.addWidget(self.mail_header)
        self.mail_preview = QTextBrowser()
        preview_layout.addWidget(self.mail_preview, 1)
        right.addWidget(preview)
        right.setSizes([220, 230])
        split.addWidget(right)
        split.setSizes([145, 650])
        layout.addWidget(split, 1)
        return page

    def _calendar_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        bar = QHBoxLayout()
        add = QPushButton("New Appointment")
        edit = QPushButton("Edit")
        delete = QPushButton("Delete")
        for button, callback in ((add, self.add_event), (edit, self.edit_event), (delete, self.delete_event)):
            button.clicked.connect(callback)
            bar.addWidget(button)
        bar.addStretch()
        layout.addLayout(bar)
        self.event_list = QTreeWidget()
        self.event_list.setRootIsDecorated(False)
        self.event_list.setHeaderLabels(["Date", "Time", "Subject", "Details"])
        self.event_list.header().setStretchLastSection(True)
        self.event_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.event_list.itemDoubleClicked.connect(lambda *_args: self.edit_event())
        layout.addWidget(self.event_list, 1)
        return page

    def _tasks_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        bar = QHBoxLayout()
        add = QPushButton("New Task")
        complete = QPushButton("Toggle Complete")
        edit = QPushButton("Edit")
        delete = QPushButton("Delete")
        for button, callback in ((add, self.add_task), (edit, self.edit_task),
                                 (complete, self.toggle_task), (delete, self.delete_task)):
            button.clicked.connect(callback)
            bar.addWidget(button)
        bar.addStretch()
        layout.addLayout(bar)
        self.task_list = QTreeWidget()
        self.task_list.setRootIsDecorated(False)
        self.task_list.setHeaderLabels(["Status", "Task", "Due Date", "Notes"])
        self.task_list.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.task_list.header().setStretchLastSection(True)
        self.task_list.itemDoubleClicked.connect(lambda *_args: self.edit_task())
        layout.addWidget(self.task_list, 1)
        return page

    def _contacts_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        bar = QHBoxLayout()
        for label, callback in (("New Contact", self.add_contact), ("Edit", self.edit_contact),
                                ("Delete", self.delete_contact), ("New E-mail", self.email_contact)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            bar.addWidget(button)
        bar.addStretch()
        layout.addLayout(bar)
        self.contact_list = QTreeWidget()
        self.contact_list.setRootIsDecorated(False)
        self.contact_list.setHeaderLabels(["Name", "E-mail", "Phone", "Type"])
        self.contact_list.header().setStretchLastSection(True)
        self.contact_list.itemDoubleClicked.connect(lambda *_args: self.email_contact())
        layout.addWidget(self.contact_list, 1)
        return page

    def refresh_all(self):
        self.refresh_mail()
        self.refresh_calendar()
        self.refresh_tasks()
        self.refresh_contacts()

    def refresh(self):
        self.refresh_mail()

    def refresh_mail(self):
        if not isValid(self):
            return
        store = _store()
        sim = _life()
        unread = len(sim.mailbox.unread()) if sim is not None else 0
        selected = self.mail_list.currentItem()
        selected_id = selected.data(0, Qt.UserRole).get("id") if selected else None
        self.mail_folders.blockSignals(True)
        self.mail_folders.clear()
        for key, label in FOLDERS:
            count = unread if key == "inbox" else len(store.get(key, [])) if key in ("outbox", "drafts") else 0
            item = QTreeWidgetItem([f"{label} ({count})" if count else label])
            item.setData(0, Qt.UserRole, key)
            self.mail_folders.addTopLevelItem(item)
            if key == self.folder:
                self.mail_folders.setCurrentItem(item)
        self.mail_folders.blockSignals(False)
        incoming = self.folder in ("inbox", "deleted")
        if incoming:
            messages = sim.mailbox.messages() if sim is not None else []
            messages = [dict(message, kind="in") for message in messages
                        if message.get("folder", "inbox") == self.folder]
        else:
            messages = [dict(message, kind=self.folder) for message in store.get(self.folder, [])]
        self.mail_list.blockSignals(True)
        self.mail_list.clear()
        self.mail_list.setHeaderLabels(["From" if incoming else "To", "Subject", "Date"])
        for message in reversed(messages):
            who = message.get("from", "") if incoming else message.get("to", "")
            item = QTreeWidgetItem([who, message.get("subject", ""), message.get("date", "")])
            item.setData(0, Qt.UserRole, message)
            if message.get("kind") == "in" and not message.get("read"):
                for col in range(3):
                    font = item.font(col)
                    font.setBold(True)
                    item.setFont(col, font)
            self.mail_list.addTopLevelItem(item)
            if message.get("id") == selected_id:
                self.mail_list.setCurrentItem(item)
        self.mail_list.blockSignals(False)
        if self.mail_list.currentItem() is None:
            self.mail_header.clear()
            self.mail_preview.clear()
        self.status.setText(f"{len(messages)} message(s)    "
                            f"{'Working Online' if network.is_connected() else 'Working Offline'}")

    def _folder_changed(self, item, _previous):
        if item is not None and item.data(0, Qt.UserRole):
            self.folder = item.data(0, Qt.UserRole)
            self.refresh_mail()

    def _current_mail(self):
        item = self.mail_list.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def _show_mail(self, item, _previous=None):
        if item is None:
            return
        message = item.data(0, Qt.UserRole)
        if message.get("kind") == "in":
            self.mail_header.setText(f"From: {message.get('from', '')} <{message.get('addr', '')}>"
                                     f"    Subject: {message.get('subject', '')}")
            if not message.get("read") and _life() is not None:
                _life().mailbox.mark_read(message["id"])
                QTimer.singleShot(0, self.refresh_mail)
        else:
            self.mail_header.setText(f"To: {message.get('to', '')}    Subject: {message.get('subject', '')}")
        self.mail_preview.setPlainText(message.get("body", ""))

    def _open_mail(self, item, _column=0):
        message = item.data(0, Qt.UserRole)
        if message.get("kind") == "drafts":
            self.compose(message.get("to", ""), message.get("subject", ""), message.get("body", ""),
                         message.get("id"))

    def compose(self, to="", subject="", body="", draft_id=None):
        body_widget = GeminiCompose(self, to, subject, body, draft_id)
        window = XPWindow(self.desktop, subject or "New E-mail", body_widget, gemini_outlook_icon(),
                          (560, 440))
        body_widget.frame = window
        self.desktop.open_window(window)
        (body_widget.body if to else body_widget.to).setFocus()
        return window

    def reply(self):
        message = self._current_mail()
        if not message or message.get("kind") != "in" or message.get("from") == "Mail Delivery Subsystem":
            return
        subject = message.get("subject", "")
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        quoted = "\n".join("> " + line for line in message.get("body", "").splitlines())
        text = (f"\n\n----- Original Message -----\nFrom: {message.get('from', '')}\n"
                f"Sent: {message.get('date', '')}\nSubject: {message.get('subject', '')}\n\n{quoted}")
        self.compose(f"{message.get('from', '')} <{message.get('addr', '')}>", subject, text)

    def forward(self):
        message = self._current_mail()
        if message:
            self.compose("", f"Fw: {message.get('subject', '')}", "\n\n" + message.get("body", ""))

    def delete_mail(self):
        message = self._current_mail()
        if not message:
            return
        sim = _life()
        if message.get("kind") == "in" and sim is not None and self.folder != "deleted":
            sim.mailbox.move(message["id"], "deleted")
        elif message.get("kind") == "in" and sim is not None:
            self._message("Gemini Outlook", "Permanently delete this message?", "warning", ("Yes", "No"),
                          lambda answer: self._purge_mail(sim, message["id"]) if answer == "Yes" else None)
            return
        else:
            store = _store()
            store[self.folder] = [m for m in store.get(self.folder, []) if m.get("id") != message.get("id")]
            save_json(outlook.STORE, store)
        self.refresh_mail()

    def _purge_mail(self, sim, message_id):
        sim.mailbox.purge(message_id)
        self.refresh_mail()

    def send_receive(self):
        if not network.is_connected():
            network.connect(self.desktop, then=self.send_receive)
            return
        store = _store()
        for message in store["outbox"]:
            outlook.deliver(self.desktop, message)
            store["sent"].append(message)
        sent = len(store["outbox"])
        store["outbox"] = []
        save_json(outlook.STORE, store)
        sim = _life()
        if sim is not None:
            sim._deliver_mail()
        self.status.setText(f"Sent {sent} message(s); checking for new mail...")
        QTimer.singleShot(1200, self.refresh_mail)

    def _event_dialog(self, event=None):
        from ..network import DialogBody, _fixed_window

        data = event or {}
        body = DialogBody()
        layout = QVBoxLayout(body)
        form = QFormLayout()
        title = QLineEdit(data.get("title", ""))
        date = QDateEdit()
        date.setCalendarPopup(True)
        now = clock.now()
        date.setDate(QDate(now.year, now.month, now.day))
        if data.get("date"):
            date.setDate(QDate.fromString(data["date"], "yyyy-MM-dd"))
        time = QTimeEdit()
        time.setDisplayFormat("h:mm AP")
        if data.get("time"):
            time.setTime(QTime.fromString(data["time"], "HH:mm"))
        details = QLineEdit(data.get("details", ""))
        form.addRow("Subject:", title)
        form.addRow("Date:", date)
        form.addRow("Time:", time)
        form.addRow("Details:", details)
        layout.addLayout(form)
        row = QHBoxLayout()
        row.addStretch()
        save, cancel = QPushButton("&Save"), QPushButton("Cancel")
        row.addWidget(save)
        row.addWidget(cancel)
        layout.addLayout(row)
        holder = {}

        def close():
            if holder.get("window") is not None:
                self.desktop.close_window(holder.pop("window"))

        def commit():
            if not title.text().strip():
                return self._message("Gemini Outlook", "Enter an appointment subject.", "warning")
            record = {"title": title.text().strip(), "date": date.date().toString("yyyy-MM-dd"),
                      "time": time.time().toString("HH:mm"), "details": details.text().strip()}
            all_data = _data()
            if event is None:
                record["id"] = all_data["next_id"]
                all_data["next_id"] += 1
                all_data["events"].append(record)
            else:
                existing = next((saved for saved in all_data["events"]
                                 if saved.get("id") == event.get("id")), None)
                if existing is None:
                    return self._message("Gemini Outlook", "That appointment no longer exists.", "warning")
                existing.update(record)
            save_json(STORE, all_data)
            close()
            self.refresh_calendar()

        save.clicked.connect(commit)
        cancel.clicked.connect(close)
        holder["window"] = _fixed_window(self.desktop, "Appointment", body, close)
        self.desktop.open_window(holder["window"])
        title.setFocus()

    def add_event(self):
        self._event_dialog()

    def edit_event(self):
        item = self.event_list.currentItem()
        if item:
            self._event_dialog(item.data(0, Qt.UserRole))

    def delete_event(self):
        item = self.event_list.currentItem()
        if item is None:
            return
        data = _data()
        data["events"] = [event for event in data["events"] if event.get("id") != item.data(0, Qt.UserRole).get("id")]
        save_json(STORE, data)
        self.refresh_calendar()

    def refresh_calendar(self):
        self.event_list.clear()
        events = sorted(_data()["events"], key=lambda event: (event.get("date", ""), event.get("time", "")))
        for event in events:
            date = event.get("date", "")
            time = event.get("time", "")
            item = QTreeWidgetItem([date, time, event.get("title", ""), event.get("details", "")])
            item.setData(0, Qt.UserRole, event)
            self.event_list.addTopLevelItem(item)

    def _task_dialog(self, task=None):
        from ..network import DialogBody, _fixed_window

        record = task or {}
        body = DialogBody()
        layout = QVBoxLayout(body)
        form = QFormLayout()
        title = QLineEdit(record.get("title", ""))
        due = QDateEdit()
        due.setCalendarPopup(True)
        now = clock.now()
        due.setDate(QDate(now.year, now.month, now.day))
        if record.get("due"):
            due.setDate(QDate.fromString(record["due"], "yyyy-MM-dd"))
        notes = QLineEdit(record.get("notes", ""))
        form.addRow("Task:", title)
        form.addRow("Due Date:", due)
        form.addRow("Notes:", notes)
        layout.addLayout(form)
        row = QHBoxLayout()
        row.addStretch()
        save, cancel = QPushButton("&Save"), QPushButton("Cancel")
        row.addWidget(save)
        row.addWidget(cancel)
        layout.addLayout(row)
        holder = {}

        def close():
            if holder.get("window") is not None:
                self.desktop.close_window(holder.pop("window"))

        def commit():
            if not title.text().strip():
                return self._message("Gemini Outlook", "Enter a task name.", "warning")
            data = _data()
            updated = {"title": title.text().strip(), "due": due.date().toString("yyyy-MM-dd"),
                       "notes": notes.text().strip(), "complete": bool(record.get("complete", False))}
            if task is None:
                updated["id"] = data["next_id"]
                data["next_id"] += 1
                data["tasks"].append(updated)
            else:
                existing = next((saved for saved in data["tasks"]
                                 if saved.get("id") == task.get("id")), None)
                if existing is None:
                    return self._message("Gemini Outlook", "That task no longer exists.", "warning")
                existing.update(updated)
            save_json(STORE, data)
            close()
            self.refresh_tasks()

        save.clicked.connect(commit)
        cancel.clicked.connect(close)
        holder["window"] = _fixed_window(self.desktop, "Task", body, close)
        self.desktop.open_window(holder["window"])
        title.setFocus()

    def add_task(self):
        self._task_dialog()

    def edit_task(self):
        item = self.task_list.currentItem()
        if item is not None:
            task = item.data(0, Qt.UserRole)
            saved = next((record for record in _data()["tasks"] if record.get("id") == task.get("id")), None)
            if saved is not None:
                self._task_dialog(saved)

    def toggle_task(self):
        item = self.task_list.currentItem()
        if item is None:
            return
        task = item.data(0, Qt.UserRole)
        data = _data()
        saved = next((record for record in data["tasks"] if record.get("id") == task.get("id")), None)
        if saved is None:
            return
        saved["complete"] = not saved.get("complete", False)
        save_json(STORE, data)
        self.refresh_tasks()

    def delete_task(self):
        item = self.task_list.currentItem()
        if item is None:
            return
        task_id = item.data(0, Qt.UserRole).get("id")
        data = _data()
        data["tasks"] = [task for task in data["tasks"] if task.get("id") != task_id]
        save_json(STORE, data)
        self.refresh_tasks()

    def refresh_tasks(self):
        self.task_list.clear()
        tasks = sorted(_data()["tasks"], key=lambda task: (task.get("complete", False), task.get("due", "")))
        for task in tasks:
            state = "Complete" if task.get("complete") else "Open"
            item = QTreeWidgetItem([state, task.get("title", ""), task.get("due", ""), task.get("notes", "")])
            item.setData(0, Qt.UserRole, task)
            if task.get("complete"):
                font = item.font(1)
                font.setStrikeOut(True)
                item.setFont(1, font)
            self.task_list.addTopLevelItem(item)

    def refresh_contacts(self):
        self.contact_list.clear()
        sim = _life()
        from ..life import email_address
        entries = []
        if sim is not None:
            entries.extend(({"name": name, "email": email_address(name), "phone": "", "type": "Buddy"}
                            for name in sim.people))
        entries.extend(dict(contact, type="Personal") for contact in _data()["contacts"])
        for contact in sorted(entries, key=lambda entry: entry.get("name", "").casefold()):
            item = QTreeWidgetItem([contact.get("name", ""), contact.get("email", ""),
                                    contact.get("phone", ""), contact.get("type", "Personal")])
            item.setData(0, Qt.UserRole, contact)
            self.contact_list.addTopLevelItem(item)

    def _custom_contact(self):
        item = self.contact_list.currentItem()
        if item is None:
            return None
        contact = item.data(0, Qt.UserRole)
        return contact if contact.get("type") == "Personal" else None

    def add_contact(self):
        self._open_contact_dialog()

    def edit_contact(self):
        contact = self._custom_contact()
        if contact is None:
            return
        source = next((record for record in _data()["contacts"]
                       if record.get("name") == contact.get("name")), None)
        if source is not None:
            self._open_contact_dialog(source)

    def _open_contact_dialog(self, contact=None):
        dialog = ContactDialog(self, contact)
        dialog.frame = XPWindow(self.desktop, "Contact", dialog, book_icon(), (360, 210))
        self.desktop.open_window(dialog.frame)

    def delete_contact(self):
        contact = self._custom_contact()
        if contact is None:
            return
        data = _data()
        data["contacts"] = [record for record in data["contacts"]
                            if record.get("name") != contact.get("name")]
        save_json(STORE, data)
        self.refresh_contacts()

    def email_contact(self):
        item = self.contact_list.currentItem()
        if item is None:
            return
        contact = item.data(0, Qt.UserRole)
        if contact.get("email"):
            self.compose(f"{contact['name']} <{contact['email']}>")

    def new_item(self):
        self.compose() if self.tabs.currentIndex() == 0 else (
            self.add_event() if self.tabs.currentIndex() == 1 else
            self.add_task() if self.tabs.currentIndex() == 2 else self.add_contact())

    def save(self):
        self.status.setText("Gemini Outlook saves changes as you make them.")

    def print_current(self):
        if self.tabs.currentIndex() != 0:
            return
        message = self._current_mail()
        if message is not None:
            from ..printing import print_text
            print_text(self.desktop, message.get("subject", "E-mail"),
                       f"{message.get('body', '')}")

    def about(self):
        self._message("About Gemini Outlook", "Gemini Outlook\nVersion 1.0")

    def _mail_arrived(self):
        if isValid(self):
            self.refresh_mail()

    def _message(self, title, text, icon="info", buttons=("OK",), on_button=None):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon, buttons, on_button)

    def closeEvent(self, event):
        if self._sim is not None:
            try:
                self._sim.mail_arrived.disconnect(self._mail_arrived)
            except (RuntimeError, TypeError):
                pass
        listeners = network.get(self.desktop).disconnect_listeners
        if self._disconnect_listener in listeners:
            listeners.remove(self._disconnect_listener)
        event.accept()


class GeminiCompose(Compose):
    def pick_address(self):
        from ..life import email_address
        sim = _life()
        contacts = [{"name": name, "email": email_address(name)}
                    for name in sim.people] if sim is not None else []
        contacts.extend(_data()["contacts"])
        items = sorted({(c.get("name", ""), c.get("email", "")) for c in contacts},
                       key=lambda pair: pair[0].casefold())
        from ..network import DialogBody, _fixed_window
        body = DialogBody()
        layout = QVBoxLayout(body)
        listing = QListWidget()
        for name, address in items:
            row = QListWidgetItem(f"{name} <{address}>" if address else name)
            row.setData(Qt.UserRole, (name, address))
            listing.addItem(row)
        layout.addWidget(listing)
        buttons = QHBoxLayout()
        buttons.addStretch()
        select, cancel = QPushButton("&Select"), QPushButton("Cancel")
        buttons.addWidget(select)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        holder = {}

        def close():
            if holder.get("window") is not None:
                self.desktop.close_window(holder.pop("window"))

        def choose():
            item = listing.currentItem()
            if item is not None:
                name, address = item.data(Qt.UserRole)
                current = self.to.text().strip()
                self.to.setText((current + "; " if current else "") +
                                (f"{name} <{address}>" if address else name))
                close()

        select.clicked.connect(choose)
        cancel.clicked.connect(close)
        listing.itemDoubleClicked.connect(lambda _item: choose())
        holder["window"] = _fixed_window(self.desktop, "Select Recipients", body, close)
        self.desktop.open_window(holder["window"])


def open_gemini_outlook(desktop):
    body = GeminiOutlook(desktop)
    window = XPWindow(desktop, "Gemini Outlook", body, gemini_outlook_icon(), (920, 620))
    body.frame = window
    desktop.open_window(window)
    return window
