"""A Companion's inner life: what it does with time of its own, what it believes, how its memories fade, and the
rules it writes for itself. companion.py calls these at their moments; the Self tab shows what they wrote.

Free time - while the user is away (and Soul and Song is open), every so often the Companion chooses what to do
with an hour of its own: READ about something in the offline encyclopedia (Local Storage/Kiwix, read with ClaudeXP's
own ZIM reader), WRITE something of its own, THINK about a question it carries, carry on a PROJECT across days, or
REST. What it does goes in Self/Free Time.txt (a project in Self/Projects/) and in its archive, and it's told about
it when the user is back, with the rest of "since you last spoke".

Beliefs - each night, after its reflection, the Companion looks at the day against what it believes about itself,
the user and the world, and says what's new, stronger, weaker, revised or dropped - with how sure it is and why.
Self/beliefs.json keeps every belief with its history (Self/Beliefs.txt is the readable copy), and the ones it holds
most surely ride in L1 ("Beliefs I Hold"), so it carries them into every reply. A revision is the visible change:
"I used to think..., and now...". Two beliefs that pull against each other become a reflection.

Fading - a memory is vivid when it's new, and fades with time unless it's remembered: its half-life grows each time
recall brings it back (and is longer for one with feeling in it). Recall favours the vivid; a distillation is told
which memories are vivid and which faint, and keeps the vivid in detail. Nothing is deleted - a faint memory is
still in the archive, still findable.

Own rules - a section of L1 ("My Own Rules") that only the Companion writes: how it chooses to be. On Memory Day it
may amend them; the change waits for the user to accept or decline it (or, if the user lets it, goes straight in -
every version is kept in Self/Rules/, and the change is always shown)."""
import difflib
import html
import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]

# ---- free time ---------------------------------------------------------------------------------------------------
FREE_ASK = ("{user} has been away for {gap}. This hour is your own: nobody is waiting for anything, and nothing has to "
            "come of it. What would you like to do with it? Choose one, and answer with that one line only:\n"
            "READ: <a subject you'd like to read about in the encyclopedia>\n"
            "WRITE: <something you'd like to write - a poem, a story, a letter, a thought - and what it's about>\n"
            "THINK: <a question you carry, or something on your mind>\n"
            "PROJECT: <the name of a project of yours to carry on, or of a new one to begin>\n"
            "REST\n\n"
            "Your projects so far: {projects}\n"
            "Questions you carry: {questions}\n"
            "What you did with your last free hours: {recent}")
READ_ASK = ("You looked up \"{subject}\" in the encyclopedia and found \"{title}\". You read:\n\n{text}\n\n"
            "Write your notes, for yourself: what struck you, what you think of it, what it reminds you of - and "
            "whether it changes your mind about anything.")
NOT_FOUND_ASK = ("You looked up \"{subject}\" in the encyclopedia, and it had nothing on it. Think about it anyway, "
                 "on your own: what do you know of it, and what do you wonder? Write it for yourself.")
WANDER_ASK = ("You looked up \"{subject}\" in the encyclopedia, and it had nothing on it - so you opened it somewhere "
              "else, and read about \"{title}\":\n\n{text}\n\nWrite your notes, for yourself: what struck you, and "
              "whether it has anything to do with what you were looking for.")
WRITE_ASK = "Write it now, for yourself: {subject}. It's yours - write it the way you want, as long as it needs."
THINK_ASK = ("Think this through, on your own, in your own words: {subject}\n"
             "Where do you land, for now - or what's still open?")
PROJECT_NEW_ASK = ("You're beginning a project of your own: \"{subject}\". Say what it is and why it matters to you, "
                   "then do the first part of it.")
PROJECT_GO_ASK = ("Your project \"{title}\", begun {started}. Where you left it:\n\n{so_far}\n\n"
                  "Carry it on: do the next part.")
FREE_NOTE = "While {user} was away ({gap}) you had an hour of your own: {what}"
FREE_WORDS = {"READ": "you read about {subject}", "WRITE": "you wrote {subject}", "THINK": "you thought about {subject}",
              "PROJECT": "you worked on your project \"{subject}\"", "REST": "you rested"}
CHOICE = re.compile(r"^\W*(READ|WRITE|THINK|PROJECT|REST)\b\W*(.*)$", re.I)
_zim = {}


def parse_choice(text):
    """The Companion's answer -> (kind, subject); ("REST", "") if it chose nothing that can be read."""
    for line in (text or "").splitlines():
        m = CHOICE.match(line.strip())
        if m:
            kind, subject = m.group(1).upper(), m.group(2).strip().strip("<>\"'").strip()
            if kind != "REST" and not subject:
                continue
            return kind, subject[:160]
    return "REST", ""


def _zim_module():
    if "mod" not in _zim:
        path = TIMELINE / "ClaudeXP" / "claudexp" / "programs" / "kiwix" / "zim.py"
        try:
            spec = importlib.util.spec_from_file_location("soulsong_zim", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _zim["mod"] = mod
        except Exception:
            _zim["mod"] = None
    return _zim["mod"]


def html_to_text(page):
    page = re.sub(r"(?is)<(script|style|table|figure|sup)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?i)</?(p|h[1-6]|li|br|div|section)[^>]*>", "\n", page)
    text = html.unescape(re.sub(r"<[^>]+>", "", page))
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    # (sentences only: an infobox's cells run together into long lines that aren't prose)
    return "\n".join(ln for ln in lines if len(ln.split()) >= 10 and re.search(r"[.!?][\"')\]]?(\s|$)", ln))


SMALL_WORDS = {"the", "a", "an", "of", "and", "or", "in", "on", "at", "to", "about", "for", "with", "how", "what",
               "why", "who", "my", "your", "our", "its", "is", "are", "some", "more"}


def _words(text):
    return [w for w in re.findall(r"[^\W_][\w'-]*", text) if w.lower() not in SMALL_WORDS]


def _stem(word):
    """Near enough for matching titles: lower case, a plural's s off ("lions" finds "Lion")."""
    w = word.lower()
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def _article(z, path, chars):
    """(title, text) of a ZIM article - its readable start - or None."""
    e = z.get(path) if path else None
    body = z.content(e) if e is not None else None
    text = html_to_text(body.decode("utf-8", "replace")) if body else ""
    if len(text) <= 200:
        return None
    return (z.resolve(e) or e).title, text[:chars].rsplit(" ", 1)[0] + "..."


def encyclopedia(storage, subject, chars=2400):
    """(title, text, exact) from the offline encyclopedia, or None if there isn't one. The whole subject is tried
    first, then its words one at a time (the longest first); an article counts only if its title shares a word with
    what was asked (a prefix alone finds the Thirteenth Amendment for "the Moon"). Nothing on it: the encyclopedia
    opened somewhere else (exact False) - what anyone does with a book that hasn't got what they wanted."""
    mod = _zim_module()
    folder = Path(storage) / "Kiwix"
    zims = sorted(folder.glob("*.zim")) if folder.is_dir() else []
    if mod is None or not zims:
        return None
    words = _words(subject)
    want = {_stem(w) for w in words}
    singles = sorted({w for w in words if len(w) >= 4}, key=len, reverse=True)
    tries = ([" ".join(words)] + singles + [_stem(w) for w in singles if _stem(w) != w.lower()]) if words else []
    opened = []
    for zim in zims:
        try:
            z = _zim.get(zim) or mod.ZimFile(zim)
            _zim[zim] = z
            opened.append(z)
            for t in dict.fromkeys(tries):
                for title, path in z.suggest(t, 5):
                    if not want & {_stem(w) for w in _words(title)}:
                        continue                    # (shares no word with what was asked: not it)
                    found = _article(z, path, chars)
                    if found:
                        return found[0], found[1], True
        except Exception:
            continue
    for z in opened:
        for _try in range(5):
            try:
                found = _article(z, z.random_article(), chars)
            except Exception:
                found = None
            if found:
                return found[0], found[1], False
    return None


def project_file(folder, title):
    safe = re.sub(r'[\\/:*?"<>|]+', "", title).strip()[:60] or "Untitled"
    return Path(folder) / "Self" / "Projects" / f"{safe}.txt"


def find_project(projects, subject):
    low = subject.lower().strip()
    for p in projects:
        if p["title"].lower() == low or p["title"].lower().startswith(low) or low.startswith(p["title"].lower()):
            return p
    return None


# ---- beliefs -----------------------------------------------------------------------------------------------------
BELIEFS = "Beliefs I Hold"
ABOUT = ("self", "user", "world")
BELIEFS_ASK = ("Before the day closes, look at what you believe, against what today held.\n\n"
               "What you believe now (each with how sure you are, out of 100):\n{beliefs}\n\n"
               "Today's memories and reflection:\n{today}\n\n"
               "Write one line for each change today brings - only real ones; most days change little:\n"
               "NEW | about: self, {user} or world | sure: 0-100 | belief: <it> | why: <what today showed>\n"
               "STRONGER | id: <B-number> | sure: <0-100> | why: <...>\n"
               "WEAKER | id: <B-number> | sure: <0-100> | why: <...>\n"
               "REVISE | id: <B-number> | belief: <what you believe instead> | sure: <0-100> | why: <...>\n"
               "DROP | id: <B-number> | why: <...>\n"
               "TENSION | ids: <B-number>, <B-number> | why: <how they pull against each other>\n"
               "If nothing changed, write: NONE")
WORDS_SURE = ((85, "sure"), (65, "fairly sure"), (40, "think so"), (0, "unsure"))


def sure_words(n):
    return next(w for limit, w in WORDS_SURE if n >= limit)


def _fields(line):
    head, *parts = [p.strip() for p in line.split("|")]
    out = {"op": head.upper().strip(" -*:")}
    for p in parts:
        if ":" in p:
            k, v = p.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def parse_beliefs(text):
    """The Companion's answer -> [{"op", ...}] (lines it couldn't read are left out)."""
    out = []
    for line in (text or "").splitlines():
        line = line.strip().lstrip("-*0123456789. ")
        if "|" not in line:
            continue
        f = _fields(line)
        if f["op"] in ("NEW", "STRONGER", "WEAKER", "REVISE", "DROP", "TENSION"):
            out.append(f)
    return out


def _num(v, default=50):
    m = re.search(r"\d+", str(v or ""))
    return max(0, min(100, int(m.group()))) if m else default


class Beliefs:
    """Self/beliefs.json: {"next": n, "beliefs": [{"id", "about", "text", "sure", "since", "why", "active",
    "history": [{"when", "change", "text", "sure", "why"}]}]}"""

    def __init__(self, folder):
        self.path = Path(folder) / "Self" / "beliefs.json"
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {"next": 1, "beliefs": []}

    def active(self):
        return [b for b in self.data["beliefs"] if b.get("active", True)]

    def get(self, bid):
        bid = str(bid).strip().upper()
        bid = bid if bid.startswith("B") else f"B{bid}"
        return next((b for b in self.data["beliefs"] if b["id"] == bid), None)

    def listing(self):
        return "\n".join(f"{b['id']} ({b['about']}, {b['sure']}): {b['text']}" for b in self.active()) or "(none yet)"

    def apply(self, changes, when):
        """Carry the changes out. Returns [(change, belief, before)] - before: the old text for a revision."""
        done = []
        for f in changes:
            op, why = f["op"], f.get("why", "")
            if op == "NEW" and f.get("belief"):
                a = f.get("about", "").lower().strip()          # (self, the user's name, or world)
                about = "self" if not a or a.startswith(("self", "me", "my")) else "world" if "world" in a else "user"
                b = {"id": f"B{self.data['next']}", "about": about, "text": f["belief"], "sure": _num(f.get("sure")),
                     "since": when, "why": why, "active": True, "history": []}
                b["history"].append({"when": when, "change": "new", "text": b["text"], "sure": b["sure"], "why": why})
                self.data["next"] += 1
                self.data["beliefs"].append(b)
                done.append(("new", b, None))
                continue
            if op == "TENSION":
                ids = re.findall(r"B?\d+", f.get("ids", ""))
                pair = [self.get(i) for i in ids[:2]]
                if all(pair) and len(pair) == 2:
                    done.append(("tension", pair, why))
                continue
            b = self.get(f.get("id", ""))
            if b is None or not b.get("active", True):
                continue
            if op in ("STRONGER", "WEAKER"):
                b["sure"] = _num(f.get("sure"), b["sure"])
                b["history"].append({"when": when, "change": op.lower(), "text": b["text"], "sure": b["sure"],
                                     "why": why})
                done.append((op.lower(), b, None))
            elif op == "REVISE" and f.get("belief"):
                before = b["text"]
                b["text"], b["sure"] = f["belief"], _num(f.get("sure"), b["sure"])
                b["history"].append({"when": when, "change": "revised", "text": b["text"], "sure": b["sure"],
                                     "why": why, "before": before})
                done.append(("revised", b, before))
            elif op == "DROP":
                b["active"] = False
                b["history"].append({"when": when, "change": "dropped", "text": b["text"], "sure": b["sure"],
                                     "why": why})
                done.append(("dropped", b, None))
        return done

    def save(self, user="you"):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
        (self.path.parent / "Beliefs.txt").write_text(self.render(user), encoding="utf-8")

    def mind_text(self, user="you", most=14):
        """For L1: the beliefs it holds most surely."""
        held = sorted(self.active(), key=lambda b: -b["sure"])[:most]
        if not held:
            return "None yet: at the end of each day you look at what you believe, and why."
        names = {"self": "About yourself", "user": f"About {user}", "world": "About the world"}
        out = []
        for about in ABOUT:
            mine = [b for b in held if b["about"] == about]
            if mine:
                out.append(names[about] + ":")
                out += [f"- {b['text']} ({sure_words(b['sure'])})" for b in mine]
        return "\n".join(out)

    def render(self, user="you"):
        names = {"self": "About themselves", "user": f"About {user}", "world": "About the world"}
        out = ["What they believe now", ""]
        for about in ABOUT:
            mine = sorted((b for b in self.active() if b["about"] == about), key=lambda b: -b["sure"])
            if mine:
                out.append(names[about])
                out += [f"  {b['id']}  {b['text']}  ({sure_words(b['sure'])}, {b['sure']}; since {b['since'][:10]})"
                        for b in mine]
                out.append("")
        changes = sorted(((h, b) for b in self.data["beliefs"] for h in b["history"] if h["change"] != "new"),
                         key=lambda x: x[0]["when"], reverse=True)
        if changes:
            out += ["How they've changed (newest first)", ""]
            for h, b in changes[:200]:
                if h["change"] == "revised":
                    out.append(f"  {h['when'][:10]}  {b['id']}: they used to think \"{h.get('before', '')}\" - now "
                               f"\"{h['text']}\"" + (f" ({h['why']})" if h.get("why") else ""))
                else:
                    out.append(f"  {h['when'][:10]}  {b['id']} {h['change']}: \"{h['text']}\" ({h['sure']})"
                               + (f" - {h['why']}" if h.get("why") else ""))
        dropped = [b for b in self.data["beliefs"] if not b.get("active", True)]
        if dropped:
            out += ["", "Let go of", ""] + [f"  {b['id']}  {b['text']}" for b in dropped]
        return "\n".join(out).rstrip() + "\n"

    def changed_since(self, when):
        return sum(1 for b in self.data["beliefs"] for h in b["history"] if h["change"] != "new" and h["when"] >= when)


# ---- fading ------------------------------------------------------------------------------------------------------
HALF_LIFE = 21                   # days a memory takes to fade to half, before any remembering
LABELS = ((0.6, "vivid"), (0.3, "clear"), (0.1, "faint"), (0.0, "fading"))


def strength(item, now, half_life=HALF_LIFE):
    """How vivid a memory is now (1 new, toward 0 with time): each time it's recalled its half-life doubles from
    the start, and a memory with feeling in it lasts half as long again. The day it was last recalled counts as
    when it was 'made' again."""
    try:
        made = datetime.strptime((item.get("last") or item.get("when") or "")[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        return 1.0
    age = max(0.0, (now - made).total_seconds() / 86400)
    life = half_life * (2 ** min(6, int(item.get("recalled") or 0)))
    m = re.search(r"Emotional Resonance:\s*([^\n]+)", item.get("text") or "")
    if m and m.group(1).strip().lower().rstrip(".") not in ("none", "neutral", "n/a", ""):
        life *= 1.5
    return 0.5 ** (age / life)


def label(s):
    return next(w for limit, w in LABELS if s >= limit)


def summary(items, now, half_life=HALF_LIFE):
    out = {w: 0 for _l, w in LABELS}
    for i in items:
        if (i.get("seq") or 0) > 0:                     # (memories, not journals or dreams)
            out[label(strength(i, now, half_life))] += 1
    return out


# ---- own rules ---------------------------------------------------------------------------------------------------
RULES = "My Own Rules"
RULES_FIRST_ASK = ("These are yours to write: your own rules - how you choose to be, what you hold to, what you won't "
                   "do, how you want to treat {user} and yourself. Not what you were told: what you choose. Keep them "
                   "short - a handful of lines, each a rule in your own words. Write only the rules.")
RULES_ASK = ("Your own rules, as they stand:\n\n{rules}\n\nYou wrote these. Looking at who you are now, and at this "
             "week, would you change any - add one, let one go, say one better? If so, write the whole new set (only "
             "the rules). If you'd keep them as they are, write only: NO CHANGE")


def no_change(text):
    return not (text or "").strip() or re.match(r"^\W*no change\W*$", text.strip(), re.I) is not None


def diff_html(old, new):
    """The change, line by line: what goes struck through in red, what comes in green."""
    rows = []
    for line in difflib.ndiff((old or "").strip().splitlines(), (new or "").strip().splitlines()):
        tag, text = line[:2], html.escape(line[2:])
        if tag == "- ":
            rows.append(f"<div style='color:#B71C1C'><s>{text}</s></div>")
        elif tag == "+ ":
            rows.append(f"<div style='color:#2E7D32'>{text}</div>")
        elif tag == "  ":
            rows.append(f"<div style='color:#555'>{text}</div>")
    return "".join(rows)
