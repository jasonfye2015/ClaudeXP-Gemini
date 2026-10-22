"""Small 2011 faces for ClaudeXP pieces that keep their 2001 look otherwise: the 'Loading AI Model' box in Windows
7's style, Skype 5, Trillian 5 and ICQ 7 for the themed messengers, LiveJournal's dates, Facebook on the Furry Web
and in Internet Explorer's favorites. Each function is hooked from xpcompat.PATCHES as its module loads."""
from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen

from . import clock


# ---- the AI loading box -------------------------------------------------------------------------------------------
def _loading_paint(self, _e):
    p = QPainter(self)
    p.setRenderHint(QPainter.Antialiasing)
    w, h = self.width(), self.height()
    from . import display
    tint = QColor(display.get().aero_color()).darker(130)
    tint.setAlpha(235)
    p.setPen(QPen(QColor(0, 0, 0, 150), 1))
    p.setBrush(tint)
    p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 6, 6)
    sheen = QLinearGradient(0, 0, 0, 28)
    sheen.setColorAt(0, QColor(255, 255, 255, 110))
    sheen.setColorAt(1, QColor(255, 255, 255, 30))
    p.setPen(Qt.NoPen)
    p.setBrush(sheen)
    p.drawRoundedRect(QRectF(1, 1, w - 2, 28), 6, 6)
    p.fillRect(QRect(6, 30, w - 12, h - 36), QColor("#F0F0F0"))
    if not hasattr(self, "_icon"):
        from claudexp.aimodels_cpl import ai_icon
        self._icon = ai_icon(16)
    p.drawPixmap(8, 7, self._icon)
    f = QFont("Segoe UI")
    f.setPixelSize(12)
    p.setFont(f)
    p.setPen(QColor(0, 0, 0, 110))
    p.drawText(QRect(31, 2, w - 36, 26), Qt.AlignVCenter, "Loading AI Model")
    p.setPen(QColor("white"))
    p.drawText(QRect(30, 1, w - 36, 26), Qt.AlignVCenter, "Loading AI Model")
    frac = self.fraction()
    line = f"Loading {self.title} into memory..." if self.done_at is None else f"{self.title} is ready."
    p.setPen(QColor("#1E1E1E"))
    p.drawText(QRect(16, 36, w - 32, 16), Qt.AlignLeft | Qt.AlignVCenter, line)
    bar = QRect(16, 58, w - 76, 16)
    p.setPen(QPen(QColor("#BCBCBC"), 1))
    p.setBrush(QColor("#E6E6E6"))
    p.drawRoundedRect(QRectF(bar).adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)
    inner = bar.adjusted(1, 1, -1, -1)
    filled = int(inner.width() * frac)
    if filled > 2:
        g = QLinearGradient(0, inner.top(), 0, inner.bottom())
        g.setColorAt(0, QColor("#9BE39B"))
        g.setColorAt(0.5, QColor("#37C837"))
        g.setColorAt(1, QColor("#06B025"))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(QRectF(inner.left(), inner.top(), filled, inner.height()), 2, 2)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#1E1E1E"))
    p.drawText(QRect(bar.right() + 8, bar.top(), 50, bar.height()), Qt.AlignVCenter | Qt.AlignLeft, f"{int(frac * 100)}%")
    f = QFont("Segoe UI")
    f.setPixelSize(10)
    p.setFont(f)
    p.setPen(QColor("#555555"))
    p.drawText(QRect(16, 82, w - 32, 30), Qt.TextWordWrap,
               "This happens once per session for each model. Replies may wait until it's done.")
    p.end()


def patch_llm_loading(m):
    m.LoadingBox.paintEvent = _loading_paint
    m.LoadingBox.W, m.LoadingBox.H = 330, 122


# ---- the themed messengers in 2011 ----------------------------------------------------------------------------------
def patch_messengers(m):
    from claudexp.programs.messengers.core import AWAY, BUSY, ONLINE
    s = m.SKYPE
    s.version = "5.5.0.124"
    s.subtitle = "Free calls and video calls"
    s.font = "Segoe UI"
    s.head_top, s.head_bottom, s.head_text, s.accent, s.page = "#FFFFFF", "#DFF3FC", "#00558A", "#00AFF0", "#F4FAFE"
    s.statuses = [("Online", ONLINE), ("Away", AWAY), ("Do Not Disturb", BUSY), ("Invisible", AWAY)]
    s.buttons = ["Call", "Video call", "Send file", "Add people", "Share"]
    s.footer = ["Contacts", "Recent", "Dial pad"]
    s.main_size, s.convo_size = (270, 520), (520, 440)
    t = m.TRILLIAN
    t.version = "5.0 Pro"
    t.subtitle = "AIM, Windows Live, Yahoo!, Facebook, Twitter and more"
    t.font = "Segoe UI"
    t.tag = _trillian_tag(t.tag)
    i = m.ICQ
    i.version = "7.6 (Build #5617)"
    i.subtitle = "ICQ 7 - chat, video, games"
    i.font = "Segoe UI"
    k = m.KIK
    k.version = "1.2"
    k.subtitle = "Kik Messenger - fast, simple, free"


def _trillian_tag(original):
    names = {"MSN": "Windows Live"}

    def tag(b):
        return names.get(original(b), original(b))
    return tag


# ---- LiveJournal's dates ----------------------------------------------------------------------------------------------
def patch_lj(m):
    original_entries, original_new = m.resident_entries, m.new_entry

    def resident_entries(name):
        out = original_entries(name)
        for item in out:
            item["date"] = item.get("date", "").replace("2001", str(clock.YEAR))
        return out

    def new_entry(data, subject, text, mood, music, security):
        entry = original_new(data, subject, text, mood, music, security)
        entry["date"] = entry["date"].replace("2001", str(clock.YEAR))
        return entry
    m.resident_entries, m.new_entry = resident_entries, new_entry
    if hasattr(m, "MUSIC"):
        m.MUSIC[:] = ["Adele - Rolling in the Deep", "Foster the People - Pumped Up Kicks", "LMFAO - Party Rock Anthem",
                      "Gotye - Somebody That I Used to Know", "Fun. - We Are Young", "Skrillex - Bangarang",
                      "Coldplay - Paradise", "Lady Gaga - The Edge of Glory", "Daft Punk - Derezzed",
                      "Owl City - Fireflies", "Mumford & Sons - The Cave", "Deadmau5 - Ghosts 'n' Stuff"]


# ---- Facebook on the Furry Web ---------------------------------------------------------------------------------------
def patch_sites(m):
    original = m.services

    def services():
        out = original()
        if not any(getattr(s, "host", "") == "www.facebook.com" for s in out):
            from .sites.facebook import Facebook
            out.append(Facebook())
        return out
    m.services = services


def patch_iexplore_favorites(m):
    favs = m.DEFAULT_FAVORITES
    if isinstance(favs, list) and not any(f.get("url", "").startswith("http://www.facebook") for f in favs):
        favs.insert(2, {"title": "Facebook", "url": "http://www.facebook.com/"})
        favs.insert(3, {"title": "YouTube", "url": "http://www.youtube.com/"})
    for f in favs:
        if f.get("title") == "Free Hotmail":
            f["title"] = "Windows Live Hotmail"
        if f.get("title") == "Windows Media":
            f["title"], f["url"] = "Bing", "http://www.bing.com/"


# ---- Yahoo! Messenger 11 ---------------------------------------------------------------------------------------------
def patch_yim(m):
    from PySide6.QtWidgets import QWidget
    from claudexp.programs.messengers.core import AWAY, BUSY, ONLINE
    m.STATUSES[:] = [("Available", ONLINE), ("Busy", BUSY), ("Be Right Back", AWAY), ("Stepped Out", AWAY),
                     ("Invisible to Everyone", AWAY)]

    class Skin(m.Skin):
        def received_text(self, t):
            return f"Last message received on {t.month}/{t.day}/{str(clock.YEAR)[2:]} at {t:%I:%M %p}".replace(" 0", " ")

    class Main(m.YIMMain):
        def about(self):
            self._note("Yahoo! Messenger\nVersion 11.5.0.228\n\nCopyright © 2011 Yahoo! Inc. All rights reserved.")

    class Tabs(QWidget):
        """The tab strip of Yahoo! Messenger 11: Contacts, Updates, Messenger."""

        def __init__(self):
            super().__init__()
            self.setFixedHeight(24)

        def paintEvent(self, event):
            p = QPainter(self)
            p.fillRect(self.rect(), QColor("#E8E0F2"))
            f = QFont("Segoe UI")
            f.setPixelSize(12)
            p.setFont(f)
            x = 4
            for i, text in enumerate(("Contacts", "Updates", "Messenger")):
                w = 70
                p.setPen(QColor("#9A86B8"))
                p.setBrush(QColor("white") if i == 0 else QColor("#D9CCEA"))
                p.drawRect(x, 2, w, 19)
                p.setPen(QColor("#3A0A5A"))
                p.drawText(QRect(x, 2, w, 19), Qt.AlignCenter, text)
                x += w + 2
    m.Skin, m.YIMMain, m._Tabs = Skin, Main, Tabs


# ---- Windows Live Mail ------------------------------------------------------------------------------------------------
WLMAIL_STYLE = """
QMenu { background: #F0F0F0; border: 1px solid #979797; font-family: 'Segoe UI'; font-size: 12px; }
QMenu::item { padding: 4px 24px 4px 28px; }
QMenu::item:selected { background: #CCE8FF; border: 1px solid #99D1FF; }
QMenu::separator { height: 1px; background: #D7D7D7; margin: 3px 2px; }
QMenuBar { background: #F7F9FC; font-family: 'Segoe UI'; font-size: 12px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #CCE8FF; border: 1px solid #99D1FF; }
QWidget#oe { background: #FFFFFF; }
QWidget#oebar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F4F7FB, stop:1 #DCE6F1);
                border-bottom: 1px solid #C7D3E0; }
QToolButton { border: 1px solid transparent; border-radius: 3px; padding: 3px 8px; font-family: 'Segoe UI';
              font-size: 12px; color: #1E395B; }
QToolButton:hover { border: 1px solid #7DA2CE; background: #E8F0FA; }
QTreeWidget, QTextBrowser { background: white; border: 1px solid #D9E1EA; font-family: 'Segoe UI'; font-size: 12px; }
QTreeWidget::item { height: 22px; } QTreeWidget::item:selected { background: #CCE8FF; color: black; }
QLabel#paneTitle { background: #FFFFFF; color: #1E395B; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold;
                   padding: 4px 6px; border-bottom: 1px solid #D9E1EA; }
QLabel#header { background: #F7F9FC; border: 1px solid #D9E1EA; padding: 6px 8px; font-family: 'Segoe UI'; font-size: 12px; }
QLabel#status { border-top: 1px solid #D9E1EA; padding: 2px 6px; font-family: 'Segoe UI'; font-size: 12px; color: #6D6D6D; }
QLineEdit, QPlainTextEdit { font-family: 'Segoe UI'; font-size: 13px; }
QHeaderView::section { background: white; border: none; border-bottom: 1px solid #E5E5E5; padding: 3px 6px; color: #4C607A; }
"""


def patch_outlook(m):
    """Outlook Express 6 wears Windows Live Mail 2011's colours and name."""
    from PySide6.QtWidgets import QMenuBar, QTreeWidget
    m.STYLE = WLMAIL_STYLE
    original_open = m.open_outlook

    def open_outlook(desktop):
        win = original_open(desktop)
        try:
            win.set_title(win.title.replace("Outlook Express", "Windows Live Mail"))
            body = win.content
            bar = body.findChild(QMenuBar)
            if bar is not None:
                for top in bar.actions():
                    if top.menu() is not None:
                        for act in top.menu().actions():
                            if "Outlook Express" in act.text():
                                act.setText(act.text().replace("Outlook Express", "Windows Live Mail"))
            for tree in body.findChildren(QTreeWidget):
                for i in range(tree.topLevelItemCount()):
                    item = tree.topLevelItem(i)
                    if item.text(0) == "Outlook Express":
                        item.setText(0, "Windows Live Mail")
        except Exception:
            pass
        return win
    m.open_outlook = open_outlook
    original_message = getattr(m.OutlookExpress, "_message", None)
    if original_message is not None:
        def _message(self, title, text, *args, **kwargs):
            return original_message(self, title.replace("Outlook Express", "Windows Live Mail"),
                                    text.replace("Microsoft Outlook Express 6\nVersion 6.00.2600.0000",
                                                 "Windows Live Mail 2011\nVersion 15.4.3555.0308"), *args, **kwargs)
        m.OutlookExpress._message = _message
