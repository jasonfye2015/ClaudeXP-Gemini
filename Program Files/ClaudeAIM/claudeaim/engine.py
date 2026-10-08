"""The buddy 'world': who is online, their scripts, and conversations with Ollama."""
import random
import re
import time
from datetime import datetime, timedelta
from enum import Enum

from PySide6.QtCore import QObject, QTimer, Signal

from . import host, paths, timefmt
from .llm import LLM, SYSTEM_PROMPT, clean_reply, estimate_tokens
from .pictures import strip_tags
from .storage import History

DOOR_SECONDS = 60
REPLY_DEBOUNCE_MS = 1500     # wait for the user to finish a burst of messages
REPLY_RESERVE_TOKENS = 512   # room left in the context for the reply itself
IDLE_CHECK_MS = 15000
VISION_IMAGES = 2             # how many of the user's most recent pictures the model can see
IMAGE_TOKENS = 260            # rough context cost of one attached picture
PICTURE_COOLDOWN = 5          # user messages after a buddy shares pictures before they may again unasked
# The user asking to see pictures ("got any pics?", "show me", "send me more"...).
ASKED_FOR_PICTURES = re.compile(
    r"\b(pics?|pix|pictures?|photos?|images?|selfies?|snaps?)\b|\bshow me\b|\bsend (me|it|them|one|some|more)\b"
    r"|\b(see|share) (it|them|one|some|more|yours?|the)\b|\bany more\b|\bgot more\b", re.IGNORECASE)
PICTURE_GAP_MS = 1800         # pause between the pictures of a set arriving
GREETING_EVENTS = ("signon", "user_signon")
RECENT_CHAT_MINUTES = 20      # no sign-on greeting if you talked this recently
DEFAULT_USER_AWAY = "I am away from my computer right now."
STILL_CHATTING_SECONDS = 300  # user messaged this recently = "still chatting"
STAY_RETRY_MS = 180000        # check again this often before signing off
BEDTIME_GRACE_MINUTES = 60    # how long past bedtime a good chat can keep them up


class Presence(Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    AWAY = "away"


class Buddy:
    def __init__(self, contact):
        self.contact = contact
        self.history = History(contact.id)
        self.presence = Presence.OFFLINE
        self.door_until = 0.0
        self.window_seen = False       # their IM window is open and in front of the user
        self.busy = False              # a reply is being generated or "typed"
        self.pending_reply = False     # user said something that still needs an answer
        self.last_activity = time.monotonic()
        self.last_user_message = 0.0
        self.bedtime = None            # when their schedule sends them to bed this session
        self.fired = set()             # trigger indices used this sign-on (once / idle)
        self.waiting = []              # triggers held until the user is back
        self.auto_sent = False         # user's away message already sent this away period
        self.auto_received = False     # contact's away message already shown this away period
        self.session_timers = set()
        self.debounce = None
        self.downloading = 0           # pictures from the user still "downloading"
        self.reply_due = None          # monotonic time a slow replier will get to answering
        self.reply_instruction = None  # private note for their next reply
        self.offline_notice = False    # "they're offline, messages will be delivered" shown

    @property
    def id(self):
        return self.contact.id

    @property
    def name(self):
        return self.contact.screen_name

    @property
    def door(self):
        return time.monotonic() < self.door_until


class World(QObject):
    presence_changed = Signal(str)
    message_added = Signal(str, object)
    unread_changed = Signal(str)
    typing_changed = Signal(str, bool)
    downloading_changed = Signal(str, bool)
    user_away_changed = Signal(bool)

    def __init__(self, settings, sounds, contacts, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.sounds = sounds
        self.llm = LLM(self)
        self.buddies = {c.id: Buddy(c) for c in contacts}
        self.user_away = False
        self.running = False
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._check_idle)

    # ----- timing helpers -------------------------------------------------

    def _minutes_ms(self, minutes):
        scale = max(float(self.settings["time_scale"] or 1.0), 0.001)
        return max(0, int(minutes * 60000 / scale))

    def _rand_minutes_ms(self, rng):
        return self._minutes_ms(random.uniform(*rng))

    def _after(self, ms, fn, buddy=None):
        """Run fn after ms. If buddy is given, the timer is cancelled when they sign off."""
        t = QTimer(self)
        t.setSingleShot(True)

        def fire():
            if buddy:
                buddy.session_timers.discard(t)
            t.deleteLater()
            if self.running:
                fn()

        t.timeout.connect(fire)
        if buddy:
            buddy.session_timers.add(t)
        t.start(int(ms))

    def _cancel_session(self, b):
        for t in b.session_timers:
            t.stop()
            t.deleteLater()
        b.session_timers.clear()

    # ----- lifecycle -------------------------------------------------------

    def start(self):
        self.running = True
        already_online = self._pick_already_online()
        for b in self.buddies.values():
            c = b.contact
            if b.id in already_online:
                self._sign_on(b, already_on=True)  # was online before the user logged in
            else:
                # Offline for a while already, so they may well sign on soon.
                delay = self._rand_minutes_ms(c.offline_minutes) * random.uniform(0.05, 1.0)
                self._after(delay, lambda b=b: self._try_sign_on(b))
        self._idle_timer.start(IDLE_CHECK_MS)

    def _pick_already_online(self):
        """About `online_at_login` of the whole list, chosen from buddies who are awake.

        start_online_chance weights who gets picked.
        """
        awake = [b for b in self.buddies.values()
                 if not b.contact.schedule or
                 b.contact.schedule.awake_until(timefmt.local_now(b.contact.timezone)) is not None]
        share = float(self.settings["online_at_login"])
        target = min(len(awake), round(len(self.buddies) * share))
        # Weighted random pick without replacement.
        ranked = sorted(awake, reverse=True,
                        key=lambda b: random.random() ** (1 / max(b.contact.start_online_chance, 0.01)))
        return {b.id for b in ranked[:target]}

    def stop(self):
        self.running = False
        self._idle_timer.stop()

    def has_unread(self):
        return any(b.history.unread for b in self.buddies.values())

    # ----- presence ----------------------------------------------------------

    def _set_door(self, b):
        b.door_until = time.monotonic() + DOOR_SECONDS
        self._after(DOOR_SECONDS * 1000 + 100, lambda: self.presence_changed.emit(b.id))

    def _try_sign_on(self, b):
        """Sign on now, or later if their schedule says they're asleep."""
        schedule = b.contact.schedule
        if schedule:
            now = timefmt.local_now(b.contact.timezone)
            if schedule.awake_until(now) is None:
                wait_ms = (schedule.next_wake(now) - now).total_seconds() * 1000
                wait_ms += random.uniform(0, 20 * 60000)  # not right as the alarm goes off
                self._after(wait_ms, lambda: self._try_sign_on(b))
                return
        self._sign_on(b)

    def _sign_on(self, b, already_on=False):
        """already_on: they were online before the user logged in (no door, no sound)."""
        b.presence = Presence.ONLINE
        b.fired.clear()
        b.waiting.clear()
        b.auto_sent = b.auto_received = False
        b.last_activity = time.monotonic()
        if not already_on:
            self._set_door(b)
            self.sounds.play("buddyin.wav")
        self.presence_changed.emit(b.id)

        online_ms = self._rand_minutes_ms(b.contact.online_minutes)
        if already_on:
            online_ms *= random.uniform(0.1, 1.0)  # part of their session has already passed
        b.bedtime = None
        if b.contact.schedule:
            now = timefmt.local_now(b.contact.timezone)
            until = b.contact.schedule.awake_until(now)
            if until and (until - now).total_seconds() * 1000 < online_ms:
                online_ms = (until - now).total_seconds() * 1000
                b.bedtime = until
        self._after(online_ms, lambda: self._maybe_sign_off(b), buddy=b)
        if already_on and random.random() < b.contact.away_chance / 2:
            self._go_away(b)  # already away when the user arrives
        elif random.random() < b.contact.away_chance:
            self._after(online_ms * random.uniform(0.2, 0.7), lambda: self._go_away(b), buddy=b)
        b.offline_notice = False
        if b.history.release_held():
            # They come online to messages the user left: read them, then answer instead of greeting.
            b.reply_instruction = (f"While you were offline, {self.settings['screen_name']} sent you "
                                   "the messages above. You just signed on and read them.")
            self._after(random.uniform(15000, 90000), lambda: self._schedule_reply(b), buddy=b)
        else:
            self._fire("user_signon" if already_on else "signon", b)

    def _maybe_sign_off(self, b):
        """Sign off, unless they'd rather keep chatting with the user."""
        if b.contact.stay_while_chatting:
            chatting = (b.busy or b.pending_reply or
                        time.monotonic() - b.last_user_message < STILL_CHATTING_SECONDS)
            too_late = b.bedtime and timefmt.local_now() > b.bedtime + timedelta(minutes=BEDTIME_GRACE_MINUTES)
            if chatting and not too_late:
                self._after(STAY_RETRY_MS, lambda: self._maybe_sign_off(b), buddy=b)
                return
        self._sign_off(b)

    def _sign_off(self, b):
        self._cancel_session(b)
        b.presence = Presence.OFFLINE
        b.pending_reply = False
        self._set_door(b)
        self.sounds.play("buddyout.wav")
        self.presence_changed.emit(b.id)
        self._after(self._rand_minutes_ms(b.contact.offline_minutes), lambda: self._try_sign_on(b))

    def _go_away(self, b):
        if b.presence != Presence.ONLINE:
            return
        b.presence = Presence.AWAY
        b.auto_received = False
        self.presence_changed.emit(b.id)
        self._after(self._rand_minutes_ms(b.contact.away_minutes), lambda: self._come_back(b), buddy=b)

    def _come_back(self, b):
        if b.presence != Presence.AWAY:
            return
        b.presence = Presence.ONLINE
        b.last_activity = time.monotonic()
        self.presence_changed.emit(b.id)
        if b.pending_reply:
            self._schedule_reply(b)

    # ----- user status ---------------------------------------------------------

    def set_user_away(self, away: bool, message: str = ""):
        if away:
            self.settings.set("away_message", message)
        if away == self.user_away:
            return
        self.user_away = away
        self.user_away_changed.emit(away)
        for b in self.buddies.values():
            b.auto_sent = False
            if b.presence == Presence.OFFLINE:
                continue
            self._fire("user_away" if away else "user_back", b)
            if not away:
                held, b.waiting = b.waiting, []
                for idx, trig in held:
                    self._run_trigger(b, idx, trig)

    @property
    def user_away_message(self):
        return self.settings["away_message"] or DEFAULT_USER_AWAY

    # ----- scripts -------------------------------------------------------------

    def _fire(self, event, b):
        if event in GREETING_EVENTS and self._talked_recently(b):
            return  # you were just chatting: no "hi, good to see you!" all over again
        happened = time.monotonic()
        for idx, trig in enumerate(b.contact.triggers):
            if trig.on != event or event == "idle":
                continue
            if trig.once and idx in b.fired:
                continue
            if random.random() > trig.chance:
                continue
            delay = self._rand_minutes_ms(trig.delay_minutes)
            self._after(delay, lambda idx=idx, trig=trig: self._run_trigger(b, idx, trig, happened),
                        buddy=b)

    def _talked_recently(self, b):
        cutoff = datetime.now().astimezone() - timedelta(minutes=RECENT_CHAT_MINUTES)
        for m in reversed(b.history.messages):
            if m["kind"] in ("user", "contact"):
                ts = datetime.fromisoformat(m["ts"])
                return (ts if ts.tzinfo else ts.astimezone()) > cutoff
        return False

    def _check_idle(self):
        now = time.monotonic()
        for b in self.buddies.values():
            if b.presence != Presence.ONLINE or b.busy:
                continue
            quiet_ms = (now - b.last_activity) * 1000
            for idx, trig in enumerate(b.contact.triggers):
                if trig.on != "idle" or idx in b.fired:
                    continue
                if quiet_ms >= self._minutes_ms(trig.minutes):
                    b.fired.add(idx)  # only once per quiet stretch
                    if random.random() <= trig.chance:
                        self._run_trigger(b, idx, trig)

    def _run_trigger(self, b, idx, trig, happened=None):
        """happened: when the triggering event occurred. If the two of you have talked
        since then, the moment has passed (e.g. no "hey, you're here!" mid-conversation)."""
        if b.presence != Presence.ONLINE:
            return
        if happened is not None and b.last_activity > happened:
            return
        if trig.once and idx in b.fired and trig.on != "idle":
            return
        if self.user_away and trig.on != "user_away":
            if trig.if_user_away == "skip":
                return
            if trig.if_user_away == "wait":
                b.waiting.append((idx, trig))
                return
        count, last = self._unanswered(b)
        limit = b.contact.unanswered_limit
        if count >= limit:
            cooldown_s = self._minutes_ms(b.contact.cooldown_hours * 60) / 1000
            if last and (datetime.now().astimezone() - last).total_seconds() < cooldown_s:
                return  # backing off: they've reached out enough without hearing back
        elif count == limit - 1:
            # The last one before backing off: a gentle "is everything ok?"
            b.fired.add(idx)
            if not b.busy:
                user = self.settings["screen_name"]
                self._start_reply(b, initiated=True, instruction=(
                    f"You've messaged {user} {count} times now without hearing back. Send one "
                    "short message with a little concern, like checking everything's ok since "
                    "they haven't replied in a while. No picture."))
            return
        if trig.share_picture:
            name = self._unsent_picture(b)
            if not name:
                return  # nothing new to show
            b.fired.add(idx)
            if not b.busy:
                pics = b.contact.pictures
                key = pics.set_of(name)
                about = "; ".join(pics.captions[n] for n in pics.sets[key])
                self._start_reply(b, initiated=True, share_pictures=True, instruction=(
                    f"{trig.prompt or 'Share some of your pictures.'} Send your {key} pictures "
                    f"({about}) by writing [pic: {key}] in your message, with a comment about them."))
            return
        b.fired.add(idx)
        if trig.text:
            b.busy = True
            self.typing_changed.emit(b.id, True)
            self._after(self._typing_ms(trig.text), lambda: self._finish_reply(b, trig.text, True))
        elif not b.busy:
            self._start_reply(b, instruction=trig.prompt, initiated=True)

    def reach_out(self, buddy_id, instruction):
        """Have a buddy start a conversation (e.g. to tell the user some news). False if they can't now."""
        b = self.buddies.get(buddy_id)
        if b is None or not self.running or b.busy or b.presence != Presence.ONLINE:
            return False
        count, _last = self._unanswered(b)
        if count >= b.contact.unanswered_limit - 1:
            return False   # they've already sent a few unanswered messages
        self._start_reply(b, instruction=instruction, initiated=True)
        return True

    def _unanswered(self, b):
        """How many times they've messaged first since the user last said anything,
        and when the latest of those was."""
        count, last = 0, None
        for m in reversed(b.history.messages):
            if m["kind"] == "user":
                break
            if m["kind"] == "contact" and m.get("initiated"):
                count += 1
                if last is None:
                    ts = datetime.fromisoformat(m["ts"])
                    last = ts if ts.tzinfo else ts.astimezone()
        return count, last

    # ----- conversation ----------------------------------------------------------

    def set_window_seen(self, buddy_id, seen):
        """The IM window reports whether the user can see it (open, in front, not minimized)."""
        b = self.buddies[buddy_id]
        b.window_seen = seen
        if seen and b.history.unread:
            b.history.set_unread(False)
            self.unread_changed.emit(b.id)

    def _activity(self, b, from_user=False):
        b.last_activity = time.monotonic()
        if from_user:
            # Only the user talking ends a quiet stretch. (If the buddy's own "it's quiet..."
            # message re-armed its idle triggers, it would repeat every few minutes.)
            b.fired = {i for i in b.fired if b.contact.triggers[i].on != "idle"}

    def _add(self, b, kind, text, image="", **extra):
        entry = b.history.add(kind, text, image, **extra)
        self.message_added.emit(b.id, entry)
        return entry

    def _from_user(self, b, text, image=""):
        """Record something the user sent. True if the buddy is there to read it right now."""
        offline = b.presence == Presence.OFFLINE
        entry = b.history.add("user", text, image, **({"held": True} if offline else {}))
        self.message_added.emit(b.id, entry)
        self._activity(b, from_user=True)
        b.last_user_message = time.monotonic()
        self.sounds.play("imsend.wav")
        if offline:
            if not b.offline_notice:
                b.offline_notice = True
                self._add(b, "system", f"{b.name} is offline. Your messages will be "
                                       "delivered when they sign on.")
            return False
        if b.presence == Presence.AWAY:
            if not b.auto_received:
                b.auto_received = True
                self._after(400, lambda: self._add(b, "contact_auto", b.contact.away_message))
            b.pending_reply = True
            return False
        return True

    def user_send(self, buddy_id, text):
        b = self.buddies[buddy_id]
        if self._from_user(b, text):
            self._schedule_reply(b)

    def user_send_image(self, buddy_id, rel_path):
        """The user sent a picture (saved under data/ at rel_path)."""
        b = self.buddies[buddy_id]
        if not self._from_user(b, "", rel_path):
            return
        # A dial-up-ish download: a couple of seconds plus a bit per KB.
        try:
            kb = (paths.DATA / rel_path).stat().st_size / 1024
        except OSError:
            kb = 100
        b.downloading += 1
        self.downloading_changed.emit(b.id, True)

        def downloaded():
            b.downloading -= 1
            if b.downloading == 0:
                self.downloading_changed.emit(b.id, False)
                self._schedule_reply(b)

        self._after(min(2000 + kb * 25, 12000), downloaded)

    def _schedule_reply(self, b):
        b.pending_reply = True
        if b.busy:
            return  # picked up when the current reply finishes
        if b.debounce is None:
            b.debounce = QTimer(self)
            b.debounce.setSingleShot(True)
            b.debounce.timeout.connect(lambda: self._start_reply(b))
        now = time.monotonic()
        if b.reply_due is None:
            b.reply_due = now + self._reply_lag_ms(b) / 1000
        b.debounce.start(int(max(REPLY_DEBOUNCE_MS, (b.reply_due - now) * 1000)))

    def _reply_lag_ms(self, b):
        """Extra wait before a slow replier answers (busy driving, at work...)."""
        slow = b.contact.slow_replies
        if not slow or random.random() > slow.chance or not self._busy_now(b):
            return 0
        return self._rand_minutes_ms(slow.minutes)

    def _busy_now(self, b):
        """Inside their slow_replies days/hours (at work, on the road...), their local time."""
        slow = b.contact.slow_replies
        if not slow:
            return False
        now = timefmt.local_now(b.contact.timezone)
        if slow.days != "all":
            dow = timefmt.shifted(now).weekday()
            if (dow < 5) != (slow.days == "weekdays"):
                return False
        if slow.hours:
            minute = now.hour * 60 + now.minute
            start, end = slow.hours
            if not start <= minute < end:
                return False
        return True

    def model_for(self, b):
        return (self.settings["model_overrides"].get(b.id)
                or b.contact.model or self.settings["default_model"])

    def _start_reply(self, b, instruction=None, initiated=False, share_pictures=False):
        """initiated: the buddy is messaging first (a trigger), not answering the user.
        share_pictures: a share_picture trigger, which may always send its set."""
        b.reply_due = None
        if b.busy or not self.running or b.presence != Presence.ONLINE:
            return
        if b.downloading:
            b.pending_reply = True  # answer once the picture has arrived
            return
        if instruction is None and b.reply_instruction:
            instruction, b.reply_instruction = b.reply_instruction, None
        initiated = initiated and not b.pending_reply  # if the user just spoke, it's an answer
        pictures_ok = share_pictures or self._pictures_allowed(b)
        b.busy = True
        b.pending_reply = False
        self.typing_changed.emit(b.id, True)
        messages = self.build_messages(b, instruction)
        options = {"num_ctx": int(self.settings["context_size"]),
                   "temperature": b.contact.temperature}

        def done(text, err):
            if err:
                b.busy = False
                self.typing_changed.emit(b.id, False)
                self._add(b, "system", f"(Couldn't reach Ollama: {err})")
                return
            text = clean_reply(text, b.name)
            if not text:
                b.busy = False
                self.typing_changed.emit(b.id, False)
                return
            self._after(self._typing_ms(text),
                        lambda: self._finish_reply(b, text, initiated, pictures_ok))

        self.llm.chat(self.model_for(b), messages, options, done)

    def _typing_ms(self, text):
        return min(800 + len(text) * 35, 6000)

    def _finish_reply(self, b, text, initiated=False, pictures_ok=True):
        b.busy = False
        self.typing_changed.emit(b.id, False)
        if b.presence == Presence.OFFLINE:
            return  # they signed off mid-thought
        text, images = self._split_pictures(b, text)
        if not pictures_ok:
            images = []  # not their turn to share: keep the words, drop the pictures
        if text or images:
            self._deliver(b, text, images, initiated)
        if b.pending_reply:
            self._schedule_reply(b)

    def _split_pictures(self, b, text):
        pics = b.contact.pictures
        if pics and b.contact.picture_sharing != "never":
            text, names = pics.extract(text)
            if not names:
                return text, []
            # One set per message: the whole set the picture belongs to, skipping
            # ones the user has already seen (unless they've seen them all).
            group = pics.sets[pics.set_of(names[0])]
            sent = self._sent_pictures(b)
            return text, [n for n in group if n not in sent] or group
        return strip_tags(text), []

    def _sent_pictures(self, b):
        return {m["image"] for m in b.history.messages if m.get("image") and m["kind"] == "contact"}

    def _unsent_picture(self, b):
        pics = b.contact.pictures
        if not pics or b.contact.picture_sharing == "never":
            return None
        unsent = [n for n in pics.captions if n not in self._sent_pictures(b)]
        return random.choice(unsent) if unsent else None

    def _shared_recently(self, b):
        """Fewer than PICTURE_COOLDOWN user messages since they last sent pictures.
        (Counting the user's messages, so a big set doesn't use the cooldown up by itself.)"""
        turns = 0
        for m in reversed(b.history.messages):
            if m["kind"] == "contact" and m.get("image"):
                return turns < PICTURE_COOLDOWN
            if m["kind"] == "user":
                turns += 1
        return False

    def _user_asked_for_pictures(self, b):
        """Does the user's latest message ask to see pictures?"""
        for m in reversed(b.history.messages):
            if m["kind"] == "user":
                return bool(m.get("text") and ASKED_FOR_PICTURES.search(m["text"]))
            if m["kind"] == "contact":
                return False
        return False

    def _pictures_allowed(self, b):
        """May the reply being written right now include pictures? Enforced here, because
        small models don't reliably follow "don't send more yet" in the prompt."""
        sharing = b.contact.picture_sharing
        if sharing == "never" or not b.contact.pictures:
            return False
        if self._user_asked_for_pictures(b):
            return True
        return sharing == "eager" and not self._shared_recently(b)

    def _deliver(self, b, text, images=(), initiated=False):
        images = list(images)
        self._add(b, "contact", text, images.pop(0) if images else "",
                  **({"initiated": True} if initiated else {}))
        for i, name in enumerate(images, 1):  # the rest of a set trickles in, dial-up style
            self._after(i * PICTURE_GAP_MS, lambda name=name: self._add(b, "contact", "", name))
        self._activity(b)
        if not b.window_seen:
            b.history.set_unread(True)
            self.unread_changed.emit(b.id)
        self.sounds.play("imrcv.wav")
        if self.user_away and not b.auto_sent:
            b.auto_sent = True
            self._after(300, lambda: self._add(b, "auto", self.user_away_message))

    # ----- prompt building ---------------------------------------------------------

    def _system_prompt(self, b):
        user = self.settings["screen_name"]
        if self.user_away:
            status = (f'{user} is currently AWAY from their computer. Their away message says: '
                      f'"{self.user_away_message}". They may not read anything until they get back.')
        else:
            status = f"{user} is online and at their computer."
        tz = b.contact.timezone
        now = timefmt.now_text(tz)
        if tz:
            now += f" where you are (for {user} it's {timefmt.clock_text()})"
        prompt = SYSTEM_PROMPT.format(name=b.name, user=user, now=now,
                                      persona=b.contact.persona.strip(), status=status)
        return prompt + self._pictures_prompt(b) + self._work_note(b) + host.extra_context(b.name)

    def _work_note(self, b):
        """For buddies with work days/hours: say outright whether they're at work now.
        Small models don't reliably work out "it's Sunday, so I'm off" from the date, and
        this only sticks when it's the last thing in the system prompt."""
        slow = b.contact.slow_replies
        if not slow or (slow.days == "all" and not slow.hours):
            return ""
        day = timefmt.shifted(timefmt.local_now(b.contact.timezone)).strftime("%A")
        if self._busy_now(b):
            return f"\n\nIMPORTANT: It's {day} and you're at work right now, replying in between."
        return (f"\n\nIMPORTANT: It's {day} and you're off work right now, so you're not at "
                "work: you're at home or out doing your own thing.")

    def _pictures_prompt(self, b):
        c = b.contact
        if not c.pictures or c.picture_sharing == "never":
            return ""
        user = self.settings["screen_name"]
        sent = self._sent_pictures(b)
        lines = []
        for key, names in c.pictures.sets.items():
            count = f"{len(names)} pictures" if len(names) > 1 else "1 picture"
            seen = " (already sent)" if all(n in sent for n in names) else ""
            about = "; ".join(c.pictures.captions[n] for n in names)
            lines.append(f"- {key} ({count}){seen}: {about}")
        if c.picture_sharing == "eager" and not self._shared_recently(b):
            when = ("You like sharing these, but don't rush: you don't need to show them all, "
                    "and most messages have no pictures. Offer or send a set only when the "
                    "conversation turns to what it shows, or when the chat has gone quiet.")
        elif c.picture_sharing == "eager":
            when = (f"You shared pictures just recently, so don't send more unless "
                    f"{user} asks.")
        else:
            when = f"Only send a set if {user} asks to see pictures."
        when += " Never send more than one set in a message."
        return ("\n\nPicture sets on your computer that you can send (sending a set sends "
                "every picture in it):\n" + "\n".join(lines) +
                f"\nTo send a set, write [pic: set name] on its own line in your message. {when} "
                "Never send a set that isn't on this list, and don't resend sets marked "
                "(already sent) unless asked.")

    def _conversation(self, b):
        user = self.settings["screen_name"]
        convo = []
        user_pics = [m for m in b.history.messages if m["kind"] == "user" and m.get("image")]
        visible = {id(m) for m in user_pics[-VISION_IMAGES:]}
        for m in b.history.messages:
            kind = m["kind"]
            if kind == "user" and m.get("image"):
                path = paths.DATA / m["image"]
                if id(m) in visible and path.exists():
                    convo.append({"role": "user", "images": [str(path)],
                                  "content": f"{m['text']}\n[{user} sent you this picture. Look at it and react to what is in it.]".strip()})
                else:
                    convo.append({"role": "user",
                                  "content": f"{m['text']}\n[{user} sent you a picture earlier, which you already reacted to]".strip()})
            elif kind == "user":
                convo.append({"role": "user", "content": m["text"]})
            elif kind == "contact":
                content = m["text"]
                if m.get("image"):
                    content = f"{content}\n[pic: {m['image']}]".strip()
                convo.append({"role": "assistant", "content": content})
            elif kind == "auto":
                convo.append({"role": "user",
                              "content": f"[Auto-response: {user} is away] {m['text']}"})
        return convo

    @staticmethod
    def _tokens(message):
        return estimate_tokens(message["content"]) + IMAGE_TOKENS * len(message.get("images", ()))

    def _budget(self):
        return max(int(self.settings["context_size"]) - REPLY_RESERVE_TOKENS, 256)

    def build_messages(self, b, instruction=None):
        system = self._system_prompt(b)
        convo = self._conversation(b)
        if instruction:
            user = self.settings["screen_name"]
            convo.append({"role": "user", "content": (
                f"[Private note, not a message from {user}: {instruction} "
                f"Write only the instant message you send to {user}.]")})
        used = estimate_tokens(system) + sum(self._tokens(m) for m in convo)
        while used > self._budget() and len(convo) > 1:
            used -= self._tokens(convo.pop(0))  # oldest falls out first
        return [{"role": "system", "content": system}] + convo

    def context_fraction(self, buddy_id) -> float:
        """How full the context is; 1.0 or more means old messages are being dropped."""
        b = self.buddies[buddy_id]
        used = estimate_tokens(self._system_prompt(b))
        used += sum(self._tokens(m) for m in self._conversation(b))
        return used / self._budget()
