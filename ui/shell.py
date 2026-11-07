"""The game's window content: the view, with a panel laid over it when one is open (the title, the menu, the pack,
a vendor, a choice), and the saving."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from ..engine.sound import Sounds
from ..game import data as D
from ..game import shop
from ..game.saves import Saves
from ..game.world import Game

from . import panels
from .view import GameView


class Shell(QWidget):
    def __init__(self, saves_dir, muted=lambda: False):
        super().__init__()
        self.setMinimumSize(800, 520)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.saves = Saves(saves_dir)
        self.sounds = Sounds(muted)
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

    def set_panel(self, panel):
        if self.overlay is not None:
            self.overlay.hide()
            self.overlay.deleteLater()
            self.overlay = None
        if panel is not None:
            self.view.release()
            self.overlay = panels.Overlay(self, panel)
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
        self.view.start(backdrop)
        self.view.running = False
        self.view.inp.yaw = 0.0
        self.set_panel(panels.TitlePanel(self))

    def play(self, slot):
        d = self.saves.load(slot)
        g = Game.from_json(d, slot) if d else Game.new(slot)
        self.slot = slot
        self._stock = {}
        self.view.start(g)
        self.view.inp.yaw, self.view.inp.pitch = g.yaw, 0.0
        self.save()
        self.set_panel(None)
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
        elif kind == "vendor":
            self.set_panel(panels.VendorPanel(self, what[1]))
        elif kind == "stairs":
            nxt = g.depth + 1
            band = D.band_of(nxt)
            note = f"Floor {nxt} is in {band['name']}." if (nxt - 1) % 10 == 0 else ""
            if nxt % 10 == 0:
                note += f" Something waits on floor {nxt}: {band['guardian']}."
            choices = []
            if g.depth < D.FLOORS:
                choices.append((f"Go down to floor {nxt}", lambda: self._do(g.descend)))
            choices.append((f"Go home to {D.TOWN_NAME} (the way down will wait at floor {min(D.FLOORS, nxt)})",
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

    def greeting(self, vendor):
        """What the vendor says (the language model's line, once the NPCs speak; for now their own)."""
        return None

    def on_death(self, depth):
        self.set_panel(panels.ChoicePanel(
            "Claude falls",
            f"On floor {depth}. He wakes in the clearing in Thornwick with everything he carried, every level he'd "
            "earned and every skill he'd learned - but the Deep has shut, and the run begins again at floor 1.",
            [("Get up", self.close_panel)]))

    def on_victory(self):
        self.set_panel(panels.ChoicePanel(
            "The bottom of the Deep",
            "The Unmade King is unmade. Whatever Claude becomes after this, it begins here. (The Deep stays open: "
            "every floor of it, for as long as he likes.)",
            [("Carry on", self.close_panel)]))

    def closeEvent(self, e):
        self.save()
        super().closeEvent(e)

