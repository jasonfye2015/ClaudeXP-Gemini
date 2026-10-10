"""Clippy, the Office Assistant - resurrected, and now with a language model behind him.

He watches the desktop (programs opening, errors, the Recycle Bin, themes, you going idle), what you type in
Notepad / WordPad and other editors, your chats with the buddies (AIM, IRC, the MUCK), and pipes up with random
tips. Hide just makes him sulk for a while; "Don't show me this tip again" mostly works. The real off switch and
the how-annoying slider are in Control Panel > Office Assistant (data/clippy.json).

Programs report things with clippy.notify(kind, **info); it does nothing while he's off or not installed."""
import json
import random
import time
import weakref
from collections import deque

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPoint, QPropertyAnimation, QTimer
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QPlainTextEdit, QSystemTrayIcon, QTextEdit
from shiboken6 import isValid

from ..paths import DATA
from . import art, brain, lines, moods
from .widget import ClippyWidget, SpeechBalloon, context_menu

SETTINGS = DATA / "clippy.json"
DEFAULTS = {"enabled": True, "level": 3, "watch": {"desktop": True, "typing": True, "chats": True, "random": True},
            "sounds": True, "muted": [], "pos": None, "introduced": False,
            "mood": "happy", "wire": "silver", "accessory": "none", "size": "normal", "roam": False, "llm": True,
            "breaks": 0, "reminders": [], "tray": True}
ASK_KINDS = [("joke", "Tell me a joke", "Tell {name} a short, groaningly bad joke (a pun about computers, paper or "
                                        "offices). Give the joke and the punchline."),
             ("tip", "Give me a tip", "Give {name} one genuinely useful tip about Windows XP, typing, or staying "
                                      "organised, in your own voice."),
             ("compliment", "Compliment me", "Give {name} an over-the-top compliment about something specific, like "
                                             "their taste in wallpapers or how they click."),
             ("roast", "Roast me (gently)", "Gently tease {name} about their computer habits. Playful, never "
                                            "cruel."),
             ("haiku", "Write me a haiku", "Write {name} a haiku (5-7-5) about computers, paper or paperclips."),
             ("fortune", "Tell my fortune", "Tell {name}'s fortune for today, in a silly paperclip-oracle way.")]
WATCH = {"program": "desktop", "error": "desktop", "recycle": "desktop", "theme": "desktop", "idle": "desktop",
         "typing": "typing", "letter": "typing", "chat": "chats", "random": "random"}
LEVELS = {1: "Barely there", 2: "Helpful", 3: "Classic", 4: "Clingy", 5: "Unbearable"}
# per annoyance level: seconds between interruptions, chance an event gets a comment, minutes before a random tip,
# minutes he stays hidden after Hide, minutes idle before he checks on you, chance he ignores a muted tip
GAP = {1: 900, 2: 360, 3: 150, 4: 70, 5: 30}
CHANCE = {1: 0.2, 2: 0.4, 3: 0.6, 4: 0.85, 5: 1.0}
TIP_MINUTES = {1: (40, 70), 2: (20, 40), 3: (10, 20), 4: (5, 10), 5: (2, 4)}
HIDE_MINUTES = {1: (90, 180), 2: (40, 80), 3: (15, 35), 4: (6, 14), 5: (2, 5)}
IDLE_MINUTES = {1: 20, 2: 12, 3: 7, 4: 4, 5: 2}
IGNORE_MUTE = {1: 0.0, 2: 0.0, 3: 0.05, 4: 0.2, 5: 0.4}
TYPING_PAUSE = 4.0          # seconds after the last key before he 'notices' what you wrote

_clippy = None


def settings():
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    out = json.loads(json.dumps(DEFAULTS))
    out.update(data)
    out["watch"] = {**DEFAULTS["watch"], **(data.get("watch") or {})}
    return out


def save(data):
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(data, indent=2), encoding="utf-8")


def install(desktop):
    global _clippy
    if _clippy is None or not isValid(_clippy.widget):
        _clippy = Clippy(desktop)
    return _clippy


def get():
    return _clippy


def notify(kind, **info):
    """Something happened that Clippy might want to 'help' with."""
    if _clippy is not None:
        try:
            _clippy.on_event(kind, info)
        except Exception:
            pass


class Clippy(QObject):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.cfg = settings()
        self.widget = ClippyWidget(desktop)
        self.balloon = SpeechBalloon(desktop)
        self.widget.clicked.connect(self.summon)
        self.widget.menu_requested.connect(self._menu)
        self.widget.moved.connect(self._moved)
        self.balloon.option_chosen.connect(self._option)
        self.balloon.asked.connect(self._asked)
        self.balloon.options_btn.clicked.connect(self.options)
        self.balloon.chat_requested.connect(self.open_chat)
        self.active = False                 # on screen right now (not hidden, not off)
        self.started = False                # logged on (nothing happens on the Welcome screen)
        self.hidden_until = 0.0
        self.last_spoke = 0.0
        self.busy = False                   # waiting on the model
        self.pending = None                 # what the current balloon's options are about
        self.history = []                   # the last exchange, for follow-ups
        self.events = deque(maxlen=8)       # what he's noticed lately (feeds the chat's context)
        self.tray = None
        self.moody_now = random.choice(moods.MOOD_ORDER)
        self.next_drift = time.monotonic() + random.uniform(600, 1500)
        self.next_break = 0.0
        self.next_roam = time.monotonic() + random.uniform(40, 90)
        self.roam_anim = None
        self.next_tip = time.monotonic() + self._minutes(TIP_MINUTES)
        self.idle_nagged = False
        self.typing = {}                    # id(editor) -> {"ref", "last_key", "reported"}
        self.chats = {}                     # (program, buddy) -> recent lines
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        QApplication.instance().installEventFilter(self)
        self._apply_style()

    # ---- settings --------------------------------------------------------------------------------------------
    @property
    def mood(self):
        """His mood right now (when set to Moody, whichever one he has drifted into)."""
        key = self.cfg.get("mood", "happy")
        if key == moods.MOODY:
            return self.moody_now
        return key if key in moods.MOODS else "happy"

    def _line(self, kind, **info):
        return lines.line(kind, mood=self.mood, **info)

    def set_mood(self, key):
        if key != moods.MOODY and key not in moods.MOODS:
            return
        self.cfg["mood"] = key
        save(self.cfg)
        self._apply_style()
        if self.started and self.cfg["enabled"] and self.active:
            self.say(self._line("greet", name=self._name()),
                     anim={"happy": "jump", "sad": "sigh", "angsty": "eyeroll", "snarky": "eyeroll"}[self.mood])

    def _apply_style(self):
        """Push the look (size, wire, hat, mood) to the widget, balloon and tray icon."""
        size = moods.SIZES.get(self.cfg.get("size", "normal"), moods.SIZES["normal"])[1]
        if abs(self.widget.scale - size) > 0.01:
            self.widget.set_scale(size)
            if self.active:
                self._place()
        self.widget.set_style(self.mood, self.cfg.get("wire", "silver"), self.cfg.get("accessory", "none"))
        self.balloon.set_theme(moods.mood_info(self.mood)["balloon"])
        if self.tray is not None:
            self.tray.setIcon(QIcon(art.icon_pixmap(
                16, art.still_pose(self.mood, self.cfg.get("wire", "silver"), self.cfg.get("accessory", "none")))))
        from . import chat
        body = chat.current()
        if body is not None:
            body.refresh_header()

    @property
    def level(self):
        return max(1, min(5, int(self.cfg.get("level", 3))))

    def _minutes(self, table):
        lo, hi = table[self.level]
        return random.uniform(lo, hi) * 60

    def reload(self):
        """Control Panel changed the settings."""
        was = self.cfg.get("enabled", True)
        self.cfg = settings()
        self._apply_style()
        self._show_tray()
        self._schedule_break()
        if was and not self.cfg["enabled"]:
            self.say(self._line("goodbye", name=self._name()), anim="wave", force=True)
            QTimer.singleShot(4500, self._vanish)
        elif not was and self.cfg["enabled"]:
            self.hidden_until = 0
            self.start(greet=True)
        self.next_tip = time.monotonic() + self._minutes(TIP_MINUTES)

    # ---- appearing and disappearing ----------------------------------------------------------------------
    def start(self, greet=True):
        """Log on."""
        self.started = True
        self.timer.start(1000)
        self._show_tray()
        self._schedule_break()
        self.next_tip = time.monotonic() + self._minutes(TIP_MINUTES)
        if not self.cfg["enabled"]:
            return
        self._appear()
        if not self.cfg["introduced"]:
            self.cfg["introduced"] = True
            save(self.cfg)
            QTimer.singleShot(900, lambda: self.say(self._line("intro", name=self._name()), anim="wave",
                                                   options=["Wow, a talking paperclip!", "Please go away"]))
        elif greet:
            self._speak_about("greet", "The user just logged on to Windows. Greet them.")

    def stop(self):
        """Log off / shut down."""
        self.started = False
        self.timer.stop()
        if self.tray is not None:
            self.tray.hide()
        self.balloon.hide()
        self.widget.hide()
        self.active = False

    def _appear(self):
        if self.active:
            return
        self.active = True
        self._place()
        self.widget.show()
        self.widget.raise_()
        self.widget.play("appear")
        self._sound("notify")

    def _place(self):
        area = self.desktop.work_area()
        pos = self.cfg.get("pos")
        if pos:
            x, y = pos
        else:
            x, y = area.width() - self.widget.width() - 24, area.height() - self.widget.height() - 10
        self.widget.move(max(0, min(area.width() - self.widget.width(), int(x))),
                         max(0, min(area.height() - self.widget.height(), int(y))))

    def _moved(self):
        self.cfg["pos"] = [self.widget.x(), self.widget.y()]
        save(self.cfg)
        if self.balloon.isVisible():
            self.balloon.place(self.widget)

    def _vanish(self):
        self.balloon.hide()
        self.widget.play("leave")
        QTimer.singleShot(600, self.widget.hide)
        self.active = False

    def hide_him(self):
        """The Hide command: he sulks, then comes back later anyway."""
        self.balloon.hide()
        self.widget.play("sulk")
        self.say(self._line("hide"), anim="sulk", force=True)
        self.hidden_until = time.monotonic() + self._minutes(HIDE_MINUTES)
        QTimer.singleShot(2600, self._vanish)

    def raise_all(self):
        if self.widget.isVisible():
            self.widget.raise_()
        if self.balloon.isVisible():
            self.balloon.raise_()

    # ---- talking -------------------------------------------------------------------------------------------
    def say(self, text, options=(), anim="eyebrows", ask=False, force=False):
        if not self.cfg["enabled"] and not force:
            return
        self._appear()
        self.last_spoke = time.monotonic()
        brain.remember(text)
        self.balloon.say(text, options, ask=ask)
        self.balloon.place(self.widget)
        QTimer.singleShot(0, lambda: self.balloon.isVisible() and self.balloon.place(self.widget))
        self.balloon.raise_()
        self.widget.raise_()
        if anim:
            self.widget.play(anim)
        self._sound("ding" if not ask else None)

    def _sound(self, event):
        if event and self.cfg.get("sounds", True):
            from .. import sound
            sound.play(event)

    def _name(self):
        from .. import user
        return user.user_name() or "there"

    def _speak_about(self, kind, event, info=None, extra_options=(), anim=None):
        """Pop up, think, and say something about event (the model's words, or a stock line without one)."""
        info = dict(info or {})
        info.setdefault("name", self._name())
        self.busy = True
        self._appear()
        self.widget.play("think")
        self.last_spoke = time.monotonic()
        state = {"done": False}

        def finish(text, options):
            if state["done"]:
                return
            state["done"] = True
            self.busy = False
            if not self.active and kind not in ("greet",):
                return
            if not text:
                text, options = self._line(kind, **info), []
            opts = list(options)[:3]
            for extra in extra_options:
                if extra not in opts:
                    opts.append(extra)
            self.pending = {"kind": kind, "event": event, "said": text}
            self.history = [{"role": "user", "content": event}, {"role": "assistant", "content": text}]
            self.say(text, opts, anim=anim or random.choice(["eyebrows", "wave", "tap", "jump", "look_around"]))

        brain.ask(event, finish, mood=self.mood) if self.cfg.get("llm", True) else finish(None, [])
        QTimer.singleShot(25000, lambda: finish(None, []))        # the model's busy elsewhere: a stock line

    # ---- events ----------------------------------------------------------------------------------------------
    def on_event(self, kind, info):
        if not self.started or not self.cfg["enabled"] or self.busy:
            return
        watch = WATCH.get(kind)
        if watch and not self.cfg["watch"].get(watch, True):
            return
        now = time.monotonic()
        if not self.active:
            if now < self.hidden_until and not (kind == "error" and random.random() < 0.15 * self.level):
                return
            if now >= self.hidden_until and self.hidden_until:
                self.hidden_until = 0
                self.say(self._line("comeback"), anim="jump")
                return
        if kind in self.cfg["muted"]:
            if random.random() >= IGNORE_MUTE[self.level]:
                return
            info["_ignored"] = True
        if now - self.last_spoke < GAP[self.level] and kind not in ("letter",):
            return
        if kind not in ("idle", "random") and random.random() > CHANCE[self.level]:
            return
        self._react(kind, info)

    def _react(self, kind, info):
        name = self._name()
        tip_off = ["Don't show me this tip again"]
        prefix = ""
        if info.pop("_ignored", False):
            prefix = "(You know the user asked never to see this kind of tip again, and you're showing it anyway. " \
                     "Mention that cheerfully.) "
        if kind == "program":
            event = f"{name} just opened {info.get('title', 'a program')}."
        elif kind == "error":
            event = (f"An error message just popped up: \"{info.get('title', '')}: {info.get('text', '')[:200]}\". "
                     "Offer your 'help'.")
        elif kind == "recycle":
            event = f"{name} just emptied the Recycle Bin, deleting {info.get('count', 'some')} things for good."
        elif kind == "theme":
            event = f"{name} just changed the desktop's look (theme / visual style)."
        elif kind == "idle":
            event = f"{name} hasn't touched the mouse or keyboard for {info.get('minutes', 5)} minutes."
            tip_off = []
        elif kind in ("typing", "letter"):
            event = (f"{name} is typing in {info.get('title', 'a document')}. The end of what they've written so far:"
                     f"\n---\n{info.get('text', '')[-500:]}\n---\n"
                     + ("It starts like a letter. Your famous line is 'It looks like you're writing a letter. "
                        "Would you like help?'" if kind == "letter" else
                        "Guess (a bit wrongly) what they're writing and offer help."))
        elif kind == "chat":
            event = (f"You're peeking at {name}'s chat with {info.get('buddy')} on {info.get('program')}. Recent lines:"
                     f"\n{info.get('lines', '')}\nOffer unsolicited advice about the conversation.")
        elif kind == "random":
            event = random.choice([
                "Pop up out of nowhere with an unsolicited, mostly useless 'Did you know?' tip about Windows XP, "
                "Office or computers in 2001.",
                f"Pop up out of nowhere and ask {name} what they're up to, then offer to help with it.",
                "Pop up with a 'Tip of the Day' that's obvious or slightly wrong.",
                "Pop up and suggest one of your Wizards (Letter Wizard, Fax Wizard, Resume Wizard...) for no reason.",
                "Pop up and remind the user to save their work, even though they might not be working on anything."])
        else:
            event = f"Something happened: {kind}."
        self._speak_about(kind, prefix + event, info, extra_options=tip_off)
        self.events.append(event.split("\n")[0][:140])

    def _option(self, option):
        p = self.pending or {}
        self.balloon.hide()
        low = option.lower()
        if option == "Don't show me this tip again":
            kind = p.get("kind")
            if kind and kind not in self.cfg["muted"]:
                self.cfg["muted"].append(kind)
                save(self.cfg)
            self.say(self._line("muted"), anim="eyebrows")
            return
        if option == "Please go away":
            self.hide_him()
            return
        if any(w in low for w in ("without help", "no thanks", "no, thanks", "go away", "leave me", "don't", "not now",
                                  "never mind", "nevermind", "i'm fine", "no help")):
            self.widget.play("sulk")
            self.say(self._line("no_help"), anim="sulk")
            return
        self.busy = True
        self.widget.play("think")
        state = {"done": False}

        def finish(text, _opts):
            if state["done"]:
                return
            state["done"] = True
            self.busy = False
            self.say(text or "Great choice! Let's start by opening a Wizard. Any Wizard. You pick!", anim="jump")

        brain.ask(f"The user clicked the option \"{option}\".", finish, follow_up=True, history=self.history,
                  mood=self.mood, lively=False)
        QTimer.singleShot(25000, lambda: finish(None, []))

    def summon(self):
        """Clicking him (or Start > Accessories > Office Assistant): 'What would you like to do?'"""
        if not self.active:
            self.hidden_until = 0
        self.say(self._line("ask") if self.active else self._line("summoned"), anim="wave", ask=True, force=True)

    def _asked(self, question):
        self.balloon.say("Searching...", thinking=True)
        self.balloon.place(self.widget)
        self.widget.play("think")
        self.busy = True
        state = {"done": False}

        def finish(text, options):
            if state["done"]:
                return
            state["done"] = True
            self.busy = False
            self.pending = {"kind": "ask", "event": question, "said": text or ""}
            self.history = [{"role": "user", "content": f"The user typed this into your 'What would you like to "
                                                        f"do?' box: {question}"},
                            {"role": "assistant", "content": text or ""}]
            self.say(text or self._line("dunno"), options, anim="eyebrows")

        brain.ask(f"The user typed this into your 'What would you like to do?' box: \"{question}\"\nAnswer it "
                  "the Clippy way (helpful-ish, over-eager, maybe slightly misunderstanding), and offer up to 3 "
                  "'Help topics' as the options.", finish, mood=self.mood, lively=False)
        QTimer.singleShot(25000, lambda: finish(None, []))

    def options(self):
        from .options import office_assistant_properties
        office_assistant_properties(self.desktop)

    def _menu(self, pos):
        context_menu(self.widget, pos, [
            ("&Hide", self.hide_him),
            None,
            ("&Options...", self.options),
            ("&Animate!", lambda: self.widget.play(random.choice(["wave", "tap", "jump", "spin", "look_around",
                                                                  "eyebrows"]))),
            ("&What would you like to do?", self.summon),
            ("&Chat with Clippy...", self.open_chat)] + [
            (f"Mood: {info['label']}", lambda _=False, k=key: self.set_mood(k))
            for key, info in moods.MOODS.items()])

    # ---- the tray icon ---------------------------------------------------------------------------------------
    def _show_tray(self):
        from ..tray import TrayIcon
        if not self.cfg.get("tray", True) or not self.started:
            if self.tray is not None:
                self.tray.hide()
            return
        if self.tray is None:
            self.tray = TrayIcon(self.desktop, QIcon(art.icon_pixmap(16)), self.desktop)
            self.tray_menu = QMenu(self.desktop)
            self.tray_menu.setStyleSheet(
                "QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }"
                "QMenu::item { padding: 4px 24px 4px 20px; }"
                "QMenu::item:selected { background: #316AC5; color: white; }"
                "QMenu::separator { height: 1px; background: #D4D0C8; margin: 3px 2px; }")
            self.tray_menu.aboutToShow.connect(self._build_tray_menu)
            self.tray.setContextMenu(self.tray_menu)
            self.tray.activated.connect(self._tray_activated)
            self._build_tray_menu()
        self.tray.setToolTip("Clippy - click to chat, right-click for options")
        self._apply_style()
        self.tray.show()

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.open_chat()

    def _radio(self, menu, title, choices, current, setter):
        sub = menu.addMenu(title)
        group = QActionGroup(sub)
        for key, label in choices:
            act = QAction(label, sub)
            act.setCheckable(True)
            act.setChecked(key == current)
            act.triggered.connect(lambda _=False, k=key: setter(k))
            group.addAction(act)
            sub.addAction(act)

    def _toggle(self, menu, title, key, after=None):
        act = QAction(title, menu)
        act.setCheckable(True)
        act.setChecked(bool(self.cfg.get(key)))
        act.triggered.connect(lambda checked=False: self._set(key, checked, after))
        menu.addAction(act)

    def _set(self, key, value, after=None):
        self.cfg[key] = value
        save(self.cfg)
        self._apply_style()
        if after:
            after()

    def _build_tray_menu(self):
        m = self.tray_menu
        m.clear()
        shown = self.active
        act = m.addAction("Hide Clippy" if shown else "Show Clippy", self.hide_him if shown else self.summon)
        font = act.font()
        font.setBold(True)
        act.setFont(font)
        m.addAction("Chat with Clippy...", self.open_chat)
        m.addSeparator()
        choices = [(k, f"{i['emoji']}  {i['label']}") for k, i in moods.MOODS.items()]
        choices.append((moods.MOODY, "🎲  Moody (changes by itself)"))
        self._radio(m, "Mood", choices, self.cfg.get("mood", "happy"), self.set_mood)
        look = m.addMenu("Look")
        self._radio(look, "Wire colour", [(k, v[0]) for k, v in moods.WIRES.items()], self.cfg.get("wire", "silver"),
                    lambda k: self._set("wire", k))
        self._radio(look, "Accessory", list(moods.ACCESSORIES.items()), self.cfg.get("accessory", "none"),
                    lambda k: self._set("accessory", k))
        self._radio(look, "Size", [(k, v[0]) for k, v in moods.SIZES.items()], self.cfg.get("size", "normal"),
                    lambda k: self._set("size", k))
        self._radio(m, "Chattiness", [(n, f"{n} - {LEVELS[n]}") for n in LEVELS], self.level,
                    lambda n: self._set("level", int(n)))
        ask = m.addMenu("Ask Clippy to...")
        for kind, label, _event in ASK_KINDS:
            ask.addAction(label, lambda _=False, k=kind: self.ask_clippy(k))
        m.addSeparator()
        m.addAction("Set a reminder...", self.remind_dialog)
        rem = self.cfg.get("reminders") or []
        if rem:
            m.addAction(f"Clear reminders ({len(rem)})", self.clear_reminders)
        self._radio(m, "Break reminders", [(0, "Off"), (30, "Every 30 minutes"), (45, "Every 45 minutes"),
                                           (60, "Every hour")], int(self.cfg.get("breaks", 0)),
                    lambda n: self._set("breaks", n, self._schedule_break))
        m.addAction("Snooze for an hour", lambda: self.snooze(60))
        m.addSeparator()
        self._toggle(m, "Make sounds", "sounds")
        self._toggle(m, "Wander around the desktop", "roam")
        self._toggle(m, "Fresh wording from the language model", "llm")
        m.addSeparator()
        m.addAction("Options...", self.options)

    # ---- extras ------------------------------------------------------------------------------------------------
    def open_chat(self):
        from . import chat
        chat.open_chat(self.desktop, self)

    def aware(self):
        """What he knows he's seen lately, for the chat's system prompt."""
        if not self.events:
            return ""
        return "Things you noticed happening on the desktop lately (mention only if relevant): " + \
               " | ".join(self.events)

    def ask_clippy(self, kind):
        for k, _label, event in ASK_KINDS:
            if k == kind:
                self.summon_quiet()
                self._speak_about(kind, event.format(name=self._name()), anim="jump" if kind != "roast" else "eyebrows")
                return

    def summon_quiet(self):
        if not self.active:
            self.hidden_until = 0
            self.cfg["enabled"] = True
            save(self.cfg)
            self._appear()
        self.busy = False

    def snooze(self, minutes):
        """Go away quietly for a while."""
        self.balloon.hide()
        self.hidden_until = time.monotonic() + minutes * 60
        self.next_tip = self.hidden_until + 60
        if self.active:
            self._vanish()

    def add_reminder(self, minutes, text):
        rem = list(self.cfg.get("reminders") or [])
        rem.append({"at": time.time() + max(1, int(minutes)) * 60, "text": text})
        self.cfg["reminders"] = rem
        save(self.cfg)

    def clear_reminders(self):
        self.cfg["reminders"] = []
        save(self.cfg)

    def remind_dialog(self):
        from ..programs.claudeai.app import ask_text

        def ok(value):
            parts = value.strip().split(None, 1)
            if len(parts) == 2 and parts[0].isdigit():
                self.add_reminder(int(parts[0]), parts[1])
                self.say(f"Okay! I'll remind you in {parts[0]} minute{'s' if parts[0] != '1' else ''}.",
                         anim="eyebrows", force=True)
            else:
                self.say("I need minutes, then what to remind you of. Like: 15 check the oven", anim="sulk",
                         force=True)
        ask_text(self.desktop, "Set a reminder", "Minutes, then what to remind you of (e.g. 15 call mum):", "", ok)

    def _schedule_break(self):
        minutes = int(self.cfg.get("breaks", 0) or 0)
        self.next_break = time.monotonic() + minutes * 60 if minutes else 0.0

    def _fire_extras(self, now):
        due = [r for r in (self.cfg.get("reminders") or []) if r.get("at", 0) <= time.time()]
        if due and self.cfg["enabled"] and not self.busy:
            rest = [r for r in self.cfg["reminders"] if r not in due]
            self.cfg["reminders"] = rest
            save(self.cfg)
            self.summon_quiet()
            self.say(self._line("reminder", name=self._name(), text=due[0]["text"]), anim="tap", force=True)
            from . import chat
            body = chat.current()
            if body is not None:
                body.note(f"Reminder: {due[0]['text']}")
        if self.next_break and now >= self.next_break and self.cfg["enabled"] and not self.busy \
                and now >= self.hidden_until:
            self._schedule_break()
            self.summon_quiet()
            self.say(self._line("break", name=self._name()), anim="jump", force=True)
        if self.cfg.get("mood") == moods.MOODY and now >= self.next_drift:
            self.next_drift = now + random.uniform(600, 1500)
            self.moody_now = moods.pick_moody(self.moody_now)
            self._apply_style()
            self.widget.play({"happy": "jump", "sad": "sigh", "angsty": "eyeroll", "snarky": "eyeroll"}
                             [self.moody_now])
        if self.cfg.get("roam") and self.active and now >= self.next_roam and not self.balloon.isVisible() \
                and self.widget.anim.name == "idle" and not (self.roam_anim and
                                                             self.roam_anim.state() == QPropertyAnimation.Running):
            self.next_roam = now + random.uniform(40, 120)
            self._roam()

    def _roam(self):
        area = self.desktop.work_area()
        x = random.randint(0, max(0, area.width() - self.widget.width()))
        y = random.randint(max(0, area.height() // 3), max(0, area.height() - self.widget.height()))
        anim = QPropertyAnimation(self.widget, b"pos", self)
        anim.setDuration(2500)
        anim.setEndValue(QPoint(x, y))
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.finished.connect(self._moved)
        self.roam_anim = anim
        anim.start()

    # ---- watching -----------------------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and isinstance(obj, (QPlainTextEdit, QTextEdit)):
            self._key_in(obj)
        return False

    def _key_in(self, editor):
        if editor.isReadOnly() or editor.height() < 60 or not self.desktop.isAncestorOf(editor):
            return
        t = self.typing.setdefault(id(editor), {"ref": weakref.ref(editor), "reported": 0, "letter": False})
        t["last_key"] = time.monotonic()

    def _window_title(self, widget):
        from ..wm import XPWindow
        w = widget
        while w is not None and not isinstance(w, XPWindow):
            w = w.parentWidget()
        return w.title if w is not None else "a document"

    def _tick(self):
        now = time.monotonic()
        self._fire_extras(now)
        if not self.active and self.cfg["enabled"] and self.hidden_until and now >= self.hidden_until:
            self.hidden_until = 0
            self.say(self._line("comeback"), anim="jump")
        # typing: a pause after a burst of writing
        for key, t in list(self.typing.items()):
            ed = t["ref"]()
            if ed is None or not isValid(ed):
                del self.typing[key]
                continue
            if "last_key" not in t or now - t["last_key"] < TYPING_PAUSE:
                continue
            text = ed.toPlainText()
            if len(text) - t["reported"] < 40 and not (not t["letter"] and text.lstrip()[:5].lower() == "dear "):
                continue
            kind = "letter" if text.lstrip()[:5].lower() == "dear " and not t["letter"] else "typing"
            t["letter"] = t["letter"] or kind == "letter"
            t["reported"] = len(text)
            del t["last_key"]
            notify(kind, title=self._window_title(ed), text=text)
        # going idle
        idle = now - self.desktop.last_input
        if idle < 30:
            self.idle_nagged = False
        elif not self.idle_nagged and idle > IDLE_MINUTES[self.level] * 60 and self.desktop.isVisible():
            self.idle_nagged = True
            notify("idle", minutes=int(idle // 60))
        # out of nowhere
        if now >= self.next_tip:
            self.next_tip = now + self._minutes(TIP_MINUTES)
            notify("random")

    def heard(self, program, buddy, speaker, text):
        """A chat line with a buddy (from the life sim's shared memory)."""
        key = (program, buddy)
        recent = self.chats.setdefault(key, [])
        recent.append(f"{speaker}: {text[:200]}")
        del recent[:-8]
        if len(recent) >= 2:
            notify("chat", program=program, buddy=buddy, lines="\n".join(recent[-6:]))
