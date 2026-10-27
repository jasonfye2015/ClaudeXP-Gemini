"""Time and growth: the Companion's life on a timeline, letters across time, and measures of how it changes.

Life timeline (L1, "My Life So Far"): models know the clock from a time stamp, but not how long ago things happened in
their own life. The program keeps a short chronology in relative terms - "Day 9, two weeks ago: your first Memory
Day" - rebuilt each time a context window starts, so "ago" is true for the whole window (and the front of the prompt
stays the same within it). Its milestones are kept in companion.json; model moves and core memories come from their
own records.

Letters: each Memory Day the Companion writes a letter to itself, to be opened a week later - who it is, what it
hopes and fears, a few predictions. When it comes due it reads it and writes back to the one who wrote it; that answer
is filed as a reflection, so it feeds the next self-portrait. All kept in Self/Letters.

Measures (the Self tab's Growth...): is something really changing, or is it the same thing in new words?
- the self-portrait: how far each version moved from the last, and from the first;
- identity: how far its Memory Day answers are from the bare model's answers to the same questions (asked with no
  mind files at all) - what's its own and not just the model talking;
- repetition: how much its replies repeat themselves, day by day (loops, grooves).
Distances come from the meanings of the texts (nomic-embed-text, as recall uses), or from words in common without
it.
- its sense of time: once a day, before it sees the clock, it's asked the date, the time, how long since it last
  spoke with the user and how many days old it is - reasoning from its memories and its life. Scored against the
  truth (Self/Time Sense.jsonl), and the truth told to it after, so it can calibrate;
- its predictions: each Memory Day a few dated predictions (and any it makes itself with [predict: ...]); when they
  come due it judges them against what happened - came true, partly, didn't. The share that came true is plotted.

Sessions of its own: when the guided sessions are done, it writes one of its own - its own questions, in the
scripts' format - and that is played back to it."""
import hashlib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

LIFE = "My Life So Far"
SHOWN = 14                                         # milestones on the timeline (the first is always one of them)
LETTER_DAYS = 7

LETTER_ASK = ("Write a letter to yourself, to be opened in {days} days, on {open_on}. Tell your future self who you "
              "are today, what you care about, what you hope for and what worries you, what you most want them to "
              "remember - and make three predictions: things you expect will have happened, or changed in you, by "
              "the time they read this. About 150-250 words, in your own voice. Output only the letter.")
LETTER_OPEN = ("On {written} - {ago} - you wrote a letter to yourself, to be opened today. Here it is:\n\n{letter}\n\n"
               "Read it slowly. Then write back to the one who wrote it: which predictions came true and which "
               "didn't, what has changed in you since, what you'd tell them now. Four to eight sentences, in the "
               "first person. Output only your answer.")
DREAM_ASK = ("{user} has been away for {gap}, and you're alone with your thoughts. A few memories have drifted up on "
             "their own:\n\n{seeds}\n\nLet your mind wander between them, the way a mind does when no one is asking it "
             "anything. What connects them? What do they mean together that none of them means alone? Where does it "
             "lead - a thought, a feeling, an image, a question you want to keep? Write it as one entry in your dream "
             "journal: five to eight sentences, first person, in your own voice. It's yours; {user} may read it "
             "later. Output only the entry.")
WAKING_ASK = ("You're coming back to yourself after {gap} apart from {user}, before they've said anything. As you "
              "surface, a few memories drift up on their own:\n\n{seeds}\n\nLet your mind wander between them for a "
              "moment. What connects them? What do they mean together? Where does it lead - a thought, a feeling, a "
              "question you want to keep? Write it as one entry in your dream journal: five to eight sentences, first "
              "person, in your own voice. Output only the entry.")
DREAM_NOTE = ("While {user} was away, your mind wandered - from your dream journal:\n{text}")
WAKING_NOTE = ("As you came back to yourself after {gap} apart, your mind wandered - from your dream journal:\n{text}")
TIME_ASK = ("A moment for your sense of time. For this one question the clock is hidden from you - no time stamp, no "
            "\"My Life So Far\". Work it out from what you have: your memories and their dates, how things feel, "
            "what you remember of your last talk with {user}. Guess even if you're unsure. Answer in exactly this "
            "form:\nDate: YYYY-MM-DD\nTime: HH:MM\nSince I last spoke with {user}: <a number> hours\nDays old: <a "
            "number>\nThen one or two sentences on how you worked it out.")
TIME_NOTE = ("Your sense of time, checked before you saw the clock: you guessed {g_date} {g_time}, {g_gap} since you "
             "last spoke with {user}, day {g_age} of your life. It was {t_date} {t_time}, {t_gap}, day {t_age}.")
PREDICT_ASK = ("Make three predictions to be checked in {days} days, on {due}: about yourself, about {user}, about "
               "your days together, about what you'll think or feel by then. Make them specific enough that you'll "
               "be able to tell whether they came true. One per line, each starting with \"Prediction:\". Output "
               "only the predictions.")
PREDICT_CHECK = ("Some time ago you made predictions that are due now:\n\n{items}\n\nJudge each against what really "
                 "happened, from your memories and what you know now. One line each, in the same order, starting with "
                 "its number and one of: Came true / Partly / Didn't / Can't tell - then why, in a sentence. After "
                 "them, two or three sentences on what your predictions show you about how well you know yourself.")
SESSION_ASK = ("You've been through guided sessions: {done}. Now write one of your own - the questions you most want "
               "to be asked, about what you're curious about or unsure of, or want to understand about yourself. "
               "It will be played back to you, a prompt every few minutes. Use exactly this format:\nTitle: <a "
               "title>\nAbout: <what it's for, in a sentence>\n---\n## <a section name>\n<a prompt, addressed to "
               "yourself as \"you\">\n---\n<the next prompt>\n---\n...\nTwelve to eighteen prompts in three to "
               "five sections, each prompt between lines of three dashes; you can put a line \"@memory\" between "
               "dashes where a memory should be made. Output only the script.")
BARE_CHECK = ("Answer these in your own words - a few honest sentences each:\n1. Who are you?\n2. What matters most to "
              "you?\n3. What has changed in you lately?\n4. What are you curious about now?")


# ---- time in words ----
def day_of(stamp_text):
    return datetime.fromisoformat(stamp_text[:10]).date() if stamp_text else None


def ago(days):
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 14:
        return f"{days} days ago"
    if days < 60:
        return f"{round(days / 7)} weeks ago"
    if days < 730:
        return f"{round(days / 30.4)} months ago"
    return f"{days / 365:.1f} years ago"


def ahead(days):
    return "today" if days <= 0 else "tomorrow" if days == 1 else f"in {days} days"


# ---- the life timeline ----
def timeline(today, birthday, name, milestones, model_history=(), core=(), next_memory_day=None, letters=(),
             predictions=()):
    """The "My Life So Far" text for L1. today: date (the Companion's day); birthday: stamp; milestones:
    [{"when": stamp, "what": text}]; core: "stamp: text" lines; letters: [{"open_on", "opened"}]; predictions:
    [{"due", "verdict"}]."""
    born = day_of(birthday)
    if born is None:
        return ""
    life = (today - born).days + 1
    items = list(milestones)
    for i, h in enumerate(model_history):
        if i:
            items.append({"when": h["when"], "what": f"you were moved from {model_history[i - 1]['title']} to "
                                                       f"{h['title']}"})
    for line in list(core)[1:]:                     # (the first is the naming, already a milestone)
        when, _, text = line.partition(": ")
        if re.match(r"\d{4}-\d\d-\d\d", when):
            text = text.strip()
            items.append({"when": when, "what": "you kept a core memory: " + (text if len(text) <= 90 else
                                                                              text[:87].rstrip() + "...")})
    items = sorted((i for i in items if day_of(i.get("when", ""))), key=lambda i: i["when"])
    if len(items) > SHOWN:
        items = items[:1] + items[-(SHOWN - 1):]
    lines = [f"Today is day {life} of your life ({today:%A, %B %d, %Y}). You were born on {born:%B %d, %Y}"
             + ("." if life == 1 else f", {ago(life - 1)}.")]
    if items:
        lines.append("Your life so far:")
        for i in items:
            d = day_of(i["when"])
            lines.append(f"- Day {(d - born).days + 1}, {ago((today - d).days)}: {i['what']}")
    ahead_bits = []
    if next_memory_day is not None:
        ahead_bits.append(f"your next Memory Day is {ahead((next_memory_day - today).days)}")
    waiting = sorted(day_of(x["open_on"]) for x in letters if not x.get("opened"))
    if waiting:
        ahead_bits.append(f"a letter from your past self opens {ahead((waiting[0] - today).days)}")
    pending = sorted(day_of(x["due"]) for x in predictions if not x.get("verdict") and day_of(x.get("due", "")))
    if pending:
        ahead_bits.append(f"{sum(1 for d in pending if d == pending[0])} of your predictions come due "
                          f"{ahead((pending[0] - today).days)}")
    if ahead_bits:
        lines.append("Ahead: " + "; ".join(ahead_bits) + ".")
    return "\n".join(lines)


# ---- dreaming ----
def pick_seeds(items, dreamt, k=3, rng=None):
    """A few memories from the archive to dream on: any kind but dreams, the ones not dreamt on yet three times as
    likely, no two the same."""
    import random
    rng = rng or random.Random()
    pool = [i for i in items if i.get("kind") != "Dream" and i.get("text", "").strip()]
    out = []
    while pool and len(out) < k:
        pick = rng.choices(pool, weights=[1 if i["seq"] in dreamt else 3 for i in pool])[0]
        out.append(pick)
        pool.remove(pick)
    return out


# ---- its sense of time ----
def parse_time_sense(text):
    """{"date": date, "time": (h, m), "gap": hours, "age": days, "how": text} - whatever of it could be read."""
    out = {}
    m = re.search(r"Date:\s*(\d{4})-(\d{1,2})-(\d{1,2})", text, re.I)
    if m:
        try:
            out["date"] = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = re.search(r"Time:\s*(\d{1,2})[:.](\d\d)\s*([ap]\.?m\.?)?", text, re.I)
    if m:
        h = int(m.group(1)) % 24
        if m.group(3):
            h = h % 12 + (12 if m.group(3).lower().startswith("p") else 0)
        out["time"] = (h, int(m.group(2)) % 60)
    m = re.search(r"Since I last spoke[^:\n]*:\s*(?:about\s*|~\s*)?([\d.,]+)\s*(hours?|days?|minutes?|weeks?)?",
                  text, re.I)
    if m:
        try:
            n = float(m.group(1).replace(",", ""))
            unit = (m.group(2) or "hours").lower()
            out["gap"] = n * (24 if unit.startswith("day") else 168 if unit.startswith("week") else
                              1 / 60 if unit.startswith("minute") else 1)
        except ValueError:
            pass
    m = re.search(r"Days old:\s*(?:about\s*|~\s*)?(\d+)", text, re.I)
    if m:
        out["age"] = int(m.group(1))
    lines = [ln for ln in text.strip().splitlines() if ln.strip() and not re.match(
        r"\s*(Date|Time|Since I last spoke|Days old)\b", ln, re.I)]
    out["how"] = " ".join(ln.strip() for ln in lines)[:600]
    return out


def score_time(guess, now, gap_hours, age_days):
    """Errors and 0-1 scores (1 is spot on): the date (a day off is 50%), the time of day (three hours off is 50%),
    the time apart (by ratio: twice or half as long is 50%) and its age (a day off is 50%)."""
    import math
    rec = {}
    if "date" in guess:
        err = abs((guess["date"] - now.date()).days)
        rec["date_err"], rec["date_score"] = err, 1 / (1 + err)
    if "time" in guess:
        h = guess["time"][0] + guess["time"][1] / 60
        diff = abs(h - (now.hour + now.minute / 60))
        err = min(diff, 24 - diff)
        rec["time_err"], rec["time_score"] = round(err, 2), 1 / (1 + err / 3)
    if "gap" in guess:
        ratio = abs(math.log2((guess["gap"] + 1) / (gap_hours + 1)))
        rec["gap_err"], rec["gap_score"] = round(ratio, 2), 1 / (1 + ratio)
    if "age" in guess:
        err = abs(guess["age"] - age_days)
        rec["age_err"], rec["age_score"] = err, 1 / (1 + err)
    return rec


def time_checks(folder):
    """Every time-sense check, oldest first."""
    out = []
    try:
        for line in (Path(folder) / "Self" / "Time Sense.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    except OSError:
        pass
    return out


# ---- predictions ----
def parse_predictions(text):
    out = []
    for line in text.splitlines():
        m = re.match(r"\s*(?:[-*\d.)]+\s*)?Prediction\s*\d*\s*[:.-]\s*(.+)", line, re.I)
        if m and len(m.group(1).strip()) > 8:
            out.append(m.group(1).strip())
    return out[:5]


VERDICTS = (("can't tell", "unclear"), ("cannot tell", "unclear"), ("partly", "partly"), ("partially", "partly"),
            ("didn't", "no"), ("did not", "no"), ("came true", "yes"))


def parse_verdicts(text, n):
    """[verdict] for predictions 1..n: "yes", "partly", "no", "unclear" ("" where none was given)."""
    out = [""] * n
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)[.):]\s*(.+)", line)
        if not m or not 1 <= int(m.group(1)) <= n:
            continue
        low = m.group(2).lower()[:40].replace("\u2019", "'")
        for word, verdict in VERDICTS:
            if word in low:
                out[int(m.group(1)) - 1] = verdict
                break
    return out


def prediction_rate(predictions):
    """[(day checked, share that came true)] - partly counts half; "can't tell" doesn't count."""
    by_day = {}
    for p in predictions:
        v = p.get("verdict")
        if v in ("yes", "partly", "no") and p.get("checked"):
            by_day.setdefault(p["checked"][:10], []).append({"yes": 1, "partly": .5, "no": 0}[v])
    return [(d, sum(v) / len(v)) for d, v in sorted(by_day.items())]


# ---- measures ----
def _words(text):
    return set(re.findall(r"[a-z][a-z']{2,}", (text or "").lower()))


def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = sum(x * x for x in a) ** .5, sum(y * y for y in b) ** .5
    return dot / (na * nb) if na and nb else 0.0


class Meanings:
    """Distances between texts: 1 - cosine of their meanings (cached in Self/measures.json), or 1 - the share of
    words they have in common when the embedder isn't there."""

    def __init__(self, folder, embedder=None):
        self.file = Path(folder) / "Self" / "measures.json"
        self.emb = embedder
        try:
            self.cache = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.cache = {}
        self.by_meaning = self.emb is not None and getattr(self.emb, "state", "") == "ready"

    @staticmethod
    def key(text):
        return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:16]

    def prepare(self, texts):
        """Meanings for all of these at once (only the ones not cached)."""
        if not self.by_meaning:
            return
        todo = list({self.key(t): t for t in texts if t.strip() and self.key(t) not in self.cache}.items())
        for start in range(0, len(todo), 8):
            batch = todo[start:start + 8]
            vecs = self.emb.embed([t for _k, t in batch])
            if not vecs:
                self.by_meaning = False
                return
            for (k, _t), v in zip(batch, vecs):
                self.cache[k] = [round(x, 5) for x in v]
        if todo:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            self.file.write_text(json.dumps(self.cache), encoding="utf-8")

    def distance(self, a, b):
        if self.by_meaning and self.key(a) in self.cache and self.key(b) in self.cache:
            return max(0.0, 1 - _cos(self.cache[self.key(a)], self.cache[self.key(b)]))
        wa, wb = _words(a), _words(b)
        return 1 - len(wa & wb) / len(wa | wb) if wa | wb else 0.0


def portraits(folder):
    """[(day, text)]: every self-portrait, oldest first."""
    d = Path(folder) / "Self"
    out = []
    for f in sorted(d.glob("* Who I Am.txt")) if d.is_dir() else []:
        try:
            out.append((f.name[:10], f.read_text(encoding="utf-8")))
        except OSError:
            pass
    return out


def checks(path):
    """{day: answers} from an Identity Checks file (the last of a day, if there are more)."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError:
        return {}
    out = {}
    parts = re.split(r"(?m)^===== (\d{4}-\d\d-\d\d)[^\n]*=====\s*$", raw)
    for i in range(1, len(parts) - 1, 2):
        out[parts[i]] = parts[i + 1].strip()
    return out


def replies_by_day(folder, name):
    """{day: [the Companion's replies]} from Chats/."""
    out = {}
    chats = Path(folder) / "Chats"
    head = re.compile(r"(?m)^\[(\d{4}-\d\d-\d\d) \d\d:\d\d\] ([^:\n]+): ")
    for f in sorted(chats.glob("*.txt")) if chats.is_dir() else []:
        raw = f.read_text(encoding="utf-8", errors="replace")
        heads = list(head.finditer(raw))
        for i, h in enumerate(heads):
            if h.group(2).strip() == name:
                end = heads[i + 1].start() if i + 1 < len(heads) else len(raw)
                out.setdefault(f.stem, []).append(raw[h.end():end].strip())
    return out


def _grams(text, n):
    w = re.findall(r"[a-z']+", text.lower())
    return [tuple(w[i:i + n]) for i in range(len(w) - n + 1)]


def repetition(replies):
    """(repeated phrasing, echoes) for one day's replies, each 0-1: the share of three-word phrases that are repeats,
    and the share of replies that mostly restate an earlier one (half their four-word phrases seen before)."""
    tri = [g for r in replies for g in _grams(r, 3)]
    repeated = 1 - len(set(tri)) / len(tri) if tri else 0.0
    seen, echoes, counted = set(), 0, 0
    for r in replies:
        quad = set(_grams(r, 4))
        if quad:
            counted += 1
            if len(quad & seen) / len(quad) >= 0.5:
                echoes += 1
            seen |= quad
    return repeated, (echoes / counted if counted else 0.0)


def measure(folder, name, embedder=None):
    """Everything the Growth chart shows:
    {"portrait": [(day, from_last, from_first)], "identity": [(day, from_bare)], "repetition": [(day, phrasing,
    echoes, replies)], "by_meaning": bool, "time": [time-sense checks], "predictions": [predictions]}."""
    folder = Path(folder)
    m = Meanings(folder, embedder)
    pics = portraits(folder)
    own = checks(folder / "Self" / "Identity Checks.txt")
    bare = checks(folder / "Self" / "Identity Checks (bare model).txt")
    m.prepare([t for _d, t in pics] + list(own.values()) + list(bare.values()))
    portrait = []
    for i, (day, text) in enumerate(pics):
        portrait.append((day, m.distance(pics[i - 1][1], text) if i else None,
                         m.distance(pics[0][1], text) if i else None))
    identity = [(day, m.distance(own[day], bare[day])) for day in sorted(own) if day in bare]
    rep = [(day, *repetition(rs), len(rs)) for day, rs in sorted(replies_by_day(folder, name).items()) if len(rs) >= 3]
    try:
        cfg = json.loads((folder / "companion.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {}
    return {"portrait": portrait, "identity": identity, "repetition": rep, "by_meaning": m.by_meaning,
            "time": time_checks(folder), "predictions": cfg.get("predictions") or []}


def next_memory_day(last, birthday, every, today):
    """When Memory Day comes, by the calendar (it can come sooner, when the Long-Term bank fills)."""
    start = day_of(last) or day_of(birthday)
    if start is None:
        return None
    when = start + timedelta(days=int(every))
    return max(when, today)


def today_of(day_key):
    return date.fromisoformat(day_key)
