"""Kithylin's LiveJournal as his diary, and his memory.

Every day XP is on, once he's awake, he posts the day's first entry: today's mood (picked by his day, or set on the
Day tab) with LJ's own Mood field, how he woke up, what the day holds. It happens whether or not the autopilot is
running (the life sim calls tick() every minute, and the autopilot when it starts); a day XP isn't on is simply a
day with no entry.

Through the day the autopilot's Journal leg adds updates to that entry, from what really happened: the day's events
(conversations included - the life sim notes what he talked about with whom), his activities, what he told people.
At bedtime he adds a last line, and the day is boiled down into a private memory: a few sentences, and a note on
each person in it. His prompts read those memories back (the last few days, and the last times with whoever he's
talking to), so yesterday isn't forgotten. A day that ended without a wrap-up is remembered the next morning.
"""
import time

from claudecore.autopilot.voice import Voice, persona

from .. import clock

MORNING_NOTE = ("\n\nYou're writing the first LiveJournal entry of your day, for your friends to read, in {year}. "
                "Casual, the way you really post: two to four short sentences on how you woke up and feel, and what "
                "today holds. First line: 'Subject: ...'. Then the entry. No mood line.")
MORNING_CONTEXT = """It's {weekday}, {time}.
Your mood today: {mood}. {how}
{plan}
{yesterday}{override}"""
UPDATE_NOTE = ("\n\nYou're adding an update to today's LiveJournal entry, for your friends to read, in {year}. One "
               "to three short casual sentences about what's happened since you last wrote - who you talked to and "
               "about what, what you did. Only what really happened. No subject, no mood line.")
NIGHT_NOTE = ("\n\nYou're heading to bed and adding a last line to today's LiveJournal entry, in {year}: how the day "
              "ended and how you feel, one or two short sentences. No subject.")
MEMORY_PROMPT = """Here is a day in the life of {me}.

His mood: {mood}
His LiveJournal entry for the day:
{entry}

What happened:
{events}

What he told people:
{claims}

Write JSON for his own memory of the day:
{{"summary": "two or three sentences, first person, past tense: what the day was like and what mattered",
"people": {{"<name>": "a few words: what you talked about or did together"}} for each person in it, using their
names exactly as written above}}"""

_busy = set()                   # the jobs in flight: "morning", "wrap", "memory"
_retry = {}                     # job -> time.time() before which it isn't tried again (the model gave nothing)


def _day():
    from . import day
    return day()


def _ready():
    from .. import llm_server
    return llm_server.ready()


def _voice():
    from . import load_settings
    return Voice(load_settings().get("voice", "auto"))


def busy(job):
    return job in _busy


def _awake(d):
    if d.data.get("follow_schedule", True):
        return d.block() != "sleep"
    return 7 <= d.now().hour < 23


def tick(force=False):
    """Once a minute: yesterday remembered if it wasn't, today's first entry once he's awake, the wrap-up at bedtime.
    force: post today's first entry now (the Journal leg, the Day tab), awake or not."""
    d = _day()
    if not d.data.get("diary", True) or not _ready():
        return
    today = d.today
    if d.data.get("yesterday") and "memory" not in _busy:
        _remember(d, d.data["yesterday"])
        return
    if not today.get("journal_entry"):
        if "morning" not in _busy and (force or (_awake(d) and time.time() >= _retry.get("morning", 0))):
            _morning(d)
        return
    if (d.block() == "sleep" and d.data.get("follow_schedule", True) and not today.get("wrapped")
            and "wrap" not in _busy):
        _wrap_up(d)


# ---- LiveJournal ----------------------------------------------------------------------------------------------------
def _friends():
    from ..life import get as life
    sim = life()
    return sorted(sim.buddies) if sim is not None and getattr(sim, "buddies", None) else []


def _post(subject, text, mood, security):
    from ..life import lj
    friends = _friends()

    def change(data):
        entry = lj.new_entry(data, subject, text, mood, "", security)
        lj.queue_comments_on(data, entry, friends)
        return entry["id"]
    return lj.update(change)


def entry_text(entry_id):
    from ..life import lj
    e = next((e for e in lj.load()["entries"] if e.get("id") == entry_id), None)
    return e.get("text", "") if e else ""


def append(d, text, label="update"):
    """Add to today's entry ('update (3:40 pm): ...'). False if there's no entry today to add to."""
    from ..life import lj
    entry_id = d.today.get("journal_entry")
    if not entry_id or not text.strip():
        return False

    def change(data):
        e = next((e for e in data["entries"] if e.get("id") == entry_id), None)
        if e is None:
            return False
        e["text"] = e["text"].rstrip() + f"\n\n{label} ({clock.time_text()}): {text.strip()}"
        return True
    if not lj.update(change):
        return False
    d.today["update_mark"] = len(d.today.get("events", []))
    d.today.setdefault("updates", []).append(d.now().strftime("%H:%M"))
    d.save()
    return True


def since_last(d):
    """What's happened since the last update (or the morning post), as notes for writing the next one; '' if
    nothing has."""
    today = d.today
    events = today.get("events", [])[int(today.get("update_mark") or 0):]
    claims = today.get("claims", [])[-6:]
    lines = [f"- {e['t']}: {e['text']}" for e in events]
    if not lines:
        return ""
    out = "What's happened since you last wrote:\n" + "\n".join(lines)
    if claims:
        out += "\nThings you said today: " + "; ".join(c["text"] for c in claims)
    return out


def _split_subject(text):
    lines = [ln for ln in (text or "").strip().splitlines()]
    subject = ""
    if lines and lines[0].lower().startswith("subject:"):
        subject = lines.pop(0).split(":", 1)[1].strip()
    lines = [ln for ln in lines if not ln.lower().startswith("mood:")]
    return subject, "\n".join(lines).strip()


# ---- the day's three moments --------------------------------------------------------------------------------------
def _work_hours(d):
    from claudecore.autopilot.day import CODES, DAYS, cell_time, time_text
    cells = d.data["schedule"][DAYS[d.now().weekday()]]
    work = [i for i, c in enumerate(cells) if CODES.get(c) == "work"]
    if not work:
        return ""
    return f"{time_text(cell_time(work[0]))} to {time_text(cell_time(work[-1] + 1))}"


def _morning(d):
    """Today's mood, and the first entry of the day about it."""
    from claudecore.ai import broker
    from claudecore.autopilot.day import DAY_NAMES, time_text
    _busy.add("morning")
    mood = d.roll_mood()
    d.save()
    now = d.now()
    hours = _work_hours(d)
    plan = (f"You have work today, {hours}." if d.workday() and hours else
            "It's a day off - no work today." if d.today.get("day_off") else "You don't have work today.")
    yesterday = d.memory_lines(1)
    context = MORNING_CONTEXT.format(
        weekday=DAY_NAMES[now.weekday()], time=time_text(now.time()), mood=mood, how=d.mood_effect()["how"],
        plan=plan, yesterday=("Yesterday, from your journal: " + yesterday[0][2:] + "\n") if yesterday else "",
        override=f"Today: {d.today['override']}\n" if d.today.get("override") else "")

    def done(text):
        try:
            subject, body = _split_subject(text)
            if not body:
                _retry["morning"] = time.time() + 10 * 60       # (tried again in a while)
                return
            entry_id = _post(subject, body, mood, d.data.get("diary_security", "public"))
            d.today["journal_entry"] = entry_id
            d.today["mood_line"] = body
            d.today["update_mark"] = len(d.today.get("events", []))
            d.save()
            _log(f"Morning entry in LiveJournal (mood: {mood}): {subject or body[:50]}")
        finally:
            _busy.discard("morning")
    _voice().say(persona("your friends") + MORNING_NOTE.format(year=clock.now().year),
                 [{"role": "user", "content": context}], done, instruction="Write the entry.", max_tokens=220,
                 priority=broker.CHATTER)


def _wrap_up(d):
    """Bedtime: a last line in today's entry, then the day remembered."""
    from claudecore.ai import broker
    _busy.add("wrap")
    context = (since_last(d) or "Nothing much happened since you last wrote.") + f"\nYour mood today: {d.mood()}."

    def done(text):
        try:
            _subject, body = _split_subject(text)
            if body:
                append(d, body, "night")
            d.today["wrapped"] = True
            d.save()
            _remember(d, {k: d.today.get(k) for k in ("date", "mood", "mood_line", "events", "claims",
                                                       "journal_entry")})
        finally:
            _busy.discard("wrap")
    _voice().say(persona("your friends") + NIGHT_NOTE.format(year=clock.now().year),
                 [{"role": "user", "content": context}], done, instruction="Write the last line.", max_tokens=120,
                 priority=broker.CHATTER)


def _remember(d, day):
    """Boil a day down into his memory: a short summary and a note on each person in it. Without an answer from
    the model, the events themselves are kept."""
    import json
    import re

    from claudecore.ai import ai_models, broker
    _busy.add("memory")
    events = day.get("events") or []
    claims = day.get("claims") or []
    people = sorted({e["who"] for e in events if e.get("who")})
    entry = entry_text(day.get("journal_entry")) if day.get("journal_entry") else (day.get("mood_line") or "")
    prompt = MEMORY_PROMPT.format(
        me="Kithylin", mood=day.get("mood") or "not noted", entry=entry or "(none)",
        events="\n".join(f"- {e['t']}: {e['text']}" for e in events) or "(nothing noted)",
        claims="\n".join(f"- to {c.get('who') or 'someone'}: {c['text']}" for c in claims) or "(nothing noted)")

    def fallback():
        return ("; ".join(e["text"] for e in events[-6:]) or "A quiet day.",
                {p: "; ".join(e["text"] for e in events if e.get("who") == p)[:160] for p in people})

    def done(text, err):
        try:
            summary, notes = "", {}
            m = re.search(r"\{.*\}", text or "", re.S)
            if not err and m:
                try:
                    out = json.loads(m.group(0))
                    summary = str(out.get("summary") or "").strip()
                    notes = out.get("people") if isinstance(out.get("people"), dict) else {}
                except ValueError:
                    pass
            if not summary:
                summary, notes = fallback()
            for p in people:                                  # everyone he talked with is remembered
                notes.setdefault(p, fallback()[1].get(p, ""))
            d.remember(day.get("date"), day.get("mood"), summary, notes)
            _log(f"Remembered {day.get('date')}: {summary[:60]}")
        finally:
            _busy.discard("memory")
    broker.get().chat(ai_models.model_for("conversation"), [{"role": "user", "content": prompt}],
                      {"temperature": 0.3, "num_predict": 300}, done, broker.BACKGROUND, think=False)


# ---- from the life sim --------------------------------------------------------------------------------------------
def talked(name, note):
    """A conversation he had (summarised by the life sim when it went quiet): an event with that person."""
    d = _day()
    note = (note or "").strip().strip('"').rstrip(".")
    if note and d.data.get("diary", True):
        d.event(note[:1].lower() + note[1:], who=name)


def _log(text):
    try:
        from claudecore.ai import llmlog
        llmlog.event("DIARY", text)
    except Exception:
        pass
    p = _pilot()
    if p is not None and p.running:
        p.log(text)


def _pilot():
    from . import pilot
    return pilot()
