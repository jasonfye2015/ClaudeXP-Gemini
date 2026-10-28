"""Soul and Song reading the real web in free time (web.py) - with the real network blocked: canned answers stand in
for Wikipedia, On this day, Project Gutenberg (Gutendex, and Gutenberg's own catalogue when that's down) and news
feeds (RSS and Atom). The parsers, a free afternoon of reading (a book read to its end, part by part), nothing going
online when it's switched off, and the offline fallbacks when the web is down."""
import json
import threading
import urllib.request
from datetime import datetime, timedelta

import support

from soulsong import companion as C
from soulsong import web
from soulsong.paths import project

TEMPLATES = project()
support.needs(TEMPLATES / "Mind L1 - Mind Resources.txt", "the Companion Project's mind files in Local Storage")


def _no_network(*_a, **_k):
    raise AssertionError("a test tried to reach the real network")


urllib.request.urlopen = _no_network                     # (nothing here may go online)
PARAGRAPH = ("The sea came in and went out, and the lighthouse keeper wrote it all down in a careful hand. " * 6).strip()
BOOK = ("The Project Gutenberg eBook of The Test Book\n\nLicence words.\n\n"
        "*** START OF THE PROJECT GUTENBERG EBOOK THE TEST BOOK ***\n\n"
        + "\n\n".join(f"CHAPTER {i}\n\n{PARAGRAPH}\n\n{PARAGRAPH}" for i in range(1, 21))
        + "\n\n*** END OF THE PROJECT GUTENBERG EBOOK THE TEST BOOK ***\n\nMore licence words.").encode("utf-8")
RSS = b"""<?xml version="1.0"?><rss><channel><title>Test World News</title>
<item><title>A bridge opens</title><description>&lt;p&gt;The new bridge opened today.&lt;/p&gt;</description></item>
<item><title>Rain expected</title><description>Rain all week.</description></item></channel></rss>"""
ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Test Science</title>
<entry><title>A comet returns</title><summary>Visible next week.</summary><updated>2026-10-28</updated></entry></feed>"""
CANNED = {
    "list=search": {"query": {"search": [{"title": "Tide pool"}]}},
    "prop=extracts": {"query": {"pages": {"1": {"title": "Tide pool", "extract": "A tide pool is a shallow pool of "
                                                 "seawater on a rocky shore. " * 80}}}},
    "onthisday": {"selected": [{"year": 1969, "text": "Something happened in 1969."},
                               {"year": 1886, "text": "Something happened in 1886."}]},
    "gutendex": {"results": [{"id": 999, "title": "The Test Book", "authors": [{"name": "Writer, A."}],
                              "formats": {"text/plain; charset=utf-8":
                                          "https://www.gutenberg.org/cache/epub/999/pg999.txt"}}]},
}
calls = []


def _fake_get(url, **_k):
    calls.append(url)
    if "pg999.txt" in url:
        return BOOK
    if "rss" in url:
        return RSS
    if "atom" in url:
        return ATOM
    for key, value in CANNED.items():
        if key in url:
            return json.dumps(value).encode("utf-8")
    raise OSError(f"no canned answer for {url}")


def _down(url, **_k):
    calls.append(url)
    raise TimeoutError("the web is down")


web.get = _fake_get


def test_parsers():
    """The sources read right: Wikipedia, On this day, a Gutenberg book (without its licence), the news (RSS and Atom)"""
    title, text, url = web.wikipedia("tide pools")
    assert title == "Tide pool" and url.endswith("/Tide_pool") and len(text) <= 3300 and text.endswith(" ..."), url
    events = web.on_this_day(datetime(2026, 10, 28))
    assert [y for y, _t in events] == [1886, 1969], events
    book = web.find_book("test book")
    assert book["id"] == 999 and book["author"] == "Writer, A.", book
    text = web.book_text(BOOK)
    assert text.startswith("CHAPTER 1") and "licence" not in text.lower() and text.endswith(PARAGRAPH.strip())
    part, end = web.next_part(text, 0, 900)
    assert part and text[end - 1] != " " and text[end:end + 2] == "\n\n", "a part didn't end at a paragraph"
    items = web.news(["https://example.org/rss", "https://example.org/atom"], 3)
    assert [i["title"] for i in items] == ["A bridge opens", "A comet returns", "Rain expected"], items
    assert items[0]["summary"] == "The new bridge opened today." and items[1]["source"] == "Test Science"


def test_gutenberg_catalogue_when_gutendex_is_down():
    """Book search: Gutenberg's own catalogue when the Gutendex index doesn't answer"""
    opds = (b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>The Test Book</title><author><name>A. Writer'
            b'</name></author><link href="/ebooks/999.opds"/></entry></feed>')

    def get(url, **k):
        if "gutendex" in url:
            raise TimeoutError("slow")
        return opds
    real, web.get = web.get, get
    try:
        found = web.find_book("test book")
    finally:
        web.get = real
    assert found == {"id": 999, "title": "The Test Book", "author": "A. Writer",
                     "url": "https://www.gutenberg.org/cache/epub/999/pg999.txt"}, found


class Scripted:
    def __init__(self, choices):
        self.choices, self.asked = iter(choices), []

    def ask(self, messages, done, chunk=None, max_tokens=700, temperature=0.8):
        last = messages[-1]["content"]
        self.asked.append(last)
        if "This hour is your own" in last:
            return done(next(self.choices), None)
        return done(f"My notes ({len(self.asked)}): it made me think.", None)

    def stop(self):
        pass


def _companion(name, choices, web_on=True):
    clock = {"t": datetime(2026, 10, 28, 12, 0)}
    folder = support.scratch("web", name)
    C.create(folder, TEMPLATES, "Tester", name, "", "test")
    brain = Scripted(choices)
    c = C.Companion(folder, brain, now=lambda: clock["t"], recall=False)
    c.cfg.update(first_boot_done=True, last_day=c.day_key(), time_checks=False, dreams=False, web_reading=web_on,
                 news_feeds=["https://example.org/rss", "https://example.org/atom"], free_per_day=99)
    c.save()

    def hour():
        clock["t"] += timedelta(hours=1)
        c.cfg["last_seen"] = (clock["t"] - timedelta(hours=2)).isoformat()
        c._push(c._free_time)
        assert c.idle()
    return c, brain, hour


def test_a_free_afternoon_on_the_web():
    """Free time on the real web: Wikipedia, a book read part by part to its end, this day in history, the news"""
    calls.clear()
    c, brain, hour = _companion("Lyra", ["READ: tide pools", "BOOK: The Test Book", "BOOK", "TODAY", "NEWS"]
                                + ["BOOK"] * 30)
    for _i in range(5):
        hour()
    asked = "\n".join(brain.asked)
    assert "on Wikipedia and read \"Tide pool\"" in asked
    assert "begun reading \"The Test Book\" by Writer, A." in asked and "% of the way through" in asked
    assert "Something happened in 1969" in asked and "A comet returns (Test Science)" in asked
    assert "BOOK:" in brain.asked[0] and "NEWS" in brain.asked[0], "the web choices weren't offered"
    books = list((c.folder / "Self" / "Books").glob("*.txt"))
    assert len(books) == 1 and sum("pg999.txt" in u for u in calls) == 1, "the book wasn't kept (or was fetched twice)"
    assert c.cfg["book"]["title"] == "The Test Book" and c.cfg["book"]["last_note"].startswith("My notes")
    while c.cfg.get("book"):
        hour()
    assert [b["title"] for b in c.cfg["books_read"]] == ["The Test Book"], c.cfg["books_read"]
    reading = (c.folder / "Self" / "Reading.txt").read_text(encoding="utf-8")
    for bit in ("Tide pool - Wikipedia - https://en.wikipedia.org/wiki/Tide_pool", "Project Gutenberg - "
                "https://www.gutenberg.org/ebooks/999", "On this day, October 28", "Test Science, Test World News"):
        assert bit in reading, f"{bit!r} isn't in Reading.txt"
    log = (c.folder / "Self" / "Free Time.txt").read_text(encoding="utf-8")
    assert "read more of \"The Test Book\", to the end" in log, log[-400:]


def test_switched_off_it_stays_offline():
    """With the real web off, nothing goes online, and the web's choices aren't on offer"""
    calls.clear()
    c, brain, hour = _companion("Wren", ["BOOK: anything", "READ: tide pools", "TODAY"], web_on=False)
    for _i in range(3):
        hour()
    assert not calls, f"it went online: {calls}"
    assert "BOOK:" not in brain.asked[0] and "NEWS" not in brain.asked[0]
    assert any("in the encyclopedia" in a for a in brain.asked), "READ didn't use the offline encyclopedia"


def test_web_down_falls_back():
    """The web down: the offline encyclopedia for reading; a book or today becomes something to think about"""
    calls.clear()
    real, web.get = web.get, _down
    try:
        c, brain, hour = _companion("Ash", ["READ: tide pools", "BOOK: The Test Book", "TODAY"])
        for _i in range(3):
            hour()
    finally:
        web.get = real
    asked = "\n".join(brain.asked)
    assert calls, "it didn't try the web"
    assert "in the encyclopedia" in asked and "library couldn't be reached" in asked and "what it means to you" in asked
    log = (c.folder / "Self" / "Free Time.txt").read_text(encoding="utf-8")
    assert log.count("thought about") == 2, log


def test_the_window_reads_in_the_background():
    """In the window, the reading happens on a thread of its own, and the rest back on the window's"""
    support.qapp()
    from soulsong.app import Background
    b = Background()
    seen = {}

    def work():
        seen["work"] = threading.current_thread() is threading.main_thread()
        return 42
    b.run(work, lambda r: seen.update(then=threading.current_thread() is threading.main_thread(), result=r))
    assert support.pump(5, until=lambda: "then" in seen), "the result never came back"
    assert seen == {"work": False, "then": True, "result": 42}, seen


if __name__ == "__main__":
    support.main(globals())
