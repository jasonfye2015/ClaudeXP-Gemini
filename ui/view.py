"""The view: the night drawn in first person, and over it as little as possible - a place's name when he first comes
into it, the fade in from black, a word about the mouse, and his own state in two orbs (ui/orbs.py): health and
poison, sanity and stupor. What she thinks of him has no meter: that will show in the den itself.

Keys: W A S D walk, Shift run, Space jump, the mouse looks (click to take it, Esc gives it back and pauses), E (or L) shake the
lantern when it gutters out. On a strand, A and D lean against its sway.

The sound (ui/audio.py) hears what the night does, and follows the computer's mute."""
import math
import queue
import time

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QColor, QCursor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient,
                           QSurfaceFormat)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from ..game.night import Input
from . import dial, fonts, orbs
from ..game.death import ENDING

SENS = 0.0022
SERIF = "Georgia"


class GameView(QOpenGLWidget):
    def __init__(self, shell):
        super().__init__(shell)
        self.shell = shell
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setDepthBufferSize(24)
        fmt.setSamples(4)
        fmt.setSwapInterval(1)
        self.setFormat(fmt)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.night = None
        self.playing = False
        self.renderer = None
        self.gl_error = None
        self.keys = set()
        self.inp = Input()
        self.captured = False
        self.cards = []                          # (title, line, born)
        self.outs = 0                            # (how often the lantern has gone out: the hint shows the first times)
        self.whisper = None                      # (a few small words low on the screen: (words, when, how long))
        self.teeters = 0                         # (how often he's teetered on a strand: the hint shows the first times)
        self.tally = None                        # (this night's tallies, for the records)
        self.first_ending = False
        self.audio = None
        self.fade = None                         # (born): in from black
        from .satchel import Satchel
        self.satchel = Satchel()                 # (his satchel, opened: Tab - the night going on behind it)
        self.flying = None                       # (a thing just picked up, on its way into the satchel: (item, when))
        from .journal import Journal
        self.journal = Journal(self)             # (his notebook, in his hands: Esc - the night going on around it)
        self.glance = 0.0                        # (how far he's looking down, into it)
        self.director = None                     # (Spellbound, or F9: the letter leading him - game/autoplay.py)
        self.tutorial = None                     # (the first night: game/tutorial.py)
        self.guide = None                        # (and the letter leading him between its lessons)
        self.speed = 1                           # (F10: how fast the letter leads, between words to read)
        self.read_seen = set()
        self.reading_until = 0.0
        self.ui_did = {}
        self.auto_journal_until = None
        self.tut_travel = None
        self.last = time.perf_counter()
        self.t0 = self.last
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(0)

    # ---- GL ----------------------------------------------------------------------------------------------------
    def initializeGL(self):
        try:
            from ..engine.render import Renderer
            self.renderer = Renderer()
        except Exception as exc:                  # (shown on the view, not lost)
            import traceback
            traceback.print_exc()
            self.gl_error = str(exc)

    def paintGL(self):
        now = time.perf_counter() - self.t0
        if self.renderer and self.night:
            try:
                dpr = self.devicePixelRatioF()
                self.renderer.draw(self.night, int(self.width() * dpr), int(self.height() * dpr), now)
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self.gl_error = repr(exc)
        p = QPainter(self)
        try:
            if self.gl_error:
                p.fillRect(self.rect(), QColor(8, 6, 10))
                p.setPen(QColor(220, 200, 190))
                p.drawText(self.rect().adjusted(30, 30, -30, -30), Qt.TextWordWrap, "The den couldn't be drawn:\n\n" + self.gl_error)
            elif self.playing:
                self.hud(p, now)
        finally:
            p.end()

    # ---- the loop ----------------------------------------------------------------------------------------------
    def begin(self, night, talk_state=None):
        """A night: new (saved at once, as its first act begins), or gone on with from a save (talk_state: what was
        said and kept)."""
        self.night = night
        self.playing = True
        night.show_lantern = True
        self.outs = 0
        self.teeters = 0
        self.whisper = None
        self.tally = {"bites": 0, "slips": 0, "falls": 0, "swipes": 0, "shakes": 0, "done": False,
                      "from": night.time, "resumed": talk_state is not None}
        self.first_ending = False
        self.inp.yaw, self.inp.pitch = night.yaw, night.pitch
        self.inp.strafe = self.inp.forward = 0.0
        self.ensure_audio()
        from ..game.dialogue import Conversation
        from ..game.voice import Voice
        rec = self.shell.records
        voice = Voice(rec.options.get("voice") or "none")
        self.talk = Conversation(night, voice, dict(rec.reputation))
        from ..game import hidden
        self.talk.knows_her = hidden.knows(rec.notes)
        if talk_state:
            self.talk.memory = list(talk_state.get("memory", []))
            self.talk.lies = int(talk_state.get("lies", 0))
        if self.talk.mode == "model":
            voice.warm()                                          # (her words: the model loaded while he walks in)
        self.scene = self.scene_ui = None
        self.her_lines = queue.Queue()
        self.her_line = None                                      # (her words on screen: (text, when))
        self.last_murmur = -99.0
        self.fade = time.perf_counter()
        self.cards = []
        self.setFocus()
        from ..game.autoplay import Director
        from ..game.tutorial import Tutorial
        self.director = Director(night) if night.charmed() else None
        self.tutorial, self.guide, self.tut_travel = None, None, None
        if night.flags.get("first"):
            self.tutorial = Tutorial(night)
            self.guide = Director(night, guide=True)
            order = ("threshold", "audience", "gallery", "supper", "crown", "dawn")
            while self.tutorial.lesson and order.index(self.tutorial.lesson[1]) < order.index(night.acts.act):
                self.tutorial.skip()                             # (gone on with from a save: what's past, past)
        self.speed, self.read_seen, self.reading_until, self.ui_did = 1, set(), 0.0, {}
        self.auto_journal_until = None
        if talk_state is None:
            self.shell.saves.save("act", night, self.talk)       # (the first act, begun)
        else:
            self.whisper = ("You go on, where you were.", time.perf_counter(), 3.0)

    def quick_save(self):
        """F5, or "Save here": -> None if saved, or why it couldn't be."""
        from ..game.saving import why_not
        n = self.night
        if n is None or not self.playing:
            return "Not now."
        why = why_not(n, scene=getattr(self, "scene", None) is not None)
        if why is None and not self.shell.saves.save("quick", n, self.talk):
            why = "It couldn't be saved."
        if why is None:
            self.ui_did["saved"] = True
        return why

    def backdrop(self, night):
        """The title's backdrop: standing at the foot of the hollow, turning slowly, looking up into the dark."""
        self.night = night
        self.playing = False
        night.show_lantern = False                   # (no hand in the title's view)
        night.x, night.z = 0.8, 0.4
        night.y = night.tree.ground(0.8, 0.4)

    def tick(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last)
        self.last = now
        n = self.night
        if n is None:
            return
        if self.audio is not None:
            o = self.shell.records.options
            self.audio.volume = o["volume"] / 100.0
            self.audio.heartbeat = bool(o["heartbeat"])
            self.audio.aloud = bool(o["aloud"])
            self.audio.synth.music_gain = 0.7 * o.get("music", 70) / 70.0
            self.audio.score(n, getattr(self, "scene", None), self.playing)
        o = self.shell.records.options
        for k in n.afflict.opts:                                     # (what the night's let do to him: Options)
            n.afflict.opts[k] = bool(o.get(k, True))
        n.steady = bool(self.shell.records.options.get("steady", False))
        ui = getattr(self, "scene_ui", None)                      # (her mouth: with her voice, or her words coming)
        level = self.audio.synth.speech_level() if self.audio is not None else 0.0
        if level <= 0.02 and ui is not None and getattr(ui, "her_text", "") and ui._shown() < len(ui.her_text):
            level = 0.45 + 0.4 * abs(math.sin(now * 13.0))
        n.her.voice += (level - n.her.voice) * 0.5
        n.shadows = bool(self.shell.records.options.get("shadows", True))
        n.brightness = self.shell.records.options.get("brightness", 50)
        if self.playing and n.ending is not None and not self.shell.panel_open():     # (dawn: how it ends)
            n.step(dt, self.inp)
            if self.audio is not None:
                fire = n.ending.name == "Fire" and not n.ending.done
                self.audio.synth.set(rain=min(1.0, n.ending.t / 2.0) if fire else 0.0)   # (the roar of it)
            for e in n.events:
                if e[0] == "ending" and e[1] == "line":
                    if self.audio is not None:
                        self.audio.say(e[2])
            if n.ending.done:
                self.release()
                if self.tally is not None and not self.tally["done"]:
                    self.first_ending = self.shell.records.ending(n.ending.name)
                    self.night_done()
                if self.director is not None and n.ending.t > 20.0:
                    self.shell.show_title()                       # (led: it ends, and he wakes at the title)
                    return
            n.events.clear()
        elif self.playing and n.dying is not None and not self.shell.panel_open():      # (the end of him: no hands on it)
            if not n.dying.asked:                                 # (her last words to him: what she made of him)
                self._last_words(n)
            n.step(dt, self.inp)
            if self.audio is not None:
                self.audio.hear(n, n.events)
            for e in n.events:
                if e[0] == "death" and e[1] == "line" and self.audio is not None:
                    self.audio.say(e[2])
            from ..game.death import FADE_END
            d = n.dying
            if d.her_side and not d.side_said and d.t >= FADE_END + 0.6:   # (her side of it: aloud, too)
                d.side_said = True
                if self.audio is not None:
                    self.audio.say(" ".join(d.her_side))
            if n.dying.done:
                self.release()
                if self.tally is not None and not self.tally["done"]:
                    self.first_ending = self.shell.records.ending(ENDING[0].split(": ")[1])
                    self.night_done()
            n.events.clear()
        elif self.playing and getattr(self, "scene", None) is not None and not self.shell.panel_open():
            self._scene_tick(n, dt)                               # (her scene: his hands off; the night goes on)
        elif self.playing and not self.shell.panel_open():
            scene = n.acts.scene_for(n) if n.dying is None and n.ending is None else None
            if scene is not None and scene not in n.met:
                self.start_scene(scene)                           # (where he is, in the night's act: she comes to him)
            k = self.keys
            drive = self._drive()
            if drive is None:
                self.inp.forward = (1 if Qt.Key_W in k or Qt.Key_Up in k else 0) - \
                    (1 if Qt.Key_S in k or Qt.Key_Down in k else 0)
                self.inp.strafe = (1 if Qt.Key_D in k else 0) - (1 if Qt.Key_A in k else 0)
                self.inp.hurry = Qt.Key_Shift in k
                if self.satchel.open or self.journal.open:        # (his hands full: he stands still)
                    self.inp.forward = self.inp.strafe = 0.0
                    self.inp.jump = False
                if Qt.Key_Left in k:
                    self.inp.yaw -= 1.8 * dt
                if Qt.Key_Right in k:
                    self.inp.yaw += 1.8 * dt
            steps = 1
            if drive is self.director and drive is not None and now >= self.reading_until and not self.journal.open:
                steps = self.speed * (2 if drive.idle else 1)     # (F10; and faster still with nothing to do)
            for _ in range(min(16, steps)):
                if drive is not None:
                    self._requests(drive.step(dt, n, self.inp), n)
                want = 0.5 if self.journal.open else 0.0          # (he looks down into it)
                self.glance += (want - self.glance) * min(1.0, dt * 6.0)
                mine = self.inp.pitch
                self.inp.pitch = max(-1.45, mine - self.glance)
                n.step(dt, self.inp)
                self.inp.pitch = mine
                if n.ending is not None or n.dying is not None or n.acts.scene_for(n):
                    break
            self._lessons(n, dt)
            self._watch_text(now)
            self._afflict_events(n, now)
            if self.journal.open and any(e[0] in ("crawler", "bitten", "collapse") or e == ("dangler", "face") or
                                         e in (("her", "strike"), ("her", "bite")) for e in n.events):
                self.journal.close(knocked=True)                  # (knocked from his hands)
            if self.audio is not None:
                self.audio.hear(n, n.events)
            self._count(n.events)
            self._satchel_events(n, now)
            self._notes_from(n)
            self._murmurs(n)
            for e in n.events:
                if e[0] == "act" and e[1] != "dawn":                 # (an act begun: the night saved)
                    self.shell.saves.save("act", n, self.talk)
                if e[0] == "place":
                    self.cards.append((e[1], e[2], now))
                elif e[0] == "lantern" and e[1] == "out":
                    self.outs += 1
                elif e[0] == "lantern" and e[1] == "failed":
                    self.whisper = ("It won't catch.", now, 2.5)
                elif e[0] == "silk" and e[1] == "first":
                    self.whisper = ("The silk gives under you, and hums. Somewhere, something feels it.", now, 5.0)
                elif e[0] == "silk" and e[1] == "teeter":
                    self.teeters += 1
                elif e[0] == "silk" and e[1] == "caught":
                    self.whisper = ("Caught in her silk. Everything in the oak felt that.", now, 4.0)
                elif e == ("her", "bite"):
                    self.whisper = ("She bit you.", now, 3.0)
                elif e[0] == "bitten":
                    self.whisper = ("Bitten." if e[1] == "face" else "Something bit your hand.", now, 2.5)
                elif e[0] == "hurt" and e[1] > 20:
                    self.whisper = ("You hit the wood hard.", now, 2.5)
                elif e == ("venom", "in"):
                    self.whisper = ("Her venom is in you. It will not wear off before dawn.", now, 5.0)
                elif e[0] == "vision_end":
                    self.whisper = ("You are yourself again.", now, 2.5)
                elif e[0] == "take" and e[1] == "antidote":
                    self.whisper = ("Q  -  drink it, while her venom is in you", now, 6.0)
                elif e[0] == "spell":
                    self.whisper = (self.SPELL_WORDS.get((e[1], e[2]), ""), now, 3.0)
                elif e == ("her", "hurt"):
                    self.whisper = ("Somewhere above, something hisses and pulls back from the light.", now, 4.0)
                elif e[0] == "ablaze":
                    self.whisper = ("It catches.", now, 4.0)
                elif e[0] == "smoulder":
                    self.whisper = ("The silk blackens under your hand, and smokes. The whole oak shudders.", now, 5.0)
                elif e == ("sight", "behind"):
                    self.whisper = ("...", now, 1.5)
                elif e[0] == "mark":
                    self.whisper = ("The light finds something cut into the wood.", now, 4.0)
            n.events.clear()
        elif not self.playing:
            n.time += dt
            n.yaw = (now - self.t0) * 0.06
            n.pitch = 0.62 + 0.08 * math.sin((now - self.t0) * 0.1)
            n.her.step(dt, n)                            # (and her, up there, watching the title)
        self.update()

    # ---- her scenes -----------------------------------------------------------------------------------------------
    def start_scene(self, name):
        n = self.night
        if getattr(self, "scene", None) is not None or n is None or n.dying is not None or getattr(self, "talk", None) is None:
            return
        if n.tree.in_tunnel(n.x, n.z) and n.tree.in_tunnel(n.x, n.z)[0] > 0.2:
            return                                                # (not in the root tunnel: no room for her)
        from ..game.scene import Scene
        from .scene import SceneView
        self.journal.close()                                     # (she's here: the notebook down)
        if self.satchel.open:
            self.satchel.toggle()
        self.release()
        self.keys.clear()
        self.inp.forward = self.inp.strafe = 0.0
        self.inp.hurry = self.inp.jump = False
        self.scene = Scene(n, name)
        self.scene_ui = SceneView(self.shell, self.scene, self.talk, self._scene_over)
        n.met.setdefault(name, None)

    def _scene_tick(self, n, dt):
        sc = self.scene
        self.inp.yaw, self.inp.pitch = n.yaw, n.pitch
        n.step(dt, self.inp)
        if n.ending is not None:                                 # (fire: no more talk - it's how it ends)
            self.scene_ui.hide()
            self.scene_ui.deleteLater()
            self.scene = self.scene_ui = None
            n.riders = ()
            self.setFocus()
            return
        sc.step(dt)
        self.inp.yaw = n.yaw                                     # (he faces her)
        n.camera = sc.camera() if sc.placed and n.her.staged is not None else None
        n.riders = sc.rider_poses()
        if self.audio is not None:
            self.audio.synth.set(breath=1.0 if sc.placed else 0.0)
            self.audio.hear(n, n.events)
        n.events.clear()

    def _scene_over(self):
        n = self.night
        name = self.scene.name
        n.met[name] = self.talk.ended or "done"
        n.lies = self.talk.lies
        for e in n.acts.scene_over(name, n.met[name], n):
            n.events.append(e)
            if e == ("meal",):                                    # (her larder: he was the meal - her bite)
                self.whisper = ("She bit you.", time.perf_counter(), 3.0)
                n.bitten()
        if name == "crown":
            self.whisper = ("T  -  wait with her for the light", time.perf_counter(), 8.0)
        n.camera, n.riders = None, ()
        self.inp.yaw, self.inp.pitch = n.yaw, 0.0
        if self.audio is not None:
            self.audio.synth.set(breath=0.0)
        self.scene_ui.hide()
        self.scene_ui.deleteLater()
        self.scene = self.scene_ui = None
        self.setFocus()

    def _prompt(self, n):
        from ..game.offerings import ITEMS
        spot = n.cocoons.near(n)
        if spot is not None:
            keep = n.KEEPSAKES.get(spot["id"])
            if spot["id"] in n.cocoons.burst and keep and keep not in n.taken:
                return "take " + ITEMS[keep][0]
            return "look closer"
        item = n.finds.near(n)
        return ("take " + ITEMS[item][0]) if item else None

    def _venom(self, p, W, H, n):
        """Her venom in him: the edges of his sight darkening, pulsing; and, now and then, her eyes instead of his."""
        v = n.venom
        if v.active and v.vision is None:
            fx = self.shell.records.options.get("venom_fx", True)
            pulse = 0.5 + 0.5 * math.sin(time.perf_counter() * 2.2) if fx else 0.5
            g = QRadialGradient(QPointF(W / 2, H / 2), max(W, H) * 0.72)
            g.setColorAt(0.45 if fx else 0.55, QColor(10, 18, 6, 0))
            g.setColorAt(1, QColor(10, 18, 6, int(150 + 80 * pulse) if fx else 150))
            p.fillRect(QRectF(0, 0, W, H), g)
        if v.vision is None:
            return
        from ..game.venom import VISIONS, VISION_FOR
        vid, age = v.vision
        a = max(0.0, min(1.0, age / 0.8, (VISION_FOR - age) / 0.8))
        p.fillRect(QRectF(0, 0, W, H), QColor(60, 110, 30, int(45 * a)))         # (her sight: green, and strange)
        g = QRadialGradient(QPointF(W / 2, H / 2), max(W, H) * 0.62)
        g.setColorAt(0.5, QColor(0, 0, 0, 0))
        g.setColorAt(1, QColor(4, 10, 2, int(235 * a)))
        p.fillRect(QRectF(0, 0, W, H), g)
        p.setBrush(Qt.NoBrush)
        for i in range(8):                                                       # (eight eyes: eight rounds of seeing)
            ang = i / 8 * math.tau + 0.3
            cx, cy = W / 2 + math.cos(ang) * W * 0.32, H / 2 + math.sin(ang) * H * 0.34
            rr = min(W, H) * (0.16 if i % 2 else 0.11)
            p.setPen(QColor(150, 200, 120, int(40 * a)))
            p.drawEllipse(QPointF(cx, cy), rr, rr)
        p.setFont(fonts.her(self.shell.records, 26))
        box = QRectF(W * 0.12, H * 0.06, W * 0.76, H * 0.2)
        p.setPen(QColor(0, 0, 0, int(170 * a)))
        p.drawText(box.translated(2, 2), Qt.AlignHCenter | Qt.TextWordWrap, VISIONS[vid][0])
        p.setPen(QColor(220, 240, 200, int(235 * a)))
        p.drawText(box, Qt.AlignHCenter | Qt.TextWordWrap, VISIONS[vid][0])

    def _spell_glow(self, p, W, H, n):
        """His spells, shining: Light hung above him, Warmth in his palm, an ember on the silk; and which are ready."""
        sp = n.spells
        r = self.renderer
        if r is not None and getattr(r, "pv", None) is not None:
            import numpy as np
            for kind, pos, _w, _l in sp.lit:
                k = sp.shining(kind)
                if k <= 0 or kind not in ("light", "warmth", "ember"):
                    continue
                c = r.pv @ np.array((*pos, 1.0), np.float32)
                if c[3] <= 0.05:
                    continue
                x, y = (c[0] / c[3] * 0.5 + 0.5) * W, (0.5 - c[1] / c[3] * 0.5) * H
                size = {"light": 60.0, "warmth": 34.0, "ember": 22.0}[kind] / max(0.4, c[3]) * 2.0
                col = {"light": (225, 235, 255), "warmth": (255, 170, 80), "ember": (255, 110, 40)}[kind]
                g = QRadialGradient(QPointF(x, y), size)
                g.setColorAt(0, QColor(*col, int(230 * k)))
                g.setColorAt(0.25, QColor(*col, int(110 * k)))
                g.setColorAt(1, QColor(*col, 0))
                p.setCompositionMode(QPainter.CompositionMode_Plus)
                p.fillRect(QRectF(x - size, y - size, size * 2, size * 2), g)
                p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        if sp.illusion:                                           # (Illusion: a faint shimmer at the edges)
            a = int(40 + 20 * math.sin(time.perf_counter() * 3))
            g = QRadialGradient(QPointF(W / 2, H / 2), max(W, H) * 0.7)
            g.setColorAt(0.6, QColor(150, 160, 255, 0))
            g.setColorAt(1, QColor(150, 160, 255, a))
            p.fillRect(QRectF(0, 0, W, H), g)
        f = QFont(SERIF, 10)
        p.setFont(f)
        x = W / 2 - 144
        for i, (name, word) in enumerate((("light", "Light"), ("warmth", "Warmth"), ("illusion", "Illusion"),
                                          ("memory", "Memory"))):
            p.setPen(QColor(215, 200, 175, 190 if sp.ready(name) else 70))
            p.drawText(QRectF(x + i * 72, H - 112, 72, 20), Qt.AlignLeft, f"{i + 1}  {word}")

    SATCHEL_WORDS = {"full": "Your satchel is full. Put something down first (wheel to it, then G).",
                     "mouse_still": "The mouse in your satchel has stopped kicking.",
                     "moth_out": "A moth gets out of your satchel.",
                     "moths_gone": "The last of the moths gets away.",
                     "honey": "Honey on your fingers - and something small has found it."}

    def _satchel_events(self, n, now):
        """What's carried, as it changes: picked up (into its place on the strip), put down, tiring, escaping."""
        from ..game.offerings import ITEMS
        for e in n.events:
            if e[0] == "take":
                self.flying = (e[1], now)
                if self.audio is not None:
                    self.audio.synth.play("puff", 0.6)
            elif e[0] == "satchel":
                self.whisper = (self.SATCHEL_WORDS.get(e[1], ""), now, 3.5)
            elif e[0] == "put_down":
                st = e[1]
                self.whisper = ({"mouse": "It's gone into the roots before it touches the wood.",
                                 "moths": "They're gone, up into the dark."}.get(st) if st not in n.finds.dropped
                                else "You set down " + ITEMS[st][0] + ".", now, 3.0)
        for item, line in n.learned:                             # (what she made of it: written beside it, kept)
            if self.shell.records.learn(item, line):
                self.note_toast = ("Beside " + ITEMS[item][0] + ": " + line, time.perf_counter())
        n.learned.clear()

    # ---- led by her letter, and the first night --------------------------------------------------------------------
    AFFLICT_WORDS = {"pant": "You can't get your breath.", "bleed": "Something warm runs from your eyes.",
                     "bloodied": "Blood down the wand, over the lantern. Everything is red.",
                     "vomit": "It comes up before you can stop it.", "foam": "Foam at your mouth. Your heart misses a beat.",
                     "coat": "Over the wand, the lantern - the light goes green.  (E: shake some of it off)",
                     "sway": "The walls are breathing.", "crawl": "Your legs won't hold you. Down, on your hands.",
                     "stand": "You get to your feet again.", "eye_taken": "It's in your hand. Your eye.",
                     "refuse": "No.", "fall": "The wood comes up to meet you.", "lost": "...",
                     "haze": "Everything shimmers, far away."}
    AFFLICT_MURMUR = {"pant": "pant", "bloodied": "blood", "prey": "prey", "vomit": "sick", "eye_taken": "eye"}

    def _afflict_events(self, n, now):
        talk = getattr(self, "talk", None)
        for e in n.events:
            if e[0] != "afflict":
                continue
            words = self.AFFLICT_WORDS.get(e[1])
            if words:
                self.whisper = (words, now, 3.5)
            mk = self.AFFLICT_MURMUR.get(e[1])
            if mk and talk is not None and not n.flags.get("said_" + mk):
                n.flags["said_" + mk] = True                     # (she notices: once a night, each)
                self.last_murmur = n.time
                talk.murmur(mk, self.her_lines.put)

    def _afflict_hud(self, p, W, H, n, t):
        """His sight, as the night has left it: tints, his eyes bleeding at the edges, foam at his mouth, the dark
        where his left eye was, the moments lost."""
        af = n.afflict
        gore = af.on("health", "gore")
        h, po = af.tier("health"), af.tier("poison")
        beat = 0.0
        if n.body.beats:
            beat = math.exp(-(n.body.t - n.body.beats[-1]) * 5.0)
        if h >= 2:
            p.fillRect(QRectF(0, 0, W, H), QColor(150, 10, 10, 22 + int(10 * beat)))
            if gore:                                                  # (from his eyes: at the sides, with each beat)
                for side in (0, 1):
                    for i in range(4):
                        seed = side * 7 + i * 3.1
                        x = (8 + i * 17 + 6 * math.sin(seed)) if side == 0 else W - (8 + i * 17 + 6 * math.sin(seed))
                        length = H * (0.18 + 0.22 * (0.5 + 0.5 * math.sin(t * 0.13 + seed))) * (0.9 + 0.1 * beat)
                        g = QLinearGradient(QPointF(x, 0), QPointF(x, length))
                        g.setColorAt(0, QColor(120, 0, 0, 210))
                        g.setColorAt(1, QColor(150, 5, 5, 0))
                        p.setPen(QPen(g, 3.5 + 2 * (i % 2)))
                        p.drawLine(QPointF(x, 0), QPointF(x + 2 * math.sin(seed), length))
                        u = ((t * 0.35 + i * 0.27 + side * 0.5) % 1.0)  # (a drop, running down)
                        p.setPen(Qt.NoPen)
                        p.setBrush(QColor(130, 0, 0, int(220 * (1 - u))))
                        p.drawEllipse(QPointF(x, length + u * H * 0.5), 3.5, 5.0)
        if po >= 2:
            p.fillRect(QRectF(0, 0, W, H), QColor(40, 120, 20, 20))
            if gore:                                                  # (foam, and drips, at the bottom of his sight)
                p.setPen(Qt.NoPen)
                for i in range(46):
                    x = W * ((i * 0.618034) % 1.0)
                    edge = abs(x - W / 2) / (W / 2)
                    y = H - 4 - 22 * (0.5 + 0.5 * math.sin(t * 1.7 + i)) * (0.4 + 0.6 * edge)
                    r = 4 + 5 * abs(math.sin(i * 1.3 + t * 0.6))
                    p.setBrush(QColor(200, 230, 170, 120))
                    p.drawEllipse(QPointF(x, y), r, r)
                for i in range(6):
                    x = W * (0.12 + 0.76 * ((i * 0.381966) % 1.0))
                    u = (t * 0.25 + i * 0.37) % 1.0
                    g = QLinearGradient(QPointF(x, H * 0.82), QPointF(x, H))
                    g.setColorAt(0, QColor(90, 170, 40, 0))
                    g.setColorAt(1, QColor(90, 170, 40, 160))
                    p.setBrush(g)
                    p.drawRoundedRect(QRectF(x - 3, H * (0.82 + 0.1 * u), 6, H * 0.18), 3, 3)
        ph = af.phase()
        if ph and ph[0] == "vomit" and gore and 0.8 < ph[1] < 1.9:     # (it comes up)
            k = (ph[1] - 0.8) / 1.1
            p.setPen(Qt.NoPen)
            col = (90, 140, 20) if po >= 3 else (110, 100, 35)
            for i in range(30):
                a = -math.pi / 2 + (i / 30 - 0.5) * 1.6
                d = H * (0.15 + 0.25 * k) * (0.6 + 0.4 * ((i * 0.618) % 1.0))
                x, y = W / 2 + math.cos(a) * d * 0.8, H + math.sin(a) * d + H * 0.35 * k * k
                p.setBrush(QColor(*col, int(200 * (1 - k))))
                p.drawEllipse(QPointF(x, y), 10 + 8 * ((i * 0.37) % 1.0), 8 + 6 * ((i * 0.53) % 1.0))
        dark = 1.0 if af.eye_lost else 0.0
        if ph and ph[0] == "eye":
            dark = max(dark, min(1.0, max(0.0, (ph[1] - 1.5) / 0.4)))
        if dark > 0:                                                  # (where his left eye was)
            g = QLinearGradient(QPointF(0, 0), QPointF(W * 0.48, 0))
            g.setColorAt(0, QColor(0, 0, 0, int(250 * dark)))
            g.setColorAt(0.55, QColor(0, 0, 0, int(225 * dark)))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            p.fillRect(QRectF(0, 0, W * 0.48, H), g)
        if af.blackout > 0:
            p.fillRect(QRectF(0, 0, W, H), QColor(0, 0, 0, int(255 * af.blackout)))

    def _drive(self):
        """Who walks him now: the letter (Spellbound, F9), its guiding between lessons, or him."""
        if self.director is not None:
            return self.director
        t = self.tutorial
        if t is not None and not t.done and not t.his_turn and self.guide is not None:
            return self.guide
        return None

    def _requests(self, reqs, n):
        for r in reqs:
            if r == ("dawn",):
                self.wait_for_dawn()
            elif r[0] == "done" and self.tutorial is not None:
                self.tutorial.arrived()

    def _lessons(self, n, dt):
        """The first night: its lessons, on - and where the letter leads between them."""
        t = self.tutorial
        if t is None or t.done:
            return
        at = t.at
        for r in t.step(dt, n, list(n.events), self.ui_did):
            if r[0] == "travel" and self.tut_travel != (t.at, r[1]):
                from ..game.tutorial import travel_task
                self.tut_travel = (t.at, r[1])
                task = travel_task(r[1], n, self.guide.nav)
                self.guide.tasks = [task] if task else []
                self.guide.path, self.guide.goal = [], None
                if task is None:
                    t.arrived()
            elif r == ("call", "supper") and n.acts.act == "gallery":
                n.acts._go("supper", n.events)                 # (she calls him down)
        if t.at != at:
            self.ui_did = {}
            if t.done:
                self.whisper = ("That's all of it. The rest of the night is yours.", time.perf_counter(), 5.0)

    def _watch_text(self, now):
        """Words on the screen, new: while the letter leads, time to read them (a second, and a third of one a word)."""
        if self._drive() is None:
            return
        n = self.night
        seen = []
        if self.whisper:
            seen.append((self.whisper[0], self.whisper[1]))
        if self.cards:
            seen.append((self.cards[-1][0] + " " + self.cards[-1][1], self.cards[-1][2]))
        if getattr(self, "note_toast", None):
            seen.append(self.note_toast)
        if getattr(self, "her_line", None):
            seen.append((self.her_line[0], "her"))
        if n.venom.vision is not None:
            from ..game.venom import VISIONS
            seen.append((VISIONS[n.venom.vision[0]][0], "vision"))
        if self.tutorial is not None and self.tutorial.note:
            seen.append((self.tutorial.note, self.tutorial.at))
        for text, when in seen:
            if not text or (text, when) in self.read_seen:
                continue
            self.read_seen.add((text, when))
            hold = 1.0 + 0.3 * len(str(text).split())
            self.reading_until = max(self.reading_until, now + hold)
            d = self._drive()
            if d is not None:
                d.hold(hold)
        if self.auto_journal_until is not None and now > self.auto_journal_until:
            self.auto_journal_until = None
            self.journal.close()

    def wake(self):
        """A key of his own: the letter lets go. The night is his now (and no longer Spellbound)."""
        n = self.night
        if self.director is None or n is None:
            return
        n.flags["woke"] = True
        self.director = None
        self.whisper = ("You wake, standing in her house. The night is yours now.", time.perf_counter(), 5.0)
        if self.journal.open:
            self.journal.close()
        self.capture()

    def draw_lesson(self, p, W, H):
        """The first night's margin note: in his hand, on a scrap of his notebook's paper."""
        t = self.tutorial
        if t is None or t.done or not t.note:
            return
        from . import fonts
        from ..game.tutorial import LESSONS
        box = QRectF(W * 0.24, H * 0.13, W * 0.52, 10)
        f = fonts.his(self.shell.records, 13)
        f.setItalic(True)
        from PySide6.QtGui import QFontMetrics
        h = QFontMetrics(f).boundingRect(0, 0, int(box.width() - 40), 400, Qt.TextWordWrap, t.note).height()
        box.setHeight(h + (58 if t.prompt else 30))
        p.save()
        p.setPen(QColor(120, 96, 70))
        p.setBrush(QColor(222, 208, 178, 235))
        p.drawRoundedRect(box, 4, 4)
        p.setFont(f)
        p.setPen(QColor(52, 36, 26))
        p.drawText(box.adjusted(20, 14, -20, -14), Qt.AlignLeft | Qt.TextWordWrap, t.note)
        if t.prompt:
            g = QFont(SERIF, 11, QFont.Bold)
            p.setFont(g)
            p.setPen(QColor(110, 60, 30))
            p.drawText(QRectF(box.left() + 20, box.bottom() - 28, box.width() - 40, 20), Qt.AlignLeft,
                       ("-  " + t.prompt) if t.prompt != "Yes." else "-  Yes.")
        p.setFont(QFont(SERIF, 9))
        p.setPen(QColor(120, 96, 70))
        p.drawText(QRectF(box.left(), box.bottom() + 4, box.width(), 16), Qt.AlignHCenter,
                   f"The first night  -  {t.at + 1} of {len(LESSONS)}"
                   "   (Enter skips  -  F9: let the letter lead you through the rest)")
        p.restore()

    def _last_words(self, n):
        """Supper: what she says to him as he's hung - from what she made of him tonight, and on other nights; in a
        model's words, if one is speaking for her and answers in time."""
        from ..game.death import last_words
        d = n.dying
        d.asked = True
        talk = getattr(self, "talk", None)
        d.her_line = last_words(n, self.shell.records.reputation, talk.lies if talk else 0)
        from ..game.death import her_side
        d.her_side = her_side(n, self.shell.records.reputation, talk.lies if talk else 0)
        if talk is not None and talk.mode == "model":
            from ..game import persona

            def back(text):
                line = persona.clean(text)
                if len(line) > 3 and not d.spoke:
                    d.her_line = line
            talk.voice.ask(persona.murmur_prompt("supper_end", talk.context()), back, max_tokens=50)

    def wait_for_dawn(self):
        """Waiting with her for the light: the dark a moment, and then it's coming."""
        from ..game import sky as S
        n = self.night
        day = int(n.sky.clock // 1440) + (1 if n.sky.clock % 1440 >= S.DUSK else 0)
        n.sky.clock = day * 1440 + S.DAWN - 0.5
        self.fade = time.perf_counter()

    def ensure_audio(self):
        if self.audio is None:
            from .audio import DenAudio
            self.audio = DenAudio(self.shell.muted)
        o = self.shell.records.options
        self.audio.volume = o["volume"] / 100.0
        self.audio.aloud = bool(o["aloud"])
        self.audio.warm()                                        # (her voice, readied in the background)
        return self.audio

    def _count(self, events):
        t = self.tally
        if t is None:
            return
        for e in events:
            if e[0] == "bitten":
                t["bites"] += 1
            elif e[0] == "silk" and e[1] == "slip":
                t["slips"] += 1
            elif e[0] == "hurt":
                t["falls"] += 1
            elif e[0] == "swipe":
                t["swipes"] += e[1]
            elif e[0] == "lantern" and e[1] == "shake":
                t["shakes"] += 1

    SPELL_WORDS = {("light", "cast"): "Light: hard and white, and the dark draws back.",
                   ("warmth", "cast"): "Warmth: a small flame in your palm.",
                   ("illusion", "cast"): "Illusion: for a while, her small ones cannot find you.",
                   ("memory", "cast"): "You remember something true, and it steadies you.",
                   ("light", "missed"): "Your hands shake; the light comes apart in them.",
                   ("warmth", "missed"): "Your hands shake; the flame gutters and is gone.",
                   ("illusion", "missed"): "Your hands shake; the illusion tears like wet paper.",
                   ("memory", "missed"): "You reach for it, and her venom muddies it.",
                   ("light", "resting"): "Not yet - the light needs a moment.",
                   ("warmth", "resting"): "Not yet.", ("illusion", "resting"): "Not yet.",
                   ("memory", "resting"): "Not yet."}

    MURMUR = {"glimpse": "glimpse", "near": "dark", "turn": "turn", "hunt": "hunt", "withdraw": "withdraw"}

    def note(self, ids):
        """Pages of his notebook, written as he learns them (kept across nights): a word low on the screen."""
        for nid in ids:
            if self.shell.records.note(nid):
                from ..game.notes import PAGES
                self.note_toast = (PAGES[nid][1], time.perf_counter())
                if self.director is not None and getattr(self, "scene", None) is None and self.night.dying is None:
                    self.journal.open_to(nid)                    # (led: he lifts his notebook to what he's learned)
                    words = len(PAGES[nid][2].split())
                    self.auto_journal_until = time.perf_counter() + 2.5 + 0.3 * words

    def _notes_from(self, n):
        from ..game import notes
        for e in n.events:
            self.note(notes.unlock_for(e, n))
            if e[0] == "take":                                # (into his pack - for her)
                from ..game.offerings import ITEMS
                self.whisper = ("You take " + ITEMS[e[1]][0] + ".", time.perf_counter(), 2.5)
                if e[1] == "journal":
                    self.note(["journal"])
            if e[0] == "cocoon":                              # (her guest: who he was, now in his notes)
                self.note([e[1]])
                title = notes.PAGES[e[1]][1]
                self.whisper = (title + ("." if e[3] else " - still, now. Empty of them."), time.perf_counter(), 3.5)
        if int(n.time * 2) != int((n.time - 0.05) * 2):          # (twice a second: has he seen her moods in the light?)
            self.note(notes.for_moods(n.moods))
            from ..game import hidden
            self.note(hidden.unlock(self.shell.records.notes))
            if getattr(self, "talk", None) is not None:
                self.talk.knows_her = hidden.knows(self.shell.records.notes)

    def _murmurs(self, n):
        """Her words, unasked, now and then: when she leans out to him, comes close in the dark, turns to his
        scrambling, hunts, draws back - and when she calls him on. Shown low on the screen, and heard."""
        talk = getattr(self, "talk", None)
        if talk is None:
            return
        for e in n.events:
            if e[0] == "call":                                    # (her calling him on: always said)
                self.last_murmur = n.time
                talk.murmur("call_" + e[1], self.her_lines.put)
            elif e[0] == "act" and e[1] in ("gallery", "supper", "crown"):
                self.whisper = (n.acts.request, time.perf_counter(), 6.0)
        for e in n.events:
            if e[0] == "her" and e[1] in self.MURMUR and n.time - self.last_murmur > 25.0:
                self.last_murmur = n.time
                talk.murmur(self.MURMUR[e[1]], self.her_lines.put)
                break
        try:
            line = self.her_lines.get_nowait()
        except queue.Empty:
            return
        if line:
            from ..game import notes
            self.note(notes.for_line(line))
            self.her_line = (line, time.perf_counter())
            if self.audio is not None:
                self.audio.say(line)

    def night_done(self):
        """The night over (an ending, or left part-way): its tallies into the records, once."""
        t, n = self.tally, self.night
        if t is None or t["done"] or n is None or not self.playing:
            return
        t["done"] = True
        talk = getattr(self, "talk", None)
        ending = None
        if n.dying is not None:
            ending = "your larder" if n.dying.cause == "bite" else "your silk, wrapped and hung"
        elif n.ending is not None:
            ending = {"Dawn": "dawn, and you let him go", "Cast out": "dawn, and you cast him out",
                      "Bound": "him staying, wrapped, at his own asking",
                      "The gift": "dawn, and your gift to him",
                      "The hidden": "dawn, and he knew your name", "Fire": "fire, in your silk",
                      "Spellbound": "dawn, and you carried him home asleep"}.get(n.ending.name, "dawn")
        self.shell.records.night_over(dict(t, seconds=n.time - t.get("from", 0.0), ending=ending, manner=n.manner(),
                                           lies=talk.lies if talk else 0,
                                           kept=talk.memory[-1] if talk and talk.memory else ""))

    # ---- what's drawn over it ----------------------------------------------------------------------------------
    def hud(self, p, now):
        W, H = self.width(), self.height()
        t = time.perf_counter()
        p.setRenderHint(QPainter.Antialiasing)
        if getattr(self, "scene", None) is not None:
            return                                                # (her scene: its own frame, nothing else)
        # a place's name, the first time he comes into it: it rises out of the dark and goes again
        self.cards = [c for c in self.cards if t - c[2] < 8.0]
        if self.cards:
            title, line, born = self.cards[-1]
            age = t - born
            a = max(0.0, min(1.0, age / 1.4, (8.0 - age) / 1.8))
            p.setPen(QColor(226, 212, 190, int(235 * a)))
            p.setFont(QFont(SERIF, 26))
            p.drawText(QRectF(0, H * 0.70, W, 44), Qt.AlignHCenter, title)
            p.setPen(QColor(200, 190, 176, int(200 * a)))
            f = QFont(SERIF, 13)
            f.setItalic(True)
            p.setFont(f)
            p.drawText(QRectF(W * 0.2, H * 0.70 + 48, W * 0.6, 60), Qt.AlignHCenter | Qt.TextWordWrap, line)
        n = self.night
        if getattr(self, "debug", False):
            p.setFont(QFont("Consolas", 9))
            p.setPen(QColor(200, 200, 190, 220))
            m = n.moods.values()
            lines = [f"{k:<12}{v:6.1f}" for k, v in m.items()] + [f"her         {n.her.state}", f"bites       {n.moods.bites}",
                                                                   f"hunting     {n.moods.hunting}"]
            for i, line in enumerate(lines):
                p.drawText(12, 20 + i * 14, line)
        o = self.shell.records.options
        if n.ending is not None:
            orbs.draw_ending(p, W, H, n.ending, self.shell.records, self.first_ending, n.ending_scene)
            return
        if n.dying is not None:
            if o["orbs"]:
                orbs.draw_orbs(p, W, H, n.body, t, max(0.0, 1.0 - n.dying.t / 1.2))
            orbs.draw_death(p, W, H, n.dying, t, self.first_ending, self.shell.records)
            if o["heart"] and n.dying.black < 0.98:
                orbs.draw_heart(p, W, H, n.body, 1.0 - n.dying.black)       # (to the last beat, and the flat line)
            return
        if o["orbs"]:
            orbs.draw_danger(p, W, H, n.body, t)
            orbs.draw_orbs(p, W, H, n.body, t)
        if o["heart"]:
            orbs.draw_heart(p, W, H, n.body)
        dial.draw(p, W, H, getattr(n, "sky", None))                # (the clock, top right)
        if n.lamp.state == "out" and self.outs <= 3:             # (the lantern out: what to do, the first few times)
            a = int(150 + 60 * math.sin(t * 2.4))
            p.setPen(QColor(220, 200, 170, a))
            p.setFont(QFont(SERIF, 13))
            p.drawText(QRectF(0, H * 0.6, W, 30), Qt.AlignHCenter, "E   -   shake the lantern")
        prompt = self._prompt(n)
        if prompt and n.dying is None:                            # (something to look at, or take)
            p.setPen(QColor(220, 200, 170, 200))
            p.setFont(QFont(SERIF, 13))
            p.drawText(QRectF(0, H * 0.6, W, 30), Qt.AlignHCenter, "F   -   " + prompt)
        self._spell_glow(p, W, H, n)
        self._afflict_hud(p, W, H, n, t)
        self._venom(p, W, H, n)
        if n.pack or n.held:                                      # (what he carries: his satchel's places)
            from .satchel import strip
            strip(p, W, H, n, t, self.flying)
        if n.teetering and self.teeters <= 3:                    # (swaying on a strand: what to do, the first few times)
            p.setPen(QColor(220, 200, 170, int(150 + 60 * math.sin(t * 3.0))))
            p.setFont(QFont(SERIF, 13))
            p.drawText(QRectF(0, H * 0.6, W, 30), Qt.AlignHCenter, "A   D   -   lean against the sway")
        toast = getattr(self, "note_toast", None)
        if toast and t - toast[1] < 4.5:                         # (a page written in his notes)
            a = min(1.0, (t - toast[1]) / 0.4, (4.5 - (t - toast[1])) / 0.8)
            f = QFont(SERIF, 12)
            f.setItalic(True)
            p.setFont(f)
            p.setPen(QColor(220, 196, 150, int(220 * a)))
            p.drawText(QRectF(0, H * 0.78, W, 24), Qt.AlignHCenter, f"Written in your notes:  {toast[0]}")
        if getattr(self, "her_line", None) and t - self.her_line[1] < 7.0:     # (her words: hers, low and large)
            age = t - self.her_line[1]
            a = min(1.0, age / 0.6, (7.0 - age) / 1.2)
            p.setFont(fonts.her(self.shell.records, 30))          # (her hand: Italianno)
            p.setPen(QColor(0, 0, 0, int(200 * a)))
            box = QRectF(W * 0.12, H * 0.36, W * 0.76, 90)              # (above the middle, in the dark)
            p.drawText(box.translated(1, 1), Qt.AlignHCenter | Qt.TextWordWrap, self.her_line[0])
            p.setPen(QColor(236, 214, 200, int(235 * a)))
            p.drawText(box, Qt.AlignHCenter | Qt.TextWordWrap, self.her_line[0])
        if self.whisper and t - self.whisper[1] < self.whisper[2]:
            p.setPen(QColor(210, 190, 170, int(220 * min(1.0, 1.6 * max(0.0, 1 - (t - self.whisper[1]) / self.whisper[2])))))
            f = QFont(SERIF, 13)
            f.setItalic(True)
            p.setFont(f)
            p.drawText(QRectF(0, H * 0.6 + 28, W, 30), Qt.AlignHCenter, self.whisper[0])
        if self.fade is not None:
            age = t - self.fade
            if age > 3.0:
                self.fade = None
            else:
                p.fillRect(self.rect(), QColor(0, 0, 0, int(255 * max(0.0, 1 - age / 3.0))))
        self.satchel.draw(p, W, H, n, self.shell.records)
        self.journal.draw(p, W, H)
        self.draw_lesson(p, W, H)
        if self._drive() is not None:                             # (the letter leading him: how to wake)
            p.setFont(QFont(SERIF, 10))
            p.setPen(QColor(200, 186, 220, 170))
            line = (f"Led by her letter   -   F10: x{self.speed}   -   any move key wakes you"
                    if self.director is not None else "The letter leads you on to the next")
            p.drawText(QRectF(0, 10, W, 18), Qt.AlignHCenter, line)
        if not self.captured and not self.shell.panel_open() and not self.satchel.open and not self.journal.open \
                and self._drive() is None:
            p.setPen(QColor(220, 208, 190, 170))
            p.setFont(QFont(SERIF, 12))
            p.drawText(QRectF(0, H * 0.5 + 40, W, 30), Qt.AlignHCenter,
                       "Click to take the mouse   (Esc: your notebook  -  P pauses)")

    # ---- input -------------------------------------------------------------------------------------------------
    def capture(self):
        if self.captured or not self.playing:
            return
        self.captured = True
        self.setCursor(Qt.BlankCursor)
        self.grabMouse()
        self._centre()
        self.setFocus()

    def release(self):
        if not self.captured:
            return
        self.captured = False
        self.releaseMouse()
        self.unsetCursor()

    def _centre(self):
        c = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
        self._centre_at = c
        QCursor.setPos(c)

    def mousePressEvent(self, e):
        if self.playing and self.night is not None and self.night.ending is not None:
            if self.night.ending.done and self.night.ending.t > 14.0:
                self.shell.show_title()                          # (it's over: back to the start)
            return
        if self.playing and self.night is not None and self.night.dying is not None:
            from ..game.death import FADE_END, HER_SIDE
            if self.night.dying.done and self.night.dying.t > FADE_END + HER_SIDE + 2.0:
                self.shell.show_title()                          # (it's over: back to the start)
            return
        if self.playing and self.journal.open:                   # (his notebook's pages)
            self.journal.press(e.position())
            return
        if self.playing and self.satchel.open and self.night is not None:      # (a thing chosen, into his hand)
            item = self.satchel.click(e.position())
            if item is not None:
                self.night.held = item
            return
        if self.playing and not self.captured and getattr(self, "scene", None) is None:
            self.capture()

    def focusNextPrevChild(self, _next):
        return False                                             # (Tab is his satchel's, not the focus's)

    def wheelEvent(self, e):
        """The mouse wheel: the next thing out of his satchel into his hand (or an empty hand)."""
        n = self.night
        if not self.playing or n is None or n.dying is not None or n.ending is not None:
            return
        from ..game import satchel
        satchel.choose(n, -1 if e.angleDelta().y() > 0 else 1)

    def mouseReleaseEvent(self, e):
        if self.journal.open:
            self.journal.release()

    def mouseMoveEvent(self, e):
        if self.journal.open:
            self.journal.move(e.position())
        if not self.captured:
            return
        c = getattr(self, "_centre_at", None)
        gp = e.globalPosition().toPoint()
        if c is None or gp == c:
            return
        dx, dy = gp.x() - c.x(), gp.y() - c.y()
        sens = SENS * (0.35 + 1.3 * self.shell.records.options["look"] / 100.0)
        self.inp.yaw += dx * sens
        self.inp.pitch = max(-1.45, min(1.45, self.inp.pitch - dy * sens))
        self._centre()

    def keyPressEvent(self, e):
        if e.isAutoRepeat():
            return
        k = e.key()
        n = self.night
        reading = self.playing and n is not None and getattr(self, "scene", None) is None and n.dying is None \
            and n.ending is None
        if k == Qt.Key_Escape and reading and not self.shell.panel_open():
            if self.satchel.open:
                self.satchel.toggle()
            self.journal.toggle()                                # (he looks down, and lifts his notebook - or shuts it)
            if self.journal.open:
                self.release()
            else:
                self.ui_did["notebook"] = True
                self.capture()
            return
        if k == Qt.Key_Escape or k == Qt.Key_P:                  # (the true pause: "The night waits")
            self.release()
            self.shell.pause()
            return
        if not self.playing:
            return
        if self.director is not None and k in (Qt.Key_W, Qt.Key_A, Qt.Key_S, Qt.Key_D, Qt.Key_Up, Qt.Key_Down, Qt.Key_Space):
            self.wake()                                          # (a key of his own: the letter lets go)
        if k == Qt.Key_F9 and n is not None and n.dying is None and n.ending is None:
            if self.director is not None:
                self.wake()
            else:
                from ..game.autoplay import Director
                if self.tutorial is not None:
                    self.tutorial.done = True
                self.director = Director(n)
                self.whisper = ("You let the letter lead you.", time.perf_counter(), 3.0)
                self.release()
            return
        if k == Qt.Key_F10:
            self.speed = {1: 2, 2: 4, 4: 8, 8: 1}[self.speed]
            return
        if k in (Qt.Key_Return, Qt.Key_Enter) and self.tutorial is not None and not self.tutorial.done:
            self.tutorial.skip()
            return
        if self.journal.open:                                    # (his hands are full of it)
            return
        self.keys.add(k)
        if k == Qt.Key_F4:                                       # (for building the game: her audience, now)
            self.start_scene("audience")
            return
        if k == Qt.Key_F3:                                       # (for building the game: her moods, in numbers)
            self.debug = not getattr(self, "debug", False)
        if k == Qt.Key_T and self.night is not None and self.night.ending is None and \
                self.night.acts.act == "crown" and "crown" in self.night.acts.outcomes:
            self.wait_for_dawn()
            return
        if k == Qt.Key_F and self.night is not None and self.night.dying is None:     # (a closer look)
            self.night.examine()
        if k == Qt.Key_Space and self.night is not None:
            self.inp.jump = True
        spell = {Qt.Key_1: "light", Qt.Key_2: "warmth", Qt.Key_3: "illusion", Qt.Key_4: "memory"}.get(k)
        if spell and self.night is not None and getattr(self, "scene", None) is None:
            self.night.cast(spell)
            return
        n = self.night
        free = n is not None and getattr(self, "scene", None) is None and n.dying is None and n.ending is None
        if k == Qt.Key_Tab and free:                             # (his satchel: open, or shut)
            self.satchel.toggle()
            if self.satchel.open:
                self.release()
            else:
                self.ui_did["satchel"] = True                    # (opened, and shut: for the first night)
                self.capture()
            return
        if k == Qt.Key_G and free:                               # (what's in his hand, put down)
            n.put_down()
            return
        if k == Qt.Key_F5:                                       # (a quick save)
            why = self.quick_save()
            self.whisper = (why or "Saved.", time.perf_counter(), 2.5)
            return
        if k == Qt.Key_Q and self.night is not None and getattr(self, "scene", None) is None:   # (the antidote)
            if self.night.drink():
                self.whisper = ("You drink. It is bitter, and cold - and her venom goes out of you.",
                                time.perf_counter(), 5.0)
            return
        if k in (Qt.Key_E, Qt.Key_L) and self.night:             # (a shake of the lantern)
            self.night.shake()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            self.keys.discard(e.key())

    def focusOutEvent(self, e):
        self.keys.clear()
        super().focusOutEvent(e)
