"""Small 2025 faces for ClaudeXP pieces that keep their 2001 look otherwise: the 'Loading AI model' box in Windows
11's style, Trillian and Kik's versions, LiveJournal's dates and music, Facebook on the Furry Web and in Edge's
favourites, Outlook in place of Outlook Express, and Outlook.com's welcome mail. Each function is hooked from
xpcompat.PATCHES as its module loads."""
from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen

from . import clock


def _font(size=12, bold=False):
    from .style import font
    return font(size, QFont.DemiBold if bold else QFont.Normal)


# ---- the AI loading box -------------------------------------------------------------------------------------------
def _loading_paint(self, _e):
    p = QPainter(self)
    p.setRenderHint(QPainter.Antialiasing)
    w, h = self.width(), self.height()
    from . import display
    accent = display.get().accent()
    p.setPen(QPen(QColor(0, 0, 0, 40), 1))
    p.setBrush(QColor(249, 249, 249, 250))
    p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 8, 8)
    if not hasattr(self, "_icon"):
        from claudexp.aimodels_cpl import ai_icon
        self._icon = ai_icon(16)
    p.drawPixmap(16, 14, self._icon)
    p.setFont(_font(13, bold=True))
    p.setPen(QColor("#1A1A1A"))
    p.drawText(QRect(40, 10, w - 56, 24), Qt.AlignVCenter, "Loading AI model")
    frac = self.fraction()
    line = f"Loading {self.title} into memory…" if self.done_at is None else f"{self.title} is ready."
    p.setFont(_font(12))
    p.setPen(QColor("#5C5C5C"))
    p.drawText(QRect(16, 40, w - 32, 18), Qt.AlignLeft | Qt.AlignVCenter, p.fontMetrics().elidedText(line, Qt.ElideRight, w - 32))
    bar = QRect(16, 66, w - 76, 4)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 28))
    p.drawRoundedRect(QRectF(bar), 2, 2)
    filled = int(bar.width() * frac)
    if filled > 2:
        p.setBrush(accent)
        p.drawRoundedRect(QRectF(bar.left(), bar.top(), filled, bar.height()), 2, 2)
    p.setFont(_font(12, bold=True))
    p.setPen(QColor("#1A1A1A"))
    p.drawText(QRect(bar.right() + 10, bar.top() - 8, 50, 20), Qt.AlignVCenter | Qt.AlignLeft, f"{int(frac * 100)}%")
    p.setFont(_font(11))
    p.setPen(QColor("#5C5C5C"))
    p.drawText(QRect(16, 80, w - 32, 30), Qt.TextWordWrap,
               "This happens once per session for each model. Replies may wait until it's done.")
    p.end()


def patch_llm_loading(m):
    m.LoadingBox.paintEvent = _loading_paint
    m.LoadingBox.W, m.LoadingBox.H = 340, 118


# ---- the messengers that are still around in 2025 --------------------------------------------------------------------
def patch_messengers(m):
    t = getattr(m, "TRILLIAN", None)
    if t is not None:
        t.version = "6.5.0.10"
        t.subtitle = "Instant messaging for people and teams"
        t.font = "Segoe UI"
    k = getattr(m, "KIK", None)
    if k is not None:
        k.version = "15.73"
        k.subtitle = "Kik - chat with friends"
        k.font = "Segoe UI"


# ---- LiveJournal's dates and the music people listen to --------------------------------------------------------------
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
        m.MUSIC[:] = ["Sabrina Carpenter - Manchild", "Lady Gaga & Bruno Mars - Die With a Smile",
                      "Alex Warren - Ordinary", "Chappell Roan - The Subway", "Doechii - Anxiety", "HUNTR/X - Golden",
                      "Olivia Dean - Man I Need", "Benson Boone - Mystical Magical", "Lola Young - Messy",
                      "Kendrick Lamar & SZA - luther", "Addison Rae - Headphones On", "Tame Impala - End of Summer"]


# ---- Facebook on the Furry Web ---------------------------------------------------------------------------------------
def patch_sites(m):
    original = m.services

    def services():
        out = original()
        if not any(getattr(s, "host", "") == "www.facebook.com" for s in out):
            from .sites.facebook import Facebook
            out.append(Facebook())
        if not any(getattr(s, "host", "") == "bsky.app" for s in out):
            from .sites.bluesky import Bluesky
            out.append(Bluesky())
        return out
    m.services = services


def patch_iexplore_favorites(m):
    favs = m.DEFAULT_FAVORITES
    if isinstance(favs, list) and not any(f.get("url", "").startswith("http://www.facebook") for f in favs):
        favs.insert(2, {"title": "Facebook", "url": "http://www.facebook.com/"})
        favs.insert(3, {"title": "YouTube", "url": "http://www.youtube.com/"})
        favs.insert(4, {"title": "Bluesky", "url": "http://bsky.app/"})
    for f in favs:
        if f.get("title") == "Free Hotmail":
            f["title"] = "Outlook.com"
        if f.get("title") == "Windows Media":
            f["title"], f["url"] = "Bing", "http://www.bing.com/"


# ---- Outlook (Outlook Express's window, in 2025's clothes) ---------------------------------------------------------
OUTLOOK_STYLE = """
QMenu { background: #F9F9F9; border: 1px solid #E0E0E0; border-radius: 8px; padding: 4px; font-family: 'Segoe UI';
        font-size: 12px; }
QMenu::item { padding: 6px 28px 6px 12px; border-radius: 4px; margin: 1px 2px; }
QMenu::item:selected { background: #EAEAEA; }
QMenu::separator { height: 1px; background: #E5E5E5; margin: 4px 8px; }
QMenuBar { background: #F3F3F3; font-family: 'Segoe UI'; font-size: 12px; }
QMenuBar::item { padding: 4px 8px; background: transparent; border-radius: 4px; }
QMenuBar::item:selected { background: #E5E5E5; }
QToolBar { background: #F3F3F3; border: none; border-bottom: 1px solid #E5E5E5; spacing: 4px; padding: 4px 8px; }
QToolButton { border: 1px solid transparent; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI';
              font-size: 12px; color: #1A1A1A; }
QToolButton:hover { background: #E9E9E9; }
QTreeWidget, QTreeView { background: #FFFFFF; border: none; font-family: 'Segoe UI'; font-size: 12px;
                         alternate-background-color: #FAFAFA; }
QTreeWidget::item { height: 30px; }
QTreeWidget::item:selected { background: #E6F0FB; color: #1A1A1A; }
QHeaderView::section { background: #FFFFFF; border: none; border-bottom: 1px solid #E5E5E5; padding: 6px 8px;
                       color: #5C5C5C; font-family: 'Segoe UI'; font-size: 12px; }
QTextEdit, QPlainTextEdit, QTextBrowser { background: #FFFFFF; border: none; font-family: 'Segoe UI'; font-size: 13px; }
QLabel { font-family: 'Segoe UI'; font-size: 12px; }
QStatusBar, QWidget#statusbar { background: #F3F3F3; border-top: 1px solid #E5E5E5; }
QSplitter::handle { background: #E5E5E5; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: rgba(0, 0, 0, 60); border-radius: 3px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def patch_outlook(m):
    """Outlook Express 6 becomes Outlook: the name on the window, the folder tree and the About box."""
    from PySide6.QtWidgets import QMenuBar, QTreeWidget
    original_init = m.OutlookExpress.__init__

    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        try:
            self.setStyleSheet(OUTLOOK_STYLE)
        except Exception:
            pass
    m.OutlookExpress.__init__ = __init__
    original_open = m.open_outlook

    def open_outlook(desktop):
        win = original_open(desktop)
        try:
            win.set_title(win.title.replace("Outlook Express", "Outlook"))
            body = win.content
            bar = body.findChild(QMenuBar)
            if bar is not None:
                for top in bar.actions():
                    if top.menu() is not None:
                        for act in top.menu().actions():
                            if "Outlook Express" in act.text():
                                act.setText(act.text().replace("Outlook Express", "Outlook"))
            for tree in body.findChildren(QTreeWidget):
                for i in range(tree.topLevelItemCount()):
                    item = tree.topLevelItem(i)
                    if item.text(0) == "Outlook Express":
                        item.setText(0, "Outlook")
        except Exception:
            pass
        return win
    m.open_outlook = open_outlook
    original_refresh = m.OutlookExpress.refresh

    def refresh(self):                      # the folder tree is rebuilt on every refresh, root and all
        original_refresh(self)
        try:
            for i in range(self.folders.topLevelItemCount()):
                item = self.folders.topLevelItem(i)
                if item.text(0) == "Outlook Express":
                    item.setText(0, "Outlook")
        except Exception:
            pass
    m.OutlookExpress.refresh = refresh
    original_message = getattr(m.OutlookExpress, "_message", None)
    if original_message is not None:
        def _message(self, title, text, *args, **kwargs):
            return original_message(self, title.replace("Outlook Express", "Outlook"),
                                    text.replace("Microsoft Outlook Express 6\nVersion 6.00.2600.0000",
                                                 "Outlook for Windows\nVersion 1.2025.1008.300"), *args, **kwargs)
        m.OutlookExpress._message = _message


# ---- the inbox extras in 2025: Outlook.com's welcome, warnings and newsletters ------------------------------------
HOTMAIL_2025 = (("MSN Hotmail", "Outlook.com"), ("Hotmail Staff", "Outlook Team"), ("MSN Messenger", "Microsoft Teams"),
                ("Hotmail", "Outlook.com"))

WELCOME_2025 = """Welcome to Outlook!

Your new email address is: {addr}

With Outlook you can:
  * Read your email anywhere - on the web, in the Outlook app, or on your phone
  * Keep your calendar, contacts and To Do list together in one place
  * Let Focused Inbox and the junk filter sort the noise from the mail that matters
  * Store and share photos and documents on OneDrive - 5 GB free, 100 GB with Microsoft 365 Basic
  * Ask Copilot to summarize a long thread or help with a reply

Remember: sign in at least once every two years to keep your Microsoft account active.

Thanks for choosing Outlook.

The Outlook Team
https://outlook.live.com"""

INACTIVE_2025 = """Hello,

We noticed you haven't signed in to your Microsoft account ({addr}) in a while.

Microsoft accounts that stay inactive for two years may be closed, and the email, OneDrive files and settings
stored in them deleted. To keep your account, just sign in.

Sign in at https://account.microsoft.com

Thanks,
The Microsoft account team"""

NEWSLETTERS_2025 = [
    ("Windows 10 support ends October 14 - here's what to do",
     "Windows 10 reached the end of support on October 14, 2025.\n\n  * PCs that meet the requirements can upgrade to "
     "Windows 11 for free from Settings > Windows Update\n  * Extended Security Updates are available for one more "
     "year if you need them\n  * Windows 11 version 25H2 is rolling out now with a leaner Start menu\n\nTip of the "
     "month: Snap layouts - rest the pointer on a window's maximize button and pick where it goes.\n\nYou are receiving "
     "this newsletter because you have a Microsoft account."),
    ("Microsoft 365 Basic: 100 GB and an ad-free inbox",
     "Get more out of Outlook:\n\n  * 100 GB of cloud storage for OneDrive and your mailbox\n  * Outlook without ads, "
     "with advanced security\n  * Share with up to five people\n\nTip of the month: Sweep clears a sender's mail in "
     "one click - right-click a message and choose Sweep."),
    ("Copilot is in Outlook now",
     "Copilot can help you write, summarize and catch up:\n\n  * Summarize a long thread in a few lines\n  * Draft a "
     "reply in the tone you want\n  * Find that attachment someone sent you last spring\n\nAlso this month: the new "
     "Photos app, Click to Do, and what's new in Microsoft Edge."),
    ("Keep your Microsoft account safe",
     "Passkeys are here:\n\n  * Sign in with your face, fingerprint or PIN instead of a password\n  * Turn on "
     "two-step verification in the Microsoft Authenticator app\n  * Watch for phishing: Microsoft will never ask for "
     "your password by email\n\nTip of the month: Outlook's Focused Inbox learns which senders matter to you."),
]


def patch_mail_extras(m):
    """claudexp.life.mail_extras in 2025: the Outlook Team writes, and nothing says MSN Hotmail."""
    m.STAFF = ("Outlook Team", "outlook-team@microsoft.com")
    m.MEMBER = ("Microsoft account team", "account-security-noreply@accountprotection.microsoft.com")
    m.WELCOME = WELCOME_2025
    m.INACTIVE = INACTIVE_2025
    m.NEWSLETTERS = NEWSLETTERS_2025
    m.INACTIVE_DAYS = 365
    original_tick = m.tick

    def tick(sim):
        box = sim.mailbox
        original_add = box.add

        def add(sender, subject, body, *args, **kwargs):
            for old, new in HOTMAIL_2025:
                sender, subject, body = sender.replace(old, new), subject.replace(old, new), body.replace(old, new)
            subject = subject.replace("Welcome to Outlook.com!", "Welcome to Outlook!")
            return original_add(sender, subject, body, *args, **kwargs)
        box.add = add
        try:
            return original_tick(sim)
        finally:
            if "add" in vars(box):
                del box.add
    m.tick = tick
