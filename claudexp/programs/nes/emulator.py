"""The console emulators: one XP window driven by a libretro core (assets/emulators), set up per system.

  NES  - FCE Ultra (FCEUmm core), ROMs from E:\\Emulation\\NES...
  SNES - Snes9x (Snes9x core),     ROMs from E:\\Emulation\\SNES...

The game list shows the user's own ROMs (not in git). Picking one runs it at 2x with sound; battery saves are kept
in data/<system>/saves, save states in data/<system>/states (ten slots).

Common keys: arrows = D-pad, Enter = Start, Space or Shift = Select (see each system for the face buttons).
F5 save state, F7 load state, 0-9 pick a slot, P or Pause to pause, F1 reset, Esc back to the game list."""
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QByteArray, QElapsedTimer, QRectF, Qt, QTimer
from PySide6.QtGui import QActionGroup, QColor, QFont, QIcon, QImage, QKeySequence, QPainter
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices
from PySide6.QtWidgets import (QAbstractItemView, QLabel, QListWidget, QListWidgetItem, QMenuBar, QStackedWidget,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from ... import sound
from ...paths import DATA, ROOT, pixmap
from ...wm import XPWindow
from ..people import load_json, save_json
from . import libretro as L

EMULATORS = ROOT / "assets" / "emulators"
DPAD = {Qt.Key_Up: L.UP, Qt.Key_Down: L.DOWN, Qt.Key_Left: L.LEFT, Qt.Key_Right: L.RIGHT,
        Qt.Key_Return: L.START, Qt.Key_Enter: L.START, Qt.Key_Space: L.SELECT, Qt.Key_Shift: L.SELECT}
SHARED_HELP = ("D-pad:  Arrow keys\nStart:  Enter\nSelect:  Space or Shift\n\n"
               "Save state:  F5\nLoad state:  F7\nState slot:  0 - 9\nPause:  P or Pause\nReset:  F1\n"
               "Game list:  Esc")


@dataclass
class System:
    key: str                     # 'nes' -> data/nes, the program key
    console: str                 # menu name: 'NES'
    title: str                   # window title: 'FCE Ultra'
    core: str                    # DLL in assets/emulators
    folder: str                  # regex for its folder under E:\Emulation
    exts: set
    icon: str                    # assets/images
    width: int
    height: int
    buttons: dict = field(default_factory=dict)
    help: str = ""
    credits: str = ""


SYSTEMS = {
    "nes": System("nes", "NES", "FCE Ultra", "fceumm_libretro.dll", r"(nes|famicom)\b", {".nes", ".fds", ".unf", ".unif"},
                  "nes_icon.png", 256, 240, {Qt.Key_X: L.A, Qt.Key_Z: L.B}, "A:  X\nB:  Z\n",
                  "FCE Ultra by Bero, Xodnizel and the FCEUmm team. Free software under the GNU GPL."),
    "snes": System("snes", "SNES", "Snes9x", "snes9x_libretro.dll", r"(snes|super nintendo|super famicom|sfc)\b",
                   {".smc", ".sfc", ".swc", ".fig"}, "snes_icon.png", 256, 224,
                   {Qt.Key_X: L.A, Qt.Key_Z: L.B, Qt.Key_S: L.X, Qt.Key_A: L.Y, Qt.Key_Q: L.L, Qt.Key_W: L.R},
                   "A:  X\nB:  Z\nX:  S\nY:  A\nL:  Q\nR:  W\n",
                   "Snes9x by Gary Henderson, Jerremy Koot and the Snes9x team. Free for non-commercial use."),
}

_cores = {}                      # system key -> Core (each core DLL keeps global state)


def core(system):
    if system.key not in _cores:
        base = DATA / system.key
        (base / "system").mkdir(parents=True, exist_ok=True)
        (base / "saves").mkdir(parents=True, exist_ok=True)
        _cores[system.key] = L.Core(EMULATORS / system.core, base / "system", base / "saves")
    return _cores[system.key]


def icon_for(system):
    pm = pixmap(system.icon)
    return QIcon(pm) if not pm.isNull() else QIcon()


def rom_folders(system):
    """This system's folders under E:\\Emulation (e.g. 'SNES (33 Roms)')."""
    from ...explorer.vfs import local_storage
    emu = next((d for d in local_storage().iterdir() if d.is_dir() and d.name.lower().startswith("emulat")), None)
    if emu is None:
        return []
    return [d for d in sorted(emu.iterdir()) if d.is_dir() and re.match(system.folder, d.name.lower())]


def game_title(path):
    """'Legend of Zelda, The (U) (PRG 0).nes' -> 'The Legend of Zelda'."""
    t = re.sub(r"\s*[\[(][^\])]*[\])]", "", Path(path).stem).strip()
    m = re.match(r"(.+?), The(\s*-.*)?$", t)
    if m:
        t = "The " + m.group(1) + (m.group(2) or "")
    return t


class Screen(QWidget):
    """The console's picture, pixel-sharp, letterboxed in black, with messages in the corner."""

    def __init__(self, emu):
        super().__init__()
        self.emu = emu
        self.image = QImage()
        self.message = ""
        self.message_until = 0.0
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(emu.system.width, emu.system.height)

    def say(self, text, seconds=2.0):
        self.message, self.message_until = text, time.monotonic() + seconds
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.black)
        if not self.image.isNull():
            iw, ih = self.image.width(), self.image.height()
            if ih > 300:                                       # hi-res modes are twice as tall: same picture
                ih //= 2
            if iw > 300:
                iw //= 2
            if self.emu.state.get("tv_aspect"):
                aspect = 4 / 3
                w, h = self.width(), self.height()
                if w / h > aspect:
                    w = int(h * aspect)
                else:
                    h = int(w / aspect)
            else:                                              # whole-number scaling keeps pixels square
                k = max(1, min(self.width() // iw, self.height() // ih))
                w, h = iw * k, ih * k
            target = QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h)
            p.setRenderHint(QPainter.SmoothPixmapTransform, False)
            p.drawImage(target, self.image)
        if self.emu.paused and self.emu.game is not None:
            self._label(p, "PAUSED", Qt.AlignCenter)
        if self.message and time.monotonic() < self.message_until:
            self._label(p, self.message, Qt.AlignLeft | Qt.AlignBottom)

    def _label(self, p, text, align):
        p.setFont(QFont("Courier New", 10, QFont.Bold))
        r = self.rect().adjusted(8, 8, -8, -8)
        p.setPen(Qt.black)
        p.drawText(r.translated(1, 1), align, text)
        p.setPen(QColor("#F8F8F8"))
        p.drawText(r, align, text)

    def keyPressEvent(self, event):
        if not self.emu.key(event, True):
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not self.emu.key(event, False):
            super().keyReleaseEvent(event)

    def focusOutEvent(self, event):
        if self.emu.system.key in _cores:
            _cores[self.emu.system.key].buttons.clear()        # never leave a button stuck down
        super().focusOutEvent(event)


class Emulator(QWidget):
    def __init__(self, desktop, system):
        super().__init__()
        self.desktop = desktop
        self.system = system
        self.process_image = {"nes": "fceu.exe", "snes": "snes9x.exe"}.get(system.key)      # for Task Manager
        self.keys = {**DPAD, **system.buttons}
        self.data = DATA / system.key
        self.settings_file = self.data / "settings.json"
        self.frame = None
        self.state = load_json(self.settings_file, {"scale": 2, "sound": True, "tv_aspect": False,
                                                    "pause_inactive": True, "recent": []})
        self.game = None
        self.slot = 1
        self.paused = False
        self.auto_paused = False
        self.next_frame = 0.0
        self.last_sram = b""
        self.fps_count, self.fps_shown, self.fps_since = 0, 0, 0.0
        self.audio_out = None
        self.audio_dev = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._menus())
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.games = QListWidget()
        self.games.setIconSize(pixmap(system.icon).size().scaled(24, 24, Qt.KeepAspectRatio))
        self.games.setStyleSheet("QListWidget { background: white; border: none; font: 11px Tahoma; }"
                                 "QListWidget::item { padding: 3px; } QListWidget::item:selected {"
                                 " background: #316AC5; color: white; }")
        self.games.setSelectionMode(QAbstractItemView.SingleSelection)
        self.games.itemActivated.connect(lambda item: self.play(Path(item.data(Qt.UserRole))))
        self.stack.addWidget(self.games)
        self.screen = Screen(self)
        self.stack.addWidget(self.screen)
        self.status = QLabel()
        self.status.setStyleSheet("font: 11px Tahoma; padding: 2px 6px; background: #ECE9D8;"
                                  " border-top: 1px solid #A0A0A0;")
        lay.addWidget(self.status)

        self.clock = QElapsedTimer()
        self.clock.start()
        self.timer = QTimer(self, interval=2, timeout=self._tick)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.sram_timer = QTimer(self, interval=30000, timeout=self._save_sram)
        self.fill_games()

    @property
    def core(self):
        return core(self.system)

    # ---- menus --------------------------------------------------------------------------------------------
    def _menus(self):
        from ..notepad import MENU_STYLE
        bar = QMenuBar()
        bar.setStyleSheet(MENU_STYLE)
        f = bar.addMenu("&File")
        f.addAction("&Game List", self.show_list, QKeySequence("Ctrl+L"))
        self.recent_menu = f.addMenu("&Recent Games")
        f.addAction("&Close Game", self.close_game)
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close() if self.frame else None)
        n = bar.addMenu("&" + self.system.console)
        self.pause_action = n.addAction("&Pause", self.toggle_pause, QKeySequence("P"))
        self.pause_action.setCheckable(True)
        n.addAction("&Reset", self.reset, QKeySequence("F1"))
        n.addAction("Hard Reset (&Power)", self.power)
        s = bar.addMenu("&State")
        s.addAction("&Save State", self.save_state, QKeySequence("F5"))
        s.addAction("&Load State", self.load_state, QKeySequence("F7"))
        slots = s.addMenu("Select S&lot")
        group = QActionGroup(self)
        self.slot_actions = {}
        for i in range(10):
            a = slots.addAction(f"Slot {i}", lambda i=i: self.select_slot(i))
            a.setCheckable(True)
            a.setChecked(i == self.slot)
            group.addAction(a)
            self.slot_actions[i] = a
        o = bar.addMenu("&Options")
        size = o.addMenu("Window &Size")
        sizes = QActionGroup(self)
        for k in (1, 2, 3):
            a = size.addAction(f"{k}x", lambda k=k: self.set_scale(k))
            a.setCheckable(True)
            a.setChecked(self.state.get("scale", 2) == k)
            sizes.addAction(a)

        def toggle(label, key, after=None):
            a = o.addAction(label)
            a.setCheckable(True)
            a.setChecked(bool(self.state.get(key)))
            a.toggled.connect(lambda on: (self.state.__setitem__(key, on), self._save_settings(),
                                          after() if after else None))
            return a
        toggle("&TV Aspect Ratio (4:3)", "tv_aspect", lambda: self.screen.update())
        toggle("&Sound", "sound", self._apply_volume)
        toggle("Pause when &Inactive", "pause_inactive")
        h = bar.addMenu("&Help")
        h.addAction("&Controls...", self.show_controls)
        h.addAction(f"&About {self.system.title}...", self.about)
        # keyboard shortcuts (F5, P...) only while the emulator window has focus, not all over the desktop
        stack = list(bar.actions())
        while stack:
            a = stack.pop()
            if a.menu() is not None:
                stack += a.menu().actions()
            elif not a.shortcut().isEmpty():
                a.setShortcutContext(Qt.WidgetWithChildrenShortcut)
                self.addAction(a)
        return bar

    def _refresh_recent(self):
        self.recent_menu.clear()
        recent = [p for p in self.state.get("recent", []) if os.path.exists(p)]
        for p in recent[:8]:
            self.recent_menu.addAction(game_title(p), lambda p=p: self.play(Path(p)))
        self.recent_menu.setEnabled(bool(recent))

    # ---- the game list -----------------------------------------------------------------------------------
    def fill_games(self):
        self.games.clear()
        icon = icon_for(self.system)
        roms = []
        for folder in rom_folders(self.system):
            for f in folder.iterdir():
                if f.suffix.lower() in self.system.exts:
                    roms.append(f)
        for f in sorted(roms, key=lambda p: game_title(p).lower()):
            item = QListWidgetItem(icon, game_title(f))
            item.setData(Qt.UserRole, str(f))
            item.setToolTip(f.name)
            self.games.addItem(item)
        if not roms:
            ext = sorted(self.system.exts)[0]
            item = QListWidgetItem(f"No games found. Put your {self.system.console} ROMs ({ext}) in "
                                   f"E:\\Emulation\\{self.system.console}, then choose File > Game List.")
            item.setFlags(Qt.NoItemFlags)
            self.games.addItem(item)
        self._refresh_recent()
        if self.game is None:
            self.status.setText(f"{len(roms)} games  \u2014  double-click a game to play")

    def show_list(self):
        self.pause(True)
        self.fill_games()
        self.stack.setCurrentWidget(self.games)
        if self.game is not None:
            self.status.setText(f"{game_title(self.game)} is paused  \u2014  pick a game, or press Esc to go back")
        self.games.setFocus()

    # ---- playing -----------------------------------------------------------------------------------------
    def play(self, path):
        self.close_game()
        c = self.core
        if not c.load(path):
            from ...explorer.dialogs import msgbox
            msgbox(self.desktop, self.system.title, f"{path.name} couldn't be loaded. It may be damaged or use a "
                   "cartridge type this emulator doesn't support.", "error")
            return
        self.game = path
        sram = self._sram_file()
        if sram.exists():
            c.load_ram(sram.read_bytes())
        self.last_sram = c.save_ram()
        recent = [str(path)] + [p for p in self.state.get("recent", []) if p != str(path)]
        self.state["recent"] = recent[:10]
        self._save_settings()
        self._refresh_recent()
        self._start_audio(c.sample_rate)
        self.paused = self.auto_paused = False
        self.pause_action.setChecked(False)
        self.next_frame = self.fps_since = self.clock.elapsed() / 1000
        self.fps_count = 0
        self.stack.setCurrentWidget(self.screen)
        self.screen.image = QImage()
        self.screen.setFocus()
        self.timer.start()
        self.sram_timer.start()
        self.set_scale(self.state.get("scale", 2), save=False)
        if self.frame is not None:
            self.frame.set_title(f"{self.system.title} - {game_title(path)}")
        self.screen.say(f"Loaded {game_title(path)}")

    def close_game(self):
        if self.game is None:
            return
        self._save_sram()
        self.timer.stop()
        self.sram_timer.stop()
        self.core.unload()
        self.core.buttons.clear()
        self._stop_audio()
        self.game = None
        self.screen.image = QImage()
        self.stack.setCurrentWidget(self.games)
        self.fill_games()
        if self.frame is not None:
            self.frame.set_title(self.system.title)

    def _tick(self):
        if self.game is None:
            return
        active = self.frame is not None and self.frame.isVisible() and (
            not self.state.get("pause_inactive") or self.desktop.is_active(self.frame))
        if not active and not self.auto_paused and not self.paused:
            self.auto_paused = True
            self.core.buttons.clear()
            self.screen.update()
        elif active and self.auto_paused:
            self.auto_paused = False
            self.next_frame = self.clock.elapsed() / 1000
        if self.paused or self.auto_paused or self.stack.currentWidget() is not self.screen:
            return
        c = self.core
        now = self.clock.elapsed() / 1000
        step = 1.0 / c.fps
        ran = 0
        while now >= self.next_frame and ran < 4:          # catch up a little, never spiral
            c.run()
            self.next_frame += step
            ran += 1
        if now - self.next_frame > 0.25:                     # we fell far behind (window dragged): skip ahead
            self.next_frame = now
        if ran:
            self._push_audio(c.take_audio())
            if c.frame is not None:
                self.screen.image = c.frame
                self.screen.update()
            self.fps_count += ran
        if now - self.fps_since >= 1.0:
            self.fps_shown, self.fps_count, self.fps_since = self.fps_count, 0, now
            self.status.setText(f"{game_title(self.game)}   \u2014   {self.fps_shown} fps   \u2014   "
                                f"State slot {self.slot}")

    def key(self, event, down):
        if event.isAutoRepeat():
            return event.key() in self.keys
        k = event.key()
        if k in self.keys:
            (self.core.buttons.add if down else self.core.buttons.discard)(self.keys[k])
            return True
        if not down:
            return False
        if k == Qt.Key_Pause:
            self.toggle_pause()
        elif Qt.Key_0 <= k <= Qt.Key_9:
            self.select_slot(k - Qt.Key_0)
        elif k == Qt.Key_Escape:
            self.show_list()
        else:
            return False
        return True

    # ---- console menu ------------------------------------------------------------------------------------
    def pause(self, on):
        self.paused = on and self.game is not None
        self.pause_action.setChecked(self.paused)
        if not self.paused:
            self.next_frame = self.clock.elapsed() / 1000
        if self.system.key in _cores:
            _cores[self.system.key].buttons.clear()
        self.screen.update()

    def toggle_pause(self):
        self.pause(not self.paused)

    def reset(self):
        if self.game is not None:
            self.core.reset()
            self.screen.say("Reset")

    def power(self):
        if self.game is not None:
            self.play(self.game)
            self.screen.say("Power cycled")

    # ---- states and battery saves ------------------------------------------------------------------------
    def _sram_file(self):
        return self.data / "saves" / (self.game.stem + ".srm")

    def _state_file(self, slot):
        return self.data / "states" / f"{self.game.stem}.st{slot}"

    def _save_sram(self):
        if self.game is None:
            return
        data = self.core.save_ram()
        if data and data != self.last_sram:
            try:
                self._sram_file().write_bytes(data)
                self.last_sram = data
            except OSError:
                pass

    def save_state(self):
        if self.game is None:
            return
        data = self.core.save_state()
        if data:
            f = self._state_file(self.slot)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
            self.screen.say(f"State {self.slot} saved")

    def load_state(self):
        if self.game is None:
            return
        f = self._state_file(self.slot)
        if not f.exists():
            self.screen.say(f"State {self.slot} is empty")
            return
        self.screen.say(f"State {self.slot} loaded" if self.core.load_state(f.read_bytes())
                        else f"State {self.slot} couldn't be loaded")

    def select_slot(self, i):
        self.slot = i
        self.slot_actions[i].setChecked(True)
        if self.game is not None:
            used = self._state_file(i).exists()
            self.screen.say(f"State slot {i}" + ("" if used else " (empty)"))

    # ---- window and sound -------------------------------------------------------------------------------
    def set_scale(self, k, save=True):
        self.state["scale"] = k
        if save:
            self._save_settings()
        if self.frame is None or self.frame.maximized:
            return
        W, H = self.system.width, self.system.height
        chrome = self.frame.size() - self.size()
        extra_h = self.height() - self.stack.height()
        area = self.desktop.work_area()
        while k > 1 and (H * k + extra_h + chrome.height() > area.height() or W * k + chrome.width() > area.width()):
            k -= 1                                          # 3x doesn't fit on a 1024x768 screen
        self.frame.resize(W * k + chrome.width(), H * k + extra_h + chrome.height())
        pos = self.frame.pos()
        self.frame.move(max(0, min(pos.x(), area.right() - self.frame.width())),
                        max(0, min(pos.y(), area.bottom() - self.frame.height())))

    def _start_audio(self, rate):
        self._stop_audio()
        fmt = QAudioFormat()
        fmt.setSampleRate(rate)
        fmt.setChannelCount(2)
        fmt.setSampleFormat(QAudioFormat.Int16)
        if not QMediaDevices.defaultAudioOutput().isFormatSupported(fmt):
            return
        self.audio_out = QAudioSink(QMediaDevices.defaultAudioOutput(), fmt, self)
        self.audio_out.setBufferSize(int(rate * 4 * 0.12))           # ~120 ms
        self._apply_volume()
        self.audio_dev = self.audio_out.start()

    def _stop_audio(self):
        if self.audio_out is not None:
            self.audio_out.stop()
            self.audio_out.deleteLater()
        self.audio_out = self.audio_dev = None

    def _push_audio(self, data):
        if self.audio_dev is None or not data:
            return
        room = self.audio_out.bytesFree()
        if room <= 0:
            return
        self.audio_dev.write(QByteArray(data[:room - room % 4]))

    def _apply_volume(self):
        if self.audio_out is not None:
            self.audio_out.setVolume(0.0 if (not self.state.get("sound", True) or sound.is_muted()) else 0.8)

    def _save_settings(self):
        save_json(self.settings_file, self.state)

    # ---- help ---------------------------------------------------------------------------------------------
    def show_controls(self):
        from ...explorer.dialogs import msgbox
        msgbox(self.desktop, "Controls", self.system.help + SHARED_HELP, "info")

    def about(self):
        from ...explorer.dialogs import msgbox
        c = self.core
        msgbox(self.desktop, f"About {self.system.title}",
               f"{self.system.title} {self.system.console} Emulator\n\nEmulation core: {c.name} {c.version}\n"
               + self.system.credits, "info")

    def closeEvent(self, event):
        self.close_game()
        self._save_settings()
        event.accept()


_open = {}


def open_system(desktop, key):
    system = SYSTEMS[key]
    win = _open.get(key)
    if win is None or not isValid(win):
        if not (EMULATORS / system.core).exists():
            from ...explorer.dialogs import msgbox
            msgbox(desktop, system.title, f"The emulator core ({system.core}) is missing from assets\\emulators.",
                   "error")
            return None
        body = Emulator(desktop, system)
        win = XPWindow(desktop, system.title, body, icon_for(system),
                       (system.width * 2 + 16, system.height * 2 + 90))
        body.frame = win
        _open[key] = win
    desktop.open_window(win)
    return win


def shutdown_system(key):
    win = _open.get(key)
    if win is not None and isValid(win):
        win.content.close_game()
    c = _cores.pop(key, None)
    if c is not None:
        c.close()


# program entry points
def nes_icon():
    return icon_for(SYSTEMS["nes"])


def open_nes(desktop):
    return open_system(desktop, "nes")


def shutdown_nes():
    shutdown_system("nes")


def snes_icon():
    return icon_for(SYSTEMS["snes"])


def open_snes(desktop):
    return open_system(desktop, "snes")


def shutdown_snes():
    shutdown_system("snes")
