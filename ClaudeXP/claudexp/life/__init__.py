"""The living world: buddies' lives move on, they remember conversations across programs, and
they reach out to you.

- Journals (data/journals/<name>.json): dated notes about each buddy's life, plus notes about
  conversations with the user in any program. Every program adds the recent entries to the
  buddy's prompt (see context()), so what you said on IRC is remembered on AIM.
- Story ticks: about once an hour, one buddy's life moves forward (a new journal note). Sometimes
  they tell you about it: an AIM IM or IRC private message if they can, otherwise an email.
- Catch-up: after the PC was off, a few notes (and maybe an email) are written at login. That batch
  of background work is what Windows Update / the virus scanner hide behind.

All model work here runs at the broker's BACKGROUND priority.
"""
import random
import re
import threading
import time
from collections import namedtuple
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer, Signal

from .. import broker, clock, network, sound
from ..paths import DATA
from ..programs.people import load_buddies, load_json, save_json

JOURNAL_DIR = DATA / "journals"
MAIL_FILE = DATA / "mail.json"
STATE_FILE = DATA / "life.json"
TICK_MS = 60 * 1000
STORY_MINUTES = (45, 90)        # real minutes between story ticks while ClaudeXP is on
REACH_OUT_CHANCE = 0.4          # after a story tick, chance they tell you about it
TALK_IDLE_MINUTES = 6           # a conversation this quiet gets summarised into the journal
CATCH_UP_MIN_HOURS = 0.5        # PC off at least this long -> catch up at login
CATCH_UP_MAX_JOBS = 7
CONTEXT_ENTRIES = 8

STORY_PROMPT = """You are {name}. It is {now}, in 2001.
About you:
{persona}

Your recent diary notes (oldest first):
{notes}

{since}Write ONE new short diary note (one or two sentences, first person, casual) about something that happened in your life {when}: work or school, hobbies, friends, fandom, a con, something you bought, a small drama, a plan. Keep it consistent with who you are and with your earlier notes, and make it the kind of thing you might mention to a friend. It must be about your own life: do not invent conversations or events with {user} that aren't in your notes. Write only the note."""

TALK_PROMPT = """You are {name}. Here is a conversation you just had with your friend {user} on {program}:

{lines}

Write a one or two sentence note for your own diary about it, first person, focusing on anything worth remembering about {user} (news, plans, feelings, things you promised or asked). Always call them {user}, never he/she. Write only the note."""

MY_TALK_PROMPT = """Here is a conversation between {user} and {name} on {program}:

{lines}

In under fifteen words, note what they talked about, for {user}'s own day log, first person, starting "talked with {name} about". Write only the note."""


def _my_diary(name, note):
    """The conversation, for Kithylin's own day (his diary and memory: claudexp.autopilot.diary)."""
    try:
        from ..autopilot import diary
        diary.talked(name, note.splitlines()[0])
    except Exception:
        pass


EMAIL_PROMPT = """You are {name}, writing a short casual email to your friend {user} in 2001 (it is {now}).
About you:
{persona}

Your recent diary notes:
{notes}

Write the email about this: {topic}
Only mention things you did together with {user} if your notes say so; don't invent past conversations. Format: first line exactly "Subject: <subject>", then a blank line, then the email body (plain text, one to four short paragraphs, the way you talk), signed with your name. No markdown."""

REPLY_PROMPT = """You are {name}, answering an email from your friend {user} in 2001 (it is {now}).
About you:
{persona}

Your recent diary notes:
{notes}

{user}'s email to you, subject "{subject}":
{body}

Write your reply, the way you'd really answer them: respond to what they said and asked, share a little of your own news if it fits. Only mention things you did together with {user} if your notes say so. Format: first line exactly "Subject: <subject>" (usually "Re: " and their subject), then a blank line, then the email body (plain text, one to four short paragraphs), signed with your name. No markdown."""

MAIL_REPLY_MINUTES = (2, 9)      # how long a buddy takes to answer an email (while they're awake)

REACH_OUT = ("Message {user} first to tell them about something that just happened in your life: {topic} "
             "Keep it natural and short, like an IM between friends.")

MAIL_DOMAIN = "hotmail.com"     # everyone's on MSN Hotmail
mail_lock = threading.RLock()    # the mailbox is also used by the Hotmail web server's thread

# Anyone who can get email: AIM buddies (contact set) and the IRC/MUCK regulars (hours = their waking window).
Person = namedtuple("Person", "name persona hours contact")


def _slug(name):
    return "".join(ch if ch.isalnum() else "_" for ch in name)


def _date_text(when=None):
    now = when or clock.now()
    return f"{now:%a %b} {now.day}"


def email_address(name):
    return f"{re.sub(r'[^a-z0-9]', '', name.lower()) or 'user'}@{MAIL_DOMAIN}"


def _minutes(text):
    h, _, m = str(text).partition(":")
    try:
        return int(h) * 60 + int(m or 0)
    except ValueError:
        return None


class Journal:
    def path(self, name):
        return JOURNAL_DIR / f"{_slug(name)}.json"

    def entries(self, name):
        return load_json(self.path(name), [])

    def add(self, name, text, kind="life"):
        text = text.strip().strip('"')
        if not text:
            return
        entries = self.entries(name)
        entries.append({"when": datetime.now().astimezone().isoformat(timespec="seconds"),
                        "date": _date_text(), "kind": kind, "text": text})
        save_json(self.path(name), entries[-60:])

    def last(self, name, kind=None):
        for e in reversed(self.entries(name)):
            if kind is None or e["kind"] == kind:
                return e
        return None

    def notes(self, name, n=CONTEXT_ENTRIES):
        return "\n".join(f"- {e['date']}: {e['text']}" for e in self.entries(name)[-n:]) or "(nothing yet)"


class Mailbox:
    """Your Hotmail inbox (data/mail.json). Folders: 'inbox', 'bulk' (Bulk Mail) and 'deleted'."""

    def messages(self):
        with mail_lock:
            return load_json(MAIL_FILE, [])

    def add(self, sender, subject, body, folder="inbox", addr=None, to=None, cc=None, kind=None):
        """to/cc: lists of addresses when it wasn't just to you; kind: 'spam', 'notice', 'forward', 'group'..."""
        with mail_lock:
            msgs = self.messages()
            now = clock.now()
            m = {"id": (msgs[-1]["id"] + 1) if msgs else 1, "from": sender, "addr": addr or email_address(sender),
                 "subject": subject, "body": body,
                 "date": f"{now:%a, %b} {now.day} {now.year} {clock.time_text(now)}", "read": False,
                 "ts": int(time.time())}
            if folder != "inbox":
                m["folder"] = folder
            if to:
                m["to"] = to
            if cc:
                m["cc"] = cc
            if kind:
                m["kind"] = kind
            msgs.append(m)
            save_json(MAIL_FILE, msgs)
            return m

    def unread(self):
        return [m for m in self.messages() if not m["read"] and m.get("folder", "inbox") == "inbox"]

    def _update(self, msg_id, **fields):
        with mail_lock:
            msgs = self.messages()
            for m in msgs:
                if m["id"] == msg_id:
                    m.update(fields)
            save_json(MAIL_FILE, msgs)

    def mark_read(self, msg_id, read=True):
        self._update(msg_id, read=read)

    def move(self, msg_id, folder):
        """'inbox', 'bulk' or 'deleted'."""
        self._update(msg_id, folder=folder)

    def purge(self, msg_id):
        with mail_lock:
            save_json(MAIL_FILE, [m for m in self.messages() if m["id"] != msg_id])


class LifeSim(QObject):
    mail_arrived = Signal()

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.journal = Journal()
        self.mailbox = Mailbox()
        self.broker = broker.get()
        buddies, _errors = load_buddies("life")
        self.buddies = {c.screen_name: c for c, _section in buddies}
        self._people = None
        self.talks = {}            # (name, program) -> {"lines": [...], "last": t, "user_spoke": bool}
        self.aim_world = None
        self.irc = None            # the FurNet object while ClaudeIRC is connected
        self.state = load_json(STATE_FILE, {})
        self.powered_off = False      # Windows is shut down but the PC is on ('safe to turn off')
        self.next_story = time.monotonic() + random.uniform(*STORY_MINUTES) * 60
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(TICK_MS)

    @property
    def user(self):
        """What the buddies call you (follows renames invisibly)."""
        from .. import user as account
        return account.known_as() or "your buddy"

    # ---- context for prompts ----------------------------------------------------------------
    def context(self, name):
        """What a buddy remembers: their recent journal, for any program's prompt."""
        if name not in self.buddies:
            return ""
        from .. import fursonas
        about = fursonas.knowledge(name, self.user)
        entries = self.journal.entries(name)[-CONTEXT_ENTRIES:]
        if not entries:
            return about
        lines = "\n".join(f"- {e['date']}: {e['text']}" for e in entries)
        return about + (f"\n\nYour recent diary notes, including things you talked about with {self.user} on "
                        f"AIM, IRC, the MUCK or email (use them naturally if they come up; don't recite them):"
                        f"\n{lines}")

    # ---- everyone with an email address ------------------------------------------------------------
    @property
    def people(self):
        """name -> Person: the AIM buddies, then every IRC and MUCK regular."""
        if self._people is None:
            from ..paths import ROOT
            people = {name: Person(name, c.persona, None, c) for name, c in self.buddies.items()}
            for path, key in ((ROOT / "Program Files" / "ClaudeIRC" / "regulars.json", "nick"),
                              (ROOT / "Program Files" / "ClaudeMUCK" / "world" / "regulars.json", "name")):
                for r in load_json(path, {}).get("regulars", []):
                    name = r.get(key)
                    if not name or not r.get("persona") or name in people:
                        continue
                    hours = r.get("hours") or []
                    span = tuple(_minutes(h) for h in hours[:2]) if len(hours) >= 2 else None
                    people[name] = Person(name, r["persona"], span if span and None not in span else None, None)
            self._people = people
        return self._people

    def person_by_address(self, addr):
        addr = addr.strip().lower()
        return next((p for name, p in self.people.items() if email_address(name) == addr), None)

    def awake(self, person):
        from ..programs.people import available
        return available(person.contact) if person.contact is not None else available(hours=person.hours)

    # ---- model helpers ----------------------------------------------------------------------
    def _model(self, contact):
        """The life sim's journals, e-mail and catch-up run on AI Models' background model."""
        from .. import ai_models
        return ai_models.model_for("background"), int(ai_models.config()["context"])

    def _ask(self, contact, prompt, callback, priority=broker.BACKGROUND):
        """contact: a buddy (for their temperature), or None for anyone else."""
        model, ctx = self._model(contact)
        temperature = getattr(contact, "temperature", None) or 0.85
        self.broker.chat(model, [{"role": "user", "content": prompt}],
                         {"num_ctx": ctx, "temperature": temperature}, lambda text, err: callback(
                             None if err else (text or "").strip()), priority, think=False)

    # ---- conversations -------------------------------------------------------------------------
    def heard(self, name, program, speaker, text):
        """A line of conversation involving a buddy (speaker is their name or the user's)."""
        if name not in self.buddies or not text:
            return
        from .. import clippy
        if clippy.get() is not None:
            clippy.get().heard(program, name, speaker, text)
        talk = self.talks.setdefault((name, program), {"lines": [], "last": 0.0, "user_spoke": False})
        talk["lines"].append(f"{speaker}: {text}")
        del talk["lines"][:-30]
        talk["last"] = time.monotonic()
        if speaker != name:
            talk["user_spoke"] = True

    def _summarise_quiet_talks(self, force=False):
        now = time.monotonic()
        for key, talk in list(self.talks.items()):
            if not force and now - talk["last"] < TALK_IDLE_MINUTES * 60:
                continue
            del self.talks[key]
            name, program = key
            if not talk["user_spoke"] or len(talk["lines"]) < 2:
                continue
            prompt = TALK_PROMPT.format(name=name, user=self.user, program=program, lines="\n".join(talk["lines"]))
            self._ask(self.buddies[name], prompt, lambda note, name=name: note and self.journal.add(name, note, "talk"))
            mine = MY_TALK_PROMPT.format(name=name, user=self.user, program=program, lines="\n".join(talk["lines"]))
            self._ask(None, mine, lambda note, name=name: note and _my_diary(name, note))

    def watch_aim(self, world):
        """ClaudeAIM signed on: listen to its IMs."""
        self.aim_world = world

        def added(buddy_id, entry):
            b = world.buddies.get(buddy_id)
            if b is None or entry.get("kind") not in ("user", "contact"):
                return
            speaker = self.user if entry["kind"] == "user" else b.name
            self.heard(b.name, "AIM", speaker, entry.get("text", ""))

        world.message_added.connect(added)

    # ---- the clock ---------------------------------------------------------------------------------
    # ---- email from the user (Outlook Express) ------------------------------------------------------------
    def user_address(self):
        from .. import user as account
        return account.email_address(self.user)

    def receive_email(self, to_addr, subject, body):
        """The user sent an email. Buddies answer a few minutes later (once they're awake); an address
        nobody has bounces back from the Mail Delivery Subsystem."""
        person = self.person_by_address(to_addr)
        name = person.name if person is not None else None
        if name is not None:
            self.journal.add(name, f'Got an email from {self.user}, "{subject}": {body.strip()[:300]}', "talk")
        delay = random.uniform(*MAIL_REPLY_MINUTES) * 60 if name else random.uniform(40, 90)
        queue = self.state.setdefault("mail_queue", [])
        queue.append({"name": name, "addr": to_addr.strip(), "subject": subject, "body": body,
                      "due": time.time() + delay})
        save_json(STATE_FILE, self.state)

    def _deliver_mail(self):
        queue = self.state.get("mail_queue", [])
        now = time.time()
        due = [q for q in queue if q["due"] <= now]
        if not due:
            return
        for item in due:
            queue.remove(item)
            name = item["name"]
            if name is None:
                self.mailbox.add("Mail Delivery Subsystem", f"Undeliverable: {item['subject']}",
                                 f"Your message did not reach some or all of the intended recipients.\n\n"
                                 f"      Subject:  {item['subject']}\n\nThe following recipient(s) could not be "
                                 f"reached:\n\n      {item['addr']}\n            550 User unknown\n")
                self.mail_arrived.emit()
                self._announce_mail()
                continue
            person = self.people.get(name)
            if person is None:
                continue
            if not self.awake(person):
                item["due"] = now + 20 * 60         # asleep: they'll answer when they're up
                queue.append(item)
                continue
            self._reply_email(person, name, item)
        save_json(STATE_FILE, self.state)

    def _reply_email(self, person, name, item):
        now = clock.now()
        prompt = REPLY_PROMPT.format(name=name, user=self.user, now=f"{now:%A, %B} {now.day}, {now.year}",
                                     persona=person.persona, notes=self.journal.notes(name),
                                     subject=item["subject"], body=item["body"].strip()[:3000])

        def done(text):
            if not text:
                item["due"] = time.time() + 10 * 60     # the model was busy or failed: try again later
                self.state.setdefault("mail_queue", []).append(item)
                save_json(STATE_FILE, self.state)
                return
            m = re.match(r"\s*Subject:\s*(.+?)\s*\n(.*)", text, re.S)
            subject, body = (m.group(1).strip('"'), m.group(2).strip()) if m else (f"Re: {item['subject']}", text)
            self.mailbox.add(name, subject, body)
            self.journal.add(name, f"Replied to {self.user}'s email: {subject}", "talk")
            self.mail_arrived.emit()
            self._announce_mail()

        self._ask(person.contact, prompt, done)

    def _tick(self):
        self.state["last_running"] = datetime.now().astimezone().isoformat(timespec="seconds")
        from .. import llm_server
        if llm_server.ready():                   # without a model, replies wait (they're not lost)
            self._deliver_mail()
        if not self.powered_off:
            from . import lj, mail_extras
            mail_extras.tick(self)
            lj.tick(self)
            try:
                from ..autopilot import diary            # Kithylin's diary: today's first entry, the bedtime wrap-up
                diary.tick()
            except Exception:
                pass
        save_json(STATE_FILE, self.state)
        self._summarise_quiet_talks()
        if time.monotonic() >= self.next_story and (self.desktop.isVisible() or self.powered_off):
            self.next_story = time.monotonic() + random.uniform(*STORY_MINUTES) * 60
            if self.broker.background_pending() == 0:
                self.story_tick()

    def story_tick(self, name=None, reach_out=None):
        """Move one buddy's life forward a little."""
        if not self.buddies:
            return
        if name is None:
            def staleness(n):
                last = self.journal.last(n, "life")
                return datetime.fromisoformat(last["when"]).timestamp() if last else 0
            names = sorted(self.buddies, key=staleness)
            name = random.choice(names[:max(1, len(names) // 2)])
        contact = self.buddies[name]

        def done(note):
            if not note:
                return
            self.journal.add(name, note, "life")
            if reach_out or (reach_out is None and random.random() < REACH_OUT_CHANCE):
                self.reach_out(name, note)

        self._ask(contact, self._story_prompt(contact, "today"), done)

    def _story_prompt(self, contact, when, since=""):
        now = clock.now()
        return STORY_PROMPT.format(name=contact.screen_name, user=self.user, now=f"{now:%A, %B} {now.day}, {now.year}",
                                   persona=contact.persona, notes=self.journal.notes(contact.screen_name),
                                   since=since, when=when)

    # ---- reaching out -------------------------------------------------------------------------------
    def reach_out(self, name, topic):
        """Tell the user some news: AIM if possible, then IRC, otherwise email."""
        contact = self.buddies.get(name)
        if contact is None:
            return
        instruction = REACH_OUT.format(user=self.user, topic=topic)
        if self.aim_world is not None and self.aim_world.running:
            if self.aim_world.reach_out(contact.id, instruction):
                return
        if self.irc is not None and self.irc.connected:
            p = self.irc.person(name)
            if p is not None and p.online:
                self.irc.reach_out(p, instruction)
                return
        self.send_email(name, topic)

    def send_email(self, name, topic):
        contact = self.buddies[name]
        now = clock.now()
        prompt = EMAIL_PROMPT.format(name=name, user=self.user, now=f"{now:%A, %B} {now.day}, {now.year}",
                                     persona=contact.persona, notes=self.journal.notes(name), topic=topic)

        def done(text):
            if not text:
                return
            m = re.match(r"\s*Subject:\s*(.+?)\s*\n(.*)", text, re.S)
            subject, body = (m.group(1), m.group(2).strip()) if m else ("Hey!", text)
            self.mailbox.add(name, subject.strip('"'), body)
            self.journal.add(name, f"Emailed {self.user}: {subject}", "talk")
            self.mail_arrived.emit()
            self._announce_mail()

        self._ask(contact, prompt, done)

    def _announce_mail(self):
        if not network.is_connected():
            return   # they'll hear about it when they next connect
        unread = self.mailbox.unread()
        if not unread:
            return
        sound.play_file("gotmail.wav")
        last = unread[-1]
        text = f"{last['from']}: {last['subject']}" + (f"  (+{len(unread) - 1} more)" if len(unread) > 1 else "")
        from .. import mailtray
        tray = mailtray.get()
        if tray is not None:                       # the balloon comes from MSN Hotmail's envelope
            tray.notify("You've got mail!", text + f"\nClick here to open {mailtray.MAIL_NAME}.")
            return
        net = network.get(self.desktop)
        if net.tray is not None:
            net.tray.showMessage("You've got mail!", text, None, 8000)

    def connected(self):
        """Just dialed up: mention any mail that came in while offline."""
        QTimer.singleShot(6000, self._announce_mail)

    # ---- catching up after the PC was off -------------------------------------------------------------
    def catch_up(self):
        """At login: if ClaudeXP was off for a while, move everyone's lives along a little."""
        last = self.state.get("last_running")
        self.state["last_running"] = datetime.now().astimezone().isoformat(timespec="seconds")
        save_json(STATE_FILE, self.state)
        if not last or not self.buddies:
            return 0
        gap = datetime.now().astimezone() - datetime.fromisoformat(last)
        hours = gap.total_seconds() / 3600
        if hours < CATCH_UP_MIN_HOURS:
            return 0
        if hours < 24:
            when, since = "since your last note (a few hours ago)", f"It's been about {max(1, round(hours))} hours. "
        else:
            when = f"over the last {round(hours / 24)} days"
            since = f"It's been about {round(hours / 24)} days since your last note. "
        names = list(self.buddies)
        random.shuffle(names)
        jobs = min(len(names), CATCH_UP_MAX_JOBS, 2 + int(hours))
        mailers = set(random.sample(names[:jobs], k=min(jobs, 1 + int(hours > 12))))
        for name in names[:jobs]:
            contact = self.buddies[name]

            def done(note, name=name):
                if note:
                    self.journal.add(name, note, "life")
                    if name in mailers:
                        self.send_email(name, note)

            self._ask(contact, self._story_prompt(contact, when, since), done)
        return jobs


_life = None


def install(desktop):
    global _life
    _life = LifeSim(desktop)
    return _life


def get():
    return _life
