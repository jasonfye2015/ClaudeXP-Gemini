"""The rest of Windows XP's Control Panel: Date and Time, Internet Options, Fonts, Scheduled Tasks, Power Options,
Keyboard, Regional and Language Options, Accessibility Options, Folder Options, Game Controllers, Taskbar and Start
Menu, Phone and Modem Options, Speech and Administrative Tools (with an Event Viewer that shows what really happened).

Settings are kept in data/cpl.json. Some do something: Internet Options sets Internet Explorer's home page and empties
the page cache, Keyboard sets the cursor blink rate, Programs picks the default browser.
"""
import math
import time
from datetime import datetime

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCalendarWidget, QCheckBox, QComboBox, QGroupBox,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                               QRadioButton, QSlider, QSpinBox, QStyle, QTabWidget, QTextEdit, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from . import clock, sound
from .paths import DATA
from .programs.people import load_json, save_json

SETTINGS = DATA / "cpl.json"
TAB_CSS = ("QTabWidget::pane { background: #FCFCFE; border: 1px solid #919B9C; }"
           "QTabBar::tab { background: #F0EFE6; border: 1px solid #919B9C; padding: 3px 8px; font-family: Tahoma;"
           " font-size: 11px; } QTabBar::tab:selected { background: #FCFCFE; border-bottom-color: #FCFCFE; }"
           "QLabel, QCheckBox, QRadioButton, QComboBox, QGroupBox, QPushButton, QLineEdit, QSpinBox { font-family:"
           " Tahoma; font-size: 11px; }")
_open = {}


def std(which):
    return QApplication.style().standardIcon(which)


def get(key, default=None):
    return load_json(SETTINGS, {}).get(key, default)


def put(**values):
    data = load_json(SETTINGS, {})
    data.update(values)
    save_json(SETTINGS, data)


# ---- a property sheet ----------------------------------------------------------------------------------------------

def sheet(desktop, title, icon, tabs, on_ok=None, width=400):
    """An XP property sheet: tabs [(name, widget)], OK / Cancel / Apply. on_ok() saves."""
    win = _open.get(title)
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    from .network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(8, 8, 8, 8)
    tw = QTabWidget()
    tw.setStyleSheet(TAB_CSS)
    for name, w in tabs:
        tw.addTab(w, name)
    v.addWidget(tw)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel, apply = QPushButton("OK"), QPushButton("Cancel"), QPushButton("Apply")
    for b in (ok, cancel, apply):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(width)
    holder = {}

    def close():
        if holder.get("win") is not None and isValid(holder["win"]):
            desktop.close_window(holder.pop("win"))

    def save():
        if on_ok:
            on_ok()

    ok.clicked.connect(lambda: (save(), close()))
    cancel.clicked.connect(close)
    apply.clicked.connect(save)
    win = holder["win"] = _fixed_window(desktop, title, body, close)
    win.icon = icon
    _open[title] = win
    desktop.open_window(win)
    return win


def page(*items, margins=10):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(margins, margins, margins, margins)
    for x in items:
        if isinstance(x, str):
            x = QLabel(x)
            x.setWordWrap(True)
        if isinstance(x, QHBoxLayout):
            v.addLayout(x)
        else:
            v.addWidget(x)
    v.addStretch()
    return w


def group(title, *items):
    g = QGroupBox(title)
    v = QVBoxLayout(g)
    for x in items:
        if isinstance(x, str):
            x = QLabel(x)
            x.setWordWrap(True)
        if isinstance(x, QHBoxLayout):
            v.addLayout(x)
        else:
            v.addWidget(x)
    return g


def check(text, key, default=False):
    c = QCheckBox(text)
    c.setChecked(bool(get(key, default)))
    c.setProperty("cpl_key", key)
    return c


def combo(items, key, default=None):
    c = QComboBox()
    c.addItems(items)
    value = get(key, default if default is not None else items[0])
    if value in items:
        c.setCurrentText(value)
    c.setProperty("cpl_key", key)
    return c


def row(*items):
    h = QHBoxLayout()
    for x in items:
        if isinstance(x, str):
            x = QLabel(x)
        h.addWidget(x)
    h.addStretch()
    return h


def saver(*widgets):
    """on_ok for checkboxes / combo boxes / sliders made with check() and combo() (or given a cpl_key)."""
    def save():
        values = {}
        for w in widgets:
            key = w.property("cpl_key")
            if not key:
                continue
            if isinstance(w, QCheckBox):
                values[key] = w.isChecked()
            elif isinstance(w, QComboBox):
                values[key] = w.currentText()
            elif isinstance(w, (QSlider, QSpinBox)):
                values[key] = w.value()
            elif isinstance(w, QLineEdit):
                values[key] = w.text()
        put(**values)
    return save


def slider(key, default, lo=0, hi=10):
    s = QSlider(Qt.Horizontal)
    s.setRange(lo, hi)
    s.setValue(int(get(key, default)))
    s.setProperty("cpl_key", key)
    return s


# ---- Date and Time -------------------------------------------------------------------------------------------------

class AnalogClock(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(150, 150)
        t = QTimer(self)
        t.timeout.connect(self.update)
        t.start(1000)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QPointF(75, 75)
        p.setPen(QPen(QColor("#2A2A2A"), 2))
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(c, 70, 70)
        for i in range(12):
            a = math.radians(i * 30)
            p.drawLine(QPointF(75 + 60 * math.sin(a), 75 - 60 * math.cos(a)),
                       QPointF(75 + 66 * math.sin(a), 75 - 66 * math.cos(a)))
        now = clock.now()
        for value, length, width, color in ((now.hour % 12 + now.minute / 60, 36, 4, "#1A1A1A"),
                                            (now.minute + now.second / 60, 52, 3, "#1A1A1A"),
                                            (now.second, 58, 1, "#C02020")):
            a = math.radians(value * (30 if length == 36 else 6))
            p.setPen(QPen(QColor(color), width, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(c, QPointF(75 + length * math.sin(a), 75 - length * math.cos(a)))


def date_and_time(desktop):
    now = clock.now()
    cal = QCalendarWidget()
    cal.setSelectedDate(now.date())
    cal.setGridVisible(True)
    cal.setFixedHeight(170)
    time_box = QLineEdit(clock.time_text(now))
    time_box.setReadOnly(True)
    note = ("ClaudeXP keeps your PC's own date and time - it's always 2001 here. Change the time in your real "
            "Windows and ClaudeXP follows.")
    dt = page(row(cal, _vbox(AnalogClock(), time_box)), note)
    zone = combo(["(GMT-08:00) Pacific Time (US & Canada); Tijuana", "(GMT-07:00) Mountain Time (US & Canada)",
                  "(GMT-06:00) Central Time (US & Canada)", "(GMT-05:00) Eastern Time (US & Canada)",
                  "(GMT) Greenwich Mean Time : Dublin, Edinburgh, Lisbon, London",
                  "(GMT+01:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna",
                  "(GMT+09:00) Osaka, Sapporo, Tokyo", "(GMT+10:00) Canberra, Melbourne, Sydney"],
                 "timezone", _local_zone())
    dst = check("Automatically adjust clock for daylight saving changes", "dst", True)
    tz = page(zone, _world_map(), dst)
    sync = check("Automatically synchronize with an Internet time server", "timesync", True)
    server = combo(["time.windows.com", "time.nist.gov"], "timeserver")
    status = QLabel(get("timesync_status", "The time has not been synchronized yet."))
    status.setWordWrap(True)
    upd = QPushButton("Update Now")

    def update_now():
        from . import network
        if not network.is_connected():
            status.setText(f"An error occurred while Windows was synchronizing with {server.currentText()}. This "
                           "operation returned because the timeout period expired.")
            return
        n = clock.now()
        text = (f"The time has been successfully synchronized with {server.currentText()} on {n.month}/{n.day}/"
                f"{n.year} at {clock.time_text(n)}.")
        status.setText(text)
        put(timesync_status=text)
    upd.clicked.connect(update_now)
    it = page(sync, row("Server:", server, upd), status,
              "Synchronization can occur only when your computer is connected to the Internet.")
    sheet(desktop, "Date and Time Properties", std(QStyle.SP_FileDialogInfoView),
          [("Date && Time", dt), ("Time Zone", tz), ("Internet Time", it)], saver(zone, dst, sync, server), 470)


def _vbox(*items):
    w = QWidget()
    v = QVBoxLayout(w)
    for x in items:
        v.addWidget(x)
    return w


def _local_zone():
    off = -time.timezone // 3600
    return {-8: "(GMT-08:00) Pacific Time (US & Canada); Tijuana", -7: "(GMT-07:00) Mountain Time (US & Canada)",
            -6: "(GMT-06:00) Central Time (US & Canada)", -5: "(GMT-05:00) Eastern Time (US & Canada)"}.get(
        off, "(GMT-05:00) Eastern Time (US & Canada)")


def _world_map():
    lab = QLabel()
    lab.setFixedHeight(120)
    lab.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2C6AC0, stop:1 #1C4A90);"
                      " border: 1px solid #7F9DB9; color: #9CE07A; font-family: 'Lucida Console'; font-size: 9px;")
    lab.setText("   .-~~-.        _.--.      __.--~~-.\n  (      )~-._ (     )~-.-(        )\n   ~-.__.-'   "
                "~~-.__.-'    ~-.___.-'")
    lab.setAlignment(Qt.AlignCenter)
    return lab


# ---- Internet Options ----------------------------------------------------------------------------------------------

def ie_home():
    from .programs.navigator import web
    return get("ie_home", web.MSN_URL)


def internet_options(desktop):
    from .programs.navigator import web
    home = QLineEdit(ie_home())
    cur, dflt, blank = QPushButton("Use Current"), QPushButton("Use Default"), QPushButton("Use Blank")

    def current():
        from .programs.navigator import iexplore
        if iexplore._frame is not None and isValid(iexplore._frame):
            home.setText(iexplore._frame.content.url or web.MSN_URL)
    cur.clicked.connect(current)
    dflt.clicked.connect(lambda: home.setText(web.MSN_URL))
    blank.clicked.connect(lambda: home.setText("about:blank"))
    files_status = QLabel(f"Pages stored: {_cache_count()}")
    del_files = QPushButton("Delete Files...")
    del_cookies = QPushButton("Delete Cookies...")

    def delete_files():
        from .explorer.dialogs import msgbox

        def go(b):
            if b == "OK":
                n = 0
                for f in web.CACHE_DIR.glob("*.html"):
                    try:
                        f.unlink()
                        n += 1
                    except OSError:
                        pass
                files_status.setText(f"Pages stored: {_cache_count()}  ({n} deleted)")
        msgbox(desktop, "Delete Files", "Delete all files in the Temporary Internet Files folder?\n\nPages you visit "
               "will be written fresh the next time you go to them.", "question", ("OK", "Cancel"), go)
    del_files.clicked.connect(delete_files)
    del_cookies.clicked.connect(lambda: __import__("claudexp.explorer.dialogs", fromlist=["x"]).msgbox(
        desktop, "Delete Cookies", "All cookies in the Temporary Internet Files folder have been deleted.", "info"))
    days = QSpinBox()
    days.setRange(0, 999)
    days.setValue(int(get("ie_history_days", 20)))
    days.setProperty("cpl_key", "ie_history_days")
    clear = QPushButton("Clear History")

    def clear_history():
        from .programs.navigator import iexplore
        if iexplore._frame is not None and isValid(iexplore._frame):
            b = iexplore._frame.content
            b.history = b.history[b.index:b.index + 1]
            b.index = 0
            b._update_buttons()
    clear.clicked.connect(clear_history)
    general = page(group("Home page", "You can change which page to use for your home page.", row("Address:", home),
                         row(cur, dflt, blank)),
                   group("Temporary Internet files", "Pages you view on the Internet are stored in a special folder "
                         "for quick viewing later.", row(del_cookies, del_files), files_status),
                   group("History", "The History folder contains links to pages you've visited.",
                         row("Days to keep pages in history:", days, clear)))
    zones = QListWidget()
    zones.setViewMode(QListWidget.IconMode)
    zones.setFixedHeight(70)
    for name, which in (("Internet", QStyle.SP_DriveNetIcon), ("Local intranet", QStyle.SP_ComputerIcon),
                        ("Trusted sites", QStyle.SP_DialogApplyButton), ("Restricted sites", QStyle.SP_DialogNoButton)):
        zones.addItem(QListWidgetItem(std(which), name))
    level = slider("ie_security", 2, 0, 3)
    level.setOrientation(Qt.Vertical)
    level.setFixedHeight(90)
    security = page("Select a Web content zone to specify its security settings.", zones,
                    group("Security level for this zone", row(level, QLabel("<b>Medium</b><br>- Safe browsing and "
                          "still functional<br>- Prompts before downloading potentially unsafe content<br>- Unsigned "
                          "ActiveX controls will not be downloaded"))))
    priv = slider("ie_privacy", 2, 0, 5)
    priv.setOrientation(Qt.Vertical)
    priv.setFixedHeight(90)
    privacy = page(group("Settings", "Move the slider to select a privacy setting for the Internet zone.",
                         row(priv, QLabel("<b>Medium</b><br>- Blocks third-party cookies that do not have a compact "
                                          "privacy policy<br>- Restricts first-party cookies that use personally "
                                          "identifiable information without implicit consent"))))
    content = page(group("Content Advisor", "Ratings help you control the Internet content that can be viewed on "
                         "this computer.", row(QPushButton("Enable..."), QPushButton("Settings..."))),
                   group("Certificates", "Use certificates to positively identify yourself, certification "
                         "authorities, and publishers.", row(QPushButton("Clear SSL State"), QPushButton("Certificates..."),
                                                             QPushButton("Publishers..."))),
                   group("Personal information", "AutoComplete stores previous entries and suggests matches for you.",
                         row(QPushButton("AutoComplete..."), QPushButton("My Profile..."))))
    conns = QListWidget()
    conns.addItem(QListWidgetItem(std(QStyle.SP_DriveNetIcon), "America Online (Default)"))
    conns.setFixedHeight(60)
    setup = QPushButton("Setup...")
    from . import programs
    setup.clicked.connect(lambda: programs.launch(desktop, "connect"))
    dial = QButtonGroup()
    radios = []
    for i, text in enumerate(("Never dial a connection", "Dial whenever a network connection is not present",
                              "Always dial my default connection")):
        rb = QRadioButton(text)
        rb.setChecked(i == 1)
        dial.addButton(rb)
        radios.append(rb)
    connections = page(row("To set up an Internet connection, click Setup.", setup),
                       group("Dial-up and Virtual Private Network settings", conns, *radios),
                       group("Local Area Network (LAN) settings", "LAN Settings do not apply to dial-up connections.",
                             row(QPushButton("LAN Settings..."))))
    from . import defaults
    browser = QComboBox()
    for key, name in defaults.CHOICES["browser"]:
        browser.addItem(name, key)
    browser.setCurrentIndex(max(0, browser.findData(defaults.get("browser"))))
    email = combo(["Outlook Express", "MSN Hotmail", "Gemini Outlook"], "ie_email")
    check_default = check("Internet Explorer should check to see whether it is the default browser", "ie_check", True)
    programs_tab = page("You can specify which program Windows automatically uses for each Internet service.",
                        row("HTML editor:", combo(["Notepad", "Gemini Word"], "ie_html"))
                        , row("E-mail:", email), row("Newsgroups:", combo(["Outlook Express"], "ie_news")),
                        row("Internet call:", combo(["NetMeeting"], "ie_call")),
                        row("Default Web browser:", browser), check_default)

    def save():
        saver(days, level, priv, email, check_default)()
        put(ie_home=home.text().strip() or web.MSN_URL)
        defaults.set("browser", browser.currentData())
    sheet(desktop, "Internet Properties", std(QStyle.SP_BrowserReload),
          [("General", general), ("Security", security), ("Privacy", privacy), ("Content", content),
           ("Connections", connections), ("Programs", programs_tab)], save, 440)


def _cache_count():
    from .programs.navigator import web
    try:
        return sum(1 for _ in web.CACHE_DIR.glob("*.html"))
    except OSError:
        return 0


# ---- Fonts ------------------------------------------------------------------------------------------------------------

def fonts(desktop):
    from .wm import XPWindow
    win = _open.get("fonts")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return
    lst = QListWidget()
    lst.setViewMode(QListWidget.IconMode)
    lst.setGridSize(QSize(110, 70))
    lst.setIconSize(QSize(32, 32))
    lst.setWordWrap(True)
    lst.setResizeMode(QListWidget.Adjust)
    lst.setStyleSheet("QListWidget { background: white; border: none; font-family: Tahoma; font-size: 11px; }")
    icon = _tt_icon()
    families = QFontDatabase.families()
    for fam in families:
        lst.addItem(QListWidgetItem(icon, fam))
    lst.itemActivated.connect(lambda it: _font_viewer(desktop, it.text()))
    status = QLabel(f"  {len(families)} font(s)")
    status.setStyleSheet("font-family: Tahoma; font-size: 11px; border-top: 1px solid #ACA899;")
    body = _vbox(lst, status)
    body.layout().setContentsMargins(0, 0, 0, 0)
    win = _open["fonts"] = XPWindow(desktop, "Fonts", body, icon, size=(620, 440))
    desktop.open_window(win)


def _tt_icon():
    from PySide6.QtGui import QPixmap
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#808080")))
    p.setBrush(QColor("#FFFFFF"))
    p.drawRect(QRectF(5.5, 2.5, 21, 27))
    f = QFont("Times New Roman", 1)
    f.setPixelSize(15)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#2A5ABE"))
    p.drawText(QRectF(6, 5, 12, 20), Qt.AlignCenter, "T")
    p.setPen(QColor("#5A5A5A"))
    p.drawText(QRectF(13, 10, 12, 20), Qt.AlignCenter, "T")
    p.end()
    return QIcon(pm)


def _font_viewer(desktop, family):
    from .wm import XPWindow
    t = QTextEdit()
    t.setReadOnly(True)
    sample = "The quick brown fox jumps over the lazy dog. 1234567890"
    html = (f"<p style='font-family: Tahoma; font-size: 11px'><b>{family}</b><br>Typeface name: {family}<br>"
            f"File size: 64 KB<br>Version: 2.82</p><hr><p style='font-family: \"{family}\"'>abcdefghijklmnopqrstuvwxyz"
            f"<br>ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>1234567890.:,; ' \" (!?) +-*/=</p><hr>")
    for size in (12, 18, 24, 36, 48, 60, 72):
        html += f"<p style='font-family: \"{family}\"; font-size: {size}px; margin: 2px'>{size} {sample}</p>"
    t.setHtml(html)
    desktop.open_window(XPWindow(desktop, f"{family} (TrueType)", t, _tt_icon(), size=(560, 460)))


# ---- Scheduled Tasks ------------------------------------------------------------------------------------------------

def scheduled_tasks(desktop):
    from .wm import XPWindow
    tree = QTreeWidget()
    tree.setRootIsDecorated(False)
    tree.setHeaderLabels(["Name", "Schedule", "Next Run Time", "Last Run Time", "Status"])
    tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
    now = clock.now()
    tom = f"{now.month}/{now.day}/{now.year}"
    for name, sched, nxt in (("Add Scheduled Task", "", ""),
                             ("Automatic Updates", "Every day, starting when Windows starts", "When Windows starts"),
                             ("ClaudeShield Scheduled Scan", "At 8:00 PM every Fri of every week", f"8:00:00 PM {tom}"),
                             ("Disk Defragmenter", "When idle for 3 minutes", "When idle"),
                             ("Ad-aware Scan", "When the computer is busy catching up", "Never"),
                             ("Windows Messenger Check", "At logon", "At logon")):
        item = QTreeWidgetItem([name, sched, nxt, "Never" if sched else "", ""])
        item.setIcon(0, std(QStyle.SP_FileDialogDetailedView if sched else QStyle.SP_FileDialogNewFolder))
        tree.addTopLevelItem(item)
    tree.itemActivated.connect(lambda it: __import__("claudexp.explorer.dialogs", fromlist=["x"]).msgbox(
        desktop, it.text(0), "The Scheduled Task Wizard helps you schedule Windows tasks.\n\nClaudeXP schedules its "
        "own maintenance: Windows Update, the virus scan and Disk Defragmenter run when the computer has catching up "
        "to do." if it.text(0) == "Add Scheduled Task" else f"{it.text(0)}\n\nSchedule: {it.text(1)}", "info"))
    desktop.open_window(XPWindow(desktop, "Scheduled Tasks", tree, std(QStyle.SP_FileDialogDetailedView),
                                 size=(640, 300)))


# ---- Power Options -------------------------------------------------------------------------------------------------

def power_options(desktop):
    times = ["After 1 min", "After 5 mins", "After 10 mins", "After 15 mins", "After 20 mins", "After 30 mins",
             "After 1 hour", "After 2 hours", "Never"]
    scheme = combo(["Home/Office Desk", "Portable/Laptop", "Presentation", "Always On", "Minimal Power Management",
                    "Max Battery"], "power_scheme")
    mon = combo(times, "power_monitor", "After 20 mins")
    disk = combo(times, "power_disks", "Never")
    standby = combo(times, "power_standby", "Never")
    schemes = page("Select the power scheme with the most appropriate settings for this computer.", scheme,
                   group(f"Settings for {scheme.currentText()} power scheme", row("Turn off monitor:", mon),
                         row("Turn off hard disks:", disk), row("System standby:", standby)))
    icon = check("Always show icon on the taskbar", "power_icon")
    pw = check("Prompt for password when computer resumes from standby", "power_pw", True)
    button = combo(["Shut down", "Stand by", "Ask me what to do", "Do nothing"], "power_button")
    advanced = page(group("Options", icon, pw), group("Power buttons", row("When I press the power button on my "
                                                                           "computer:"), button))
    hib = check("Enable hibernation", "power_hibernate")
    hibernate = page("When your computer hibernates, it stores whatever it has in memory on your hard disk and then "
                     "shuts down. When your computer comes out of hibernation, it returns to its previous state.",
                     group("Hibernate", hib), group("Disk space for hibernation", "Free disk space: 7,382 MB\n"
                                                    "Disk space required to hibernate: 511 MB"))
    ups = page(group("Status", "Current power source: AC Power\nEstimated UPS runtime: \nEstimated UPS capacity: \n"
                     "Battery condition: "), group("Details", "Manufacturer: \nModel: "),
               "No UPS is installed on this computer.")
    sheet(desktop, "Power Options Properties", std(QStyle.SP_BrowserStop),
          [("Power Schemes", schemes), ("Advanced", advanced), ("Hibernate", hibernate), ("UPS", ups)],
          saver(scheme, mon, disk, standby, icon, pw, button, hib), 420)


# ---- Keyboard ---------------------------------------------------------------------------------------------------------

def keyboard(desktop):
    delay = slider("kb_delay", 1, 0, 3)
    rate = slider("kb_rate", 9, 0, 10)
    test = QLineEdit()
    test.setPlaceholderText("Click here and hold down a key to test repeat rate")
    blink = slider("kb_blink", 5, 0, 10)
    speed = page(group("Character repeat", row("Repeat delay:  Long", delay, "Short"),
                       row("Repeat rate:  Slow", rate, "Fast"), test),
                 group("Cursor blink rate", row("None", blink, "Fast")))
    hardware = page(group("Devices", "Name: Standard 101/102-Key or Microsoft Natural PS/2 Keyboard\nType: Keyboards"),
                    group("Device Properties", "Manufacturer: (Standard keyboards)\nLocation: plugged into keyboard "
                          "port\nDevice status: This device is working properly."))

    def save():
        saver(delay, rate, blink)()
        apply_blink()
    sheet(desktop, "Keyboard Properties", std(QStyle.SP_ComputerIcon),
          [("Speed", speed), ("Hardware", hardware)], save)


def apply_blink():
    v = int(get("kb_blink", 5))
    QApplication.instance().setCursorFlashTime(0 if v == 0 else int(1600 - v * 130))


# ---- Regional and Language Options ----------------------------------------------------------------------------------

def regional(desktop):
    now = clock.now()
    fmt = combo(["English (United States)", "English (United Kingdom)", "English (Canada)", "English (Australia)",
                 "French (France)", "German (Germany)", "Japanese", "Spanish (Mexico)"], "region_format")
    loc = combo(["United States", "Canada", "United Kingdom", "Australia", "Germany", "Japan"], "region_location")
    samples = QLabel(f"Number:\t123,456,789.00\nCurrency:\t$123,456,789.00\nTime:\t{clock.time_text(now)}\n"
                     f"Short date:\t{now.month}/{now.day}/{now.year}\nLong date:\t{clock.long_date_text(now)}")
    opts = page(group("Standards and formats", "This option affects how some programs format numbers, currencies, "
                      "dates, and time.", row(fmt, QPushButton("Customize...")), group("Samples", samples)),
                group("Location", "To help services provide you with local information, such as news and weather, "
                      "select your present location:", loc))
    langs = page(group("Text services and input languages", "To view or change the languages and methods you can "
                       "use to enter text, click Details.", row(QPushButton("Details..."))),
                 group("Supplemental language support", check("Install files for complex script and right-to-left "
                       "languages (including Thai)", "lang_complex"), check("Install files for East Asian languages",
                                                                             "lang_east")))
    adv = page(group("Language for non-Unicode programs", combo(["English (United States)"], "lang_nonuni")),
               group("Code page conversion tables", "10000 (MAC - Roman)\n10001 (MAC - Japanese)\n20127 (US-ASCII)"))
    sheet(desktop, "Regional and Language Options", std(QStyle.SP_DriveNetIcon),
          [("Regional Options", opts), ("Languages", langs), ("Advanced", adv)], saver(fmt, loc), 420)


# ---- Accessibility Options ------------------------------------------------------------------------------------------

def accessibility(desktop):
    boxes = [check("Use StickyKeys", "acc_sticky"), check("Use FilterKeys", "acc_filter"),
             check("Use ToggleKeys", "acc_toggle"), check("Use SoundSentry", "acc_sentry"),
             check("Use ShowSounds", "acc_showsounds"), check("Use High Contrast", "acc_contrast"),
             check("Use MouseKeys", "acc_mousekeys"), check("Turn off accessibility features after idle for:",
                                                             "acc_idle")]
    kb = page(group("StickyKeys", "Use StickyKeys if you want to use SHIFT, CTRL, ALT, or Windows logo key by "
                    "pressing one key at a time.", boxes[0]),
              group("FilterKeys", "Use FilterKeys if you want Windows to ignore brief or repeated keystrokes.",
                    boxes[1]),
              group("ToggleKeys", "Use ToggleKeys if you want to hear tones when pressing CAPS LOCK, NUM LOCK, and "
                    "SCROLL LOCK.", boxes[2]))
    snd = page(group("SoundSentry", "Use SoundSentry if you want Windows to generate visual warnings when your system "
                     "makes a sound.", boxes[3]),
               group("ShowSounds", "Use ShowSounds to tell your programs to display captions for the speech and sounds "
                     "they make.", boxes[4]))
    disp = page(group("High Contrast", "Use this option if you want Windows to use colors and fonts designed for easy "
                      "reading.", boxes[5]))
    mouse = page(group("MouseKeys", "Use MouseKeys if you want to control the pointer with the numeric keypad on "
                       "your keyboard.", boxes[6]))
    gen = page(group("Automatic reset", boxes[7]), group("Notification", check("Give warning message when turning a "
                                                                                 "feature on", "acc_warn", True),
                                                          check("Make a sound when turning a feature on or off",
                                                                "acc_sound", True)))
    sheet(desktop, "Accessibility Options", std(QStyle.SP_MessageBoxInformation),
          [("Keyboard", kb), ("Sound", snd), ("Display", disp), ("Mouse", mouse), ("General", gen)],
          saver(*boxes), 400)


# ---- Folder Options ---------------------------------------------------------------------------------------------------

def folder_options(desktop):
    tasks = QRadioButton("Show common tasks in folders")
    classic = QRadioButton("Use Windows classic folders")
    (classic if get("fo_classic") else tasks).setChecked(True)
    same = QRadioButton("Open each folder in the same window")
    own = QRadioButton("Open each folder in its own window")
    (own if get("fo_own") else same).setChecked(True)
    single = QRadioButton("Single-click to open an item (point to select)")
    double = QRadioButton("Double-click to open an item (single-click to select)")
    (single if get("fo_single") else double).setChecked(True)
    for a, b in ((tasks, classic), (same, own), (single, double)):
        g = QButtonGroup(a)
        g.addButton(a)
        g.addButton(b)
    general = page(group("Tasks", tasks, classic), group("Browse folders", same, own),
                   group("Click items as follows", single, double))
    adv = QTreeWidget()
    adv.setHeaderHidden(True)
    adv.setRootIsDecorated(False)
    adv_items = [("Display the contents of system folders", "fo_sys", False),
                 ("Display the full path in the address bar", "fo_fullpath", False),
                 ("Do not cache thumbnails", "fo_nothumbs", False),
                 ("Hide extensions for known file types", "fo_hideext", True),
                 ("Hide protected operating system files (Recommended)", "fo_hidesys", True),
                 ("Launch folder windows in a separate process", "fo_process", False),
                 ("Remember each folder's view settings", "fo_remember", True),
                 ("Show Control Panel in My Computer", "fo_cpl", False),
                 ("Show encrypted or compressed NTFS files in color", "fo_color", True),
                 ("Show pop-up description for folder and desktop items", "fo_popup", True),
                 ("Use simple file sharing (Recommended)", "fo_simple", True)]
    for text, key, default in adv_items:
        it = QTreeWidgetItem([text])
        it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
        it.setCheckState(0, Qt.Checked if get(key, default) else Qt.Unchecked)
        it.setData(0, Qt.UserRole, key)
        adv.addTopLevelItem(it)
    view = page(group("Folder views", "You can apply the view (such as Details or Tiles) that you are using for this "
                      "folder to all folders.", row(QPushButton("Apply to All Folders"), QPushButton("Reset All "
                                                                                                    "Folders"))),
                "Advanced settings:", adv)
    types = QTreeWidget()
    types.setRootIsDecorated(False)
    types.setHeaderLabels(["Extensions", "File Types"])
    for ext, kind in (("AVI", "Video Clip"), ("BMP", "Bitmap Image"), ("CBR", "Comic Book Archive"),
                      ("DOC", "Gemini Word Document"), ("GIF", "GIF Image"), ("HTM", "HTML Document"),
                      ("JPG", "JPEG Image"), ("MP3", "MP3 Format Sound"), ("MOV", "QuickTime Movie"),
                      ("RM", "RealMedia File"), ("SWF", "Shockwave Flash Object"), ("TXT", "Text Document"),
                      ("WAV", "Wave Sound"), ("WMV", "Windows Media Audio/Video file"), ("ZIP", "Compressed Folder")):
        types.addTopLevelItem(QTreeWidgetItem([ext, kind]))
    filetypes = page("Registered file types:", types, row(QPushButton("New"), QPushButton("Delete")))
    offline = page(check("Enable Offline Files", "fo_offline"), "Offline Files lets you work with network files "
                   "and programs even when you are not connected to the network.")

    def save():
        values = {"fo_classic": classic.isChecked(), "fo_own": own.isChecked(), "fo_single": single.isChecked()}
        for i in range(adv.topLevelItemCount()):
            it = adv.topLevelItem(i)
            values[it.data(0, Qt.UserRole)] = it.checkState(0) == Qt.Checked
        put(**values)
    sheet(desktop, "Folder Options", std(QStyle.SP_DirIcon),
          [("General", general), ("View", view), ("File Types", filetypes), ("Offline Files", offline)], save, 420)


# ---- Game Controllers, Phone and Modem, Taskbar ------------------------------------------------------------------

def game_controllers(desktop):
    lst = QTreeWidget()
    lst.setRootIsDecorated(False)
    lst.setHeaderLabels(["Controller", "Status"])
    lst.addTopLevelItem(QTreeWidgetItem(["Gamepad (via your PC's controllers)", "OK"]))
    tab = page("These settings help you configure the game controllers installed on your computer.",
               group("Installed game controllers", lst), row(QPushButton("Add..."), QPushButton("Remove"),
                                                            QPushButton("Properties")),
               "The emulators and Doom use the controllers and keyboard of your real PC.")
    sheet(desktop, "Game Controllers", std(QStyle.SP_MediaPlay), [("General", tab), ("Advanced", page(
        group("Preferred device", "Select the preferred device for older programs.", combo(["(none)", "Gamepad"],
                                                                                           "gc_pref"))))])


def phone_modem(desktop):
    area = QLineEdit(get("phone_area", "212"))
    area.setProperty("cpl_key", "phone_area")
    locs = QTreeWidget()
    locs.setRootIsDecorated(False)
    locs.setHeaderLabels(["Location", "Area Code"])
    locs.addTopLevelItem(QTreeWidgetItem(["My Location", area.text()]))
    dialing = page("The list below displays the locations you have specified.", locs, row("Area code:", area),
                   row(QPushButton("New..."), QPushButton("Edit..."), QPushButton("Delete")))
    modems = QTreeWidget()
    modems.setRootIsDecorated(False)
    modems.setHeaderLabels(["Modem", "Attached To"])
    modems.addTopLevelItem(QTreeWidgetItem(["U.S. Robotics 56K Voice Win", "COM3"]))
    modem_tab = page("The following modems are installed:", modems,
                     row(QPushButton("Add..."), QPushButton("Remove"), QPushButton("Properties")))
    adv = page("The following telephony providers are installed on this computer:",
               "Microsoft H.323 Telephony Service Provider\nNDIS Proxy TAPI Service Provider\nTAPI Kernel-Mode "
               "Service Provider\nUnimodem 5 Service Provider")
    sheet(desktop, "Phone and Modem Options", std(QStyle.SP_DriveNetIcon),
          [("Dialing Rules", dialing), ("Modems", modem_tab), ("Advanced", adv)], saver(area))


def taskbar_start(desktop):
    lock = check("Lock the taskbar", "tb_lock", True)
    autohide = check("Auto-hide the taskbar", "tb_autohide")
    ontop = check("Keep the taskbar on top of other windows", "tb_ontop", True)
    grp = check("Group similar taskbar buttons", "tb_group", True)
    quick = check("Show Quick Launch", "tb_quick")
    clk = check("Show the clock", "tb_clock", True)
    hide = check("Hide inactive icons", "tb_hideinactive", True)
    customize = QPushButton("Customize...")
    customize.setFixedWidth(90)
    customize.clicked.connect(lambda: __import__("claudexp.tray", fromlist=["customize_notifications"])
                              .customize_notifications(desktop))
    hide.toggled.connect(customize.setEnabled)
    customize.setEnabled(hide.isChecked())
    hide_row = QHBoxLayout()
    hide_row.addWidget(hide)
    hide_row.addStretch()
    hide_row.addWidget(customize)
    taskbar = page(group("Taskbar appearance", lock, autohide, ontop, grp, quick),
                   group("Notification area", clk, "You can keep the notification area uncluttered by hiding icons "
                         "that you have not clicked recently.", hide_row))
    xp = QRadioButton("Start menu")
    cl = QRadioButton("Classic Start menu")
    (cl if get("sm_classic") else xp).setChecked(True)
    g = QButtonGroup(xp)
    g.addButton(xp)
    g.addButton(cl)
    start = page(xp, "Select this menu style for easy access to the Internet, e-mail, and your favorite programs.",
                 cl, "Select this option to use the menu style from earlier versions of Windows.",
                 "(ClaudeXP's Start menu follows the visual style: Windows Classic in Display Properties gives you "
                 "the classic look.)")

    def save():
        saver(lock, autohide, ontop, grp, quick, clk, hide)()
        put(sm_classic=cl.isChecked())
    sheet(desktop, "Taskbar and Start Menu Properties", std(QStyle.SP_TitleBarMenuButton),
          [("Taskbar", taskbar), ("Start Menu", start)], save)


# ---- Speech -----------------------------------------------------------------------------------------------------------

def speech(desktop):
    voice = combo(["Microsoft Sam", "Microsoft Mary", "Microsoft Mike"], "speech_voice")
    text = QLineEdit(f"You have selected {voice.currentText()} as the computer's default voice.")
    voice.currentTextChanged.connect(lambda v: text.setText(f"You have selected {v} as the computer's default voice."))
    say = QPushButton("Preview Voice")
    rate = slider("speech_rate", 5, 0, 10)
    shown = QLabel(" ")
    shown.setStyleSheet("font-family: Tahoma; font-size: 12px; color: #1C3D91;")

    def preview():
        words = text.text().split()
        state = {"i": 0}
        t = QTimer(shown)

        def step():
            if state["i"] >= len(words):
                t.stop()
                return
            shown.setText("<b>" + " ".join(words[:state["i"] + 1]) + "</b> " + " ".join(words[state["i"] + 1:]))
            state["i"] += 1
        t.timeout.connect(step)
        t.start(int(520 - rate.value() * 35))
        sound.play("default")
    say.clicked.connect(preview)
    tts = page(group("Voice selection", voice, "Use the following text to preview the voice:", text, row(say), shown),
               group("Voice speed", row("Slow", rate, "Fast")),
               group("Audio Output", "Audio output: Use default audio output device"))
    sheet(desktop, "Speech Properties", std(QStyle.SP_MediaVolume), [("Text To Speech", tts)], saver(voice, rate))


# ---- Administrative Tools and the Event Viewer ------------------------------------------------------------------

def admin_tools(desktop):
    from .wm import XPWindow
    lst = QListWidget()
    lst.setViewMode(QListWidget.IconMode)
    lst.setGridSize(QSize(110, 74))
    lst.setIconSize(QSize(32, 32))
    lst.setWordWrap(True)
    lst.setStyleSheet("QListWidget { background: white; border: none; font-family: Tahoma; font-size: 11px; }")
    tools = [("Component Services", QStyle.SP_FileDialogContentsView), ("Computer Management", QStyle.SP_ComputerIcon),
             ("Data Sources (ODBC)", QStyle.SP_DriveHDIcon), ("Event Viewer", QStyle.SP_FileDialogDetailedView),
             ("Local Security Policy", QStyle.SP_DialogNoButton), ("Performance", QStyle.SP_MediaSeekForward),
             ("Services", QStyle.SP_BrowserReload)]
    for name, which in tools:
        lst.addItem(QListWidgetItem(std(which), name))

    def open_tool(it):
        if it.text() == "Event Viewer":
            event_viewer(desktop)
        elif it.text() == "Services":
            services(desktop)
        elif it.text() == "Performance":
            from . import programs
            programs.launch(desktop, "taskmgr")
        else:
            from .explorer.dialogs import msgbox
            msgbox(desktop, it.text(), f"{it.text()} is a Microsoft Management Console snap-in for system "
                   "administrators.\n\nYou need administrator tools that aren't part of ClaudeXP to use it.", "info")
    lst.itemActivated.connect(open_tool)
    desktop.open_window(XPWindow(desktop, "Administrative Tools", lst, std(QStyle.SP_DirIcon), size=(560, 300)))


def _events():
    """(log, type, date, time, source, event, text) from what really happened on this PC."""
    from .programs import installed
    out = []

    def at(ts):
        d = datetime.fromtimestamp(ts).replace(year=2001)
        return f"{d.month}/{d.day}/{d.year}", d.strftime("%I:%M:%S %p").lstrip("0")
    d, t = at(time.time() - 120)
    out.append(("System", "Information", d, t, "EventLog", 6005, "The Event log service was started."))
    out.append(("System", "Information", d, t, "EventLog", 6009, "Microsoft (R) Windows (R) 5.01. 2600 Service "
                "Pack 0 Uniprocessor Free."))
    from .paths import ROOT
    crash = ROOT / "logs" / "crash.log"
    try:
        for line in crash.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]:
            if line.startswith("=== ClaudeXP started"):
                stamp = line.split("started", 1)[1].split("(")[0].strip()
                ts = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S").timestamp()
                d2, t2 = at(ts)
                out.append(("System", "Information", d2, t2, "EventLog", 6005, "The Event log service was started."))
            elif "Fatal Python error" in line or "Qt QtFatalMsg" in line:
                out.append(("System", "Error", d, t, "EventLog", 6008, "The previous system shutdown was "
                            "unexpected."))
    except OSError:
        pass
    usage = load_json(installed.USAGE_FILE, {})
    for key, u in sorted(usage.items(), key=lambda kv: kv[1].get("last", 0))[-25:]:
        d2, t2 = at(u.get("last", time.time()))
        out.append(("Application", "Information", d2, t2, "Userenv", 1000, f"Started program '{key}'."))
    upd = load_json(DATA / "updates.json", {})
    for name in (upd.get("installed") or [])[-10:]:
        out.append(("System", "Information", d, t, "NtServicePack", 4377, f"Windows XP Hotfix {name} was installed."))
    out.append(("Application", "Information", d, t, "Winlogon", 1000, "User logon notification."))
    if get("timesync_status"):
        out.append(("System", "Information", d, t, "W32Time", 35, get("timesync_status")))
    out.append(("System", "Warning", d, t, "Dhcp", 1003, "Your computer was not able to renew its address from the "
                "network (from the DHCP Server) for the Network Card with network address 0050BA3C4F21."))
    return out


def event_viewer(desktop):
    from .wm import XPWindow
    logs = QListWidget()
    logs.setFixedWidth(170)
    for name in ("Application", "Security", "System"):
        logs.addItem(QListWidgetItem(std(QStyle.SP_FileDialogDetailedView), name))
    tree = QTreeWidget()
    tree.setRootIsDecorated(False)
    tree.setHeaderLabels(["Type", "Date", "Time", "Source", "Category", "Event"])
    tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
    events = _events()
    icons = {"Information": std(QStyle.SP_MessageBoxInformation), "Warning": std(QStyle.SP_MessageBoxWarning),
             "Error": std(QStyle.SP_MessageBoxCritical)}

    def show(log):
        tree.clear()
        for ev in reversed([e for e in events if e[0] == log]):
            it = QTreeWidgetItem([ev[1], ev[2], ev[3], ev[4], "None", str(ev[5])])
            it.setIcon(0, icons[ev[1]])
            it.setData(0, Qt.UserRole, ev)
            tree.addTopLevelItem(it)
    logs.currentTextChanged.connect(show)

    def details(it):
        ev = it.data(0, Qt.UserRole)
        from .explorer.dialogs import msgbox
        msgbox(desktop, "Event Properties", f"Date: {ev[2]}   Time: {ev[3]}\nType: {ev[1]}\nSource: {ev[4]}\n"
               f"Event ID: {ev[5]}\n\nDescription:\n{ev[6]}", "info")
    tree.itemActivated.connect(details)
    body = QWidget()
    h = QHBoxLayout(body)
    h.setContentsMargins(0, 0, 0, 0)
    h.addWidget(logs)
    h.addWidget(tree, 1)
    logs.setCurrentRow(2)
    desktop.open_window(XPWindow(desktop, "Event Viewer", body, std(QStyle.SP_FileDialogDetailedView),
                                 size=(720, 420)))


def services(desktop):
    from .wm import XPWindow
    tree = QTreeWidget()
    tree.setRootIsDecorated(False)
    tree.setHeaderLabels(["Name", "Description", "Status", "Startup Type", "Log On As"])
    tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
    for name, desc, status, start in (
            ("Alerter", "Notifies selected users and computers of administrative alerts.", "", "Disabled"),
            ("Automatic Updates", "Enables the download and installation of critical Windows updates.", "Started",
             "Automatic"),
            ("ClaudeXP Language Model", "Runs the llama.cpp engine the residents talk with.", "Started", "Automatic"),
            ("DHCP Client", "Manages network configuration by registering and updating IP addresses.", "Started",
             "Automatic"),
            ("Event Log", "Enables event log messages issued by Windows-based programs to be viewed.", "Started",
             "Automatic"),
            ("Fast User Switching Compatibility", "Provides management for applications that require assistance in "
             "a multiple user environment.", "Started", "Manual"),
            ("Messenger", "Transmits net send and Alerter service messages.", "Started", "Automatic"),
            ("Print Spooler", "Loads files to memory for later printing.", "Started", "Automatic"),
            ("Remote Access Connection Manager", "Creates a network connection.", "Started", "Manual"),
            ("System Restore Service", "Performs system restore functions.", "Started", "Automatic"),
            ("Themes", "Provides user experience theme management.", "Started", "Automatic"),
            ("Windows Audio", "Manages audio devices for Windows-based programs.", "Started", "Automatic"),
            ("Windows Time", "Maintains date and time synchronization.", "Started", "Automatic")):
        tree.addTopLevelItem(QTreeWidgetItem([name, desc, status, start, "Local System"]))
    desktop.open_window(XPWindow(desktop, "Services", tree, std(QStyle.SP_BrowserReload), size=(760, 380)))
