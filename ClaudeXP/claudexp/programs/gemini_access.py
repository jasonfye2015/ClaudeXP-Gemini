"""Gemini Access: a small, file-based database manager for ClaudeXP."""
import json
import math
import re
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QIcon, QKeySequence, QTextDocument
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateEdit, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenuBar, QPushButton,
                               QStyle, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .. import clock, sound
from ..wm import XPWindow
from .notepad import MENU_STYLE, SaveAsDialog

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_TABLES = 100
MAX_FIELDS = 32
MAX_RECORDS = 50000
MAX_TEXT_LENGTH = 10000
FIELD_TYPES = ("Text", "Number", "Date", "Yes/No")
NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_ ]{0,63}$")
STYLE = MENU_STYLE + """
QWidget#geminiAccess { background: #ECE9D8; }
QWidget#accessBar { background: #ECE9D8; border-bottom: 1px solid #ACA899; }
QListWidget, QTableWidget { background: white; border: 1px solid #7F9DB9;
                            font-family: Tahoma; font-size: 11px; }
QHeaderView::section { background: #E7E8EA; border: 1px solid #C5C5C5; padding: 3px; }
QLineEdit { background: white; font-family: Arial; font-size: 12px; }
QLabel#accessStatus { border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
"""


def _valid_name(name):
    return bool(NAME_PATTERN.fullmatch(name.strip()))


def _empty_database():
    return {"format": "GeminiDatabase", "version": 1, "tables": []}


def _validate_database(data):
    if (not isinstance(data, dict) or data.get("format") != "GeminiDatabase"
            or data.get("version") != 1 or not isinstance(data.get("tables"), list)):
        raise ValueError("This is not a supported Gemini Access database.")
    if len(data["tables"]) > MAX_TABLES:
        raise ValueError(f"A database can contain at most {MAX_TABLES} tables.")
    names = set()
    for table in data["tables"]:
        if not isinstance(table, dict):
            raise ValueError("The database contains an invalid table.")
        name, fields, records = table.get("name"), table.get("fields"), table.get("records")
        if not isinstance(name, str) or not _valid_name(name) or name.casefold() in names:
            raise ValueError("The database contains an invalid or duplicate table name.")
        names.add(name.casefold())
        if not isinstance(fields, list) or not 1 <= len(fields) <= MAX_FIELDS:
            raise ValueError(f"Table '{name}' must contain between 1 and {MAX_FIELDS} fields.")
        field_names = set()
        for field in fields:
            if (not isinstance(field, dict) or not isinstance(field.get("name"), str)
                    or not _valid_name(field["name"]) or field["name"].casefold() in field_names
                    or field.get("type") not in FIELD_TYPES):
                raise ValueError(f"Table '{name}' contains an invalid or duplicate field.")
            field_names.add(field["name"].casefold())
        if not isinstance(records, list) or len(records) > MAX_RECORDS:
            raise ValueError(f"Table '{name}' has an invalid number of records.")
        for record in records:
            if not isinstance(record, dict):
                raise ValueError(f"Table '{name}' contains an invalid record.")
            for field in fields:
                value = record.get(field["name"])
                if field["type"] == "Text" and value is not None and (
                        not isinstance(value, str) or len(value) > MAX_TEXT_LENGTH):
                    raise ValueError(f"Table '{name}' contains invalid text data.")
                if field["type"] == "Number" and value is not None and (
                        isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value)):
                    raise ValueError(f"Table '{name}' contains invalid number data.")
                if field["type"] == "Date" and value is not None:
                    if not isinstance(value, str) or not QDate.fromString(value, "yyyy-MM-dd").isValid():
                        raise ValueError(f"Table '{name}' contains invalid date data.")
                if field["type"] == "Yes/No" and value is not None and not isinstance(value, bool):
                    raise ValueError(f"Table '{name}' contains invalid Yes/No data.")
    return data


def gemini_access_icon():
    from .office_icons import office_icon
    icon = office_icon("access")
    if not icon.isNull():
        return icon
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QPainter, QPen, QPixmap

    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#5D4E35"), 1))
    painter.setBrush(QColor("#F8F6EE"))
    painter.drawRoundedRect(QRectF(3.5, 4.5, 25, 22), 2, 2)
    painter.setPen(QPen(QColor("#C8B996"), 1))
    for y in (11, 17, 23):
        painter.drawLine(5, y, 27, y)
    for x in (13, 21):
        painter.drawLine(x, 6, x, 25)
    painter.setPen(QPen(QColor("#184B78"), 1))
    painter.setBrush(QColor("#F5C451"))
    painter.drawEllipse(QRectF(18, 18, 13, 13))
    painter.drawText(QRectF(18, 18, 13, 13), Qt.AlignCenter, "G")
    painter.end()
    return QIcon(pixmap)


class GeminiAccess(QWidget):
    def __init__(self, desktop, path=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.database = _empty_database()
        self.modified = False
        self._loading = False
        self.setObjectName("geminiAccess")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._menu())
        toolbar = QWidget()
        toolbar.setObjectName("accessBar")
        bar = QHBoxLayout(toolbar)
        bar.setContentsMargins(5, 3, 5, 3)
        for label, callback in (("New Table", self.add_table), ("Design", self.design_table),
                                ("Delete Table", self.delete_table), ("Add Record", self.add_record),
                                ("Edit Record", self.edit_record), ("Delete Record", self.delete_record)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            bar.addWidget(button)
        bar.addStretch()
        root.addWidget(toolbar)
        split_row = QHBoxLayout()
        split_row.setContentsMargins(5, 5, 5, 5)
        split_row.setSpacing(6)
        left = QVBoxLayout()
        left.addWidget(QLabel("Tables"))
        self.table_list = QListWidget()
        self.table_list.currentItemChanged.connect(self._table_changed)
        left.addWidget(self.table_list, 1)
        split_row.addLayout(left, 1)
        right = QVBoxLayout()
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Find:"))
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter records in this table")
        self.filter.textChanged.connect(self.refresh_records)
        filter_row.addWidget(self.filter, 1)
        right.addLayout(filter_row)
        self.records = QTableWidget()
        self.records.setAlternatingRowColors(True)
        self.records.setSortingEnabled(True)
        self.records.setSelectionBehavior(QTableWidget.SelectRows)
        self.records.setSelectionMode(QTableWidget.SingleSelection)
        self.records.itemDoubleClicked.connect(lambda *_args: self.edit_record())
        right.addWidget(self.records, 1)
        split_row.addLayout(right, 4)
        root.addLayout(split_row, 1)
        self.status = QLabel("Ready")
        self.status.setObjectName("accessStatus")
        root.addWidget(self.status)
        if path is not None:
            self.load(Path(path))
        else:
            self.refresh_tables()

    def _menu(self):
        menu = QMenuBar()
        menu.triggered.connect(lambda _action: sound.play("menu"))
        file_menu = menu.addMenu("&File")
        file_menu.addAction("&New", self.new, QKeySequence("Ctrl+N"))
        file_menu.addAction("&Open...", self.open_dialog, QKeySequence("Ctrl+O"))
        file_menu.addAction("&Save", self.save, QKeySequence("Ctrl+S"))
        file_menu.addAction("Save &As...", self.save_as)
        file_menu.addSeparator()
        file_menu.addAction("&Print...", self.print_table, QKeySequence("Ctrl+P"))
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close())
        table_menu = menu.addMenu("&Table")
        table_menu.addAction("&New Table", self.add_table)
        table_menu.addAction("&Design Table", self.design_table)
        table_menu.addAction("&Delete Table", self.delete_table)
        records = menu.addMenu("&Records")
        records.addAction("&Add Record", self.add_record, QKeySequence("Ctrl+Plus"))
        records.addAction("&Edit Record", self.edit_record)
        records.addAction("&Delete Record", self.delete_record, QKeySequence("Ctrl+D"))
        menu.addMenu("&Help").addAction("&About Gemini Access", self.about)
        return menu

    def name(self):
        return self.path.name if self.path else "Database"

    def _update_title(self):
        if self.frame is not None:
            prefix = "*" if self.modified else ""
            self.frame.set_title(f"{prefix}{self.name()} - Gemini Access")

    def _message(self, title, text, icon="info", buttons=("OK",), on_button=None):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon, buttons, on_button)

    def current_table(self):
        item = self.table_list.currentItem()
        name = item.data(Qt.UserRole) if item else None
        return next((table for table in self.database["tables"] if table["name"] == name), None)

    def refresh_tables(self, selected=None):
        selected = selected or (self.table_list.currentItem().data(Qt.UserRole)
                                if self.table_list.currentItem() else None)
        self._loading = True
        self.table_list.clear()
        for table in self.database["tables"]:
            item = QListWidgetItem(f"{table['name']}  ({len(table['records'])})")
            item.setData(Qt.UserRole, table["name"])
            self.table_list.addItem(item)
            if table["name"] == selected:
                self.table_list.setCurrentItem(item)
        self._loading = False
        if self.current_table() is None and self.table_list.count():
            self.table_list.setCurrentRow(0)
        elif self.current_table() is None:
            self.records.clear()
            self.records.setRowCount(0)
            self.records.setColumnCount(0)
        self._update_title()

    def _table_changed(self, item, _previous=None):
        if item is not None and not self._loading:
            self.filter.clear()
            self.refresh_records()

    def refresh_records(self, *_args):
        table = self.current_table()
        if table is None:
            self.records.clear()
            self.records.setRowCount(0)
            self.records.setColumnCount(0)
            self.status.setText("No table selected")
            return
        fields = table["fields"]
        query = self.filter.text().strip().casefold()
        shown = [(index, record) for index, record in enumerate(table["records"])
                 if not query or any(query in str(record.get(field["name"], "")).casefold()
                                     for field in fields)]
        self.records.setSortingEnabled(False)
        self.records.clear()
        self.records.setColumnCount(len(fields))
        self.records.setHorizontalHeaderLabels([field["name"] for field in fields])
        self.records.setRowCount(len(shown))
        for row, (record_index, record) in enumerate(shown):
            for column, field in enumerate(fields):
                value = record.get(field["name"])
                if field["type"] == "Yes/No":
                    text = "Yes" if value is True else "No" if value is False else ""
                else:
                    text = "" if value is None else str(value)
                cell = QTableWidgetItem(text)
                cell.setData(Qt.UserRole, record_index)
                self.records.setItem(row, column, cell)
        self.records.resizeColumnsToContents()
        self.records.setSortingEnabled(True)
        self.status.setText(f"Table: {table['name']}    {len(shown)} of {len(table['records'])} record(s)")

    def _set_modified(self):
        self.modified = True
        self._update_title()

    def _open_dialog(self, title, body, closer):
        from ..network import _fixed_window
        window = _fixed_window(self.desktop, title, body, closer)
        self.desktop.open_window(window)
        return window

    def _design_dialog(self, table=None):
        from ..network import DialogBody
        body = DialogBody()
        layout = QVBoxLayout(body)
        form = QFormLayout()
        table_name = QLineEdit(table["name"] if table else "")
        form.addRow("Table name:", table_name)
        layout.addLayout(form)
        grid = QTableWidget(0, 2)
        grid.setHorizontalHeaderLabels(["Field Name", "Data Type"])
        grid.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(grid)

        def append_field(field=None):
            if grid.rowCount() >= MAX_FIELDS:
                return self._message("Gemini Access", f"A table can have at most {MAX_FIELDS} fields.", "warning")
            row = grid.rowCount()
            grid.insertRow(row)
            if field:
                grid.setItem(row, 0, QTableWidgetItem(field["name"]))
            combo = QComboBox()
            combo.addItems(FIELD_TYPES)
            if field:
                combo.setCurrentText(field["type"])
            grid.setCellWidget(row, 1, combo)

        for field in table["fields"] if table else []:
            append_field(field)
        for _ in range(3 if table is None else 0):
            append_field()
        controls = QHBoxLayout()
        add = QPushButton("Add Field")
        remove = QPushButton("Remove Field")
        controls.addWidget(add)
        controls.addWidget(remove)
        controls.addStretch()
        save, cancel = QPushButton("&Save"), QPushButton("Cancel")
        controls.addWidget(save)
        controls.addWidget(cancel)
        layout.addLayout(controls)
        holder = {}

        def close():
            window = holder.pop("window", None)
            if window is not None:
                self.desktop.close_window(window)

        def commit():
            name = table_name.text().strip()
            if not _valid_name(name):
                return self._message("Gemini Access", "Use a table name starting with a letter or underscore; "
                                     "letters, numbers, spaces, and underscores are allowed.", "warning")
            duplicate = next((saved for saved in self.database["tables"]
                              if saved["name"].casefold() == name.casefold()
                              and (table is None or saved is not table)), None)
            if duplicate:
                return self._message("Gemini Access", "A table with that name already exists.", "warning")
            fields = []
            seen = set()
            for row in range(grid.rowCount()):
                item = grid.item(row, 0)
                field_name = item.text().strip() if item else ""
                if not field_name:
                    continue
                if not _valid_name(field_name) or field_name.casefold() in seen:
                    return self._message("Gemini Access", "Field names must be valid and unique.", "warning")
                seen.add(field_name.casefold())
                fields.append({"name": field_name, "type": grid.cellWidget(row, 1).currentText()})
            if not fields:
                return self._message("Gemini Access", "Add at least one field to the table.", "warning")
            if table is None and len(self.database["tables"]) >= MAX_TABLES:
                return self._message("Gemini Access", f"A database can have at most {MAX_TABLES} tables.",
                                     "warning")
            if table is None:
                record = {"name": name, "fields": fields, "records": []}
                self.database["tables"].append(record)
            else:
                old_names = {field["name"] for field in table["fields"]}
                new_names = {field["name"] for field in fields}
                for record in table["records"]:
                    for removed in old_names - new_names:
                        record.pop(removed, None)
                table["name"] = name
                table["fields"] = fields
            self._set_modified()
            close()
            self.refresh_tables(name)

        add.clicked.connect(append_field)
        remove.clicked.connect(lambda: grid.removeRow(grid.currentRow())
                               if grid.currentRow() >= 0 else None)
        save.clicked.connect(commit)
        cancel.clicked.connect(close)
        holder["window"] = self._open_dialog("Design Table", body, close)
        table_name.setFocus()

    def add_table(self):
        self._design_dialog()

    def design_table(self):
        table = self.current_table()
        if table is not None:
            self._design_dialog(table)

    def delete_table(self):
        table = self.current_table()
        if table is None:
            return
        self._message("Gemini Access", f"Delete table '{table['name']}' and all its records?", "warning",
                      ("Delete", "Cancel"), lambda answer: self._delete_table(table) if answer == "Delete" else None)

    def _delete_table(self, table):
        if table in self.database["tables"]:
            self.database["tables"].remove(table)
            self._set_modified()
            self.refresh_tables()

    def _record_dialog(self, record_index=None):
        from ..network import DialogBody
        table = self.current_table()
        if table is None:
            return
        record = table["records"][record_index] if record_index is not None and (
            0 <= record_index < len(table["records"])) else None
        if record_index is not None and record is None:
            return self._message("Gemini Access", "That record no longer exists.", "warning")
        if record_index is None and len(table["records"]) >= MAX_RECORDS:
            return self._message("Gemini Access", f"A table can have at most {MAX_RECORDS} records.", "warning")
        body = DialogBody()
        layout = QVBoxLayout(body)
        form = QFormLayout()
        editors = {}
        for field in table["fields"]:
            name, kind = field["name"], field["type"]
            value = record.get(name) if record else None
            if kind == "Yes/No":
                editor = QCheckBox()
                editor.setChecked(bool(value))
                editor.setTristate(True)
                editor.setCheckState(Qt.PartiallyChecked if value is None else
                                     Qt.Checked if value else Qt.Unchecked)
            elif kind == "Date":
                editor = QDateEdit()
                editor.setCalendarPopup(True)
                now = clock.now()
                editor.setDate(QDate(now.year, now.month, now.day))
                if value:
                    date = QDate.fromString(value, "yyyy-MM-dd")
                    if date.isValid():
                        editor.setDate(date)
            else:
                editor = QLineEdit("" if value is None else str(value))
                if kind == "Text":
                    editor.setMaxLength(MAX_TEXT_LENGTH)
            editors[name] = (kind, editor)
            form.addRow(f"{name}:", editor)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        buttons.addStretch()
        save, cancel = QPushButton("&Save"), QPushButton("Cancel")
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        holder = {}

        def close():
            window = holder.pop("window", None)
            if window is not None:
                self.desktop.close_window(window)

        def commit():
            updated = {}
            for name, (kind, editor) in editors.items():
                if kind == "Yes/No":
                    state = editor.checkState()
                    updated[name] = None if state == Qt.PartiallyChecked else state == Qt.Checked
                elif kind == "Date":
                    updated[name] = editor.date().toString("yyyy-MM-dd")
                elif kind == "Number":
                    text = editor.text().strip()
                    if not text:
                        updated[name] = None
                    else:
                        try:
                            number = float(text)
                        except ValueError:
                            return self._message("Gemini Access", f"'{text}' is not a valid number.", "warning")
                        if not math.isfinite(number):
                            return self._message("Gemini Access", "Numbers must be finite.", "warning")
                        updated[name] = number
                else:
                    updated[name] = editor.text()
            if record_index is None:
                table["records"].append(updated)
            else:
                if (record_index >= len(table["records"])
                        or table["records"][record_index] != record):
                    return self._message("Gemini Access", "That record no longer exists.", "warning")
                table["records"][record_index] = updated
            self._set_modified()
            close()
            self.refresh_tables(table["name"])
            self.refresh_records()

        save.clicked.connect(commit)
        cancel.clicked.connect(close)
        holder["window"] = self._open_dialog("Record", body, close)
        if editors:
            next(iter(editors.values()))[1].setFocus()

    def add_record(self):
        if self.current_table() is not None:
            self._record_dialog()

    def edit_record(self):
        item = self.records.currentItem()
        if item is not None:
            self._record_dialog(item.data(Qt.UserRole))

    def delete_record(self):
        item = self.records.currentItem()
        table = self.current_table()
        record_index = item.data(Qt.UserRole) if item is not None else None
        if table is not None and record_index is not None and record_index < len(table["records"]):
            table["records"].pop(record_index)
            self._set_modified()
            self.refresh_tables(table["name"])
            self.refresh_records()

    def new(self):
        self._maybe_save(lambda: self._reset_database())

    def _reset_database(self):
        self.path = None
        self.database = _empty_database()
        self.modified = False
        self.filter.clear()
        self.refresh_tables()

    def load(self, path):
        try:
            if path.stat().st_size > MAX_FILE_SIZE:
                raise ValueError("The database file is larger than the 10 MB limit.")
            data = json.loads(path.read_text(encoding="utf-8"))
            _validate_database(data)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            self._message("Gemini Access", f"Cannot open {path.name}.\n{error}", "error")
            return False
        self.path = path
        self.database = data
        self.modified = False
        self.filter.clear()
        self.refresh_tables()
        self._update_title()
        return True

    def save(self, then=None):
        if self.path is None:
            self.save_as(then)
            return
        try:
            payload = json.dumps(_validate_database(self.database), ensure_ascii=False, indent=2)
            if len(payload.encode("utf-8")) > MAX_FILE_SIZE:
                raise ValueError("The database would exceed the 10 MB file limit.")
            self.path.write_text(payload, encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as error:
            self._message("Gemini Access", f"Cannot save {self.path.name}.\n{error}", "error")
            return
        self.modified = False
        self._update_title()
        if callable(then):
            then()

    def save_as(self, then=None):
        name = self.path.name if self.path else "Database.gdb"
        folder = self.path.parent if self.path else None

        def saved(path):
            if path.suffix.lower() != ".gdb":
                path = path.with_suffix(".gdb")
            self.path = path
            self.save(then)

        SaveAsDialog(self.desktop, name, folder, saved)

    def open_dialog(self):
        from ..explorer import vfs
        from ..network import DialogBody, _fixed_window
        from PySide6.QtWidgets import QComboBox, QGridLayout

        places = [("My Documents", vfs.my_documents()), ("Desktop", vfs.user_home() / "Desktop"),
                  ("Shared Documents", vfs.shared_documents()), ("External Drive (E:)", vfs.local_storage())]
        body = DialogBody()
        grid = QGridLayout(body)
        where = QComboBox()
        for label, folder in places:
            where.addItem(QApplication.style().standardIcon(QStyle.SP_DirIcon),
                          label, str(folder))
        files = QListWidget()
        files.setMinimumSize(360, 200)
        grid.addWidget(QLabel("Look in:"), 0, 0)
        grid.addWidget(where, 0, 1)
        grid.addWidget(files, 1, 0, 1, 2)

        def fill():
            files.clear()
            folder = Path(where.currentData())
            if folder.is_dir():
                for candidate in sorted(folder.iterdir(), key=lambda item: item.name.casefold()):
                    if candidate.is_file() and candidate.suffix.lower() == ".gdb":
                        item = QListWidgetItem(candidate.name)
                        item.setData(Qt.UserRole, str(candidate))
                        files.addItem(item)

        where.currentIndexChanged.connect(fill)
        fill()
        holder = {}

        def close():
            window = holder.pop("window", None)
            if window is not None:
                self.desktop.close_window(window)

        def open_selected():
            item = files.currentItem()
            if item is not None:
                path = Path(item.data(Qt.UserRole))
                self._maybe_save(lambda: (close(), self.load(path)))

        open_button, cancel = QPushButton("&Open"), QPushButton("Cancel")
        grid.addWidget(open_button, 2, 0)
        grid.addWidget(cancel, 2, 1)
        holder["window"] = _fixed_window(self.desktop, "Open Gemini Database", body, close)
        open_button.clicked.connect(open_selected)
        cancel.clicked.connect(close)
        files.itemDoubleClicked.connect(lambda _item: open_selected())
        self.desktop.open_window(holder["window"])

    def print_table(self):
        table = self.current_table()
        if table is None:
            return
        from html import escape
        from ..printing import print_document
        headers = "".join(f"<th>{escape(field['name'])}</th>" for field in table["fields"])
        rows = []
        for record in table["records"]:
            cells = "".join(f"<td>{escape(str(record.get(field['name']) if record.get(field['name']) is not None else ''))}</td>"
                            for field in table["fields"])
            rows.append(f"<tr>{cells}</tr>")
        document = QTextDocument()
        document.setHtml(f"<table border='1' cellspacing='0' cellpadding='4'><tr>{headers}</tr>"
                         + "".join(rows) + "</table>")
        print_document(self.desktop, table["name"], document)

    def about(self):
        self._message("About Gemini Access", "Gemini Access\nVersion 1.0\n\n"
                      "A lightweight table-based database manager. Files use the Gemini .gdb format.")

    def _maybe_save(self, proceed):
        if not self.modified:
            proceed()
            return

        def answer(button):
            if button == "Yes":
                self.save(proceed)
            elif button == "No":
                proceed()

        self._message("Gemini Access", f"Save changes to {self.name()}?", "warning",
                      ("Yes", "No", "Cancel"), answer)

    def closeEvent(self, event):
        if not self.modified:
            event.accept()
            return
        event.ignore()
        self._maybe_save(lambda: self.desktop.close_window(self.frame) if self.frame is not None else None)


def open_gemini_access(desktop, path=None):
    body = GeminiAccess(desktop, path)
    window = XPWindow(desktop, f"{body.name()} - Gemini Access", body, gemini_access_icon(), (860, 560))
    body.frame = window
    desktop.open_window(window)
    return window
