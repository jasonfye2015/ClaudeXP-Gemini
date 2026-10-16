"""Gemini Excel: a lightweight multi-sheet spreadsheet for ClaudeXP."""
import ast
import csv
from html import escape
import json
import math
import operator
import re
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMenuBar, QPushButton, QStyle, QTabWidget, QTableWidget, QTableWidgetItem,
                               QStyledItemDelegate, QVBoxLayout, QWidget)

from .. import sound
from ..wm import XPWindow
from .notepad import MENU_STYLE, SaveAsDialog

ROWS, COLUMNS = 1000, 26
RAW_ROLE = Qt.UserRole
STYLE = MENU_STYLE + """
QWidget#geminiExcel { background: #ECE9D8; }
QWidget#excelBar { background: #ECE9D8; border-bottom: 1px solid #ACA899; }
QLineEdit, QTableWidget { background: white; border: 1px solid #7F9DB9; }
QTableWidget { gridline-color: #D7D7D7; font-family: Arial; font-size: 11px; }
QHeaderView::section { background: #E7E8EA; border: 1px solid #C5C5C5; padding: 3px; }
QLabel#excelStatus { border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
"""

_BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
_CELL = re.compile(r"^([A-Z]{1,3})([1-9]\d*)$", re.IGNORECASE)
_RANGE = re.compile(r"\b([A-Z]{1,3}[1-9]\d*):([A-Z]{1,3}[1-9]\d*)\b", re.IGNORECASE)
_FUNCTIONS = {"SUM", "AVERAGE", "MIN", "MAX", "COUNT"}


def column_name(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def cell_address(row, column):
    return f"{column_name(column + 1)}{row + 1}"


def parse_address(address):
    match = _CELL.fullmatch(address)
    if not match:
        raise ValueError("Invalid cell address")
    column = 0
    for char in match.group(1).upper():
        column = column * 26 + ord(char) - 64
    row = int(match.group(2))
    if column > COLUMNS or row > ROWS:
        raise ValueError("Cell reference is outside this worksheet")
    return row - 1, column - 1


def _formula_value(expression, get_cell):
    if len(expression) > 1024:
        raise ValueError("Formula is too long")

    def range_call(match):
        return f'RANGE("{match.group(1).upper()}","{match.group(2).upper()}")'

    tree = ast.parse(_RANGE.sub(range_call, expression), mode="eval")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            if _CELL.fullmatch(node.id):
                value = get_cell(node.id)
                return 0 if value is None else value
            raise ValueError("Unknown name")
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            left, right = visit(node.left), visit(node.right)
            left = 0 if left is None else left
            right = 0 if right is None else right
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent is too large")
            return _BINARY[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            value = 0 if value is None else value
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id.upper()
            if name == "RANGE" and len(node.args) == 2 and all(
                    isinstance(arg, ast.Constant) and isinstance(arg.value, str) for arg in node.args):
                return [get_cell(address) for address in _expand_range(node.args[0].value, node.args[1].value)]
            if name not in _FUNCTIONS or node.keywords:
                raise ValueError("Unsupported function")
            values = []
            for arg in node.args:
                result = visit(arg)
                values.extend(result if isinstance(result, list) else [result])
            values = [value for value in values if isinstance(value, (int, float))]
            if name == "SUM":
                return sum(values)
            if name == "AVERAGE":
                return sum(values) / len(values) if values else 0
            if name == "MIN":
                return min(values, default=0)
            if name == "MAX":
                return max(values, default=0)
            return len(values)
        raise ValueError("Unsupported formula")

    return visit(tree)


def _expand_range(start, end):
    first_row, first_col = parse_address(start)
    last_row, last_col = parse_address(end)
    top, bottom = sorted((first_row, last_row))
    left, right = sorted((first_col, last_col))
    if (bottom - top + 1) * (right - left + 1) > 10000:
        raise ValueError("Range is too large")
    return [cell_address(row, column)
            for row in range(top, bottom + 1) for column in range(left, right + 1)]


def gemini_excel_icon():
    from .office_icons import office_icon
    icon = office_icon("excel")
    if not icon.isNull():
        return icon
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#395342"), 1))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(QRectF(4.5, 3.5, 23, 24), 1, 1)
    painter.setPen(QPen(QColor("#A3BBA8"), 1))
    for x in (11, 17, 23):
        painter.drawLine(x, 5, x, 26)
    for y in (10, 16, 22):
        painter.drawLine(6, y, 26, y)
    painter.setPen(QPen(QColor("#184B78"), 1))
    painter.setBrush(QColor("#F5C451"))
    painter.drawEllipse(QRectF(17, 17, 13, 13))
    painter.drawText(QRectF(16.5, 17, 14, 14), Qt.AlignCenter, "G")
    painter.end()
    return QIcon(pm)


class ChartWidget(QWidget):
    def __init__(self, title, points):
        super().__init__()
        self.title = title
        self.points = points
        self.setMinimumSize(420, 300)
        self.setStyleSheet("background: white;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("white"))
        painter.setPen(QColor("#333333"))
        title_font = QFont("Tahoma", 12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(QRectF(12, 8, self.width() - 24, 26), Qt.AlignCenter, self.title)

        left, right, top, bottom = 52, self.width() - 16, 48, self.height() - 48
        painter.setPen(QPen(QColor("#808080"), 1))
        painter.drawLine(left, top, left, bottom)
        painter.drawLine(left, bottom, right, bottom)
        maximum = max((abs(value) for _label, value in self.points), default=0) or 1
        slot = (right - left) / len(self.points)
        bar_width = min(46, slot * 0.65)
        painter.setFont(QFont("Tahoma", 8))
        for index, (label, value) in enumerate(self.points):
            center = left + slot * (index + 0.5)
            bar_height = (bottom - top - 10) * abs(value) / maximum
            y = bottom - bar_height
            painter.fillRect(QRectF(center - bar_width / 2, y, bar_width, bar_height),
                             QColor("#55965A" if value >= 0 else "#B64B4B"))
            painter.setPen(QColor("#303030"))
            painter.drawText(QRectF(center - slot / 2, bottom + 4, slot, 32),
                             Qt.AlignHCenter | Qt.AlignTop, label[:14])
            painter.drawText(QRectF(center - slot / 2, max(top, y - 18), slot, 16),
                             Qt.AlignHCenter | Qt.AlignVCenter, f"{value:g}")
            painter.setPen(QPen(QColor("#808080"), 1))
        painter.end()


class _CellDelegate(QStyledItemDelegate):
    def setEditorData(self, editor, index):
        raw = index.data(RAW_ROLE)
        if raw is None:
            super().setEditorData(editor, index)
        else:
            editor.setText(str(raw))


class GeminiExcel(QWidget):
    def __init__(self, desktop, path=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.modified = False
        self._refreshing = False
        self._sheets = []
        self.setObjectName("geminiExcel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        menu = self._make_menu()
        root.addWidget(menu)

        formula_bar = QWidget()
        formula_bar.setObjectName("excelBar")
        formula_bar.setAttribute(Qt.WA_StyledBackground, True)
        row = QHBoxLayout(formula_bar)
        row.setContentsMargins(5, 3, 5, 3)
        self.address = QLineEdit("A1")
        self.address.setFixedWidth(70)
        self.address.setToolTip("Selected cell address")
        self.formula = QLineEdit()
        self.formula.setPlaceholderText("Enter a value or formula, e.g. =SUM(A1:A5)")
        self.formula.setClearButtonEnabled(True)
        row.addWidget(self.address)
        row.addWidget(QLabel("fx"))
        row.addWidget(self.formula, 1)
        root.addWidget(formula_bar)

        self.sheets = QTabWidget()
        self.sheets.setTabsClosable(False)
        self.sheets.currentChanged.connect(lambda _index: self._refresh_formula())
        root.addWidget(self.sheets, 1)
        bottom = QWidget()
        bottom.setObjectName("excelBar")
        bottom.setAttribute(Qt.WA_StyledBackground, True)
        bottom_row = QHBoxLayout(bottom)
        bottom_row.setContentsMargins(5, 2, 5, 2)
        add_sheet = QPushButton("+")
        add_sheet.setFixedWidth(28)
        add_sheet.setToolTip("Add worksheet")
        add_sheet.clicked.connect(self.add_sheet)
        bottom_row.addWidget(add_sheet)
        self.status = QLabel("Ready")
        self.status.setObjectName("excelStatus")
        bottom_row.addWidget(self.status, 1)
        root.addWidget(bottom)

        self.formula.returnPressed.connect(self.commit_formula)
        self.address.returnPressed.connect(self.select_address)
        if path is None:
            self.add_sheet("Sheet1")
            self.modified = False
        else:
            self.load(Path(path))

    def _make_menu(self):
        bar = QMenuBar()
        bar.triggered.connect(lambda _action: sound.play("menu"))
        file_menu = bar.addMenu("&File")
        file_menu.addAction("&New", self.new, QKeySequence("Ctrl+N"))
        file_menu.addAction("&Open...", self.open_dialog, QKeySequence("Ctrl+O"))
        file_menu.addAction("&Save", self.save, QKeySequence("Ctrl+S"))
        file_menu.addAction("Save &As...", self.save_as)
        file_menu.addSeparator()
        file_menu.addAction("&Print...", self.print_sheet, QKeySequence("Ctrl+P"))
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close())
        edit = bar.addMenu("&Edit")
        edit.addAction("&Copy", self.copy, QKeySequence("Ctrl+C"))
        edit.addAction("&Paste", self.paste, QKeySequence("Ctrl+V"))
        edit.addAction("Select &All", lambda: self.current_sheet().selectAll(), QKeySequence("Ctrl+A"))
        sheet_menu = bar.addMenu("&Sheet")
        sheet_menu.addAction("&Insert Worksheet", self.add_sheet, QKeySequence("Shift+F11"))
        data_menu = bar.addMenu("&Data")
        data_menu.addAction("Sort &Ascending", lambda: self.sort_selection(False))
        data_menu.addAction("Sort &Descending", lambda: self.sort_selection(True))
        data_menu.addAction("Create &Chart...", self.create_chart)
        help_menu = bar.addMenu("&Help")
        help_menu.addAction("&About Gemini Excel", self.about)
        return bar

    def current_sheet(self):
        return self.sheets.currentWidget()

    def add_sheet(self, name=None, values=None):
        if name is None or isinstance(name, bool):
            name = f"Sheet{self.sheets.count() + 1}"
        table = QTableWidget(ROWS, COLUMNS, self)
        table.setHorizontalHeaderLabels([column_name(i + 1) for i in range(COLUMNS)])
        table.setVerticalHeaderLabels([str(i + 1) for i in range(ROWS)])
        table.setSelectionMode(QTableWidget.ContiguousSelection)
        table.setSelectionBehavior(QTableWidget.SelectItems)
        table.setItemDelegate(_CellDelegate(table))
        table.setAlternatingRowColors(True)
        table.setColumnWidth(0, 90)
        table.itemChanged.connect(lambda item, grid=table: self._item_changed(grid, item))
        table.currentCellChanged.connect(
            lambda _r, _c, _pr, _pc, grid=table: self._refresh_formula(grid))
        index = self.sheets.addTab(table, self._unique_sheet_name(name))
        self._sheets.append(table)
        self.sheets.setCurrentIndex(index)
        if values:
            self._refreshing = True
            try:
                for address, raw in values.items():
                    r, c = parse_address(address)
                    self._set_raw(table, r, c, str(raw))
            finally:
                self._refreshing = False
            self.recalculate(table)
        self.modified = True
        return table

    def _unique_sheet_name(self, name):
        base = str(name)[:31] or "Sheet"
        existing = {self.sheets.tabText(i).casefold() for i in range(self.sheets.count())}
        candidate, number = base, 2
        while candidate.casefold() in existing:
            suffix = f" ({number})"
            candidate = base[:31 - len(suffix)] + suffix
            number += 1
        return candidate

    def _item_changed(self, table, item):
        if self._refreshing:
            return
        self._refreshing = True
        item.setData(RAW_ROLE, item.text())
        self._refreshing = False
        self.modified = True
        self.recalculate(table)

    def sort_selection(self, descending=False):
        table = self.current_sheet()
        ranges = table.selectedRanges()
        if not ranges:
            self._message("Gemini Excel", "Select a range to sort.", "info")
            return
        selection = ranges[0]
        rows = []
        for row in range(selection.topRow(), selection.bottomRow() + 1):
            values = [self._raw(table, row, column)
                      for column in range(selection.leftColumn(), selection.rightColumn() + 1)]
            first_item = table.item(row, selection.leftColumn())
            key_value = first_item.text().strip() if first_item else ""
            try:
                sort_key = (0, 0, float(key_value))
            except ValueError:
                sort_key = (0, 1, key_value.casefold())
            rows.append((not key_value, sort_key, values))
        populated = [entry for entry in rows if not entry[0]]
        blanks = [entry for entry in rows if entry[0]]
        populated.sort(key=lambda entry: entry[1], reverse=descending)
        sorted_rows = populated + blanks
        self._refreshing = True
        try:
            for row_offset, (_blank, _key, values) in enumerate(sorted_rows):
                row = selection.topRow() + row_offset
                for column_offset, raw in enumerate(values):
                    self._set_raw(table, row, selection.leftColumn() + column_offset, raw)
        finally:
            self._refreshing = False
        self.modified = True
        self.recalculate(table)

    def create_chart(self):
        table = self.current_sheet()
        ranges = table.selectedRanges()
        if not ranges or ranges[0].columnCount() < 2 or ranges[0].rowCount() < 2:
            self._message("Gemini Excel", "Select at least two columns and two rows: category labels in the "
                         "first column and numbers in the second.", "info")
            return
        selection = ranges[0]
        points = []
        for row in range(selection.topRow(), selection.bottomRow() + 1):
            label_item = table.item(row, selection.leftColumn())
            value_item = table.item(row, selection.leftColumn() + 1)
            label = label_item.text() if label_item else ""
            value = value_item.text() if value_item else ""
            try:
                number = float(value)
            except ValueError:
                continue
            if label and math.isfinite(number):
                points.append((label, number))
        if not points:
            self._message("Gemini Excel", "The selected range does not contain any category-and-number rows.",
                          "error")
            return
        chart = ChartWidget(self.sheets.tabText(self.sheets.currentIndex()), points)
        window = XPWindow(self.desktop, f"{self.sheets.tabText(self.sheets.currentIndex())} - Chart",
                          chart, gemini_excel_icon(), (600, 400))
        self.desktop.open_window(window)

    def _set_raw(self, table, row, column, raw):
        was_refreshing = self._refreshing
        self._refreshing = True
        item = table.item(row, column)
        if item is None:
            item = QTableWidgetItem()
            table.setItem(row, column, item)
        item.setData(RAW_ROLE, raw)
        item.setText(raw)
        self._refreshing = was_refreshing
        self.modified = True

    def _raw(self, table, row, column):
        item = table.item(row, column)
        if item is None:
            return ""
        raw = item.data(RAW_ROLE)
        return item.text() if raw is None else str(raw)

    def _refresh_formula(self, table=None):
        table = table or self.current_sheet()
        if table is None:
            return
        row, column = table.currentRow(), table.currentColumn()
        if row < 0 or column < 0:
            return
        self.address.setText(cell_address(row, column))
        self.formula.setText(self._raw(table, row, column))
        self.status.setText(f"{self.sheets.tabText(self.sheets.currentIndex())}  |  "
                            f"Cell {cell_address(row, column)}")

    def commit_formula(self):
        table = self.current_sheet()
        if table is None or table.currentRow() < 0:
            return
        self._set_raw(table, table.currentRow(), table.currentColumn(), self.formula.text())
        self.recalculate(table)
        table.setFocus()
        self._refresh_formula(table)

    def copy(self):
        table = self.current_sheet()
        ranges = table.selectedRanges()
        if not ranges:
            return
        selection = ranges[0]
        rows = []
        for row in range(selection.topRow(), selection.bottomRow() + 1):
            rows.append("\t".join(self._raw(table, row, column)
                                  for column in range(selection.leftColumn(), selection.rightColumn() + 1)))
        QApplication.clipboard().setText("\n".join(rows))

    def paste(self):
        table = self.current_sheet()
        row, column = table.currentRow(), table.currentColumn()
        if row < 0 or column < 0:
            return
        try:
            rows = list(csv.reader(QApplication.clipboard().text().splitlines(), delimiter="\t"))
        except csv.Error as error:
            self._message("Gemini Excel", f"Cannot paste clipboard data.\n{error}", "error")
            return
        for row_offset, values in enumerate(rows):
            for column_offset, value in enumerate(values):
                target_row, target_column = row + row_offset, column + column_offset
                if target_row < ROWS and target_column < COLUMNS:
                    self._set_raw(table, target_row, target_column, value)
        self.recalculate(table)

    def select_address(self):
        try:
            row, column = parse_address(self.address.text())
        except ValueError as error:
            self._refresh_formula()
            self._message("Gemini Excel", f"Enter a cell address from A1 to Z{ROWS}.\n{error}", "error")
            return
        self.current_sheet().setCurrentCell(row, column)
        self.current_sheet().setFocus()

    def recalculate(self, table=None):
        table = table or self.current_sheet()
        if table is None:
            return
        cache, visiting = {}, set()

        def value(address):
            row, column = parse_address(address)
            key = (row, column)
            if key in cache:
                return cache[key]
            if key in visiting:
                raise ArithmeticError("Circular reference")
            visiting.add(key)
            raw = self._raw(table, row, column).strip()
            try:
                if not raw:
                    result = None
                elif raw.startswith("="):
                    result = _formula_value(raw[1:], value)
                else:
                    try:
                        result = float(raw)
                    except ValueError:
                        result = raw
                cache[key] = result
                return result
            finally:
                visiting.remove(key)

        self._refreshing = True
        try:
            for row in range(ROWS):
                for column in range(COLUMNS):
                    item = table.item(row, column)
                    if item is None:
                        continue
                    raw = self._raw(table, row, column)
                    if not raw:
                        shown = ""
                    else:
                        try:
                            result = value(cell_address(row, column))
                            shown = f"{result:g}" if isinstance(result, float) else str(result)
                        except ZeroDivisionError:
                            shown = "#DIV/0!"
                        except ArithmeticError:
                            shown = "#CIRC!"
                        except (SyntaxError, TypeError, ValueError, OverflowError, RecursionError):
                            shown = "#VALUE!"
                    item.setText(shown)
        finally:
            self._refreshing = False
        self._refresh_formula(table)

    def workbook_data(self):
        sheets = []
        for index, table in enumerate(self._sheets):
            cells = {}
            for row in range(ROWS):
                for column in range(COLUMNS):
                    raw = self._raw(table, row, column)
                    if raw:
                        cells[cell_address(row, column)] = raw
            sheets.append({"name": self.sheets.tabText(index), "cells": cells})
        return {"format": "Gemini Excel Workbook", "version": 1,
                "active_sheet": max(0, self.sheets.currentIndex()), "sheets": sheets}

    def load(self, path):
        path = Path(path)
        try:
            if path.suffix.lower() == ".csv":
                with path.open("r", encoding="utf-8-sig", newline="") as stream:
                    rows = list(csv.reader(stream))
                cells = {cell_address(r, c): value
                         for r, values in enumerate(rows[:ROWS])
                         for c, value in enumerate(values[:COLUMNS]) if value}
                content = [{"name": path.stem or "Sheet1", "cells": cells}]
                active_sheet = 0
            else:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or data.get("format") != "Gemini Excel Workbook" or data.get("version") != 1:
                    raise ValueError("This is not a supported Gemini Excel workbook.")
                content = data.get("sheets")
                if not isinstance(content, list) or not content:
                    raise ValueError("The workbook does not contain any worksheets.")
                active_sheet = data.get("active_sheet", 0)
                if not isinstance(active_sheet, int):
                    active_sheet = 0
                for sheet in content:
                    if not isinstance(sheet, dict) or not isinstance(sheet.get("cells", {}), dict):
                        raise ValueError("The workbook contains an invalid worksheet.")
                    for address in sheet.get("cells", {}):
                        parse_address(address)
        except (OSError, UnicodeError, json.JSONDecodeError, csv.Error, ValueError) as error:
            return self._message("Gemini Excel", f"Cannot open {path.name}.\n{error}", "error")
        self._refreshing = True
        self.sheets.clear()
        self._sheets.clear()
        self._refreshing = False
        for sheet in content:
            self.add_sheet(sheet.get("name", "Sheet"), sheet.get("cells", {}))
        self.sheets.setCurrentIndex(min(max(0, active_sheet), self.sheets.count() - 1))
        self.path = path
        self.modified = False
        self._update_title()

    def new(self):
        self._maybe_save(self._reset_workbook)

    def _reset_workbook(self):
        self._refreshing = True
        self.sheets.clear()
        self._sheets.clear()
        self._refreshing = False
        self.path = None
        self.modified = False
        self.add_sheet("Sheet1")
        self.modified = False
        self._update_title()

    def save(self, then=None, csv_confirmed=False):
        if self.path is None:
            self.save_as(then)
            return
        if self.path.suffix.lower() == ".csv" and self.sheets.count() > 1 and not csv_confirmed:
            self._message("Gemini Excel", "CSV files can store only one worksheet. Save only the active "
                         "worksheet as CSV?", "warning", ("Save", "Cancel"),
                         lambda answer: self.save(then, True) if answer == "Save" else None)
            return
        try:
            if self.path.suffix.lower() == ".csv":
                table = self.current_sheet()
                max_row = max((r for r in range(ROWS) for c in range(COLUMNS)
                               if self._raw(table, r, c)), default=-1)
                max_column = max((c for r in range(ROWS) for c in range(COLUMNS)
                                  if self._raw(table, r, c)), default=-1)
                with self.path.open("w", encoding="utf-8-sig", newline="") as stream:
                    writer = csv.writer(stream)
                    for row in range(max_row + 1):
                        writer.writerow([table.item(row, column).text() if table.item(row, column) else ""
                                         for column in range(max_column + 1)])
            else:
                self.path.write_text(json.dumps(self.workbook_data(), ensure_ascii=False, indent=2),
                                     encoding="utf-8")
        except (OSError, UnicodeError, csv.Error) as error:
            self._message("Gemini Excel", f"Cannot save {self.path.name}.\n{error}", "error")
            return
        self.modified = False
        self._update_title()
        if callable(then):
            then()

    def save_as(self, then=None):
        name = self.path.name if self.path else "Book.gwb"
        folder = self.path.parent if self.path else None

        def saved(path):
            if path.suffix.lower() not in (".gwb", ".csv"):
                path = path.with_suffix(".gwb")
            if path.suffix.lower() == ".csv" and self.sheets.count() > 1:
                self._message("Gemini Excel", "CSV files can store only one worksheet. Save only the active "
                             "worksheet as CSV?", "warning", ("Save", "Cancel"),
                             lambda answer: self._save_as_path(path, then) if answer == "Save" else None)
            else:
                self._save_as_path(path, then)

        SaveAsDialog(self.desktop, name, folder, saved)

    def _save_as_path(self, path, then):
        self.path = path
        self.save(then)

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
            where.addItem(QApplication.style().standardIcon(QStyle.SP_DirIcon), label, str(folder))
        files = QListWidget()
        files.setMinimumSize(360, 200)
        grid.addWidget(QLabel("Look in:"), 0, 0)
        grid.addWidget(where, 0, 1)
        grid.addWidget(files, 1, 0, 1, 2)

        def fill():
            files.clear()
            folder = Path(where.currentData())
            if folder.is_dir():
                for item_path in sorted(folder.iterdir(), key=lambda candidate: candidate.name.lower()):
                    if item_path.is_file() and item_path.suffix.lower() in (".gwb", ".csv"):
                        item = QListWidgetItem(QApplication.style().standardIcon(QStyle.SP_FileIcon),
                                               item_path.name)
                        item.setData(Qt.UserRole, str(item_path))
                        files.addItem(item)

        where.currentIndexChanged.connect(fill)
        fill()
        holder = {}

        def close():
            if holder.get("win") is not None:
                self.desktop.close_window(holder.pop("win"))

        def open_selected():
            item = files.currentItem()
            if item is not None:
                self._maybe_save(lambda: (close(), self.load(item.data(Qt.UserRole))))

        open_button = QPushButton("&Open")
        cancel = QPushButton("Cancel")
        grid.addWidget(open_button, 2, 0)
        grid.addWidget(cancel, 2, 1)
        holder["win"] = _fixed_window(self.desktop, "Open", body, close)
        open_button.clicked.connect(open_selected)
        cancel.clicked.connect(close)
        files.itemDoubleClicked.connect(lambda _item: open_selected())
        self.desktop.open_window(holder["win"])

    def print_sheet(self):
        from PySide6.QtGui import QTextDocument
        from ..printing import print_document

        table = self.current_sheet()
        max_row = max((r for r in range(ROWS) for c in range(COLUMNS)
                       if self._raw(table, r, c)), default=-1)
        max_column = max((c for r in range(ROWS) for c in range(COLUMNS)
                          if self._raw(table, r, c)), default=-1)
        rows = []
        for row in range(max_row + 1):
            cells = []
            for column in range(max_column + 1):
                item = table.item(row, column)
                value = item.text() if item else ""
                cells.append(f"<td>{escape(value)}</td>")
            rows.append("<tr>" + "".join(cells) + "</tr>")
        document = QTextDocument()
        document.setHtml("<table border='1' cellspacing='0' cellpadding='4'>" + "".join(rows) + "</table>")
        print_document(self.desktop, self.sheets.tabText(self.sheets.currentIndex()), document)

    def about(self):
        self._message("About Gemini Excel", "Gemini Excel\nVersion 1.0")

    def name(self):
        return self.path.name if self.path else "Book"

    def _update_title(self):
        if self.frame is not None:
            self.frame.set_title(f"{self.name()} - Gemini Excel")

    def _message(self, title, text, icon="info", buttons=("OK",), on_button=None):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon, buttons, on_button)

    def closeEvent(self, event):
        if not self.modified:
            event.accept()
            return
        event.ignore()

        def answer(button):
            if button == "Yes":
                self.save(lambda: self._close_after_save())
            elif button == "No":
                self._close_after_save()

        self._message("Gemini Excel", f"Save changes to {self.name()}?", "warning",
                      ("Yes", "No", "Cancel"), answer)

    def _close_after_save(self):
        if self.frame is not None:
            self.desktop.close_window(self.frame)

    def _maybe_save(self, proceed):
        if not self.modified:
            proceed()
            return

        def answer(button):
            if button == "Yes":
                self.save(proceed)
            elif button == "No":
                proceed()

        self._message("Gemini Excel", f"Save changes to {self.name()}?", "warning",
                      ("Yes", "No", "Cancel"), answer)


def open_gemini_excel(desktop, path=None):
    body = GeminiExcel(desktop, path)
    win = XPWindow(desktop, f"{body.name()} - Gemini Excel", body, gemini_excel_icon(), (780, 560))
    body.frame = win
    desktop.open_window(win)
    body.current_sheet().setFocus()
    return win
