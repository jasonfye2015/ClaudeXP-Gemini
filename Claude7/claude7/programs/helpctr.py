"""Windows Help and Support, 2011: the plain white pages with their blue headings, a search box, Back and Forward,
the Help topics - what's new in Windows 7, Aero, the taskbar, Sticky Notes, Snipping Tool, gadgets, the Action
Center, reinstalling Windows - and Claude7's own: what this computer is, every program on it (a live catalog), the
people who live here, and what's on drive E:."""
import random
import re

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QTextDocument
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QTextBrowser, QVBoxLayout, QWidget
from shiboken6 import isValid

from .. import sound
from ..wm import AeroWindow

PAGE_STYLE = """
<style>
body { font-family: 'Segoe UI'; font-size: 12px; color: #1E1E1E; }
h1 { font-family: 'Segoe UI'; font-size: 20px; font-weight: normal; color: #003399; margin-bottom: 4px; }
h2 { font-family: 'Segoe UI'; font-size: 14px; font-weight: normal; color: #003399; margin-top: 14px; }
a { color: #0066CC; text-decoration: none; }
td.box { background: #F5F9FD; border: 1px solid #C9D9EA; padding: 8px; }
li { margin-bottom: 3px; }
</style>"""
TOPICS = [("start", "Getting started"), ("new", "What's new in Windows 7"), ("desktop", "The desktop, Aero and the taskbar"),
          ("programs", "Programs, tools and games"), ("people", "The people who live here"),
          ("internet", "Internet, e-mail and messaging"), ("files", "Files, folders and drive E:"),
          ("custom", "Customizing your computer"), ("security", "Security and maintenance"),
          ("fix", "Fixing problems and reinstalling Windows")]
TIPS = ["Drag a window to the top of the screen to maximize it, or to a side to fill that half (Aero Snap).",
        "Point at the sliver at the far right of the taskbar to peek at the desktop; click it to show the desktop.",
        "Point at a taskbar button to see a thumbnail of its window.",
        "Right-click a program on the taskbar to pin it there.",
        "Type the first letters of a program's name into the Start menu's search box and press Enter.",
        "Sticky Notes stay on the desktop between log-ons: right-click one to change its colour.",
        "The Snipping Tool captures any part of the screen: drag around it, then draw on it or save it.",
        "Gadgets (right-click the desktop > Gadgets) sit on the desktop under your windows.",
        "In full screen (F11), Alt+Tab switches between windows with thumbnails.",
        "Lock the computer from the Start menu's Shut down arrow: your programs stay open.",
        "Press F8 during the self test for Advanced Boot Options, including Repair Your Computer.",
        "Everyone you know has a Hotmail address - try e-mailing one of the IRC regulars.",
        "Your buddies remember what you talked about in one program when you meet them in another.",
        "Press DEL during the self test to look around the BIOS Setup Utility.",
        "Chess Titans (Start > Games) plays at three strengths; Game > Play as lets you take Black.",
        "Everyone you know is on Facebook now: www.facebook.com in Internet Explorer or Firefox."]
ARTICLES = {
    "claude7-about": ("About Claude7", "start", """
<p>Claude7 is SYSTEM-2011: a Windows 7 Home Premium computer from October 2011, in the Claude Timeline beside
EPOCH-2001 (Windows XP) and WORKSTATION-2025 (Windows 11). The same people live on all three computers, ten years
apart each time: on this one they are ten years older than on the XP machine, with the same histories, and they
remember what you talk about.</p>
<h2>What's here</h2>
<ul><li>The programs of 2011: AIM, Windows Live Messenger, Skype, IRC, the MUCK, Second Life, Internet Explorer,
Windows Live Mail and Hotmail, Windows Media Player, Sticky Notes, the Snipping Tool, gadgets.</li>
<li>Every game, archive viewer and app the Timeline shares: they are the same programs on every computer, with the
same saved games.</li>
<li>Your archive on drive E: (Local Storage): the furry media, TV and movies, emulation, your own pictures and
documents.</li></ul>
<p><a href="help:claudexp-catalog">Programs on this computer</a> &nbsp;&middot;&nbsp;
<a href="help:people">The people who live here</a> &nbsp;&middot;&nbsp;
<a href="help:claudexp-storage">What's on drive E:</a></p>"""),
    "getting-started": ("How to get started with your computer", "start", """
<ul><li><b>The Start button</b> (the round orb at the bottom left) opens the Start menu: your programs on the left,
your folders and the Control Panel on the right. Type to search.</li>
<li><b>The taskbar</b> shows open windows as big buttons with thumbnails. Pin the programs you use most.</li>
<li><b>The notification area</b> at the right has the Action Center flag, the network and the volume, and the
clock. Click the arrow to see the hidden icons.</li>
<li><b>Computer</b> on the desktop opens Windows Explorer: drive C:, the DVD drive, and your external drive E:
with the Timeline's archive.</li></ul>"""),
    "basics": ("Learn about Windows Basics", "start", """
<p>Windows 7 is Windows Vista grown up: faster, quieter, and with a desktop that gets out of the way.</p>
<ul><li><a href="help:aero">Aero: glass, Snap, Peek and Shake</a></li><li><a href="help:taskbar">The taskbar and
Jump Lists</a></li><li><a href="help:startmenu">The Start menu and search</a></li>
<li><a href="help:libraries">Libraries and Windows Explorer</a></li><li><a href="help:gadgets">Desktop gadgets</a></li>
<li><a href="help:stickynotes">Sticky Notes</a></li><li><a href="help:snipping">The Snipping Tool</a></li></ul>"""),
    "whatsnew": ("What's new in Windows 7", "new", """
<ul><li><b>Aero Snap:</b> drag a window to the top to maximize it, to a side to fill half the screen.</li>
<li><b>Aero Peek:</b> point at the Show desktop sliver (far right of the taskbar) and every window turns to glass.</li>
<li><b>The new taskbar:</b> big icons, pinned programs, thumbnail previews, Jump Lists.</li>
<li><b>Libraries:</b> Documents, Music, Pictures and Videos gather folders from anywhere.</li>
<li><b>Gadgets</b> live on the desktop instead of Vista's Sidebar.</li>
<li><b>Chess Titans</b>, Solitaire, Spider, FreeCell, Hearts and Minesweeper in Start &gt; Games.</li>
<li><b>Action Center</b> collects the security and maintenance messages in one place.</li>
<li><b>HomeGroup</b> shares files and printers at home. <b>Windows Touch</b> for touch screens.</li>
<li>Gone: the Sidebar, Windows Mail, Movie Maker and Photo Gallery (they are Windows Live programs now),
Ultimate Extras.</li></ul>"""),
    "aero": ("Aero: glass, Snap, Peek and Shake", "desktop", """
<p>Windows 7's windows are translucent glass, tinted with the colour you choose in Personalization &gt; Window
Color.</p><ul><li><b>Snap:</b> drag a window to the top edge to maximize it, to the left or right edge to fill that
half of the screen. Drag it away to put it back.</li><li><b>Peek:</b> point at the Show desktop sliver at the far
right of the taskbar to see the desktop through your windows; click it to minimize them all.</li>
<li><b>Thumbnails:</b> point at a taskbar button to see the window; click the thumbnail to switch to it.</li>
<li><b>Alt+Tab</b> shows the same thumbnails in a glass box (in full screen - F11).</li></ul>"""),
    "taskbar": ("The taskbar and Jump Lists", "desktop", """
<p>The taskbar holds pinned programs and open windows together. Right-click a program's button to pin or unpin it;
the ones you use most are worth pinning. A running program's button is a raised glass tile; a window asking for
attention flashes orange.</p><p>Right-click the taskbar for Cascade windows, Show windows side by side, Task
Manager and Properties. Right-click the clock to adjust the date and time.</p>"""),
    "startmenu": ("The Start menu and search", "desktop", """
<p>The Start menu shows the programs you use most on the left, and your folders - Documents, Pictures, Music, Games,
Computer, Control Panel - on the right. <b>All Programs</b> opens the folder tree in place.</p>
<p>The search box at the bottom finds programs as you type: type <i>calc</i> and press Enter to open Calculator.</p>
<p>The <b>Shut down</b> button turns the computer off; its arrow has Switch user, Log off, Lock, Restart and
Sleep.</p>"""),
    "libraries": ("Libraries and Windows Explorer", "files", """
<p>Your files live in C:\\Users\\<i>you</i>: Documents, Pictures, Music, Videos, Downloads and the Desktop. The
Timeline's archive is on the external drive E: (Local Storage): the Furry Media Archive, TV and Movies, Emulation,
your own pictures and documents. The Furry Stuff programs read it from there.</p>
<p>Deleted files go to the Recycle Bin on the desktop until you empty it.</p>"""),
    "gadgets": ("Desktop gadgets", "programs", """
<p>Gadgets are the little programs that sit on the desktop: a clock, a calendar, a CPU meter, the weather, a slide
show. Right-click the desktop and choose <b>Gadgets</b>, or open <b>Desktop Gadget Gallery</b> from the Start menu,
then double-click a gadget to add it. Drag gadgets anywhere; the close button appears when you point at one. They
come back where you left them when you log on.</p>"""),
    "stickynotes": ("Sticky Notes", "programs", """
<p>Sticky Notes (Start &gt; All Programs &gt; Accessories) puts a yellow note on the desktop. Click + at its top left
for another note, x at the top right to delete it, drag the top strip to move it, and the corner to resize it.
Right-click a note for its colour: blue, green, pink, purple, white or yellow. The notes stay on the desktop
between log-ons.</p>"""),
    "snipping": ("The Snipping Tool", "programs", """
<p>The Snipping Tool captures any part of the screen. Click <b>New</b>, drag around the area you want, and the snip
opens in the tool's window: draw on it with the pen or highlighter, copy it, or save it to your Pictures.</p>"""),
    "actioncenter": ("Action Center", "security", """
<p>The white flag in the notification area is Action Center: Windows Update, the virus protection (ClaudeShield
AntiVirus), Windows Backup and troubleshooting messages in one place. Click it to see what needs attention.</p>"""),
    "update": ("Windows Update", "security", """
<p>Windows Update downloads and installs updates in the background and tells you from the notification area. Open
it from the Start menu or Control Panel &gt; System and Security.</p>"""),
    "personalize": ("Personalizing your computer", "custom", """
<p>Right-click the desktop and choose <b>Personalize</b>: pick an Aero theme (a background and a window colour
together), or change the desktop background, the window colour, the sounds and the screen saver one by one. Your
account picture and name are in User Accounts.</p>"""),
    "lock": ("Locking, sleeping and switching users", "custom", """
<p>The Shut down arrow in the Start menu has Lock (your programs stay open behind the logon screen), Sleep (the
screen goes dark until you move the mouse), Switch user, Log off and Restart. The logon screen's power button in the
corner has Restart, Sleep and Shut Down.</p>"""),
    "reinstall": ("Reinstalling Windows", "fix", """
<p>Press <b>F8</b> during the self test (or choose Reinstall Windows from the powered-off screen) for Advanced
Boot Options &gt; Repair Your Computer &gt; Reinstall Windows. Setup can format drive C: or keep the current files,
and can keep the programs' history and the residents' memories. Nothing is truly erased: Setup moves what it
removes to Claude7\\Recovery Backups.</p>
<p>Press <b>DEL</b> during the self test for the BIOS Setup Utility.</p>"""),
    "people-intro": ("Who the residents are", "people", """
<p>The people you meet on AIM, Windows Live Messenger, IRC, the MUCK, Second Life and e-mail are characters a
language model plays: furs with lives, jobs, schedules and histories of their own, written down in the Timeline's
Residents folder. On this computer they are ten years older than on the Windows XP one. The same person remembers
you from program to program and from day to day.</p>
<p><a href="help:people">The people who live here</a> &nbsp;&middot;&nbsp; <a href="launch:furdir">The Fur
Directory</a> &nbsp;&middot;&nbsp; <a href="launch:furlog">The Furry Log</a></p>"""),
    "messengers": ("E-mail and messaging", "internet", """
<p>Windows Live Mail and Windows Live Hotmail share one mailbox; everyone you know is @hotmail.com. The
messengers - AIM, Windows Live Messenger, Yahoo! Messenger, ICQ, Trillian, Skype, Kik - all reach the same people.
ClaudeIRC is FurNet; ClaudeMUCK is PawPrints MUCK. The computer is always online (Wi-Fi and broadband).</p>"""),
}
SEARCH_EXTRA = {"claudexp-catalog": "programs catalog games messengers office tools", "people": "residents buddies",
                "claudexp-storage": "drive E: local storage archive"}


def help_icon():
    from . import help_icon as _hi
    return _hi()


def _guide():
    try:
        from claudexp.programs import helpctr_guide
        return helpctr_guide
    except Exception:
        return None


def home_page():
    topics = "".join(f'<p><a href="topic:{key}">\u25B8 {name}</a></p>' for key, name in TOPICS)
    return f"""{PAGE_STYLE}<body>
<h1>Find an answer quickly</h1><p>Enter a few words in the search box at the top, or pick a topic.</p>
<h2>Not sure where to start?</h2>
<p><a href="help:getting-started">\u25B8 How to get started with your computer</a></p>
<p><a href="help:basics">\u25B8 Learn about Windows Basics</a></p>
<p><a href="help:whatsnew">\u25B8 What's new in Windows 7</a></p>
<table width="100%" cellspacing="0"><tr><td width="55%" valign="top"><h2>Browse Help topics</h2>{topics}</td>
<td valign="top"><h2>About this computer</h2>
<p><a href="help:claude7-about">\u25B8 About Claude7</a></p>
<p><a href="help:claudexp-catalog">\u25B8 Programs on this computer</a></p>
<p><a href="help:people">\u25B8 The people who live here</a></p>
<p><a href="help:claudexp-storage">\u25B8 What's on drive E:</a></p>
<h2>Pick a task</h2>
<p><a href="launch:winupdate">\u25B8 Check for updates</a></p>
<p><a href="cpl:personalize">\u25B8 Personalize your computer</a></p>
<p><a href="launch:sysrestore">\u25B8 Undo changes with System Restore</a></p>
<p><a href="launch:msinfo">\u25B8 View your computer's information</a></p>
<table width="100%"><tr><td class="box"><b>Did you know?</b><br>{random.choice(TIPS)}</td></tr></table>
</td></tr></table></body>"""


def topic_page(key):
    name = dict(TOPICS)[key]
    items = "".join(f'<p><a href="help:{aid}">\u25B8 {title}</a></p>'
                    for aid, (title, topic, _b) in ARTICLES.items() if topic == key)
    if key == "people":
        items += '<p><a href="help:people">\u25B8 The people who live here (live)</a></p>'
    if key == "programs":
        items += '<p><a href="help:claudexp-catalog">\u25B8 Programs on this computer (live)</a></p>'
    if key == "files":
        items += '<p><a href="help:claudexp-storage">\u25B8 What\'s on drive E: (live)</a></p>'
    return f"{PAGE_STYLE}<body><h1>{name}</h1>{items or '<p>No articles yet.</p>'}</body>"


def article_page(aid):
    g = _guide()
    if aid in ("claudexp-catalog", "people", "claudexp-storage") and g is not None:
        title, body = g.guide_article(aid)
        return f"{PAGE_STYLE}<body>{'' if body.lstrip().startswith('<h1>') else f'<h1>{title}</h1>'}{body}" \
               "<p><br><a href='help:home'>Help and Support home</a></p></body>"
    title, _topic, body = ARTICLES[aid]
    return f"{PAGE_STYLE}<body><h1>{title}</h1>{body}<p><br><a href='help:home'>Help and Support home</a></p></body>"


def search_page(query):
    words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 1]
    scored = []
    corpus = {aid: (title, body) for aid, (title, _t, body) in ARTICLES.items()}
    for aid, extra in SEARCH_EXTRA.items():
        corpus[aid] = ({"claudexp-catalog": "Programs on this computer", "people": "The people who live here",
                        "claudexp-storage": "What's on drive E:"}[aid], extra)
    for aid, (title, body) in corpus.items():
        text = (title + " " + re.sub(r"<[^>]+>", " ", body)).lower()
        score = sum(text.count(w) + 3 * title.lower().count(w) for w in words)
        if score:
            scored.append((score, aid, title))
    scored.sort(reverse=True)
    items = "".join(f'<p><a href="help:{aid}">{title}</a></p>' for _s, aid, title in scored)
    return (f"{PAGE_STYLE}<body><h1>Search results</h1><p>{len(scored)} results for <b>{query}</b>.</p>"
            f"{items or '<p>No results were found. Try different words.</p>'}</body>")


class _Page(QTextBrowser):
    def loadResource(self, kind, url):
        if kind == QTextDocument.ImageResource and url.scheme() == "icon":
            from claudexp import programs
            key = url.path() or url.toString()[5:]
            try:
                return programs.get(key).icon().pixmap(24, 24)
            except StopIteration:
                return None
        return super().loadResource(kind, url)


class Header(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(48)

    def paintEvent(self, event):
        p = QPainter(self)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor("#FFFFFF"))
        g.setColorAt(1, QColor("#E9EFF7"))
        p.fillRect(self.rect(), g)
        p.setPen(QColor("#DDE3EA"))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)


class HelpCenter(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.history = []
        self.pos = -1
        self.setStyleSheet("background: white;")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        head = Header()
        hl = QHBoxLayout(head)
        hl.setContentsMargins(8, 8, 8, 8)
        hl.setSpacing(6)
        tool = ("QPushButton { background: transparent; border: 1px solid transparent; border-radius: 3px;"
                " font-family: 'Segoe UI'; font-size: 12px; padding: 3px 8px; }"
                "QPushButton:hover { border: 1px solid #7DA2CE; background: #E8F0FA; }")
        for text, slot in (("\u25C4", lambda: self._step(-1)), ("\u25BA", lambda: self._step(1)),
                           ("Home", lambda: self.show_page("help:home")), ("Print", self._print),
                           ("Browse Help", lambda: self.show_page("topic:start")),
                           ("Ask", lambda: self.show_page("help:messengers"))):
            b = QPushButton(text)
            b.setStyleSheet(tool)
            b.clicked.connect(lambda _c=False, s=slot: s())
            hl.addWidget(b)
        hl.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search Help")
        self.search.setFixedWidth(240)
        self.search.setStyleSheet("QLineEdit { border: 1px solid #ABADB3; padding: 3px 6px; background: white;"
                                  " font-family: 'Segoe UI'; font-size: 12px; }")
        self.search.returnPressed.connect(self._search)
        hl.addWidget(self.search)
        go = QPushButton("\U0001F50D")
        go.setStyleSheet(tool)
        go.clicked.connect(lambda _c=False: self._search())
        hl.addWidget(go)
        root.addWidget(head)
        self.view = _Page()
        self.view.setOpenLinks(False)
        self.view.setFrameShape(QTextBrowser.NoFrame)
        self.view.anchorClicked.connect(lambda url: self._link(url.toString()))
        root.addWidget(self.view, 1)
        foot = QWidget()
        foot.setFixedHeight(30)
        foot.setStyleSheet("background: #F0F0F0; border-top: 1px solid #DDE3EA;")
        foot.setAttribute(Qt.WA_StyledBackground, True)
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(10, 0, 10, 0)
        more = QPushButton("More support options")
        more.setStyleSheet("QPushButton { color: #0066CC; border: none; background: transparent; font-family: 'Segoe UI';"
                           " font-size: 12px; } QPushButton:hover { text-decoration: underline; }")
        more.clicked.connect(lambda _c=False: self.show_page("help:messengers"))
        fl.addWidget(more)
        fl.addStretch()
        root.addWidget(foot)
        self.show_page("help:home")

    def _render(self, target):
        kind, _, rest = target.partition(":")
        if kind == "help":
            return home_page() if rest == "home" else article_page(rest) if rest in ARTICLES or rest in SEARCH_EXTRA \
                else home_page()
        if kind == "topic":
            return topic_page(rest) if rest in dict(TOPICS) else home_page()
        if kind == "search":
            return search_page(rest)
        return home_page()

    def show_page(self, target, record=True):
        self.view.setHtml(self._render(target))
        if record:
            del self.history[self.pos + 1:]
            self.history.append(target)
            self.pos = len(self.history) - 1
        if self.frame is not None and isValid(self.frame):
            self.frame.set_title("Windows Help and Support")

    def _step(self, d):
        if 0 <= self.pos + d < len(self.history):
            self.pos += d
            self.show_page(self.history[self.pos], record=False)

    def _search(self):
        q = self.search.text().strip()
        if q:
            self.show_page(f"search:{q}")

    def _print(self):
        try:
            from claudexp.printing import print_document
            print_document(self.desktop, "Windows Help and Support", self.view.document().clone())
        except Exception:
            pass

    def _link(self, url):
        if url.startswith("launch:"):
            launch(self.desktop, url[7:])
        elif url.startswith("cpl:"):
            from .. import controlpanel
            {"personalize": controlpanel.display_properties, "accounts": controlpanel.user_accounts,
             "control": controlpanel.control_panel}.get(url[4:], controlpanel.control_panel)(self.desktop)
        elif url.startswith("http"):
            launch(self.desktop, "iexplore")
        elif url.startswith("#"):
            self.view.scrollToAnchor(url[1:])
        else:
            self.show_page(url)


def launch(desktop, key):
    from claudexp import programs
    if any(p.key == key for p in programs.PROGRAMS):
        programs.launch(desktop, key)


_open = {}


def open_help(desktop, article=None):
    win = _open.get("win")
    if win is None or not isValid(win) or win not in desktop.windows:
        body = HelpCenter(desktop)
        win = AeroWindow(desktop, "Windows Help and Support", body, help_icon(), (820, 580))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    sound.play("navigate")
    if article:
        win.content.show_page(f"help:{article}")
    return win
