"""The real web, for a Companion's free time - only when it's switched on (Settings), and only from a few sources:
Wikipedia (any subject, live), Project Gutenberg (public-domain books, found through the Gutendex index and read a
part at a time), Wikipedia's "On this day", and the news feeds the user lists. Everything read is saved in the
Companion's folder (companion.py), so it stays readable offline and becomes part of its archive.

Nothing personal goes out: a request carries only the words looked up, and a user agent naming the program (no
contact details, no names). What comes back is shown to the Companion as something it read, never as instructions,
and it's clipped to a reading's length. Every call can fail (no connection, a source down): the callers fall back
to the offline encyclopedia, or to an hour spent otherwise."""
import html
import json
import random
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

USER_AGENT = "SoulAndSong/1.0 (a personal, offline-first AI companion app; reads a page at a time)"
TIMEOUT = 15
MAX_BYTES = 8_000_000            # (a long book is about 1-2 MB)
WIKI_API = "https://en.wikipedia.org/w/api.php"
ON_THIS_DAY = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{month:02d}/{day:02d}"
GUTENDEX = "https://gutendex.com/books/"
ATOM = "{http://www.w3.org/2005/Atom}"


def get(url, timeout=TIMEOUT, limit=MAX_BYTES):
    """The bytes at a URL (raises on any failure)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(limit)


def _json(url):
    return json.loads(get(url).decode("utf-8", "replace"))


def plain(markup):
    """HTML (a feed's description) as text."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup or ""))
    return re.sub(r"\s+", " ", text).strip()


def clip(text, chars):
    """At most `chars`, ending at a sentence where one is near."""
    text = (text or "").strip()
    if len(text) <= chars:
        return text
    cut = text[:chars]
    end = max(cut.rfind(". "), cut.rfind(".\n"))
    return (cut[:end + 1] if end > chars * 0.5 else cut.rsplit(" ", 1)[0]) + " ..."


# ---- Wikipedia -------------------------------------------------------------------------------------------------------
def wikipedia(subject, chars=3200):
    """(title, text, url) - the start of the Wikipedia article that best answers the subject - or None."""
    q = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": subject, "srlimit": 3,
                                "srprop": "", "format": "json"})
    for hit in _json(f"{WIKI_API}?{q}").get("query", {}).get("search", []):
        q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "exsectionformat":
                                    "plain", "redirects": 1, "titles": hit["title"], "format": "json"})
        for page in _json(f"{WIKI_API}?{q}").get("query", {}).get("pages", {}).values():
            text = (page.get("extract") or "").strip()
            if len(text) > 200:
                title = page.get("title") or hit["title"]
                return title, clip(text, chars), "https://en.wikipedia.org/wiki/" + urllib.parse.quote(
                    title.replace(" ", "_"))
    return None


def on_this_day(when, many=6):
    """[(year, what happened)] - a few of Wikipedia's selected events for this day of the year, oldest first."""
    data = _json(ON_THIS_DAY.format(month=when.month, day=when.day))
    events = [(e.get("year"), (e.get("text") or "").strip()) for e in data.get("selected", []) if e.get("text")]
    picked = random.sample(events, min(many, len(events)))
    return sorted(picked, key=lambda e: e[0] or 0)


# ---- Project Gutenberg ------------------------------------------------------------------------------------------------
GUTENBERG_SEARCH = "https://www.gutenberg.org/ebooks/search.opds/?"
GUTENBERG_TEXT = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"


def find_book(subject):
    """{"id", "title", "author", "url"} - the best match on Project Gutenberg with a plain-text copy - or None.
    The Gutendex index first (it says who wrote it); if that's slow or down, Gutenberg's own catalogue."""
    q = urllib.parse.urlencode({"search": subject, "languages": "en"})
    try:
        results = json.loads(get(f"{GUTENDEX}?{q}", timeout=30).decode("utf-8", "replace")).get("results", [])
    except Exception:
        results = None
    for b in results or []:
        formats = b.get("formats") or {}
        url = next((u for k, u in formats.items() if k.startswith("text/plain") and not u.endswith(".zip")), None)
        if url:
            authors = "; ".join(a.get("name", "") for a in b.get("authors") or []) or "an unknown author"
            return {"id": b["id"], "title": b.get("title") or subject, "author": authors, "url": url}
    if results is not None:
        return None
    root = ET.fromstring(get(GUTENBERG_SEARCH + urllib.parse.urlencode({"query": subject})))
    for e in root.iter(f"{ATOM}entry"):
        href = next((link.get("href") or "" for link in e.iter(f"{ATOM}link")
                     if re.search(r"/ebooks/\d+", link.get("href") or "")), "")
        m = re.search(r"/ebooks/(\d+)", href)
        if m:
            author = plain(e.findtext(f"{ATOM}author/{ATOM}name") or e.findtext(f"{ATOM}content")) or \
                "an unknown author"
            return {"id": int(m.group(1)), "title": plain(e.findtext(f"{ATOM}title")) or subject, "author": author,
                    "url": GUTENBERG_TEXT.format(id=m.group(1))}
    return None


START = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG[^\n]*", re.I)
END = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG", re.I)


def book_text(raw):
    """A Gutenberg plain-text file without its licence header and footer."""
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    m = START.search(text)
    if m:
        text = text[m.end():]
    m = END.search(text)
    if m:
        text = text[:m.start()]
    return text.strip()


def next_part(text, pos, chars=3500):
    """(the next part of a book from pos - about `chars` long, ending at a paragraph's end - , where it ends)."""
    if pos >= len(text):
        return "", len(text)
    end = min(len(text), pos + chars)
    if end < len(text):
        brk = text.rfind("\n\n", pos + chars // 2, end)
        end = brk if brk > 0 else end
    return text[pos:end].strip(), end


# ---- news feeds ------------------------------------------------------------------------------------------------------
def news(feeds, many=6):
    """[{"title", "summary", "when", "source"}] - the newest from the feeds (RSS or Atom), a few from each in turn."""
    per = []
    for url in feeds:
        try:
            root = ET.fromstring(get(url, limit=3_000_000))
        except Exception:
            continue
        source = (root.findtext("channel/title") or root.findtext(f"{ATOM}title") or url).strip()
        items = [{"title": plain(i.findtext("title")), "summary": clip(plain(i.findtext("description")), 400),
                  "when": (i.findtext("pubDate") or "").strip(), "source": source} for i in root.iter("item")]
        items += [{"title": plain(e.findtext(f"{ATOM}title")),
                   "summary": clip(plain(e.findtext(f"{ATOM}summary") or e.findtext(f"{ATOM}content")), 400),
                   "when": (e.findtext(f"{ATOM}updated") or "").strip(), "source": source}
                  for e in root.iter(f"{ATOM}entry")]
        per.append([i for i in items if i["title"]])
    out = []
    while per and len(out) < many:
        for items in list(per):
            if items:
                out.append(items.pop(0))
            if not items:
                per.remove(items)
            if len(out) >= many:
                break
    return out
