"""Help and Support Center: Windows XP's blue home page (Pick a Help topic, Ask for assistance, Pick a task, Did you
know?), an Index, Search, Back/Forward/Home, and articles that are a real guide to ClaudeXP. Links can open
programs (launch:key), other articles (help:id) or web pages (opened in Netscape)."""
import random
import re

from PySide6.QtCore import QRectF, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextBrowser, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ..wm import XPWindow

# id: (title, topic, html body)
ARTICLES = {
    "welcome": ("Welcome to Windows XP", "new", """
<p>This computer is a Windows XP machine from 2001, complete with dial-up Internet and friends who are always
around. Everything here runs on this one computer; your buddies are characters played by a language model running
on the real PC (through Ollama).</p>
<p>New to XP? <a href="launch:tour">Take a tour of Windows XP</a>, or browse the topics on the
<a href="help:home">Help and Support home page</a>.</p>"""),
    "startmenu": ("Using the Start menu", "new", """
<p>Click <b>start</b> to see your programs. Your most-used programs are listed on the left;
<b>All Programs</b> holds everything, sorted into folders like <b>Accessories</b> and <b>Games</b>.
The right side opens My Documents, My Pictures, My Music, My Computer, the Control Panel, Printers and Faxes,
<a href="launch:search">Search</a>, <a href="launch:run">Run...</a> and this Help and Support Center.</p>
<p>Right-click the taskbar for Cascade, Tile, Show the Desktop and <a href="launch:taskmgr">Task Manager</a>.</p>"""),
    "shutdown": ("Turning off the computer", "new", """
<p>Click <b>start</b>, then <b>Turn Off Computer</b>. When Windows says <i>It's now safe to turn off your
computer</i>, the PC is still on: your buddies' lives carry on, and you can choose <b>Turn off</b>,
<b>Restart computer</b> or <b>Start recovery/format</b>.</p>"""),
    "keys": ("Keyboard shortcuts", "access", """
<table cellpadding="3">
<tr><td><b>Ctrl+Alt+End</b></td><td>Windows Task Manager (your real PC keeps Ctrl+Alt+Del for itself)</td></tr>
<tr><td><b>F11</b></td><td>Full screen on or off</td></tr>
<tr><td><b>F2</b></td><td>Rename a desktop icon or file; new game in the games</td></tr>
<tr><td><b>F5</b></td><td>Refresh the desktop</td></tr>
<tr><td><b>Ctrl+C / Ctrl+V</b></td><td>Copy and paste</td></tr>
<tr><td><b>Space</b> at startup</td><td>System Recovery (reinstall Windows)</td></tr>
<tr><td><b>Z</b> and <b>/</b></td><td>Pinball flippers (Space launches the ball)</td></tr>
</table>"""),
    "connect": ("Connecting to the Internet", "web", """
<p>This computer reaches the Internet with a 56K modem and America Online. Double-click <b>America Online</b> on
the desktop, or choose <a href="launch:connect">Connect to the Internet</a>, then Dial. You'll hear the modem
handshake; the connection icon appears by the clock. To hang up, right-click that icon and choose Disconnect.</p>
<p>Programs that need the Internet (Netscape, the Zone games, Windows Update, Outlook Express's Send/Recv) offer to
connect for you.</p>"""),
    "netscape": ("Browsing the Web with Netscape Navigator", "web", """
<p><a href="launch:navigator">Netscape Navigator</a> shows the Web of 2001. Pages are written on the fly the
first time you visit them and kept in the cache afterwards (<a href="launch:cleanmgr">Disk Cleanup</a> can clear
it). WebMail on the Netscape home page shows the same e-mail as Outlook Express.</p>"""),
    "email": ("Sending and receiving e-mail", "web", """
<p><a href="launch:outlook">Outlook Express</a> holds the e-mail your buddies send you. Click <b>Create Mail</b>,
pick someone from <b>Addresses</b>, and send. Your buddy answers a few minutes later in their own words (if
they're asleep, when they wake up). Mail written offline waits in the Outbox until you press <b>Send/Recv</b>.
Mail to an address nobody uses comes back from the Mail Delivery Subsystem.</p>"""),
    "buddies": ("Your buddies", "web", """
<p>The people on <a href="launch:aim">ClaudeAIM</a>, FurNet <a href="launch:irc">IRC</a> and PawPrints
<a href="launch:muck">MUCK</a> lead lives of their own. They keep diaries, remember what you talked about in any
program (and the games you played on the Zone), and sometimes IM or e-mail you with news. Their lives keep moving
even while the computer is at 'It's now safe to turn off your computer'.</p>"""),
    "media": ("Playing music and video", "media", """
<p><a href="launch:wmp">Windows Media Player</a> plays MP3, WMA and WAV files. Its Media Library finds music in
My Music, Shared Music, C:\\WINDOWS\\Media and the external drive (E:). Try the visualizations under
View &gt; Visualizations, and the skins in the Skin Chooser. <a href="launch:sndrec">Sound Recorder</a> records
from your microphone.</p>"""),
    "pictures": ("Drawing and pictures", "media", """
<p><a href="launch:paint">Paint</a> draws and edits pictures (.bmp, .png, .jpg, .gif). Right-click a picture in
My Pictures and choose <b>Edit</b> to open it in Paint, or <b>Set as Desktop Background</b>.</p>"""),
    "games": ("Games", "media", """
<p>Start &gt; All Programs &gt; Games has <a href="launch:solitaire">Solitaire</a>,
<a href="launch:freecell">FreeCell</a>, <a href="launch:spider">Spider Solitaire</a>,
<a href="launch:minesweeper">Minesweeper</a>, <a href="launch:hearts">Hearts</a> and
<a href="launch:pinball">3D Pinball</a>. The <b>Internet</b> games (Backgammon, Checkers, Hearts, Reversi,
Spades) match you with buddies who are awake; they chat with the Zone's phrases and remember the game.</p>"""),
    "display": ("Changing the desktop and screen saver", "custom", """
<p>Right-click the desktop and choose <b>Properties</b> (or <a href="launch:desk">Display Properties</a>) to pick
a background, a screen saver, and its settings. Right-click the desktop for Arrange Icons By, Refresh and New.
Your account name and picture are in <a href="launch:accounts">User Accounts</a>.</p>"""),
    "printing": ("Printing", "print", """
<p>The printer, an Epson LQ-570+ dot-matrix, prints to PDF files in <b>E:\\Printed</b> on the external drive.
Text comes out on green-bar paper; pictures and web pages print as normal pages. You'll hear it printing.</p>"""),
    "taskmgr": ("Windows Task Manager", "perf", """
<p>Press <b>Ctrl+Alt+End</b> or right-click the taskbar to open <a href="launch:taskmgr">Task Manager</a>. The
Performance tab's CPU graph climbs while your buddies are 'thinking'. Ending <b>explorer.exe</b> makes the
taskbar disappear: use File &gt; New Task and type <b>explorer</b> to bring it back.</p>"""),
    "maintenance": ("Keeping your computer running smoothly", "perf", """
<p><a href="launch:winupdate">Windows Update</a> keeps Windows current; <a href="launch:antivirus">ClaudeShield
AntiVirus</a> scans for trouble; <a href="launch:defrag">Disk Defragmenter</a> tidies the hard disk and
<a href="launch:cleanmgr">Disk Cleanup</a> frees space. The green light by the clock is the hard disk working.</p>"""),
    "restore": ("Undoing changes with System Restore", "perf", """
<p><a href="launch:sysrestore">System Restore</a> puts Windows' settings (background, desktop, account, game
statistics, program preferences) back the way they were at an earlier restore point. It never changes your
documents, e-mail or what your buddies remember. A checkpoint is made every day and before Windows Update
installs; you can make your own too, and every restore can be undone.</p>"""),
    "recovery": ("Reinstalling Windows (System Recovery)", "fix", """
<p>To start over completely, press <b>Space</b> while the computer starts (during the memory test), or click
<b>Start recovery/format</b> on the 'safe to turn off' screen, or type <b>format c:</b> in the
<a href="launch:cmd">Command Prompt</a>. Setup can format drive C: and erase program history and your buddies'
memories of you. Nothing is truly lost: everything erased is moved to the 'Recovery Backups' folder on the real
computer. Files on the external drive (E:) are never touched.</p>"""),
    "slow-buddies": ("My buddies don't answer", "fix", """
<p>Your buddies are played by a language model through <b>Ollama</b> on the real computer.</p>
<ul><li>Make sure Ollama is running, and that the model ClaudeAIM uses is installed.</li>
<li>Replies can take a few seconds; the hard disk light by the clock flickers while the model is working.</li>
<li>Buddies keep their own hours: someone asleep won't be online, and answers e-mail after they wake up.</li>
<li>Windows Update or a virus scan in the tray can mean the model is busy catching up on everyone's lives.</li></ul>"""),
    "no-sound": ("I can't hear anything", "fix", """
<p>Click the speaker by the clock to turn sound back on (a red circle means it's muted). Windows Media Player has
its own volume and Mute button too.</p>"""),
}
TOPICS = [("new", "What's new in Windows XP"), ("media", "Music, video, games, and photos"),
          ("web", "Networking and the Web"), ("custom", "Customizing your computer"),
          ("access", "Accessibility"), ("print", "Printing and faxing"), ("perf", "Performance and maintenance"),
          ("fix", "Fixing a problem")]
TIPS = ["You can drag icons around the desktop, and right-click it to arrange them by name, size or type.",
        "Hold Shift in Paint to draw straight lines, perfect squares and circles.",
        "In Minesweeper, click a number with both mouse buttons to uncover all the squares around it.",
        "FreeCell game #11982 is the only one of the 32,000 that can't be won.",
        "Type 'explorer' into Run... (or File > New Task in Task Manager) if your taskbar ever disappears.",
        "Your buddies remember games you played with them on the Zone, and might bring them up later."]

PAGE_STYLE = """
<style>
body { font-family: Tahoma; font-size: 11px; color: #000000; }
h1 { font-family: 'Trebuchet MS'; font-size: 18px; color: #1C3D91; }
h2 { font-family: 'Trebuchet MS'; font-size: 13px; color: #1C3D91; margin-top: 10px; }
a { color: #0033CC; }
td.box { background: #EEF3FD; border: 1px solid #99B4E5; padding: 6px; }
</style>"""


def help_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 32, 32)
    g.setColorAt(0, QColor("#6FA3F7"))
    g.setColorAt(1, QColor("#1D4FC4"))
    p.setPen(QPen(QColor("#163A8F"), 1))
    p.setBrush(g)
    p.drawEllipse(QRectF(3, 3, 26, 26))
    f = QFont("Arial")
    f.setPixelSize(20)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("white"))
    p.drawText(QRectF(3, 3, 26, 26), Qt.AlignCenter, "?")
    p.end()
    return QIcon(pm)


def home_page():
    topics = "".join(f'<p><a href="topic:{key}">\u25B8 {name}</a></p>' for key, name in TOPICS)
    return f"""{PAGE_STYLE}<body><table width="100%" cellspacing="8"><tr>
<td width="50%" valign="top"><h2>Pick a Help topic</h2>{topics}</td>
<td width="50%" valign="top">
<h2>Ask for assistance</h2>
<p><a href="launch:outlook">\u25B8 E-mail one of your buddies for help</a></p>
<p><a href="http://groups.google.com/">\u25B8 Get support in Windows XP newsgroups</a></p>
<h2>Pick a task</h2>
<p><a href="launch:winupdate">\u25B8 Keep your computer up-to-date with Windows Update</a></p>
<p><a href="launch:search">\u25B8 Find files and folders with Search</a></p>
<p><a href="launch:sysrestore">\u25B8 Undo changes to your computer with System Restore</a></p>
<p><a href="launch:msinfo">\u25B8 Use Tools to view your computer information</a></p>
<p><a href="launch:tour">\u25B8 Take a tour of Windows XP</a></p>
<table width="100%"><tr><td class="box"><b>Did you know?</b><br>{random.choice(TIPS)}</td></tr></table>
</td></tr></table></body>"""


def topic_page(key):
    name = dict(TOPICS)[key]
    items = "".join(f'<p><a href="help:{aid}">\u25B8 {title}</a></p>'
                    for aid, (title, topic, _b) in ARTICLES.items() if topic == key)
    return f"{PAGE_STYLE}<body><h1>{name}</h1>{items or '<p>No articles yet.</p>'}</body>"


def article_page(aid):
    title, _topic, body = ARTICLES[aid]
    return f"{PAGE_STYLE}<body><h1>{title}</h1>{body}<p><br><a href='help:home'>Help and Support home</a></p></body>"


def index_page():
    items = "".join(f'<p><a href="help:{aid}">{title}</a></p>'
                    for aid, (title, _t, _b) in sorted(ARTICLES.items(), key=lambda kv: kv[1][0].lower()))
    return f"{PAGE_STYLE}<body><h1>Index</h1>{items}</body>"


def search_page(query):
    words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 1]
    scored = []
    for aid, (title, _t, body) in ARTICLES.items():
        text = (title + " " + re.sub(r"<[^>]+>", " ", body)).lower()
        score = sum(text.count(w) + 3 * title.lower().count(w) for w in words)
        if score:
            scored.append((score, aid, title))
    scored.sort(reverse=True)
    items = "".join(f'<p><a href="help:{aid}">{title}</a></p>' for _s, aid, title in scored)
    return (f"{PAGE_STYLE}<body><h1>Search Results</h1><p>{len(scored)} results for <b>{query}</b>.</p>"
            f"{items or '<p>No topics were found. Try different words.</p>'}</body>")


class Header(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(56)

    def paintEvent(self, event):
        p = QPainter(self)
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0, QColor("#0A2A7A"))
        g.setColorAt(1, QColor("#2A62D6"))
        p.fillRect(self.rect(), g)
        p.drawPixmap(12, 8, help_icon().pixmap(40, 40))
        f = QFont("Trebuchet MS")
        f.setPixelSize(20)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(60, 6, 400, 28), Qt.AlignVCenter, "Help and Support Center")
        f.setPixelSize(11)
        f.setBold(False)
        p.setFont(f)
        p.drawText(QRectF(62, 30, 400, 20), Qt.AlignVCenter, "Windows XP Home Edition")


class HelpCenter(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.history, self.pos = [], -1
        self.setObjectName("hc")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#hc { background: #ECE9D8; } QWidget#nav { background: qlineargradient(x1:0, "
                           "y1:0, x2:0, y2:1, stop:0 #FDFDFB, stop:1 #E3E0D0); border-bottom: 1px solid #ACA899; }"
                           "QPushButton, QLineEdit, QLabel { font-family: Tahoma; font-size: 11px; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(Header())
        nav = QWidget()
        nav.setObjectName("nav")
        nav.setAttribute(Qt.WA_StyledBackground, True)
        h = QHBoxLayout(nav)
        h.setContentsMargins(6, 3, 6, 3)
        self.back_btn, self.fwd_btn = QPushButton("\u25C0 Back"), QPushButton("Forward \u25B6")
        home, index = QPushButton("Home"), QPushButton("Index")
        for b in (self.back_btn, self.fwd_btn, home, index):
            h.addWidget(b)
        h.addStretch()
        h.addWidget(QLabel("Search"))
        self.query = QLineEdit()
        self.query.setFixedWidth(200)
        go = QPushButton("\u25B6")
        go.setFixedWidth(28)
        h.addWidget(self.query)
        h.addWidget(go)
        v.addWidget(nav)
        self.view = QTextBrowser()
        self.view.setOpenLinks(False)
        self.view.anchorClicked.connect(self._link)
        v.addWidget(self.view, 1)
        self.back_btn.clicked.connect(lambda: self._step(-1))
        self.fwd_btn.clicked.connect(lambda: self._step(1))
        home.clicked.connect(lambda: self.show_page("help:home"))
        index.clicked.connect(lambda: self.show_page("index"))
        go.clicked.connect(self._search)
        self.query.returnPressed.connect(self._search)
        self.show_page("help:home")

    def _render(self, target):
        if target == "help:home":
            return home_page()
        if target == "index":
            return index_page()
        if target.startswith("topic:"):
            return topic_page(target[6:])
        if target.startswith("search:"):
            return search_page(target[7:])
        if target.startswith("help:") and target[5:] in ARTICLES:
            return article_page(target[5:])
        return home_page()

    def show_page(self, target, record=True):
        self.view.setHtml(self._render(target))
        if record:
            del self.history[self.pos + 1:]
            self.history.append(target)
            self.pos = len(self.history) - 1
        self.back_btn.setEnabled(self.pos > 0)
        self.fwd_btn.setEnabled(self.pos < len(self.history) - 1)

    def _step(self, d):
        self.pos = max(0, min(len(self.history) - 1, self.pos + d))
        self.show_page(self.history[self.pos], record=False)

    def _search(self):
        q = self.query.text().strip()
        if q:
            self.show_page(f"search:{q}")

    def _link(self, url):
        target = url.toString()
        if target.startswith("launch:"):
            launch(self.desktop, target[7:])
        elif target.startswith(("http://", "https://")):
            from . import navigator
            navigator.launch(self.desktop, target)
        else:
            self.show_page(target)


def launch(desktop, key):
    """Open whatever a help link points at."""
    from .. import programs
    if key == "run":
        from .run import open_run
        return open_run(desktop)
    if key == "desk":
        from ..controlpanel import display_properties
        return display_properties(desktop)
    if key == "accounts":
        from ..controlpanel import user_accounts
        return user_accounts(desktop)
    if key == "search":
        from .search import open_search
        return open_search(desktop)
    if any(p.key == key for p in programs.PROGRAMS):
        programs.launch(desktop, key)


_open = {}


def open_help(desktop, article=None):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = HelpCenter(desktop)
        win = XPWindow(desktop, "Help and Support Center", body, help_icon(), (780, 540))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    if article:
        win.content.show_page(f"help:{article}")
    return win
