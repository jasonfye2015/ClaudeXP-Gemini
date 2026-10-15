"""The Furry LiveJournal's data and its life: your own journal (data/livejournal.json) and the comments on everyone's
entries. The residents' entries themselves are their life-journal notes (see Journal) - what they post on LiveJournal
is what they'll mention on AIM.

When you post, a few buddies come by and comment (in character, background priority); when you comment on someone's
entry, they answer. Every comment you receive is also e-mailed to you by LiveJournal, as it was in 2001, and the
commenters remember it (a note in their journal), so it can come up on AIM or IRC.

The web server's thread writes here too (posting, commenting), hence the lock.
"""
import hashlib
import random
import re
import threading
import time
from datetime import datetime, timedelta

from .. import clock
from ..paths import DATA
from ..programs.people import load_json, save_json

STORE = DATA / "livejournal.json"
lock = threading.RLock()
COMMENT_MINUTES = (8, 45)          # buddies commenting on your new entry
REPLY_MINUTES = (4, 25)            # someone answering your comment on their entry
NOTIFY = ("LiveJournal Comment", "lj_notify@livejournal.com")

MOODS = ["accomplished", "amused", "artistic", "awake", "bitchy", "blah", "bored", "bouncy", "busy", "calm",
         "cheerful", "chipper", "content", "contemplative", "cranky", "creative", "crushed", "curious",
         "determined", "ditzy", "drained", "ecstatic", "energetic", "exhausted", "geeky", "giddy", "good", "grumpy",
         "happy", "hopeful", "hungry", "hyper", "indescribable", "lazy", "lonely", "mellow", "mischievous",
         "nerdy", "nostalgic", "optimistic", "pensive", "playful", "pleased", "quixotic", "relaxed", "restless",
         "sleepy", "silly", "stressed", "sympathetic", "thoughtful", "tired", "weird", "working"]
MUSIC = ["Daft Punk - One More Time", "Linkin Park - In the End", "Gorillaz - Clint Eastwood", "Weezer - Hash Pipe",
         "Dido - Thank You", "Nelly Furtado - I'm Like a Bird", "Fatboy Slim - Weapon of Choice",
         "Radiohead - Pyramid Song", "Destiny's Child - Survivor", "Staind - It's Been Awhile",
         "Alien Ant Farm - Smooth Criminal", "The Strokes - Last Nite", "Coldplay - Yellow", "Incubus - Drive",
         "Shaggy - It Wasn't Me", "Enya - Only Time", "U2 - Elevation", "OutKast - Ms. Jackson",
         "System of a Down - Chop Suey!", "Basement Jaxx - Where's Your Head At",
         "Kylie Minogue - Can't Get You Out of My Head", "Moby - South Side", "Blink-182 - The Rock Show",
         "Nobuo Uematsu - To Zanarkand", "Bjork - Hidden Place", "They Might Be Giants - Istanbul",
         "Barenaked Ladies - Pinch Me", "Smash Mouth - All Star", "Eiffel 65 - Blue (Da Ba Dee)",
         "Dream Theater - The Glass Prison", "the Hampster Dance song", "Ultima Online soundtrack", ""]

BACKFILL_ENTRIES = 3               # a journal with fewer entries than this gets a few from the past week
BACKFILL_PROMPT = """You are {name}. It is {now}, in 2001.
About you:
{persona}

You keep a LiveJournal. Write {n} short entries from the past week or two, oldest first, about your own everyday life: work or school, hobbies, friends, fandom, cons, things you bought, small dramas, plans. One to three sentences each, casual, first person, in your own voice. Do not mention {user}. Put each entry on its own line starting with "- "."""

COMMENT_PROMPT = """You are {name}. It is {now}, in 2001.
About you:
{persona}

Your friend {user} just posted this in their LiveJournal{subject}:
{text}

Write a short comment on it, the way you'd really comment on a friend's LiveJournal in 2001: react, sympathise, joke, ask something - one to three sentences, in your own voice. Write only the comment."""

REPLY_PROMPT = """You are {name}. It is {now}, in 2001.
About you:
{persona}

You wrote this in your LiveJournal:
{text}

Your friend {user} commented on it:
{comment}

Write your reply to their comment, short and in your own voice (one to three sentences). Write only the reply."""


def load():
    with lock:
        data = load_json(STORE, {})
    data.setdefault("entries", [])
    data.setdefault("profile", {})
    data.setdefault("comments", {})
    data.setdefault("queue", [])
    data.setdefault("next_id", 1)
    data.setdefault("backfilled", [])
    return data


def save(data):
    with lock:
        save_json(STORE, data)


def update(fn):
    """Load, change with fn(data), save - all under the lock. Returns fn's result."""
    with lock:
        data = load()
        result = fn(data)
        save(data)
        return result


# ---- what's shown ------------------------------------------------------------------------------------------------

def _pick(seq, key, salt):
    h = int(hashlib.md5(f"{key}:{salt}".encode()).hexdigest(), 16)
    return seq[h % len(seq)]


def clean_note(text):
    """A diary note as a post: without the model's 'Okay, here's my note:' preamble or wrapping quotes."""
    text = (text or "").strip()
    first, _, rest = text.partition("\n")
    if rest and first.rstrip().endswith(":") and len(first) < 80:
        text = rest.strip()
    return text.strip().strip('"').strip()


def resident_entries(name):
    """[{id, text, mood, music, date, time}] newest first, from their life journal (only the 'life' notes - the
    notes about talking with you stay private)."""
    from . import Journal
    out = []
    for e in Journal().entries(name):
        if e.get("kind") != "life":
            continue
        try:
            when = datetime.fromisoformat(e["when"])
        except (KeyError, ValueError):
            continue
        item = int(when.timestamp())
        out.append({"id": item, "text": clean_note(e.get("text")), "mood": _pick(MOODS, name, item),
                    "music": _pick(MUSIC, name, item + 1), "date": f"{e.get('date', '')} 2001".strip(),
                    "time": clock.time_text(when), "subject": ""})
    return out[::-1]


def comments(data, owner, item):
    return data["comments"].get(f"{owner}/{item}", [])


def add_comment(data, owner, item, who, text):
    now = clock.now()
    c = {"who": who, "text": text.strip(), "ts": int(time.time()),
         "date": f"{now:%b} {now.day}, {now.year} {clock.time_text(now)}"}
    data["comments"].setdefault(f"{owner}/{item}", []).append(c)
    return c


def new_entry(data, subject, text, mood, music, security):
    now = clock.now()
    entry = {"id": data["next_id"], "subject": subject.strip(), "text": text.strip(), "mood": mood.strip(),
             "music": music.strip(), "security": security, "ts": int(time.time()),
             "date": f"{now:%a %b} {now.day} 2001", "time": clock.time_text(now)}
    data["next_id"] += 1
    data["entries"].append(entry)
    return entry


# ---- queued reactions (web server thread adds, LifeSim's tick runs them) ----------------------------------------

def queue_comments_on(data, entry, friends):
    """A few friends will come by and comment on your new entry."""
    if entry.get("security") == "private" or not friends:
        return
    for name in random.sample(friends, k=min(len(friends), random.randint(1, 3))):
        data["queue"].append({"kind": "comment", "who": name, "item": entry["id"],
                              "due": time.time() + random.uniform(*COMMENT_MINUTES) * 60})


def request_backfill(data, name, count):
    """Someone looked at a nearly empty journal: its owner writes a few older entries (once it worked)."""
    if count >= BACKFILL_ENTRIES or name in data["backfilled"]:
        return False
    if any(q["kind"] == "backfill" and q["who"] == name for q in data["queue"]):
        return False
    data["queue"].append({"kind": "backfill", "who": name, "item": 0, "due": time.time()})
    return True


def queue_reply(data, owner, item, comment):
    data["queue"].append({"kind": "reply", "who": owner, "item": item, "comment": comment[:1500],
                          "due": time.time() + random.uniform(*REPLY_MINUTES) * 60})


def _now_text():
    now = clock.now()
    return f"{now:%A, %B} {now.day}, {now.year}"


def tick(sim):
    from .. import llm_server
    if not llm_server.ready():                    # comments and backfills wait for a model
        return
    with lock:
        data = load()
        now = time.time()
        due = [q for q in data["queue"] if q["due"] <= now]
        if not due:
            return
        for q in due:
            data["queue"].remove(q)
        save(data)
    for q in due:
        person = sim.people.get(q["who"])
        if person is None:
            continue
        if q["kind"] == "backfill":
            _backfill(sim, person)
            continue
        if not sim.awake(person):
            q["due"] = time.time() + 30 * 60
            update(lambda d, q=q: d["queue"].append(q))
            continue
        if q["kind"] == "comment":
            _comment_on_user(sim, person, q)
        else:
            _reply_to_user(sim, person, q)


def _backfill(sim, person):
    n = random.randint(3, 5)
    prompt = BACKFILL_PROMPT.format(name=person.name, persona=person.persona, user=sim.user, now=_now_text(), n=n)

    def done(text):
        notes = [clean_note(line.lstrip("-*0123456789. ").strip()) for line in (text or "").splitlines()
                 if line.strip().startswith(("-", "*")) or line.strip()[:2].rstrip(".").isdigit()]
        notes = [x for x in notes if len(x) > 12][:n]
        if not notes:
            return                                # not marked done: the next visit asks again
        update(lambda d: d["backfilled"].append(person.name) if person.name not in d["backfilled"] else None)
        from . import _date_text
        journal = sim.journal
        entries = journal.entries(person.name)
        now_real, now_game = datetime.now().astimezone(), clock.now()
        for i, note in enumerate(notes):
            back = timedelta(days=(len(notes) - i) * random.uniform(1.5, 3.0), hours=random.uniform(-6, 6))
            entries.append({"when": (now_real - back).isoformat(timespec="seconds"),
                            "date": _date_text(now_game - back), "kind": "life", "text": note})
        entries.sort(key=lambda e: e.get("when", ""))
        save_json(journal.path(person.name), entries[-60:])

    sim._ask(person.contact, prompt, done)


def _comment_on_user(sim, person, q):
    entry = next((e for e in load()["entries"] if e["id"] == q["item"]), None)
    if entry is None:
        return
    subject = f', titled "{entry["subject"]}"' if entry.get("subject") else ""
    prompt = COMMENT_PROMPT.format(name=person.name, persona=person.persona, user=sim.user, now=_now_text(),
                                   subject=subject, text=entry["text"][:2500])

    def done(text):
        if not text:
            return
        from .. import user
        me = user.online_handle()
        update(lambda d: add_comment(d, me, entry["id"], person.name, text.strip().strip('"')))
        sim.journal.add(person.name, f"Commented on {sim.user}'s LiveJournal post"
                        f"{' ' + chr(34) + entry['subject'] + chr(34) if entry.get('subject') else ''}: "
                        f"{text.strip()[:200]}", "talk")
        _notify(sim, person.name, entry, text, me, entry["id"])

    sim._ask(person.contact, prompt, done)


def _reply_to_user(sim, person, q):
    entry = next((e for e in resident_entries(person.name) if e["id"] == q["item"]), None)
    if entry is None:
        return
    prompt = REPLY_PROMPT.format(name=person.name, persona=person.persona, user=sim.user, now=_now_text(),
                                 text=entry["text"][:2500], comment=q["comment"])

    def done(text):
        if not text:
            return
        update(lambda d: add_comment(d, person.name, entry["id"], person.name, text.strip().strip('"')))
        sim.journal.add(person.name, f"Answered {sim.user}'s comment on my LiveJournal: {text.strip()[:200]}", "talk")
        _notify(sim, person.name, entry, text, person.name, entry["id"])

    sim._ask(person.contact, prompt, done)


def _notify(sim, who, entry, text, owner, item):
    """LiveJournal's 'someone replied' e-mail."""
    from urllib.parse import quote
    url = f"http://www.livejournal.com/users/{quote(owner)}/{item}.html"
    about = f'"{entry["subject"]}"' if entry.get("subject") else "an entry"
    body = (f"{who} replied to {'your' if owner != who else 'their'} LiveJournal entry ({about}).\n\n"
            f"Their reply was:\n\n  {text.strip()}\n\nYou can view the discussion here:\n\n  {url}\n\n"
            "--\nLiveJournal.com")
    sim.mailbox.add(NOTIFY[0], f"Reply to your LiveJournal {'entry' if owner != who else 'comment'}", body,
                    addr=NOTIFY[1], kind="notice")
    sim.mail_arrived.emit()
    sim._announce_mail()


def friends_of(sim, name):
    """Who's on someone's friends list: AIM buddies know each other; regulars know a handful of people."""
    names = sorted(sim.people)
    if name in sim.buddies:
        pool = [n for n in sim.buddies if n != name]
    else:
        pool = [n for n in names if n != name]
    rnd = random.Random(name)
    return sorted(rnd.sample(pool, k=min(len(pool), 6 + rnd.randint(0, 8))), key=str.lower)


def about(persona):
    """A one-line public bio from the (second-person) persona."""
    first = re.split(r"(?<=[.!?])\s", (persona or "").strip(), maxsplit=1)[0]
    for a, b in (("You're ", "I'm "), ("You are ", "I am "), (" your ", " my "), (" you ", " me "),
                 ("You ", "I ")):
        first = first.replace(a, b)
    return first
