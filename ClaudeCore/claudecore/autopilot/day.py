"""Kithylin's day: one true story of what he's up to, so everyone he talks to hears the same one.

- The schedule: a week of half-hour cells on the real clock, each one a block - free time, work, lunch, asleep,
  out. A block has a scene (a line for his prompt: where he is and how he's chatting), an away message (asleep,
  out), how quickly he answers, and how well each leg suits it (no TV at work).
- Today: what he's really doing (the legs running now), what has happened (events the legs log: the movie, the
  comic, the e-mail he sent), a one-line override ("home sick today", or a day off), and the claims - what he has
  told people. After each reply a quick pass lists the facts and plans he stated, so he keeps to them later.
- Threads: the stories and bits of his life he brings up. Life arcs run over several days, one beat a day; there
  are daily openers, recurring bits and roleplay seeds. He gets at most one suggestion per conversation, and a
  follow-up with someone who already heard the start. A thread can name legs it makes likelier, and a leg can start
  a small thread of its own (the movie he just watched).
- Interests: who matters to him. Each contact is a love interest, a close acquaintance or a friend; the tier sets
  how quickly he answers them, how long a conversation runs, whether he IMs them first (a love interest at once when
  they come online), how likely a roleplay is, and a line in his prompt about who they are to him.
- RP tracks: roleplay scenes from his own logs (selfmodel.rptracks), each a premise, two roles and the beats from
  opening to wind-down. In a roleplay he follows one and leads it, a beat at a time, instead of waiting on his
  partner; who gets which tracks follows his interests.
- The style card: his openers, closers, reply lengths by time of day and habits, mined from his recent Telegram
  logs by selfmodel.threads, used once it has been ticked.

    day = Day(path, defaults=...)                          # defaults: the computer's standard set-up
    system = day.prompt(persona, note, who="Renamon")      # the layered prompt
    text = yield from speak(ctx, "Renamon", note, history) # ask, check against today, rewrite once on a clash

Everything lives in one JSON file per computer; the autopilot panel's Day and Threads tabs edit it.
"""
import datetime
import json
import random
import re
import time
import uuid
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[3]
MINED_FILE = TIMELINE / "Local Storage" / "LLM Models" / "selfmodel" / "threads.json"   # selfmodel.threads writes it
TRACKS_FILE = MINED_FILE.with_name("rptracks.json")                                    # selfmodel.rptracks writes it
TRACK_FOR = {"love": "Love interests", "close": "Close and love", "anyone": "Anyone"}
TRACK_KINDS = {"adult": "Adult", "roleplay": "Roleplay"}
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CELLS = 48                                  # half-hour cells in a day
CODES = {".": "free", "w": "work", "l": "lunch", "s": "sleep", "o": "out"}
CODE_OF = {v: k for k, v in CODES.items()}
DAY_STARTS = 4                              # "today" runs from 4 am to 4 am, so after midnight is still today
THREAD_KINDS = {"life": "Life arc", "opener": "Daily opener", "bit": "Recurring bit", "roleplay": "Roleplay seed"}
THREAD_STATUS = ["active", "paused", "done", "suggested"]
MAX_EVENTS, MAX_CLAIMS, MAX_AUTO_THREADS = 40, 40, 5

# Interests: who he talks to more. reply: seconds before he answers; exchanges: how many replies before he lets a
# conversation rest, and rest: minutes it rests; hello: how often he IMs them first (love interests: as soon as they're
# online); roleplay: how likely they're his roleplay partner, and turns: how long a scene runs.
TIERS = {
    "love": {"title": "Love interest", "reply": (2, 8), "exchanges": (16, 32), "rest": (4, 12), "hello": 6.0,
             "roleplay": 6.0, "turns": (25, 40), "greet_at_once": True,
             "line": "{who} is someone you're sweet on: you light up when they message, you're warm, affectionate and a "
                     "little flirty with them, and you're happy to talk for a long time.",
             "blurb": "IMs them as soon as they're online; answers at once; long conversations and roleplays"},
    "close": {"title": "Close acquaintance", "reply": (4, 15), "exchanges": (8, 16), "rest": (10, 25), "hello": 3.0,
              "roleplay": 2.0, "turns": (18, 28), "greet_at_once": False,
              "line": "{who} is a close friend: easy and familiar, you're glad to hear from them and happy to chat a "
                      "while.",
              "blurb": "quick to answer; might IM them first; lengthy conversations"},
    "friend": {"title": "Friend", "reply": (20, 90), "exchanges": (3, 7), "rest": (25, 60), "hello": 1.0,
               "roleplay": 0.5, "turns": (10, 18), "greet_at_once": False,
               "line": "{who} is a friend, but not someone you're especially close to: friendly, and you keep it "
                       "lighter and shorter.",
               "blurb": "may take a while to answer; shorter conversations"},
}
TIER_ORDER = ["love", "close", "friend"]

# His mood: picked each morning (or set on the Day tab) from LiveJournal's own moods, in five groups. The odds are
# nudged by the day ahead (a workday leans tired or grumpy, a free day bright) and by how yesterday went. A mood
# changes how often he IMs first, how quickly he answers, which legs he's drawn to, and a line in his prompt.
MOOD_GROUPS = {
    "bright": ["cheerful", "chipper", "happy", "bouncy", "energetic", "optimistic", "giddy", "hyper"],
    "content": ["content", "mellow", "calm", "relaxed", "good", "pleased", "awake"],
    "tired": ["tired", "sleepy", "drained", "exhausted", "blah", "lazy"],
    "grumpy": ["grumpy", "cranky", "stressed", "restless"],
    "low": ["lonely", "pensive", "contemplative", "nostalgic", "crushed"],
}
MOOD_ORDER = ["bright", "content", "tired", "grumpy", "low"]
MOOD_TITLES = {"bright": "Bright", "content": "Content", "tired": "Tired", "grumpy": "Grumpy", "low": "Down"}
MOOD_ODDS = {"bright": 20, "content": 35, "tired": 20, "grumpy": 15, "low": 10}
MOOD_EFFECTS = {
    "bright": {"hello": 1.4, "reply": 0.85, "legs": {"roleplay": 1.4, "muck": 1.3, "browse": 1.2},
               "how": "You're in a great mood: chatty, playful and quick to reach out to people."},
    "content": {"hello": 1.0, "reply": 1.0, "legs": {},
                "how": "You're in an easy, even mood."},
    "tired": {"hello": 0.7, "reply": 1.25, "legs": {"tv": 1.4, "music": 1.3, "idle": 1.5, "roleplay": 0.7},
              "how": "You're tired: lower energy, shorter replies, the odd yawn."},
    "grumpy": {"hello": 0.6, "reply": 1.2, "legs": {"music": 1.3, "rpg": 1.3, "roleplay": 0.6},
               "how": "You're a bit grumpy today: shorter and a little sarcastic, though never mean to friends - "
                      "good company can cheer you up."},
    "low": {"hello": 0.6, "reply": 1.3, "legs": {"stories": 1.4, "music": 1.4, "chatlogs": 1.3, "roleplay": 0.8},
            "how": "You're feeling a bit down today: quieter, and glad when someone reaches out to you."},
}
MAX_MEMORIES = 60                           # days of his journal he remembers


def mood_group(mood):
    return next((g for g, words in MOOD_GROUPS.items() if mood in words), "content")

BLOCKS = {
    "free": {"title": "Free time", "colour": "#DDEFFC",
             "scene": "You're at home with your free time, at your computer.",
             "away": "", "asleep": False, "reply_pace": 1.0, "legs": {}},
    "work": {"title": "At work", "colour": "#F6D88C",
             "scene": "You're at work, chatting from your desk between tasks: you answer when you can, a bit slower "
                      "and shorter, and you don't start anything long.",
             "away": "", "asleep": False, "reply_pace": 2.2,
             "legs": {"tv": 0, "rpg": 0, "roleplay": 0, "journal": 0, "muck": 0.3, "idle": 0.4, "comics": 0.3,
                      "stories": 0.3, "portfolios": 0.3, "pictures": 0.2, "miscart": 0.2, "artcds": 0.2,
                      "camroll": 0.2, "chatlogs": 0.2, "explore": 0.3, "wikipedia": 0.8, "browse": 1.0, "mail": 1.2,
                      "music": 1.0}},
    "lunch": {"title": "Lunch break", "colour": "#BFE7B5",
              "scene": "You're on your lunch break at work: eating, catching up with people, an hour to yourself.",
              "away": "", "asleep": False, "reply_pace": 0.9,
              "legs": {"tv": 0, "rpg": 0, "roleplay": 0, "journal": 0.5, "browse": 1.5, "comics": 1.3,
                       "wikipedia": 1.3}},
    "sleep": {"title": "Asleep", "colour": "#9DA9C8",
              "scene": "You're asleep.", "away": "zzz... asleep! talk in the morning ❤️",
              "asleep": True, "reply_pace": 1.0, "legs": {}},
    "out": {"title": "Out", "colour": "#E8B9D0",
            "scene": "You're out, away from the computer.", "away": "out and about, back in a bit!",
            "asleep": True, "reply_pace": 1.0, "legs": {}},
}


def _hhmm_cell(text):
    h, _, m = text.partition(":")
    return (int(h) * 60 + int(m or 0)) // 30


def default_schedule():
    """Mon-Fri at work 9:30 am - 6:30 pm with lunch 2:30 - 3:30 pm; asleep 11 pm - 7 am every night."""
    week = {}
    for i, d in enumerate(DAYS):
        cells = ["."] * CELLS
        for c in list(range(_hhmm_cell("23:00"), CELLS)) + list(range(0, _hhmm_cell("07:00"))):
            cells[c] = "s"
        if i < 5:
            for c in range(_hhmm_cell("09:30"), _hhmm_cell("18:30")):
                cells[c] = "w"
            for c in range(_hhmm_cell("14:30"), _hhmm_cell("15:30")):
                cells[c] = "l"
        week[d] = "".join(cells)
    return week


def cell_time(cell):
    return datetime.time(cell // 2, 30 * (cell % 2))


def time_text(t):
    """'9:30 am', '11 pm'."""
    h = t.hour % 12 or 12
    return f"{h}:{t.minute:02d} {'am' if t.hour < 12 else 'pm'}".replace(":00 ", " ")


def part_of_day(hour):
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 22:
        return "evening"
    return "night"


def ago_text(seconds):
    if seconds < 90:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    if seconds < 2 * 3600:
        return "an hour ago"
    if seconds < 20 * 3600:
        return f"{int(seconds // 3600)} hours ago"
    days = int(seconds // 86400) or 1
    return "yesterday" if days == 1 else f"{days} days ago"


def new_thread(title="", kind="life", facts="", beats=None, status="active", legs=None, source="you", **extra):
    t = {"id": uuid.uuid4().hex[:10], "title": title, "kind": kind, "facts": facts, "beats": list(beats or []),
         "status": status, "legs": list(legs or []), "source": source, "started": "", "told": {}, "when": ""}
    t.update(extra)
    return t


class Day:
    """The day file, and everything that reads and writes it. now() is the real clock (a test can replace it)."""

    def __init__(self, path, now=None, defaults=None):
        self.path = path
        self.now = now or datetime.datetime.now
        self.defaults = defaults or {}      # the computer's standard set-up, for whatever the file doesn't have
        self.doing_now = {}                 # leg key -> what he's doing in it ("reading a comic")
        self.offered = {}                   # who -> thread id offered in the current conversation ("" = none)
        self.last_talked = {}               # who -> time.time() of his last line to them
        self.data = self._load()
        self._dirty = False

    # ---- the file -------------------------------------------------------------------------------------------
    def _load(self):
        d = {}
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(d, dict):
                d = {}
        except (OSError, ValueError):
            pass
        for key in ("follow_schedule", "check_replies", "use_style", "schedule", "blocks", "interests", "dismissed"):
            if key not in d and key in self.defaults:
                d[key] = json.loads(json.dumps(self.defaults[key]))
        if "threads" not in d:
            d["threads"] = json.loads(json.dumps(self.defaults.get("threads", [])))
        d.setdefault("follow_schedule", True)
        sched = d.get("schedule")
        if not isinstance(sched, dict) or any(len(sched.get(k, "")) != CELLS for k in DAYS):
            d["schedule"] = self.standard_schedule()
        blocks = d.setdefault("blocks", {})
        for key, base in BLOCKS.items():
            b = blocks.setdefault(key, {})
            for k, v in base.items():
                b.setdefault(k, json.loads(json.dumps(v)))
        d.setdefault("threads", [])
        d.setdefault("style", {})
        d.setdefault("use_style", False)
        d.setdefault("check_replies", True)
        d.setdefault("people", {})
        d.setdefault("memories", [])            # [{date, mood, summary, people: {name: note}}], from his journal
        for key, value in (("mood_odds", dict(MOOD_ODDS)), ("diary", True), ("diary_security", "public"),
                           ("tv_channels", {})):            # channel number -> how much he likes it (Media tab)
            if key not in d:
                d[key] = json.loads(json.dumps(self.defaults.get(key, value)))
        d.setdefault("interests", {})            # contact id -> "love" | "close" | "friend" (friend if unset)
        for key, value in (("rp_tracks", []), ("rp_use_tracks", True), ("rp_adult", True), ("dismissed_tracks", [])):
            if key not in d:
                d[key] = json.loads(json.dumps(self.defaults.get(key, value)))
        d.setdefault("today", {})
        self.data = d
        self._roll_day()
        return d

    def standard_schedule(self):
        """The computer's standard week, else the built-in one."""
        sched = self.defaults.get("schedule")
        if isinstance(sched, dict) and all(len(sched.get(k, "")) == CELLS for k in DAYS):
            return dict(sched)
        return default_schedule()

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=1, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.path)
            self._dirty = False
        except OSError:
            pass

    def reload(self):
        self.data = self._load()

    # ---- the clock and the schedule ---------------------------------------------------------------------------
    def today_key(self):
        return (self.now() - datetime.timedelta(hours=DAY_STARTS)).date().isoformat()

    def _roll_day(self):
        """A new day: yesterday's claims, events and override go; auto threads past their date go too."""
        d = self.data
        key = self.today_key()
        today = d.get("today") or {}
        if today.get("date") != key:
            if today.get("date") and (today.get("events") or today.get("claims") or today.get("mood")) \
                    and not any(m.get("date") == today["date"] for m in d.get("memories", [])):
                d["yesterday"] = {k: today.get(k) for k in ("date", "mood", "mood_line", "events", "claims")}
            d["today"] = {"date": key, "override": "", "day_off": False, "events": [], "claims": []}
            self.offered.clear()
            d["threads"] = [t for t in d.get("threads", [])
                            if not (t.get("source") == "auto" and t.get("expires", "9999") < key)]
            self._dirty = True
        return d["today"]

    @property
    def today(self):
        return self._roll_day()

    def block_at(self, when):
        if not self.data.get("follow_schedule", True):
            return "free"
        code = self.data["schedule"][DAYS[when.weekday()]][(when.hour * 60 + when.minute) // 30]
        key = CODES.get(code, "free")
        if key in ("work", "lunch") and self.today.get("day_off") and when.date() == self.now().date():
            return "free"
        return key

    def block(self):
        return self.block_at(self.now())

    def block_info(self, key=None):
        return self.data["blocks"].get(key or self.block(), BLOCKS["free"])

    def block_ends(self):
        """When the block he's in now ends (the next cell with a different block)."""
        now = self.now()
        here = self.block_at(now)
        t = now.replace(minute=30 * (now.minute // 30), second=0, microsecond=0)
        for _ in range(CELLS * 7):
            t += datetime.timedelta(minutes=30)
            if self.block_at(t) != here:
                return t
        return t

    def asleep(self):
        return bool(self.block_info().get("asleep"))

    def reply_pace(self):
        return float(self.block_info().get("reply_pace", 1.0) or 1.0) * self.mood_effect()["reply"]

    def hello_factor(self):
        """How much more (or less) often than usual he IMs people first, today."""
        return self.mood_effect()["hello"]

    def leg_weight(self, key):
        """How well a leg suits the block he's in, times his mood's leaning and a boost if an active thread asks
        for it."""
        w = float(self.block_info().get("legs", {}).get(key, 1.0))
        if w > 0:
            w *= self.mood_effect()["legs"].get(key, 1.0)
        if w > 0 and any(key in t.get("legs", []) for t in self.active_threads()):
            w *= 1.6
        return w

    # ---- his mood ------------------------------------------------------------------------------------------------
    def mood(self):
        return self.today.get("mood", "")

    def mood_effect(self):
        return MOOD_EFFECTS[mood_group(self.mood())] if self.mood() else MOOD_EFFECTS["content"]

    def workday(self):
        """Whether today has work in it (and isn't a day off)."""
        now = self.now() - datetime.timedelta(hours=DAY_STARTS)
        return (self.data.get("follow_schedule", True) and not self.today.get("day_off")
                and "w" in self.data["schedule"][DAYS[now.weekday()]])

    def roll_mood(self):
        """Today's mood, picked once: the odds (the Day tab's, or the standard ones), leaning tired or grumpy on a
        workday and bright on a free one, and towards how he ended yesterday."""
        today = self.today
        if today.get("mood"):
            return today["mood"]
        odds = {g: float(self.data.get("mood_odds", {}).get(g, MOOD_ODDS[g])) for g in MOOD_ORDER}
        if self.workday():
            odds["tired"] *= 1.4
            odds["grumpy"] *= 1.4
        else:
            odds["bright"] *= 1.5
            odds["content"] *= 1.2
        last = (self.data.get("memories") or [{}])[-1].get("mood") or (self.data.get("yesterday") or {}).get("mood")
        if last:
            odds[mood_group(last)] *= 1.8
        groups = [g for g in MOOD_ORDER if odds[g] > 0] or ["content"]
        group = random.choices(groups, weights=[odds[g] for g in groups])[0]
        today["mood"] = random.choice(MOOD_GROUPS[group])
        self._dirty = True
        return today["mood"]

    def set_mood(self, mood):
        self.today["mood"] = mood
        self.save()

    # ---- what he remembers -----------------------------------------------------------------------------------------
    def remember(self, date, mood, summary, people):
        """One day kept in his memory (from the day's journal): the summary and a note on each person in it."""
        mem = self.data.setdefault("memories", [])
        mem[:] = [m for m in mem if m.get("date") != date]
        mem.append({"date": date, "mood": mood or "", "summary": summary.strip(),
                    "people": {k: str(v).strip() for k, v in (people or {}).items() if str(v).strip()}})
        mem.sort(key=lambda m: m["date"])
        del mem[:-MAX_MEMORIES]
        if (self.data.get("yesterday") or {}).get("date") == date:
            self.data.pop("yesterday", None)
        self.save()

    def memory_lines(self, days=3):
        """The last few days from his journal, newest last, for every prompt."""
        out = []
        for m in [m for m in self.data.get("memories", []) if m.get("date") != self.today_key()][-days:]:
            when = datetime.date.fromisoformat(m["date"])
            out.append(f"- {DAY_NAMES[when.weekday()]} {when.day} {when:%b}"
                       + (f" ({m['mood']})" if m.get("mood") else "") + f": {m['summary']}")
        return out

    def person_lines(self, who, days=2):
        """What he remembers about someone: their last days in his journal, and today so far."""
        out = []
        for m in [m for m in self.data.get("memories", []) if who in m.get("people", {})][-days:]:
            when = datetime.date.fromisoformat(m["date"])
            out.append(f"{DAY_NAMES[when.weekday()]} {when.day} {when:%b}: {m['people'][who]}")
        today = [e["text"] for e in self.today.get("events", []) if e.get("who") == who][-2:]
        if today:
            out.append("Earlier today: " + "; ".join(today))
        return out

    # ---- interests ---------------------------------------------------------------------------------------------
    def tier(self, who):
        """'love', 'close' or 'friend' for a contact (by id or screen name)."""
        t = self.data.get("interests", {}).get(who or "")
        return t if t in TIERS else "friend"

    def tier_info(self, who):
        return TIERS[self.tier(who)]

    def set_tier(self, who, tier):
        self.data.setdefault("interests", {})[who] = tier if tier in TIERS else "friend"
        self.save()

    # ---- what he's doing ----------------------------------------------------------------------------------------
    def doing(self, key, text):
        self.doing_now[key] = text

    def done(self, key):
        self.doing_now.pop(key, None)

    def event(self, text, share=False, legs=(), who=None):
        """Something that happened today. share: also a small thread he might mention, for a day or two. who: the
        person it was with (a conversation), so he remembers it with them."""
        ev = self.today["events"]
        ev.append({"t": self.now().strftime("%H:%M"), "text": text, **({"who": who} if who else {})})
        del ev[:-MAX_EVENTS]
        if share:
            autos = [t for t in self.data["threads"] if t.get("source") == "auto"]
            for old in autos[:max(0, len(autos) - MAX_AUTO_THREADS + 1)]:
                self.data["threads"].remove(old)
            expires = (datetime.date.fromisoformat(self.today_key()) + datetime.timedelta(days=1)).isoformat()
            self.data["threads"].append(new_thread(text[:1].upper() + text[1:], "life", f"Today you {text}.",
                                                   source="auto", legs=list(legs), expires=expires,
                                                   started=self.today_key()))
        self._dirty = True
        self.save()

    def claim(self, who, text):
        cl = self.today["claims"]
        if any(c["text"].lower() == text.lower() for c in cl[-12:]):
            return
        cl.append({"t": self.now().strftime("%H:%M"), "who": who or "", "text": text})
        del cl[:-MAX_CLAIMS]
        self._dirty = True

    # ---- threads -------------------------------------------------------------------------------------------------
    def threads(self, kind=None, status=None):
        self._roll_day()
        return [t for t in self.data["threads"] if (kind is None or t.get("kind") == kind)
                and (status is None or t.get("status") == status)]

    def active_threads(self):
        return self.threads(status="active")

    def thread(self, tid):
        return next((t for t in self.data["threads"] if t.get("id") == tid), None)

    def beat(self, t):
        """Where a life arc is today: one beat a day from when it started."""
        beats = [b for b in t.get("beats", []) if b.strip()]
        if not beats:
            return ""
        if not t.get("started"):
            t["started"] = self.today_key()
            self._dirty = True
        days = (datetime.date.fromisoformat(self.today_key()) - datetime.date.fromisoformat(t["started"])).days
        return beats[max(0, min(days, len(beats) - 1))]

    def thread_for(self, who):
        """The one thread for this conversation, chosen once: a follow-up on something they've heard, a new one
        now and then, or none. (thread, "follow"|"new") or (None, "")."""
        if who in self.offered:
            t = self.thread(self.offered[who])
            if t is None:
                return None, ""
            return t, ("follow" if who in t.get("told", {}) else "new")
        cands = [t for t in self.active_threads() if t.get("kind") in ("life", "bit")]
        follow = [t for t in cands if who in t.get("told", {}) and t.get("beats")
                  and t["told"][who] < self.today_key()]
        fresh = [t for t in cands if who not in t.get("told", {})]
        pick, mode = None, ""
        if follow and random.random() < 0.6:
            pick, mode = random.choice(follow), "follow"
        elif fresh and random.random() < 0.5:
            weights = [3.0 if t.get("source") == "auto" else 1.0 for t in fresh]
            pick, mode = random.choices(fresh, weights=weights)[0], "new"
        self.offered[who] = pick["id"] if pick else ""
        return pick, mode

    def told(self, who, thread_id):
        t = self.thread(thread_id)
        if t is not None and who:
            t.setdefault("told", {})[who] = self.today_key()
            if not t.get("started"):
                t["started"] = self.today_key()
            self._dirty = True

    def merge_mined(self):
        """Bring in what selfmodel.threads found in the logs: its threads as suggestions (nothing is used until it's
        ticked; one you deleted stays gone) and its style card. Returns how many suggestions are new."""
        try:
            m = json.loads(MINED_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return 0
        have = {t.get("mined_id") for t in self.data["threads"]}
        dismissed = set(self.data.get("dismissed", []))
        added = 0
        for t in m.get("threads", []):
            mid = t.get("id")
            if not mid or mid in have or mid in dismissed or not t.get("title"):
                continue
            status = self.defaults.get("thread_status", {}).get(mid, "suggested")
            self.data["threads"].append(new_thread(t["title"], t.get("kind", "life"), t.get("facts", ""),
                                                   t.get("beats"), status=status, source="mined", mined_id=mid,
                                                   when=t.get("when", ""), support=t.get("support", 0)))
            added += 1
        if m.get("style"):
            self.data["style"] = m["style"]
            self.data["style_built"] = m.get("built", "")
        if added or m.get("style"):
            self.save()
        return added

    # ---- RP tracks ---------------------------------------------------------------------------------------------
    def merge_tracks(self):
        """Bring in the tracks selfmodel.rptracks found (switched on, for love interests if adult, else close
        friends too); ones already here keep your edits, deleted ones stay gone. Returns how many are new."""
        try:
            found = json.loads(TRACKS_FILE.read_text(encoding="utf-8")).get("tracks", [])
        except (OSError, ValueError, AttributeError):
            return 0
        have = {t.get("id") for t in self.data["rp_tracks"]} | set(self.data.get("dismissed_tracks", []))
        settings = self.defaults.get("track_settings", {})
        added = 0
        for t in found:
            if not t.get("id") or t["id"] in have:
                continue
            t = dict(t, used=0, last_used="")
            t.setdefault("for", "love" if t.get("kind") == "adult" else "close")
            t.setdefault("enabled", True)
            t.update(settings.get(t["id"], {}))
            self.data["rp_tracks"].append(t)
            added += 1
        if added:
            self.save()
        return added

    def track(self, tid):
        return next((t for t in self.data["rp_tracks"] if t.get("id") == tid), None)

    def remove_track(self, tid):
        t = self.track(tid)
        if t is not None:
            self.data.setdefault("dismissed_tracks", []).append(tid)
            self.data["rp_tracks"].remove(t)
            self.save()

    def track_for(self, who):
        """A track to follow in a roleplay with this person, or None: switched on, adult only if allowed, meant for
        someone as close as they are; the less used, the likelier."""
        if not self.data.get("rp_use_tracks", True):
            return None
        rank = {"love": 0, "close": 1, "friend": 2}[self.tier(who)]
        reach = {"love": 0, "close": 1, "anyone": 2}
        cands = [t for t in self.data["rp_tracks"] if t.get("enabled", True) and t.get("beats")
                 and (self.data.get("rp_adult", True) or t.get("kind") != "adult")
                 and rank <= reach.get(t.get("for"), 2)]
        if not cands:
            return None
        return random.choices(cands, weights=[1.0 / (1 + int(t.get("used") or 0)) for t in cands])[0]

    def track_used(self, tid):
        t = self.track(tid)
        if t is not None:
            t["used"] = int(t.get("used") or 0) + 1
            t["last_used"] = self.today_key()
            self.save()

    @staticmethod
    def track_step(t, who, step, total):
        """(note for his prompt, instruction for this turn) at one step of a scene `total` turns long."""
        beats = [b for b in t.get("beats", []) if b.strip()]
        i = min(len(beats) - 1, step * len(beats) // max(1, total))
        lines = [f"You're playing a scene you know well, and YOU lead it: \"{t.get('title', '')}\"."]
        if t.get("setting"):
            lines.append(f"Setting: {t['setting']}")
        if t.get("premise"):
            lines.append(f"How it starts: {t['premise']}")
        if t.get("his_role") or t.get("their_role"):
            lines.append(f"You are {t.get('his_role') or 'yourself'}; {who} is {t.get('their_role') or 'your partner'}.")
        lines.append("The scene, beat by beat: " + " / ".join(f"{n + 1}. {b}" for n, b in enumerate(beats)))
        if t.get("moves"):
            lines.append("How you lead: " + "; ".join(t["moves"]) + ".")
        if t.get("tone"):
            lines.append(f"Tone: {t['tone']}.")
        if t.get("lines"):
            lines.append("Lines you've written in scenes like this: " + " | ".join(t["lines"][:3]))
        lines.append("Don't wait for them to decide what happens: move it forward yourself, one beat at a time, "
                     "and react to what they do.")
        note = "\n\n" + "\n".join(partner_is(ln, who) for ln in lines)
        def said(text):
            text = partner_is(text, who).strip()
            return text if text[-1:] in ".!?" else text + "."
        beat = said(beats[i])
        if step >= total - 1:
            return note, f"Bring the scene to its close: {said(beats[-1])}"
        nxt = said(beats[min(i + 1, len(beats) - 1)])
        return note, (f"Continue the roleplay - you lead. Now (beat {i + 1} of {len(beats)}): {beat}"
                      + (f" Then steer toward: {nxt}" if nxt != beat else ""))

    def remove_thread(self, tid):
        t = self.thread(tid)
        if t is None:
            return
        if t.get("mined_id"):
            self.data.setdefault("dismissed", []).append(t["mined_id"])
        self.data["threads"].remove(t)
        self.save()

    def end_conversation(self, who):
        self.offered.pop(who, None)

    def opener(self):
        """A daily opener of his, for starting a conversation, or ''."""
        ops = self.threads(kind="opener", status="active")
        if not ops:
            return ""
        t = random.choice(ops)
        return t.get("facts") or t.get("title", "")

    def roleplay_seed(self):
        seeds = self.threads(kind="roleplay", status="active")
        return random.choice(seeds) if seeds else None

    # ---- the prompt ------------------------------------------------------------------------------------------------
    def facts(self, who=None):
        """Today's facts as lines: the time and block, the override, what he's doing, what happened."""
        now = self.now()
        info = self.block_info()
        lines = [f"It's {DAY_NAMES[now.weekday()]} {part_of_day(now.hour)}, {time_text(now.time())}."]
        if self.mood():
            lines.append(f"Your mood today: {self.mood()}. {self.mood_effect()['how']}")
        if self.today.get("mood_line"):
            lines.append(f"This morning you wrote in your LiveJournal: \"{self.today['mood_line'][:300]}\"")
        scene = info.get("scene", "")
        if scene:
            ends = self.block_ends()
            lines.append(f"{scene} (until {time_text(ends.time())})" if info.get("title") != "Free time" else scene)
        today = self.today
        if today.get("day_off"):
            lines.append("You're not working today: it's a day off.")
        if today.get("override"):
            lines.append(f"Today: {today['override']}")
        doing = [v for k, v in self.doing_now.items() if k != "messengers" and v]
        if doing:
            lines.append("Right now you're also " + ", ".join(doing).rstrip(".!?") + ".")
        events = today.get("events", [])[-6:]
        if events:
            lines.append("Earlier today: " + "; ".join(f"{e['text']} ({e['t']})" for e in events) + ".")
        return lines

    def claims_lines(self, who=None, limit=8):
        cl = self.today.get("claims", [])
        mine = [c for c in cl if c["who"] == who]
        others = [c for c in cl if c["who"] != who]
        chosen = (mine[-4:] + others[-(limit - min(4, len(mine))):])
        chosen.sort(key=lambda c: c["t"])
        return [f"- {c['t']}, to {'them' if c['who'] == who else (c['who'] or 'someone')}: {c['text']}"
                for c in chosen]

    def style_lines(self, who=None, now=None):
        if not self.data.get("use_style") or not self.data.get("style"):
            return []
        s = json.loads(json.dumps(self.data["style"]).replace("{name}", json.dumps(who or "them")[1:-1]))
        now = now or self.now()
        out = []
        if s.get("openers"):
            out.append("You often open with things like: " + ", ".join(f'"{o}"' for o in s["openers"][:5]) + ".")
        if s.get("closers"):
            out.append("You sign off with things like: " + ", ".join(f'"{c}"' for c in s["closers"][:5]) + ".")
        words = (s.get("words_by_block") or {}).get(self.style_block(now))
        if words:
            out.append(f"At this time of day your messages run about {round(words)} words.")
        if s.get("habits"):
            out.append("Your habits: " + ", ".join(s["habits"][:10]) + ".")
        return out

    def style_block(self, now):
        if now.weekday() >= 5 and 7 <= now.hour < 23:
            return "weekend"
        b = self.block_at(now)
        if b in ("work", "lunch"):
            return b
        if 5 <= now.hour < 12:
            return "morning"
        if 12 <= now.hour < 23:
            return "evening"
        return "late"

    def prompt(self, persona, note="", who=None, thread_ok=True):
        """The layered system prompt: who he is; today (one story for everyone); what he's told people; this person;
        maybe one thread; how he writes; then the program's own note. Returns (text, thread id or "")."""
        parts = [persona.rstrip()]
        today = ["Today - the same day for everyone you talk to; keep to it:"] + self.facts(who)
        claims = self.claims_lines(who)
        if claims:
            today += ["Things you've already told people today (stay consistent with them):"] + claims
        parts.append("\n".join(today))
        memories = self.memory_lines()
        if memories:
            parts.append("The last few days, from your journal (you remember them):\n" + "\n".join(memories))
        tid = ""
        if who:
            person = []
            if who in self.data.get("interests", {}):
                person.append(TIERS[self.tier(who)]["line"].format(who=who))
            last = self.last_talked.get(who) or self.data["people"].get(who, {}).get("last")
            if last:
                person.append(f"You last talked to {who} {ago_text(time.time() - float(last))}.")
            remembered = self.person_lines(who)
            if remembered:
                person.append(f"What you remember with {who} (from your journal): " + " / ".join(remembered))
            known = [t["title"] for t in self.data["threads"] if who in t.get("told", {})][-4:]
            if known:
                person.append(f"{who} already knows about: " + "; ".join(known) + ".")
            if thread_ok:
                t, mode = self.thread_for(who)
                if t is not None:
                    tid = t["id"]
                    beat = self.beat(t)
                    facts = (t.get("facts") or "").strip()
                    if mode == "follow":
                        person.append(f"Follow up with {who} on \"{t['title']}\" - they heard about it before. "
                                      + (f"Where it's at now: {beat}" if beat else facts))
                    else:
                        person.append(f"Maybe bring up, only if it fits naturally: \"{t['title']}\". {facts}"
                                      + (f" Where it's at: {beat}" if beat else ""))
            if person:
                parts.append(f"With {who}:\n" + "\n".join(person))
        style = self.style_lines(who)
        if style:
            parts.append("How you write (from your own chats):\n" + "\n".join(style))
        text = "\n\n".join(parts) + (note if note.startswith("\n") else ("\n\n" + note if note else ""))
        return text, tid

    def talked(self, who):
        self.last_talked[who] = time.time()
        self.data["people"].setdefault(who, {})["last"] = time.time()
        self._dirty = True

    def flush(self):
        if self._dirty:
            self.save()


# ---- the consistency check and the claims, through the broker ------------------------------------------------------
CHECK_SYSTEM = ("You read one chat message written by Kithylin and compare it with the facts about his day. You "
                "answer with JSON only.")
CHECK_USER = """Facts about Kithylin's day:
{facts}

What he has already told people today:
{claims}

His new message to {who}:
\"\"\"{text}\"\"\"
{thread}
Answer with a JSON object:
{{"clash": true or false - does the message contradict the facts or what he already told people (say he's
somewhere he isn't, doing something he isn't, or a plan that conflicts)? Small talk, feelings and roleplay actions
in *asterisks* are not clashes,
"why": "if it clashes, what is wrong, in a few words",
"claims": ["each fact or plan he states about HIMSELF in the message, a few words each, e.g. 'about to walk the
dog', 'had pizza for lunch'; [] if none"]{brought}}}"""
REWRITE_NOTE = ("\n\n(Your first try said something that isn't true today: {why}. Write it again, keeping to "
                "today's facts.)")


def partner_is(text, who):
    """A track's partner ('your partner', 'his partner', "Kithylin's partner") as the buddy he's playing with."""
    return re.sub(r"\b(?:your|his|Kithylin's) partner\b", who, text, flags=re.I)


def _json_of(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        d = json.loads(m.group(0))
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


def check(day, who, text, thread=None, done=None, model=None):
    """Ask the residents' model (already on the card) whether the reply keeps to today, and what it claims.
    done({"clash", "why", "claims", "brought_up"}) on the UI thread; {} on failure."""
    from claudecore.ai import ai_models, broker
    claims = day.claims_lines(who) or ["(nothing yet)"]
    thread_line = f"\nA topic he might have mentioned: \"{thread['title']}\"\n" if thread else ""
    brought = (',\n"brought_up": true or false - did he bring up that topic?') if thread else ""
    msgs = [{"role": "system", "content": CHECK_SYSTEM},
            {"role": "user", "content": CHECK_USER.format(facts="\n".join(day.facts(who)), claims="\n".join(claims),
                                                          who=who or "someone", text=text, thread=thread_line,
                                                          brought=brought)}]
    model = model or ai_models.model_for("conversation")
    return broker.get().chat(model, msgs, {"temperature": 0.1, "num_predict": 200},
                             lambda out, err: done({} if err else _json_of(out)), broker.REPLY, think=False)


def polish(text):
    """The last tidy-up: no notes to the reader, no 'as an AI', no doubled sign-off punctuation."""
    lines = []
    for ln in (text or "").splitlines():
        low = ln.strip().lower()
        if low.startswith(("(note:", "note:", "(ooc", "[ooc", "(this message", "(i'm an ai", "as an ai")):
            continue
        lines.append(ln)
    text = "\n".join(lines).strip()
    text = re.sub(r"([!?.])\1{3,}", r"\1\1\1", text)
    return text


def speak(ctx, who, persona, note, history, instruction=None, max_tokens=140, max_lines=None, thread_ok=True,
          temperature=0.9, check=True):
    """Kithylin's next line as a generator step, kept to today: `text = yield from speak(...)`. The layered prompt,
    the voice, then (if the day says so) the check - one rewrite on a clash - and the claims and thread noted."""
    day = getattr(ctx.engine, "day", None)
    if day is None:
        system, tid = persona + note, ""
    else:
        system, tid = day.prompt(persona, note, who=who, thread_ok=thread_ok)
    text = yield from _ask(ctx, system, history, instruction, max_tokens, max_lines, temperature)
    if not text or day is None:
        return text
    if not check or not day.data.get("check_replies", True):        # (a roleplay line isn't a claim about today)
        day.talked(who)
        return polish(text)
    thread = day.thread(tid) if tid else None
    verdict = yield from _check(ctx, day, who, text, thread)
    if verdict.get("clash") and not ctx.stopping:
        why = str(verdict.get("why") or "it doesn't match what you're doing")[:160]
        ctx.note(f"Kept to today's story ({who}): {why}")
        again = yield from _ask(ctx, system + REWRITE_NOTE.format(why=why), history, instruction, max_tokens,
                                max_lines, temperature)
        if again:
            text = again
            verdict = yield from _check(ctx, day, who, text, thread)
    for c in verdict.get("claims") or []:
        if isinstance(c, str) and 2 < len(c) < 120:
            day.claim(who, c.strip())
    if thread is not None and verdict.get("brought_up"):
        day.told(who, thread["id"])
        ctx.note(f"Told {who} about: {thread['title']}")
    day.talked(who)
    day.flush()
    return polish(text)


def _ask(ctx, system, history, instruction, max_tokens, max_lines, temperature=0.9):
    box = {}
    ctx.voice.say(system, history, lambda text: box.__setitem__("text", text), instruction, max_tokens,
                  temperature=temperature)
    yield (lambda: "text" in box, 180)
    text = box.get("text", "")
    if max_lines:
        text = "\n".join(text.splitlines()[:max_lines])
    return text


def _check(ctx, day, who, text, thread):
    box = {}
    try:
        check(day, who, text, thread, lambda r: box.__setitem__("r", r))
    except Exception:
        return {}
    yield (lambda: "r" in box, 90)
    return box.get("r") or {}
