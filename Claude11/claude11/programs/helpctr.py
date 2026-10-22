"""Tips, 2025: the plain white pages with their blue headings, a search box, Back and Forward,
the topics - what's new in Windows 11, Snap, the taskbar, Sticky Notes, Snipping Tool, Widgets, Quick
Settings, resetting Windows - and Claude11's own: what this computer is, every program on it (a live catalog), the
people who live here, and what's on drive E:."""
import random
import re

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QTextDocument
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QTextBrowser, QVBoxLayout, QWidget
from shiboken6 import isValid

from .. import sound
from ..wm import MicaWindow

PAGE_STYLE = """
<style>
body { font-family: 'Segoe UI'; font-size: 12px; color: #1E1E1E; }
h1 { font-family: 'Segoe UI'; font-size: 20px; font-weight: normal; color: #003399; margin-bottom: 4px; }
h2 { font-family: 'Segoe UI'; font-size: 14px; font-weight: normal; color: #003399; margin-top: 14px; }
a { color: #0066CC; text-decoration: none; }
td.box { background: #F5F9FD; border: 1px solid #C9D9EA; padding: 8px; }
li { margin-bottom: 3px; }
</style>"""
TOPICS = [("start", "Getting started"), ("new", "What's new in Windows 11"), ("desktop", "The desktop, Snap and the taskbar"),
          ("files", "Files, folders and File Explorer"), ("programs", "Programs"), ("internet", "The web, e-mail and chat"),
          ("people", "The people who live here"), ("custom", "Personalizing your computer"),
          ("security", "Security and updates"), ("fix", "Fixing problems and resetting Windows")]
TIPS = ["Drag a window to the top of the screen to maximize it, or to a side to fill that half (Snap).",
        "Rest the pointer on a window's maximize button for Snap layouts: pick where the window goes.",
        "Point at a taskbar button to see a thumbnail of its window.",
        "Right-click a program on the taskbar to pin it there; right-click one in Start to pin it to Start.",
        "Type the first letters of a program's name into the Start menu's search box and press Enter.",
        "The weather at the left corner of the taskbar opens the Widgets board: your inbox, the TV Guide and more.",
        "Click the clock for your notifications and the calendar; click the network and volume icons for Quick Settings.",
        "Sticky Notes stay on the desktop between sign-ins: right-click one to change its colour.",
        "The Snipping Tool captures any part of the screen: drag around it, then draw on it or save it.",
        "In full screen (F11), Alt+Tab switches between windows with thumbnails. Task View does the same from the taskbar.",
        "Lock the computer from your name in the Start menu: your programs stay open.",
        "Press F8 during the self test for the recovery environment, including Reset this PC.",
        "Press DEL or F2 during the self test to look around the UEFI BIOS.",
        "Everyone you know has an e-mail address - try writing to one of the IRC regulars from Outlook.",
        "Your friends remember what you talked about in one program when you meet them in another.",
        "Right-click Start for the quick menu: Settings, Task Manager, Terminal, File Explorer.",
        "Everyone you know is on Facebook and Bluesky: open them in Microsoft Edge or Firefox."]
ARTICLES = {
    "claude11-about": ("About Claude11", "start", """
<p>Claude11 is WORKSTATION-2025: a Windows 11 Home computer from October 2025, in the Claude Timeline beside
EPOCH-2001 (Windows XP) and SYSTEM-2011 (Windows 7). The same people live on all three computers, ten and fourteen
years apart: on this one they are twenty-four years older than on the XP machine, with the same histories, and
they remember what you talk about.</p>
<h2>What's here</h2>
<ul><li>The programs of 2025: Microsoft Edge and Firefox, Outlook and Outlook.com, Telegram, Discord, IRC, the MUCK,
Second Life, Trillian, Media Player, Clipchamp, Sticky Notes, the Snipping Tool, the Widgets board.</li>
<li>Every game, archive viewer and app the Timeline shares: they are the same programs on every computer, with the
same saved games.</li>
<li>Your archive on drive E: (Local Storage): the furry media, TV and movies, emulation, your own pictures and
documents.</li></ul>
<p><a href="help:claudexp-catalog">Programs on this computer</a> &nbsp;&middot;&nbsp;
<a href="help:people">The people who live here</a> &nbsp;&middot;&nbsp;
<a href="help:claudexp-storage">What's on drive E:</a></p>"""),
    "getting-started": ("How to get started with your computer", "start", """
<ul><li><b>Start</b> (the four squares in the middle of the taskbar) opens the Start menu: your pinned programs,
the ones you used recently, and a search box. Type to search.</li>
<li><b>The taskbar</b> is centered: Search, Task View, your pinned programs and the open windows, with a little
line under the ones that are running. Point at one to see its thumbnail.</li>
<li><b>The right corner</b> has the hidden icons chevron, the network and volume (Quick Settings), and the clock
(notifications and the calendar). The left corner shows the weather: click it for the Widgets board.</li>
<li><b>File Explorer</b> (the folder on the taskbar) opens at This PC: drive C:, the USB drive, and your external
drive E: with the Timeline's archive.</li></ul>"""),
    "basics": ("Learn about Windows basics", "start", """
<p>Windows 11 is Windows 10 with a calmer face: rounded corners, a centered taskbar, Snap layouts, Widgets and a
Settings app that has taken over most of the Control Panel.</p>
<ul><li><a href="help:snap">Snap, Snap layouts and Task View</a></li><li><a href="help:taskbar">The taskbar</a></li>
<li><a href="help:startmenu">The Start menu and search</a></li>
<li><a href="help:explorer">File Explorer</a></li><li><a href="help:widgets">Widgets</a></li>
<li><a href="help:stickynotes">Sticky Notes</a></li><li><a href="help:snipping">The Snipping Tool</a></li></ul>"""),
    "whatsnew": ("What's new in Windows 11", "new", """
<ul><li><b>A centered taskbar</b> with Start in the middle, and a Start menu of pinned and recommended programs.</li>
<li><b>Snap layouts:</b> rest on a window's maximize button and choose a layout; drag to the edges as before.</li>
<li><b>Widgets:</b> the board that slides in from the left with the weather, your calendar and inbox, the TV
Guide, your friends' posts.</li>
<li><b>Rounded corners</b> everywhere, Mica windows that let the wallpaper's colour through, Fluent icons.</li>
<li><b>Settings</b> replaces most of the Control Panel; Quick Settings and the notification center replace Action
Center.</li>
<li><b>Microsoft Edge</b> is the browser; Internet Explorer is gone (2022). <b>Outlook</b> replaces Mail.</li>
<li><b>Microsoft Solitaire Collection</b> in Start &gt; All &gt; Games; Chess Titans did not survive.</li>
<li>Gone since 2011: Windows Live Messenger, Skype (retired May 2025), AIM, ICQ, Yahoo! Messenger, gadgets, Aero
glass, Flash Player (Ruffle plays the old movies now).</li></ul>"""),
    "snap": ("Snap, Snap layouts and Task View", "desktop", """
<ul><li><b>Snap:</b> drag a window to the top edge to maximize it, to the left or right edge to fill that half of
the screen. Drag it away to put it back.</li>
<li><b>Snap layouts:</b> rest the pointer on the maximize button and a panel of layouts drops down - halves,
thirds, quarters. Click a zone and the window goes there.</li>
<li><b>Thumbnails:</b> point at a taskbar button to see the window; click the thumbnail to switch to it.</li>
<li><b>Task View</b> (the two squares on the taskbar) and <b>Alt+Tab</b> (in full screen - F11) show every window
as a big thumbnail.</li></ul>"""),
    "taskbar": ("The taskbar", "desktop", """
<p>The taskbar holds pinned programs and open windows together, centered. Right-click a program's button to pin
or unpin it. A running program has a little line under its icon; the active one's line is wider and coloured; a
window asking for attention flashes.</p><p>Right-click the taskbar for Task Manager and Taskbar settings
(alignment, Search, Task View and Widgets). Right-click Start for the quick menu.</p>"""),
    "startmenu": ("The Start menu and search", "desktop", """
<p>Start shows your <b>Pinned</b> programs in a grid and the <b>Recommended</b> programs you used lately. <b>All</b>
lists every program alphabetically, with folders for the groups (Furry Programs, Games, Social Programs...).
Right-click a program to pin it to Start or the taskbar.</p>
<p>The search box at the top finds programs as you type: type <i>calc</i> and press Enter to open Calculator.</p>
<p>Your name at the bottom has Lock and Sign out; the power button has Sleep, Shut down and Restart.</p>"""),
    "explorer": ("File Explorer", "files", """
<p>Your files live in C:\\Users\\<i>you</i>: Documents, Pictures, Music, Videos, Downloads and the Desktop. The
Timeline's archive is on the external drive E: (Local Storage): the Furry Media Archive, TV and Movies, Emulation,
your own pictures and documents. The Furry Stuff programs read it from there.</p>
<p>The command bar has New, Cut, Copy, Paste, Rename, Share and Delete, then Sort, View and Filter. The navigation
pane on the left has Home, Gallery, your folders, This PC and Network. Deleted files go to the Recycle Bin on the
desktop until you empty it.</p>"""),
    "widgets": ("Widgets", "programs", """
<p>The weather at the left corner of the taskbar opens the <b>Widgets board</b>: cards for the Weather, your
Calendar, your Outlook inbox, the TV Guide, Top stories (your friends' posts), Photos, Performance and a Clock.
<b>Add widgets</b> picks which cards you keep. Click elsewhere and the board slides away.</p>
<p>The <b>Outlook</b> card shows your inbox and how much of it is unread; click a message to read it in Outlook. The
<b>TV Guide</b> card shows what is on every ClaudeTV channel right now and what is next: click a channel to watch
it, the heading for the full guide, and use the wheel to scroll through the channels.</p>"""),
    "stickynotes": ("Sticky Notes", "programs", """
<p>Sticky Notes (Start &gt; All) puts a yellow note on the desktop. Click + at its top left for another note, x at
the top right to delete it, drag the top strip to move it, and the corner to resize it. Right-click a note for its
colour: blue, green, pink, purple, white or yellow. The notes stay on the desktop between sign-ins.</p>"""),
    "snipping": ("The Snipping Tool", "programs", """
<p>The Snipping Tool captures any part of the screen. Click <b>New</b>, drag around the area you want, and the snip
opens in the tool's window: draw on it with the pen or highlighter, copy it, or save it to your Pictures.</p>"""),
    "quicksettings": ("Quick Settings and notifications", "security", """
<p>Click the network and volume icons at the right of the taskbar for <b>Quick Settings</b>: Wi-Fi, Bluetooth,
Airplane mode, Night light, Accessibility and Cast, with the brightness and volume sliders. Click the clock for the
<b>notification center</b> - the toasts that came in, and the calendar. Windows Security (ClaudeShield Antivirus)
and Windows Update live in Settings.</p>"""),
    "update": ("Windows Update", "security", """
<p>Windows Update downloads and installs updates in the background and tells you from the notification center.
Open it from Settings &gt; Windows Update; this computer runs Windows 11 version 25H2.</p>"""),
    "personalize": ("Personalizing your computer", "custom", """
<p>Right-click the desktop and choose <b>Personalize</b>, or open Settings &gt; Personalization: the background
(Windows 11's wallpapers or your own picture), the accent colour, the lock screen picture, the themes, and the
taskbar (alignment, Search, Task View, Widgets). Your account picture and name are in Settings &gt; Accounts.</p>"""),
    "lock": ("Locking, sleeping and signing out", "custom", """
<p>Your name in the Start menu has Lock (your programs stay open behind the lock screen) and Sign out; the power
button has Sleep (the screen goes dark until you move the mouse), Shut down and Restart. Click or press a key on
the lock screen to get to sign-in.</p>"""),
    "reinstall": ("Resetting Windows", "fix", """
<p>Press <b>F8</b> during the self test (or choose Reinstall Windows from the powered-off screen, or Settings &gt;
System &gt; Recovery) for the recovery environment: Troubleshoot &gt; Reset this PC. Setup can format drive C: or
keep the current files, and can keep the programs' history and the residents' memories. Nothing is truly erased:
Setup moves what it removes to Claude11\\Recovery Backups.</p>
<p>Press <b>DEL</b> or <b>F2</b> during the self test for the ASUS UEFI BIOS Utility.</p>"""),
    "people-intro": ("Who the residents are", "people", """
<p>The people you meet on Telegram, Discord, IRC, the MUCK, Second Life and e-mail are characters a language model
plays: furs with lives, jobs, schedules and histories of their own, written down in the Timeline's Residents folder.
On this computer they are fourteen years older than on the Windows 7 one, and twenty-four older than on the XP one.
The same person remembers you from program to program and from day to day.</p>
<p><a href="help:people">The people who live here</a> &nbsp;&middot;&nbsp; <a href="launch:furdir">The Fur
Directory</a> &nbsp;&middot;&nbsp; <a href="launch:furlog">The Furry Log</a></p>"""),
    "messengers": ("E-mail and messaging", "internet", """
<p>Outlook and Outlook.com share one mailbox; you are @outlook.com, and most of your friends still have the
@hotmail.com addresses they made twenty years ago. The messengers that are left in 2025 - Telegram, Discord,
Trillian, Kik - reach the same people, and so do ClaudeIRC (FurNet) and ClaudeMUCK (PawPrints MUCK). The computer is
always online (Wi-Fi 6E and fibre).</p>"""),
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
<p><a href="help:whatsnew">\u25B8 What's new in Windows 11</a></p>
<table width="100%" cellspacing="0"><tr><td width="55%" valign="top"><h2>Browse Help topics</h2>{topics}</td>
<td valign="top"><h2>About this computer</h2>
<p><a href="help:claude11-about">\u25B8 About Claude11</a></p>
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
               "<p><br><a href='help:home'>Tips home</a></p></body>"
    title, _topic, body = ARTICLES[aid]
    return f"{PAGE_STYLE}<body><h1>{title}</h1>{body}<p><br><a href='help:home'>Tips home</a></p></body>"


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
            self.frame.set_title("Tips")

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
            print_document(self.desktop, "Tips", self.view.document().clone())
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
        win = MicaWindow(desktop, "Tips", body, help_icon(), (820, 580))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    sound.play("navigate")
    if article:
        win.content.show_page(f"help:{article}")
    return win
