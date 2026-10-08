"""The 2001 World Wide Web, written by the model: prompts, streaming page loads, the page cache,
built-in images, and the Netcenter home page."""
import hashlib
import html
import random
import re
from urllib.parse import parse_qs, quote_plus, urlparse

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF

from ... import clock
from ...paths import ROOT
from ..people import aim_screen_name, load_buddies, load_json, save_json

NAV_DIR = ROOT / "Program Files" / "Netscape"
DATA_DIR = NAV_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
HOME_URL = "http://home.netscape.com/"
SEARCH_URL = "http://search.netscape.com/search?q="
MAX_TOKENS = 3500

PROMPT = """You are the World Wide Web on {date}. Given a URL, you write the complete HTML page that web server would send back, exactly as it would have looked in October 2001.

Rules:
- Output ONLY the HTML document, from <html> to </html>. No explanations, no markdown, no code fences.
- Use 2001-era HTML 3.2/4.0: <table> layouts, <font face="..." color="..." size="...">, <center>, <hr>, <b>, <i>, <ul>, and colors on <body bgcolor text link vlink>. No CSS files, no <style> blocks, no JavaScript, no forms or input boxes, no frames or iframes.
- Images: only these built-in images exist, always give width and height:
    /img/construction.gif  (animated 'under construction' sign, 100x50)
    /img/counter.gif       (hit counter, 88x20)
    /img/new.gif           (a 'NEW!' badge, 32x16)
    /img/email.gif         (a mail icon, 32x32)
    /img/line.gif          (a decorative divider line, 400x8)
    /img/button.gif?text=Some+Words      (an 88x31 web button saying those words)
    /img/photo.gif?text=what+it+shows    (a photo or picture; describe what it shows)
  Any other image shows as a broken image.
- Make it specific and believable for 2001: real-sounding names, dates, prices, 2001 events and technology (Windows XP just came out, Napster, dial-up, AIM, ICQ, Geocities-style homepages, webrings, guestbooks, 'best viewed in 800x600', Netscape vs Internet Explorer).
- Include 6 to 15 links: relative links to other pages on the same site, and full http:// links to other plausible sites. Link text should say clearly what's there.
- Keep the page between one and three screens long."""

SEARCH_EXTRA = """This is a Netscape Search results page for the query "{q}". Show the search box area as plain text (no forms), then 8 to 10 results: each with a linked title (a full http:// URL to a plausible 2001 website about the query), a one or two line description, and the URL in green. Add 'Result Page: 1 2 3 Next' links at the bottom (links to the same search with &page=2 etc)."""

BUDDY_EXTRA = """This is the personal homepage of {name}. Here is who they are (write the page as they would, in their own voice, reflecting their personality, interests and how they type):
{persona}
{relationship}"""


# ---- URLs -------------------------------------------------------------------------------

def normalize(text):
    """What the user typed into Location -> a URL (plain words become a search)."""
    text = text.strip()
    if not text:
        return HOME_URL
    if text.startswith(("about:", "http://", "https://")):
        url = text
    elif " " in text or "." not in text:
        return SEARCH_URL + quote_plus(text)
    else:
        url = "http://" + text
    parts = urlparse(url)
    if not parts.path:
        url += "/"
    return url


def cache_key(url):
    parts = urlparse(url)
    norm = f"{parts.netloc.lower().removeprefix('www.')}{parts.path or '/'}"
    if parts.query:
        norm += "?" + parts.query
    return hashlib.sha1(norm.encode()).hexdigest()[:16]


def title_of(page):
    m = re.search(r"<title>(.*?)</title>", page, re.I | re.S)
    return html.unescape(m.group(1).strip()) if m else ""


def clean_html(text):
    """Strip code fences / chatter around the HTML the model wrote."""
    text = re.sub(r"^\s*```[a-zA-Z]*\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    start = re.search(r"<(!doctype|html|head|body)", text, re.I)
    if start:
        text = text[start.start():]
    end = text.lower().rfind("</html>")
    if end >= 0:
        text = text[:end + 7]
    return text


def body_colors(page):
    """Qt ignores <body text= link= vlink=>; read them so the viewer can apply them."""
    m = re.search(r"<body([^>]*)>", page, re.I)
    attrs = {}
    if m:
        for key, value in re.findall(r'(\w+)\s*=\s*"?([#\w]+)"?', m.group(1)):
            attrs[key.lower()] = value
    return attrs.get("text"), attrs.get("link"), attrs.get("bgcolor")


# ---- the people of the Web ------------------------------------------------------------------

class WebKnowledge:
    """Who and what the Web knows about: buddy homepages and site facts."""

    def __init__(self):
        self.sites = load_json(NAV_DIR / "sites.json", {}).get("sites", {})
        self.people = {}            # lowercase name -> (display name, persona)
        buddies, _ = load_buddies("web")
        self.buddy_names = []
        for contact, _web in buddies:
            self.people[contact.screen_name.lower()] = (contact.screen_name, contact.persona, True)
            self.buddy_names.append(contact.screen_name)
        for path, key, name_key in ((ROOT / "Program Files" / "ClaudeMUCK" / "world" / "regulars.json", "regulars", "name"),
                                    (ROOT / "Program Files" / "ClaudeIRC" / "regulars.json", "regulars", "nick")):
            for r in load_json(path, {}).get(key, []):
                if r.get("persona"):
                    self.people.setdefault(r[name_key].lower(), (r[name_key], r["persona"], False))
        self.aim_name = aim_screen_name()

    def person_in(self, url):
        """(name, persona, is_buddy) if this URL is someone's personal page, else None."""
        parts = urlparse(url)
        host = parts.netloc.lower()
        lowered = url.lower()
        for key, person in self.people.items():
            if re.search(rf"(^|[/~._-]){re.escape(key)}($|[/._?-])", lowered.replace(host, "", 1)) \
                    or host.startswith(key + "."):
                return person
        return None

    def context(self, url):
        parts = urlparse(url)
        host = parts.netloc.lower()
        notes = [facts for key, facts in self.sites.items() if key in host]
        person = self.person_in(url)
        if person is not None:
            name, persona, is_buddy = person
            rel = (f"Their AIM buddy {self.aim_name} might visit; they're good friends."
                   if is_buddy and self.aim_name else "")
            notes.append(BUDDY_EXTRA.format(name=name, persona=persona, relationship=rel))
            news = _life_news(name) if is_buddy else ""
            if news:
                notes.append("What's been going on in their life lately (a personal page would often have a "
                             f"'What's New' or 'Updates' section mentioning some of it):\n{news}")
        if host.startswith("search.netscape.com"):
            q = parse_qs(parts.query).get("q", [""])[0]
            notes.append(SEARCH_EXTRA.format(q=q))
        return "\n\n".join(notes)


# ---- loading pages -------------------------------------------------------------------------------

class PageLoader(QObject):
    """Streams one page from the model through the broker. chunk(text_so_far), finished_page(html, error)."""
    chunk = Signal(str)
    finished_page = Signal(str, str)

    def __init__(self, url, referrer, knowledge, model, num_ctx):
        super().__init__()
        self.url, self.referrer, self.knowledge = url, referrer, knowledge
        self.model, self.num_ctx = model, num_ctx
        self.job = None

    def stop(self):
        if self.job is not None:
            self.job.stop()

    def start(self):
        from ... import broker
        now = clock.now()
        system = PROMPT.format(date=f"{now:%A, %B} {now.day}, {now.year}")
        user = f"URL: {self.url}"
        if self.referrer:
            ref_url, ref_title, link_text = self.referrer
            user += (f"\nThe visitor got here by clicking the link \"{link_text}\" on the page "
                     f"\"{ref_title}\" ({ref_url}). The page must fit what that link promised.")
        extra = self.knowledge.context(self.url)
        if extra:
            user += "\n\n" + extra
        self.job = broker.get().stream(
            self.model, [{"role": "system", "content": system}, {"role": "user", "content": user}],
            {"num_ctx": self.num_ctx, "num_predict": MAX_TOKENS, "temperature": 0.9},
            self.chunk.emit, self.finished_page.emit, broker.FOREGROUND, think=False)


def _life_news(name):
    from ...life import get as life
    if life() is None:
        return ""
    entries = [e for e in life().journal.entries(name) if e["kind"] == "life"][-6:]
    return "\n".join(f"- {e['date']}: {e['text']}" for e in entries)


def life_updated_since(name, timestamp):
    """True if this buddy's life moved on (a new journal note) after the given time."""
    from datetime import datetime
    from ...life import get as life
    if life() is None:
        return False
    last = life().journal.last(name, "life")
    return bool(last) and datetime.fromisoformat(last["when"]).timestamp() > timestamp


class Cache:
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def get(self, url):
        path = CACHE_DIR / f"{cache_key(url)}.html"
        return path.read_text(encoding="utf-8") if path.exists() else None

    def put(self, url, page):
        (CACHE_DIR / f"{cache_key(url)}.html").write_text(page, encoding="utf-8")

    def mtime(self, url):
        path = CACHE_DIR / f"{cache_key(url)}.html"
        return path.stat().st_mtime if path.exists() else 0

    def drop(self, url):
        (CACHE_DIR / f"{cache_key(url)}.html").unlink(missing_ok=True)


# ---- built-in images ---------------------------------------------------------------------------------

def image_for(url):
    """A QPixmap for /img/... images (and a broken-image box for anything else)."""
    parts = urlparse(url)
    name = parts.path.rsplit("/", 1)[-1].lower()
    text = parse_qs(parts.query).get("text", [""])[0]
    if "/img/" not in parts.path:
        return _broken()
    return {"construction.gif": _construction, "counter.gif": lambda _t: _counter(url),
            "new.gif": _new, "email.gif": _email, "line.gif": _line,
            "button.gif": _button, "photo.gif": _photo}.get(name, lambda _t: _broken())(text)


def _canvas(w, h, color="#c0c0c0"):
    pm = QPixmap(w, h)
    pm.fill(QColor(color))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    return pm, p


def _construction(_text):
    pm, p = _canvas(100, 50, "#FFD700")
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("black"))
    for x in range(-50, 120, 16):  # hazard stripes along the top and bottom
        for y in (0, 40):
            p.drawPolygon(QPolygonF([QPointF(x, y), QPointF(x + 8, y), QPointF(x + 18, y + 10), QPointF(x + 10, y + 10)]))
    p.setPen(QColor("black"))
    font = QFont("Arial Black", 7)
    font.setBold(True)
    p.setFont(font)
    p.drawText(QRectF(0, 10, 100, 30), Qt.AlignCenter, "UNDER\nCONSTRUCTION")
    p.end()
    return pm


def _counter(url):
    digits = f"{random.Random(url).randint(1200, 98000):06d}"
    pm, p = _canvas(88, 20, "black")
    p.setFont(QFont("Courier New", 11, QFont.Bold))
    for i, d in enumerate(digits):
        p.fillRect(2 + i * 14, 2, 12, 16, QColor("#202020"))
        p.setPen(QColor("#33FF33"))
        p.drawText(QRectF(2 + i * 14, 1, 12, 18), Qt.AlignCenter, d)
    p.end()
    return pm


def _new(_text):
    pm, p = _canvas(32, 16, "#FF0000")
    p.setPen(QColor("#FFFF00"))
    p.setFont(QFont("Arial", 7, QFont.Bold))
    p.drawText(QRectF(0, 0, 32, 16), Qt.AlignCenter, "NEW!")
    p.end()
    return pm


def _email(_text):
    pm, p = _canvas(32, 32, "#FFFFFF")
    p.setPen(QPen(QColor("#404040"), 1.5))
    p.setBrush(QColor("#F5F0D0"))
    p.drawRect(QRectF(3, 8, 26, 17))
    p.drawLine(3, 8, 16, 18)
    p.drawLine(29, 8, 16, 18)
    p.end()
    return pm


def _line(_text):
    pm = QPixmap(400, 8)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    g = QLinearGradient(0, 0, 400, 0)
    for at, c in ((0, "#FF0000"), (0.2, "#FFA500"), (0.4, "#FFFF00"), (0.6, "#00C000"), (0.8, "#0000FF"), (1, "#8000FF")):
        g.setColorAt(at, QColor(c))
    p.fillRect(0, 2, 400, 4, g)
    p.end()
    return pm


def _button(text):
    rnd = random.Random(text)
    base = QColor.fromHsv(rnd.randint(0, 359), 160, 200)
    pm, p = _canvas(88, 31, base.name())
    g = QLinearGradient(0, 0, 0, 31)
    g.setColorAt(0, base.lighter(140))
    g.setColorAt(1, base.darker(130))
    p.fillRect(0, 0, 88, 31, g)
    p.setPen(QColor("black"))
    p.drawRect(0, 0, 87, 30)
    p.setPen(QColor("white"))
    p.setFont(QFont("Verdana", 6, QFont.Bold))
    p.drawText(QRectF(2, 1, 84, 29), Qt.AlignCenter | Qt.TextWordWrap, text or "Click Here!")
    p.end()
    return pm


def _photo(text):
    rnd = random.Random(text)
    pm, p = _canvas(200, 150)
    g = QLinearGradient(0, 0, 200, 150)
    g.setColorAt(0, QColor.fromHsv(rnd.randint(0, 359), 90, 230))
    g.setColorAt(1, QColor.fromHsv(rnd.randint(0, 359), 120, 140))
    p.fillRect(0, 0, 200, 150, g)
    p.setPen(QColor(255, 255, 255, 230))
    p.setFont(QFont("Arial", 9, QFont.Bold))
    p.drawText(QRectF(10, 10, 180, 130), Qt.AlignCenter | Qt.TextWordWrap, f"[ {text or 'photo'} ]")
    p.end()
    return pm


def _broken():
    pm, p = _canvas(36, 38, "#FFFFFF")
    p.setPen(QColor("#808080"))
    p.drawRect(0, 0, 35, 37)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#4080C0"))
    p.drawRect(9, 9, 14, 12)
    p.setBrush(QColor("#30A030"))
    p.drawEllipse(QRectF(15, 15, 11, 11))
    p.setPen(QPen(QColor("#C00000"), 2))
    p.drawLine(6, 30, 29, 6)
    p.end()
    return pm


# ---- the home page ----------------------------------------------------------------------------------

WEBMAIL_URL = "http://home.netscape.com/webmail/"


def _mail_frame(title, inner):
    return f"""<html><head><title>{title}</title></head><body bgcolor="#FFFFFF" text="#000000" link="#0000CC">
<table width="100%" cellpadding="6" cellspacing="0" bgcolor="#003366"><tr><td>
<font face="Arial" size="5" color="#FFFFFF"><b>Netscape WebMail</b></font></td>
<td align="right"><font face="Arial" size="2"><a href="{WEBMAIL_URL}"><font color="#FFCC00">Inbox</font></a> |
<a href="{HOME_URL}"><font color="#FFCC00">Netcenter</font></a></font></td></tr></table><br>{inner}
<br><center><font face="Arial" size="1" color="#808080">Netscape WebMail - free email for life!</font></center>
</body></html>"""


def webmail_page(messages):
    rows = []
    for m in reversed(messages):
        b, nb = ("", "") if m["read"] else ("<b>", "</b>")
        rows.append(
            f'<tr bgcolor="{"#FFFFFF" if m["read"] else "#FFFFE0"}">'
            f'<td><font face="Arial" size="2">{b}{html.escape(m["from"])}{nb}</font></td>'
            f'<td><font face="Arial" size="2"><a href="{WEBMAIL_URL}read?id={m["id"]}">'
            f'{b}{html.escape(m["subject"])}{nb}</a></font></td>'
            f'<td><font face="Arial" size="2">{html.escape(m["date"])}</font></td></tr>')
    unread = sum(1 for m in messages if not m["read"])
    inner = (f'<font face="Arial" size="3"><b>Inbox</b> ({len(messages)} messages, {unread} unread)</font><br><br>'
             '<table width="100%" border="1" cellpadding="4" cellspacing="0">'
             '<tr bgcolor="#D0D8E8"><td><font face="Arial" size="2"><b>From</b></font></td>'
             '<td><font face="Arial" size="2"><b>Subject</b></font></td>'
             '<td><font face="Arial" size="2"><b>Date</b></font></td></tr>'
             + ("".join(rows) or '<tr><td colspan="3"><font face="Arial" size="2">Your Inbox is empty.</font></td></tr>')
             + "</table>")
    return _mail_frame("Netscape WebMail - Inbox", inner)


def message_page(m):
    body = html.escape(m["body"]).replace("\n", "<br>")
    inner = (f'<table width="100%" cellpadding="4" bgcolor="#E8E8E8"><tr><td><font face="Arial" size="2">'
             f'<b>From:</b> {html.escape(m["from"])} &lt;{html.escape(m["addr"])}&gt;<br>'
             f'<b>Subject:</b> {html.escape(m["subject"])}<br><b>Date:</b> {html.escape(m["date"])}</font></td></tr></table>'
             f'<br><font face="Courier New" size="3">{body}</font><br><br>'
             f'<font face="Arial" size="2"><a href="mailto:{html.escape(m["addr"])}">Reply</a> | '
             f'<a href="{WEBMAIL_URL}">Back to Inbox</a></font>')
    return _mail_frame(f"Netscape WebMail - {m['subject']}", inner)


def home_page(knowledge, unread=0):
    now = clock.now()
    webmail = "WebMail" + (f" ({unread} new)" if unread else "")
    buddies = "".join(
        f'<li><a href="http://www.furrycities.com/{name}/">{html.escape(name)}\'s homepage</a></li>'
        for name in knowledge.buddy_names)
    return f"""<html><head><title>Netscape Netcenter</title></head>
<body bgcolor="#FFFFFF" text="#000000" link="#0000CC" vlink="#551A8B">
<table width="100%" cellpadding="6" cellspacing="0" bgcolor="#003366"><tr>
<td><font face="Arial" size="6" color="#FFFFFF"><b>Netscape Netcenter</b></font><br>
<font face="Arial" size="2" color="#FFCC00">{now:%A, %B} {now.day}, {now.year}</font></td>
<td align="right"><font face="Arial" size="2" color="#FFFFFF">Welcome back! |
<a href="http://home.netscape.com/webmail/"><font color="#FFCC00">{webmail}</font></a> |
<a href="http://home.netscape.com/help/"><font color="#FFCC00">Help</font></a></font></td></tr></table>
<table width="100%" cellpadding="4" bgcolor="#E8E8E8"><tr><td><font face="Arial" size="2">
<b>Search the Web:</b> type your words in the <b>Location</b> box above and press Enter.
&nbsp; Popular: <a href="{SEARCH_URL}furry+conventions+2002">furry conventions 2002</a>,
<a href="{SEARCH_URL}windows+xp+review">Windows XP review</a>,
<a href="{SEARCH_URL}napster+alternatives">Napster alternatives</a>,
<a href="{SEARCH_URL}free+aim+buddy+icons">free AIM buddy icons</a></font></td></tr></table>
<table width="100%" cellpadding="8"><tr valign="top">
<td width="33%"><font face="Arial" size="3" color="#003366"><b>Channels</b></font><font face="Arial" size="2">
<ul><li><a href="http://news.netscape.com/">News</a></li>
<li><a href="http://news.netscape.com/tech/">Computing &amp; Internet</a></li>
<li><a href="http://games.netscape.com/">Games</a></li>
<li><a href="http://music.netscape.com/">Music &amp; MP3</a></li>
<li><a href="http://movies.netscape.com/">Movies</a></li>
<li><a href="http://weather.netscape.com/">Weather</a></li>
<li><a href="http://horoscopes.netscape.com/">Horoscopes</a></li>
<li><a href="http://shopping.netscape.com/">Shopping</a></li></ul></font></td>
<td width="34%"><font face="Arial" size="3" color="#003366"><b>Furry Fandom</b></font><font face="Arial" size="2">
<ul><li><a href="http://www.furnet.irc/">FurNet IRC Network</a></li>
<li><a href="http://www.pawprintsmuck.com/">PawPrints MUCK</a></li>
<li><a href="http://www.furrycities.com/">FurryCities - free furry homepages</a></li>
<li><a href="http://www.furryconventions.com/">Convention listings 2001-2002</a></li>
<li><a href="http://www.fursuitnation.com/">Fursuit Nation</a></li>
<li><a href="http://www.claudeaim.com/">ClaudeAIM - download &amp; buddy icons</a></li></ul></font></td>
<td width="33%"><font face="Arial" size="3" color="#003366"><b>Your Buddies on the Web</b></font><font face="Arial" size="2">
<ul>{buddies or "<li>(no buddies yet)</li>"}</ul></font></td></tr></table>
<hr size="1"><center><font face="Arial" size="2"><b>Cool Sites:</b>
<a href="http://www.homestarrunner.com/">Homestar Runner</a> |
<a href="http://www.hampsterdance.com/">Hampster Dance</a> |
<a href="http://www.zombo.com/">Zombo.com</a> |
<a href="http://www.slashdot.org/">Slashdot</a> |
<a href="http://www.penny-arcade.com/">Penny Arcade</a></font><br><br>
<font face="Arial" size="1" color="#808080">Copyright &copy; 2001 Netscape Communications Corp. All rights reserved.
Best viewed with Netscape Navigator 4.79.</font></center>
</body></html>"""
