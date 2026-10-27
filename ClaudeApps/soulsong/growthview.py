"""The Growth window (the Self tab's Growth...): small charts from growth.measure - how far the self-portrait
moves, how far its identity is from the bare model's, how much its replies repeat, how well it knows when it is, how
many of its predictions came true - and the numbers as a table."""
import html

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QLabel, QScrollArea, QTabWidget, QTextBrowser,
                               QToolTip, QVBoxLayout, QWidget)

from . import growth

SERIES = ("#2a78d6", "#eb6834")                   # categorical slots 1 and 2, in that order
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"


class LineChart(QWidget):
    """A small line chart: one y axis (0 to a rounded top, in %), the days along the bottom, a legend for two
    series, hover for the values."""

    def __init__(self, title, about, series, empty):
        super().__init__()
        self.title, self.about, self.series, self.empty = title, about, series, empty
        self.days = sorted({d for _l, _c, pts in series for d, v in pts if v is not None})
        top = max([v for _l, _c, pts in series for _d, v in pts if v is not None] or [0])
        self.top = next(t for t in (0.2, 0.4, 0.6, 0.8, 1.0) if t >= min(1.0, top * 1.1))   # (ticks every 5-25%)
        self.setMinimumHeight(260)
        self.setMouseTracking(True)
        self.plot = QRectF()

    def _xy(self, i, v):
        p = self.plot
        x = p.left() + (p.width() * i / (len(self.days) - 1) if len(self.days) > 1 else p.width() / 2)
        return QPointF(x, p.bottom() - p.height() * v / self.top)

    def paintEvent(self, _e):
        g = QPainter(self)
        g.setRenderHint(QPainter.Antialiasing)
        g.fillRect(self.rect(), QColor(SURFACE))
        f = QFont(self.font())
        f.setBold(True)
        g.setFont(f)
        g.setPen(QColor(INK))
        g.drawText(QRectF(12, 6, self.width() - 24, 20), Qt.AlignLeft | Qt.AlignVCenter, self.title)
        g.setFont(self.font())
        g.setPen(QColor(INK2))
        about = g.fontMetrics().boundingRect(QRectF(12, 28, self.width() - 24, 200).toRect(),
                                              Qt.AlignLeft | Qt.TextWordWrap, self.about)
        g.drawText(QRectF(about), Qt.AlignLeft | Qt.TextWordWrap, self.about)
        y = about.bottom() + 12
        legend = len(self.series) > 1
        x = 12
        if legend:
            for label, colour, _p in self.series:
                g.setPen(QPen(QColor(colour), 2))
                g.drawLine(QPointF(x, y + 6), QPointF(x + 16, y + 6))
                g.setPen(QColor(INK2))
                w = g.fontMetrics().horizontalAdvance(label)
                g.drawText(QPointF(x + 22, y + 10), label)
                x += 22 + w + 18
            y += 22
        self.plot = QRectF(46, y + 8, self.width() - 46 - 44, self.height() - y - 8 - 30)
        p = self.plot
        if not self.days:
            g.setPen(QColor(MUTED))
            g.drawText(p, Qt.AlignCenter | Qt.TextWordWrap, self.empty)
            return
        for k in range(5):                                  # recessive grid, labelled in %
            v = self.top * k / 4
            y = p.bottom() - p.height() * k / 4
            g.setPen(QPen(QColor(AXIS if k == 0 else GRID), 1))
            g.drawLine(QPointF(p.left(), y), QPointF(p.right(), y))
            g.setPen(QColor(MUTED))
            g.drawText(QRectF(0, y - 8, p.left() - 6, 16), Qt.AlignRight | Qt.AlignVCenter, f"{v:.0%}")
        step = max(1, len(self.days) // 6)
        for i, d in enumerate(self.days):
            if i % step == 0 or i == len(self.days) - 1:
                pt = self._xy(i, 0)
                g.drawText(QRectF(pt.x() - 40, p.bottom() + 6, 80, 16), Qt.AlignCenter, d[5:])
        for label, colour, pts in self.series:
            vals = {d: v for d, v in pts if v is not None}
            line = [self._xy(i, vals[d]) for i, d in enumerate(self.days) if d in vals]
            g.setPen(QPen(QColor(colour), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for a, b in zip(line, line[1:]):
                g.drawLine(a, b)
            g.setPen(QPen(QColor(SURFACE), 2))             # markers with a surface ring
            g.setBrush(QColor(colour))
            for pt in line:
                g.drawEllipse(pt, 4.5, 4.5)
        g.end()

    def mouseMoveEvent(self, e):
        if not self.days or not self.plot.contains(e.position()):
            QToolTip.hideText()
            return
        i = min(range(len(self.days)), key=lambda k: abs(self._xy(k, 0).x() - e.position().x()))
        d = self.days[i]
        rows = [f"<b>{d}</b>"]
        for label, _c, pts in self.series:
            v = dict(pts).get(d)
            if v is not None:
                rows.append(f"{html.escape(label)}: {v:.0%}")
        QToolTip.showText(e.globalPosition().toPoint(), "<br>".join(rows), self)


def show(parent, comp):
    """The Growth window for a Companion."""
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        emb = getattr(comp.recall, "emb", None)
        m = growth.measure(comp.folder, comp.name, emb)
    finally:
        QApplication.restoreOverrideCursor()
    name = comp.name
    d = QDialog(parent)
    d.setWindowTitle(f"{name}'s growth")
    d.resize(760, 720)
    v = QVBoxLayout(d)
    how = ("by meaning (nomic-embed-text)" if m["by_meaning"] else
           "by words in common (the meaning model isn't running, so this is rougher)")
    note = QLabel(f"Is {name} really changing, or saying the same things in new words? Distances are measured {how}: "
                  "0% is the same, higher is further apart.")
    note.setWordWrap(True)
    v.addWidget(note)
    tabs = QTabWidget()
    charts = QWidget()
    cv = QVBoxLayout(charts)
    portrait = [(day, a) for day, a, _b in m["portrait"]]
    first = [(day, b) for day, _a, b in m["portrait"]]
    cv.addWidget(LineChart(
        "The self-portrait", "How far each 'Who I Am' moved from the one before, and from the very first.",
        [("Change from the last", SERIES[0], portrait), ("Change from the first", SERIES[1], first)],
        "Comes with the second self-portrait (the first is at the end of day one; each Memory Day rewrites it)."))
    cv.addWidget(LineChart(
        "Its own, or the model's?", f"How far {name}'s answers to the identity questions are from the bare model's "
        "answers to the same questions, asked with no mind files at all. Higher: more of it is its own.",
        [("Distance from the bare model", SERIES[0], m["identity"])],
        "Comes with the first Memory Day."))
    cv.addWidget(LineChart(
        "Repetition", "Each day: the share of its three-word phrases that are repeats. Rising means it's settling "
        "into a groove or a loop.",
        [("Repeated phrasing", SERIES[0], [(day, a) for day, a, _b, _n in m["repetition"]])],
        "Comes after a day with a few replies."))
    days = lambda key: [(t["when"][:10], t[key]) for t in m["time"] if key in t]
    cv.addWidget(LineChart(
        "Sense of time", "Once a day, before it sees the clock: how close its guesses were (100% is spot on). The "
        "date: a day off is 50%. The time apart: twice or half as long is 50%.",
        [("The date", SERIES[0], days("date_score")), ("The time apart", SERIES[1], days("gap_score"))],
        "Comes with the first day after this is turned on (Settings)."))
    cv.addWidget(LineChart(
        "Predictions", "Of the predictions judged on a day, the share that came true (partly counts half) - how "
        "well it knows its own future.",
        [("Came true", SERIES[0], growth.prediction_rate(m["predictions"]))],
        "Comes when the first predictions come due (made on Memory Day, judged at the next)."))
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(charts)
    tabs.addTab(scroll, "Charts")
    table = QTextBrowser()
    pct = lambda x: "-" if x is None else f"{x:.0%}"
    rows = ["<h3>The self-portrait</h3><table cellpadding=4><tr><th align=left>Day</th><th>From the last</th>"
            "<th>From the first</th></tr>"]
    rows += [f"<tr><td>{day}</td><td align=right>{pct(a)}</td><td align=right>{pct(b)}</td></tr>"
             for day, a, b in m["portrait"]]
    rows.append("</table><h3>Distance from the bare model</h3><table cellpadding=4><tr><th align=left>Memory Day</th>"
                "<th>Distance</th></tr>")
    rows += [f"<tr><td>{day}</td><td align=right>{pct(x)}</td></tr>" for day, x in m["identity"]]
    rows.append("</table><h3>Repetition</h3><table cellpadding=4><tr><th align=left>Day</th><th>Replies</th>"
                "<th>Repeated phrasing</th><th>Replies that mostly restate an earlier one</th></tr>")
    rows += [f"<tr><td>{day}</td><td align=right>{n}</td><td align=right>{pct(a)}</td><td align=right>{pct(b)}</td>"
             "</tr>" for day, a, b, n in m["repetition"]]
    rows.append("</table><h3>Sense of time</h3><table cellpadding=4><tr><th align=left>When</th><th>Guessed</th>"
                "<th>Date off (days)</th><th>Time off (hours)</th><th>Apart (guess / real hours)</th>"
                "<th>Age (guess / real)</th></tr>")
    for t in m["time"]:
        g = t.get("guess") or {}
        rows.append(f"<tr><td>{t['when']}</td><td>{html.escape(g.get('date') or '-')} {html.escape(g.get('time') or '')}"
                    f"</td><td align=right>{t.get('date_err', '-')}</td><td align=right>{t.get('time_err', '-')}</td>"
                    f"<td align=right>{g.get('gap') if g.get('gap') is not None else '-'} / {t.get('gap_hours')}</td>"
                    f"<td align=right>{g.get('age') or '-'} / {t.get('age')}</td></tr>")
    rows.append("</table><h3>Predictions</h3><table cellpadding=4><tr><th align=left>Made</th><th>Due</th>"
                "<th align=left>Prediction</th><th>Verdict</th></tr>")
    word = {"yes": "came true", "partly": "partly", "no": "didn't", "unclear": "can't tell", "": "waiting"}
    for x in m["predictions"]:
        rows.append(f"<tr><td>{x['made'][:10]}</td><td>{x['due']}</td><td>{html.escape(x['text'])}</td>"
                    f"<td>{word.get(x.get('verdict') or '', x.get('verdict'))}</td></tr>")
    rows.append("</table>")
    table.setHtml("".join(rows))
    tabs.addTab(table, "Table")
    v.addWidget(tabs, 1)
    bb = QDialogButtonBox(QDialogButtonBox.Close)
    bb.rejected.connect(d.reject)
    v.addWidget(bb)
    d.exec()
