"""The game's window content: the view, with a panel laid over it when one is open (the title, the menu, the pack,
a vendor, a choice), and the saving."""
import json
import random

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QWidget

from ..engine.sound import Sounds
from ..engine.speech import Speech
from ..game import people
from ..game import data as D
from ..game import shop
from ..game.saves import Saves
from ..game.world import Game

from . import panels
from .audio import Music
from .title import TitleScreen
from .view import GameView


class _Bridge(QObject):
    """Brings a thread's answer back to the window's own thread."""
    got = Signal(object, object)


class Shell(QWidget):
    def __init__(self, saves_dir, muted=lambda: False):
        super().__init__()
        self.setMinimumSize(800, 520)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.saves = Saves(saves_dir)
        self.settings = self._read_settings()
        self.sounds = Sounds(lambda: muted() or not self.settings.get("sound", True))
        self.music = Music(enabled=lambda: self.settings.get("music", True),
                           volume=lambda: self.settings.get("music_volume", 0.8), muted=muted)
        self.speech = Speech(enabled=self.settings.get("speech", True))
        self.talk = {}                                       # vendor -> [(who, text)] this visit
        self.rng = random.Random()
        self._bridge = _Bridge()
        self._bridge.got.connect(lambda fn, text: fn(text))
        self.view = GameView(self)
        self.overlay = None
        self.slot = None
        self._stock = {}
        self.show_title()

    # ---- layout ------------------------------------------------------------------------------------------------
    def resizeEvent(self, e):
        self.view.setGeometry(self.rect())
        if self.overlay:
            self.overlay.setGeometry(self.rect())
        super().resizeEvent(e)

    def panel_open(self):
        return self.overlay is not None

    def set_panel(self, panel, full=False):
        if self.overlay is not None:
            self.overlay.hide()
            self.overlay.deleteLater()
            self.overlay = None
        if panel is not None:
            self.view.release()
            self.overlay = panels.Overlay(self, panel, full)
            self.overlay.setGeometry(self.rect())
            self.overlay.show()
            self.overlay.raise_()

    def close_panel(self):
        self.set_panel(None)
        if self.view.game and self.slot is not None:
            self.view.setFocus()
            self.view.capture()

    # ---- the title, and playing --------------------------------------------------------------------------------
    def show_title(self):
        self.slot = None
        backdrop = Game.new(seed=4242)                      # (Thornwick behind the title, turning slowly)
        backdrop.yaw = 0.0
        backdrop.hand = False                               # (no wand in hand on the title)
        self.view.start(backdrop)
        self.view.running = False
        self.view.inp.yaw = 0.0
        self.music.place("title")
        self.set_panel(TitleScreen(self), full=True)

    def play(self, slot):
        d = self.saves.load(slot)
        g = Game.from_json(d, slot) if d else Game.new(slot)
        self.slot = slot
        self._stock = {}
        self.view.start(g)
        self.view.inp.yaw, self.view.inp.pitch = g.yaw, 0.0
        self.save()
        self.set_panel(None)
        self.talk = {}
        self.speech.warm()
        self.view.toasts.append((f"{D.TOWN_NAME}. The Deep's mouth is in the square: floor {g.run_floor} is open.",
                                 (0.95, 0.88, 0.7), __import__("time").perf_counter()))
        self.view.setFocus()

    def save(self):
        g = self.view.game
        if g is None or self.slot is None:
            return
        self.saves.save(self.slot, g.to_json())

    def quit_to_title(self):
        self.save()
        for name in ("rain", "wind"):
            self.sounds.loop(name, 0)
        self.show_title()

    # ---- what the game asks for --------------------------------------------------------------------------------
    def pause(self):
        if self.slot is None:
            return
        if self.overlay:
            self.close_panel()
            return
        self.set_panel(panels.PausePanel(self))

    def open_dialog(self, what):
        g = self.view.game
        if g is None or self.slot is None:
            return
        kind = what[0]
        if kind == "pack":
            self.set_panel(panels.PackPanel(self))
        elif kind == "calendar":
            from .dial import CalendarPanel
            self.set_panel(CalendarPanel(self))
        elif kind in ("hearth", "stash", "sign"):
            from . import home
            self.set_panel({"hearth": home.CookPanel, "stash": home.StashPanel, "sign": home.FarmPanel}[kind](self))
        elif kind == "vendor":
            self.set_panel(panels.VendorPanel(self, what[1]))
        elif kind == "stairs":
            nxt = g.depth + 1
            band = D.band_of(nxt)
            note = f"Floor {nxt} is in {band['name']}." if (nxt - 1) % 10 == 0 else ""
            if nxt % 10 == 0:
                note += f" Something waits on floor {nxt}: {band['guardian']}."
            choices = []
            if g.depth < D.FLOORS or g.endless():
                choices.append((f"Go down to floor {nxt}", lambda: self._do(g.descend)))
            choices.append((f"Go home to {D.TOWN_NAME} (the way down will wait at floor {nxt if g.endless() else min(D.FLOORS, nxt)})",
                            lambda: self._do(g.stairs_home)))
            choices.append(("Not yet", self.close_panel))
            self.set_panel(panels.ChoicePanel("The stairs", note.strip(), choices))
        elif kind == "mouth":
            choices = [(f"Go down to floor {g.run_floor} (where the run has reached)", lambda: self._do(lambda: g.go_floor(g.run_floor)))]
            if g.run_floor > 1:
                choices.append(("Start again from floor 1", lambda: self._do(lambda: self._restart(g))))
            choices.append(("Not yet", self.close_panel))
            band = D.band_of(g.run_floor)
            self.set_panel(panels.ChoicePanel("The Deep", f"Floor {g.run_floor}: {band['name']}. {band['line']}", choices))

    def _restart(self, g):
        g.run_floor = 1
        g.go_floor(1)

    def _do(self, fn):
        fn()
        self.save()
        self.close_panel()

    def stock(self, vendor):
        g = self.view.game
        if self._stock.get("_visit") != g.visits:
            self._stock = {"_visit": g.visits}
        if vendor not in self._stock:
            self._stock[vendor] = shop.stock(vendor, g.seed, g.visits, max(g.run_floor, g.player.stats["deepest"]))
        return self._stock[vendor]

    # ---- the townsfolk talking -------------------------------------------------------------------------------
    def _read_settings(self):
        try:
            return json.loads((self.saves.folder / "settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def set_setting(self, key, value):
        self.settings[key] = value
        try:
            self.saves.folder.mkdir(parents=True, exist_ok=True)
            (self.saves.folder / "settings.json").write_text(json.dumps(self.settings, indent=1), encoding="utf-8")
        except OSError:
            pass
        if key == "speech":
            self.speech.enabled = bool(value)
            if value:
                self.speech.warm()

    def greeting(self, vendor):
        """What the vendor says as Claude comes up: the last thing they said this visit, or a line of their own (the
        language model's line replaces it when it comes)."""
        said = self.talk.get(vendor)
        if said:
            return next((t for who, t in reversed(said) if who == "them"), None)
        line = people.line(vendor, self.view.game, random.Random())
        self.talk[vendor] = [("them", line)]
        if self.speech.available():
            self.speech_ask(vendor, people.greeting_request(vendor, self.view.game), replace=True)
        return line

    def speech_ask(self, vendor, messages, replace=False):
        def got(text):
            text = people.clean(text) if text else ""
            if not text:
                if not replace:
                    self.talk.setdefault(vendor, []).append(("them", "..."))
            elif replace and self.talk.get(vendor) and len(self.talk[vendor]) == 1:
                self.talk[vendor] = [("them", text)]
            else:
                self.talk.setdefault(vendor, []).append(("them", text))
            panel = self.overlay.panel if self.overlay is not None else None
            if isinstance(panel, panels.VendorPanel) and panel.key == vendor:
                panel.show_talk()
        self.speech.ask(messages, lambda text: self._bridge.got.emit(got, text))

    def say_to(self, vendor, said):
        said = said.strip()
        if not said:
            return
        hist = self.talk.setdefault(vendor, [])
        from ..game import eggs
        reply = eggs.phrase(self.view.game, vendor, said)
        if reply:
            hist.append(("claude", said))
            hist.append(("them", reply))
            return
        msgs = people.chat_request(vendor, self.view.game, hist, said)
        hist.append(("claude", said))
        self.speech_ask(vendor, msgs)

    def on_death(self, depth):
        self.set_panel(panels.ChoicePanel(
            "Claude falls",
            f"On floor {depth}. He wakes in the clearing in Thornwick with everything he carried, every level he'd "
            "earned and every skill he'd learned - but the Deep has shut, and the run begins again at floor 1.",
            [("Get up", self.close_panel)]))

    def on_victory(self):
        self.set_panel(panels.ChoicePanel(
            "The bottom of the Deep",
            "The Unmade King is unmade. Whatever Claude becomes after this, it begins here. And the Deep goes on: "
            "past the hundredth floor the bands come round again, harder each time - endless.",
            [("Carry on", self.close_panel)]))

    def closeEvent(self, e):
        self.save()
        self.music.stop()
        for name in ("rain", "wind"):
            self.sounds.loop(name, 0)
        super().closeEvent(e)

