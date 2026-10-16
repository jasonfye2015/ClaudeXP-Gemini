"""The console emulators: one XP window driven by a libretro core (assets/emulators), set up per system.

  NES      - FCE Ultra (FCEUmm)          GB   - Gambatte            GBA - mGBA
  SNES     - Snes9x                      GBC  - Gambatte (own copy of the DLL, so GB and GBC can run together)
  Genesis  - PicoDrive (Genesis + 32X)   SMS  - Genesis Plus GX
  N64      - Mupen64Plus-Next (software 'Angrylion' renderer, so it needs no 3D graphics set-up)

ROMs come from the matching folder under E:\\Emulation (e.g. 'SNES (33 Roms)').

The game list shows the user's own ROMs (not in git). Picking one runs it at 2x with sound; battery saves are kept
in data/<system>/saves, save states in data/<system>/states (ten slots).

Common keys: arrows = D-pad, Enter = Start, Space or Shift = Select (see each system for the face buttons).
F5 save state, F7 load state, 0-9 pick a slot, P or Pause to pause, F1 reset, Esc back to the game list."""
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QByteArray, QElapsedTimer, QRectF, Qt, QTimer
from PySide6.QtGui import QPixmap, QActionGroup, QColor, QFont, QIcon, QImage, QKeySequence, QPainter
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices
from PySide6.QtWidgets import (QAbstractItemView, QLabel, QListWidget, QListWidgetItem, QMenuBar, QStackedWidget,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore import host

HERE = Path(__file__).resolve().parent
_pixmaps = {}


def pixmap(name):
    """One of this package's icons (cached)."""
    if name not in _pixmaps:
        _pixmaps[name] = QPixmap(str(HERE / "icons" / name))
    return _pixmaps[name]


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)
from . import libretro as L

EMULATORS = HERE / "cores"
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
    scale: int = 2               # starting window size (handhelds start bigger)
    process: str = ""            # what Task Manager calls it
    keyboard: bool = False       # a computer: every key goes to it (no controller mapping, fewer shortcuts)
    noun: str = "game"           # 'disk' for the Apple II
    top: str = ""                # a folder right on E: (e.g. 'WADs') instead of one under E:\Emulation
    games: dict = field(default_factory=dict)      # file name (lower case) -> title; only these are listed
    dpad: bool = True            # arrows = D-pad, Enter = Start, Space/Shift = Select (the N64 uses its own keys)
    analog: dict = field(default_factory=dict)     # Qt key -> (stick, axis, -1 or +1): keys that push a stick
    options: dict = field(default_factory=dict)    # libretro core options


SYSTEMS = {
    "nes": System("nes", "NES", "FCE Ultra", "fceumm_libretro.dll", r"(nes|famicom)\b", {".nes", ".fds", ".unf", ".unif"},
                  "nes_icon.png", 256, 240, {Qt.Key_X: L.A, Qt.Key_Z: L.B}, "A:  X\nB:  Z\n",
                  "FCE Ultra by Bero, Xodnizel and the FCEUmm team. Free software under the GNU GPL.",
                  process="fceu.exe"),
    "snes": System("snes", "SNES", "Snes9x", "snes9x_libretro.dll", r"(snes|super nintendo|super famicom|sfc)\b",
                   {".smc", ".sfc", ".swc", ".fig"}, "snes_icon.png", 256, 224,
                   {Qt.Key_X: L.A, Qt.Key_Z: L.B, Qt.Key_S: L.X, Qt.Key_A: L.Y, Qt.Key_Q: L.L, Qt.Key_W: L.R},
                   "A:  X\nB:  Z\nX:  S\nY:  A\nL:  Q\nR:  W\n",
                   "Snes9x by Gary Henderson, Jerremy Koot and the Snes9x team. Free for non-commercial use.",
                   process="snes9x.exe"),
    "gb": System("gb", "Game Boy", "Gambatte", "gambatte_libretro.dll", r"(gb|game ?boy)\b(?! ?(color|advance))",
                 {".gb"}, "gb_icon.png", 160, 144, {Qt.Key_X: L.A, Qt.Key_Z: L.B}, "A:  X\nB:  Z\n",
                 "Gambatte by Sindre Aam\u00e5s and contributors. Free software under the GNU GPL.", scale=3,
                 process="gambatte.exe"),
    "gbc": System("gbc", "Game Boy Color", "Gambatte Color", "gambatte_gbc_libretro.dll", r"(gbc|game ?boy ?colou?r)\b",
                  {".gbc", ".cgb"}, "gbc_icon.png", 160, 144, {Qt.Key_X: L.A, Qt.Key_Z: L.B}, "A:  X\nB:  Z\n",
                  "Gambatte by Sindre Aam\u00e5s and contributors. Free software under the GNU GPL.", scale=3,
                  process="gambatte_gbc.exe"),
    "gba": System("gba", "Game Boy Advance", "mGBA", "mgba_libretro.dll", r"(gba|game ?boy ?advance)\b",
                  {".gba"}, "gba_icon.png", 240, 160,
                  {Qt.Key_X: L.A, Qt.Key_Z: L.B, Qt.Key_Q: L.L, Qt.Key_W: L.R}, "A:  X\nB:  Z\nL:  Q\nR:  W\n",
                  "mGBA by Vicki Pfau and contributors. Free software under the Mozilla Public License 2.0.",
                  scale=3, process="mgba.exe"),
    "gen": System("gen", "Genesis", "PicoDrive", "picodrive_libretro.dll", r"(gen|genesis|mega ?drive|md|32x)\b",
                  {".bin", ".md", ".gen", ".smd", ".32x"}, "gen_icon.png", 320, 224,
                  {Qt.Key_Z: L.Y, Qt.Key_X: L.B, Qt.Key_C: L.A, Qt.Key_A: L.Y, Qt.Key_S: L.B, Qt.Key_D: L.A},
                  "A:  Z or A\nB:  X or S\nC:  C or D\nMode:  Space or Shift\n",
                  "PicoDrive by notaz and contributors (Genesis, Mega Drive and 32X). Free for non-commercial use.",
                  process="picodrive.exe"),
    "sms": System("sms", "Master System", "Genesis Plus", "genesis_plus_gx_libretro.dll", r"(sms|master ?system)\b",
                  {".sms"}, "sms_icon.png", 256, 192, {Qt.Key_Z: L.B, Qt.Key_X: L.A},
                  "Button 1:  Z\nButton 2:  X\n(Start is the console's Pause button)\n",
                  "Genesis Plus GX by Charles MacDonald and Eke-Eke. Free for non-commercial use.",
                  process="gpgx.exe"),
    "gg": System("gg", "Game Gear", "Gearsystem", "gearsystem_libretro.dll", r"(gg|game ?gear)\b",
                 {".gg"}, "gg_icon.png", 160, 144, {Qt.Key_Z: L.B, Qt.Key_X: L.A},
                 "Button 1:  Z\nButton 2:  X\n",
                 "Gearsystem by Ignacio Sanchez. Free software under the GNU GPL v3.", scale=3,
                 process="gearsystem.exe"),
    "apple2": System("apple2", "Apple ][", "AppleWin", "applewin_libretro.dll", r"(apple ?(ii|2|\]\[)|a2)\b",
                     {".dsk", ".do", ".po", ".nib", ".woz", ".hdv", ".2mg"}, "apple2_icon.png", 560, 384, {},
                     "The whole keyboard is the Apple's keyboard (letters, numbers, Return, Esc, arrows...).\n"
                     "Most games boot by themselves; on a menu disk, type the letter or RUN name.\n\n"
                     "Save state:  F5\nLoad state:  F7\nPause:  Pause key\nReset:  F1\n"
                     "Disk list:  File > Disk List", "AppleWin by Michael O'Brien, Tom Charlesworth and the "
                     "AppleWin team. Free software under the GNU GPL.", scale=1, process="applewin.exe",
                     keyboard=True, noun="disk"),
}

N64_KEYS = {Qt.Key_X: L.B, Qt.Key_Z: L.Y, Qt.Key_Space: L.L2, Qt.Key_Q: L.L, Qt.Key_E: L.R,
            Qt.Key_Return: L.START, Qt.Key_Enter: L.START,
            Qt.Key_T: L.UP, Qt.Key_G: L.DOWN, Qt.Key_F: L.LEFT, Qt.Key_H: L.RIGHT}
N64_STICKS = {Qt.Key_Up: (L.ANALOG_LEFT, L.ANALOG_Y, -1), Qt.Key_Down: (L.ANALOG_LEFT, L.ANALOG_Y, 1),
              Qt.Key_Left: (L.ANALOG_LEFT, L.ANALOG_X, -1), Qt.Key_Right: (L.ANALOG_LEFT, L.ANALOG_X, 1),
              Qt.Key_I: (L.ANALOG_RIGHT, L.ANALOG_Y, -1), Qt.Key_K: (L.ANALOG_RIGHT, L.ANALOG_Y, 1),
              Qt.Key_J: (L.ANALOG_RIGHT, L.ANALOG_X, -1), Qt.Key_L: (L.ANALOG_RIGHT, L.ANALOG_X, 1)}
SYSTEMS["n64"] = System(
    "n64", "N64", "Mupen64Plus", "mupen64plus_next_libretro.dll", r"(n64|nintendo ?64)\b", {".z64", ".v64", ".n64"},
    "n64_icon.png", 320, 240, N64_KEYS,
    "Control Stick:  Arrow keys\nA:  X        B:  Z\nZ Trigger:  Space\nL / R:  Q / E\nStart:  Enter\n"
    "C Buttons:  I / J / K / L (up, left, down, right)\nD-pad:  T / F / G / H\n\n"
    "Save state:  F5\nLoad state:  F7\nState slot:  0 - 9\nPause:  P or Pause\nReset:  F1\nGame list:  Esc",
    "Mupen64Plus-Next by the Mupen64Plus team and the libretro project, with the Angrylion RDP renderer. "
    "Free software under the GNU GPL v2.", process="mupen64plus.exe", dpad=False, analog=N64_STICKS,
    options={"mupen64plus-rdp-plugin": "angrylion", "mupen64plus-cpucore": "dynamic_recompiler",
             "mupen64plus-pak1": "memory"})

DOOM_KEYS = {Qt.Key_Control: L.X, Qt.Key_Space: L.A, Qt.Key_Return: L.A, Qt.Key_Enter: L.A,
                 Qt.Key_Shift: L.Y, Qt.Key_Comma: L.L, Qt.Key_Period: L.R, Qt.Key_PageUp: L.L2, Qt.Key_PageDown: L.R2,
                 Qt.Key_Tab: L.SELECT, Qt.Key_Escape: L.START, Qt.Key_Backspace: L.B}
DOOM_HELP = ("Move / turn:  Arrow keys\nFire:  Ctrl\nUse / open:  Space\nRun:  Shift\nStrafe:  , and .\n"
                    "Weapons:  Page Up / Page Down\nAutomap:  Tab\nMenu:  Esc   (Enter picks)\n\n"
                    "Pause:  P\nGame list:  File > Game List")
PRBOOM = "PrBoom by Florian Schulze, Colin Phipps and the PrBoom team (libretro). Free software under the GNU GPL."
SYSTEMS.update({
    "doom": System("doom", "Doom", "Doom", "prboom_libretro.dll", "", {".wad"}, "doom_icon.png", 320, 200,
                   DOOM_KEYS, DOOM_HELP, PRBOOM, process="doom.exe", top="WADs",
                   games={"doom.wad": "Doom", "doom1.wad": "Doom (Shareware)", "freedoom1.wad": "Freedoom: Phase 1"}),
    "doom2": System("doom2", "Doom II", "Doom II", "prboom_doom2_libretro.dll", "", {".wad"}, "doom2_icon.png", 320,
                    200, DOOM_KEYS, DOOM_HELP, PRBOOM, process="doom2.exe", top="WADs",
                    games={"doom2.wad": "Doom II: Hell on Earth", "plutonia.wad": "Final Doom: The Plutonia Experiment",
                           "freedoom2.wad": "Freedoom: Phase 2"}),
    "wolf3d": System("wolf3d", "Wolfenstein 3D", "Wolfenstein 3D", "prboom_wolf3d_libretro.dll", "", {".wad"},
                     "wolf3d_icon.png", 320, 200, DOOM_KEYS, DOOM_HELP,
                     PRBOOM + " Wolfenstein 3D here is the Doom II total conversion, played on Doom II.",
                     process="wolf3d.exe", top="WADs", games={"wolfenstein 3d.wad": "Wolfenstein 3D"}),
})

# Qt key -> libretro RETROK_* code, for computer keyboards (letters and digits use their ASCII codes)
RETROK = {Qt.Key_Return: 13, Qt.Key_Enter: 13, Qt.Key_Backspace: 8, Qt.Key_Tab: 9, Qt.Key_Escape: 27,
          Qt.Key_Space: 32, Qt.Key_Delete: 127, Qt.Key_Up: 273, Qt.Key_Down: 274, Qt.Key_Right: 275,
          Qt.Key_Left: 276, Qt.Key_Insert: 277, Qt.Key_Home: 278, Qt.Key_End: 279, Qt.Key_PageUp: 280,
          Qt.Key_PageDown: 281, Qt.Key_Shift: 304, Qt.Key_Control: 306, Qt.Key_Alt: 308, Qt.Key_CapsLock: 301}


def retrok(event):
    k = event.key()
    if k in RETROK:
        return RETROK[k]
    if Qt.Key_A <= k <= Qt.Key_Z:
        return ord("a") + (k - Qt.Key_A)
    if 32 <= k < 127:                       # digits and punctuation
        return k
    return 0

_cores = {}                      # system key -> Core (each core DLL keeps global state)


def core(system):
    if system.key not in _cores:
        base = host.saves(system.key)                  # SRAM saves and BIOS files, shared by every era
        (base / "system").mkdir(parents=True, exist_ok=True)
        (base / "saves").mkdir(parents=True, exist_ok=True)
        _cores[system.key] = L.Core(EMULATORS / system.core, base / "system", base / "saves", system.options)
    return _cores[system.key]


def icon_for(system):
    pm = pixmap(system.icon)
    return QIcon(pm) if not pm.isNull() else QIcon()


def rom_folders(system):
    """This system's folders under E:\\Emulation (e.g. 'SNES (33 Roms)'), or its own folder on E: (WADs)."""
    local_storage = host.local_storage
    if system.top:
        return [d for d in local_storage().iterdir() if d.is_dir() and d.name.lower() == system.top.lower()]
    emu = next((d for d in local_storage().iterdir() if d.is_dir() and d.name.lower().startswith("emulat")), None)
    if emu is None:
        return []
    return [d for d in sorted(emu.iterdir()) if d.is_dir() and re.match(system.folder, d.name.lower())]


def game_title(path):
    """'Legend of Zelda, The (U) (PRG 0).nes' -> 'The Legend of Zelda' (WADs use their system's game names)."""
    name = Path(path).name.lower()
    for system in SYSTEMS.values():
        if name in system.games:
            return system.games[name]
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
            if ih >= 2 * self.emu.system.height:              # hi-res / interlaced modes: the same picture
                ih //= 2
            if iw >= 2 * self.emu.system.width:
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
            _cores[self.emu.system.key].release_keys()          # never leave a button stuck down
        super().focusOutEvent(event)


class Emulator(QWidget):
    def __init__(self, desktop, system):
        super().__init__()
        self.desktop = desktop
        self.system = system
        self.process_image = system.process                        # for Task Manager
        self.keys = {**(DPAD if system.dpad else {}), **system.buttons}
        self.data = host.saves(system.key)
        self.settings_file = self.data / "settings.json"
        self.frame = None
        self.state = load_json(self.settings_file, {"scale": system.scale, "sound": True, "tv_aspect": False,
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
        MENU_STYLE = host.menu_style()
        bar = QMenuBar()
        bar.setStyleSheet(MENU_STYLE)
        f = bar.addMenu("&File")
        f.addAction(f"&{self.system.noun.title()} List", self.show_list,
                    QKeySequence() if self.system.keyboard else QKeySequence("Ctrl+L"))
        self.recent_menu = f.addMenu("&Recent Games")
        f.addAction("&Close Game", self.close_game)
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close() if self.frame else None)
        n = bar.addMenu("&" + self.system.console)
        self.pause_action = n.addAction("&Pause", self.toggle_pause,
                                        QKeySequence("Pause" if self.system.keyboard else "P"))
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
            a.setChecked(self.state.get("scale", self.system.scale) == k)
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
                if f.suffix.lower() in self.system.exts and (not self.system.games or f.name.lower() in self.system.games):
                    roms.append(f)
        order = list(self.system.games)
        title = (lambda p: self.system.games[p.name.lower()]) if self.system.games else game_title
        for f in sorted(roms, key=(lambda p: order.index(p.name.lower())) if order else (lambda p: game_title(p).lower())):
            item = QListWidgetItem(icon, title(f))
            item.setData(Qt.UserRole, str(f))
            item.setToolTip(f.name)
            self.games.addItem(item)
        if not roms and self.system.top:
            item = QListWidgetItem(f"No games found. Put the {self.system.console} WAD files in "
                                   f"E:\\{self.system.top}, then choose File > Game List.")
            item.setFlags(Qt.NoItemFlags)
            self.games.addItem(item)
        elif not roms:
            ext = sorted(self.system.exts)[0]
            item = QListWidgetItem(f"No games found. Put your {self.system.console} ROMs ({ext}) in "
                                   f"E:\\Emulation\\{self.system.console}, then choose File > Game List.")
            item.setFlags(Qt.NoItemFlags)
            self.games.addItem(item)
        self._refresh_recent()
        if self.game is None:
            self.status.setText(f"{len(roms)} {self.system.noun}s  \u2014  double-click a {self.system.noun} to "
                                f"{'boot' if self.system.keyboard else 'play'}")

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
            host.message(self.desktop, self.system.title, f"{path.name} couldn't be loaded. It may be damaged or use a "
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
        self.set_scale(self.state.get("scale", self.system.scale), save=False)
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
            not self.state.get("pause_inactive") or host.in_front(self.desktop, self.frame))
        if not active and not self.auto_paused and not self.paused:
            self.auto_paused = True
            self.core.release_keys()
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
        if self.system.keyboard:
            return self.computer_key(event, down)
        if event.isAutoRepeat():
            return event.key() in self.keys or event.key() in self.system.analog
        k = event.key()
        if k in self.system.analog:
            self._stick(k, down)
            return True
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

    def _stick(self, key, down):
        """Keys pushing an analog stick all the way (two opposite keys cancel out)."""
        c = self.core
        (c.analog_keys.add if down else c.analog_keys.discard)(key)
        c.analog.clear()
        for k in c.analog_keys:
            stick, axis, sign = self.system.analog[k]
            c.analog[(stick, axis)] = c.analog.get((stick, axis), 0) + sign * 32767
        for pos, value in c.analog.items():
            c.analog[pos] = max(-32767, min(32767, value))

    def computer_key(self, event, down):
        """Computers (the Apple II): every key goes to the machine; only F-keys and Pause stay ours."""
        k = event.key()
        if Qt.Key_F1 <= k <= Qt.Key_F12:
            return False                                       # the menu shortcuts (F1 reset, F5/F7 states)
        if k == Qt.Key_Pause:
            if down:
                self.toggle_pause()
            return True
        if self.game is None:
            return False
        code = retrok(event)
        if not code:
            return False
        text = event.text().upper()                           # the Apple ][ keyboard only types capitals
        mods = (1 if event.modifiers() & Qt.ShiftModifier else 0) | (2 if event.modifiers() & Qt.ControlModifier else 0)
        if event.isAutoRepeat() and down:                     # typematic repeat: press again
            self.core.key_event(True, code, ord(text[0]) if text else 0, mods)
            return True
        self.core.key_event(down, code, ord(text[0]) if text and down else 0, mods)
        return True

    # ---- console menu ------------------------------------------------------------------------------------
    def pause(self, on):
        self.paused = on and self.game is not None
        self.pause_action.setChecked(self.paused)
        if not self.paused:
            self.next_frame = self.clock.elapsed() / 1000
        if self.system.key in _cores:
            _cores[self.system.key].release_keys()
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
            self.audio_out.setVolume(0.0 if (not self.state.get("sound", True) or host.muted()) else 0.8)

    def _save_settings(self):
        save_json(self.settings_file, self.state)

    # ---- help ---------------------------------------------------------------------------------------------
    def show_controls(self):
        host.message(self.desktop, "Controls", self.system.help + SHARED_HELP, "info")

    def about(self):
        c = self.core
        host.message(self.desktop, f"About {self.system.title}",
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
            host.message(desktop, system.title, f"The emulator core ({system.core}) is missing from ClaudeGames\\emulators\\cores.",
                   "error")
            return None
        body = Emulator(desktop, system)
        win = host.window(desktop, system.title, body, icon_for(system),
                       (system.width * system.scale + 16, system.height * system.scale + 90))
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


# program entry points: <key>_icon(), open_<key>(desktop), shutdown_<key>() for every system
def _entry_points(key):
    return (lambda: icon_for(SYSTEMS[key]), lambda desktop: open_system(desktop, key), lambda: shutdown_system(key))


for _key in SYSTEMS:
    globals()[f"{_key}_icon"], globals()[f"open_{_key}"], globals()[f"shutdown_{_key}"] = _entry_points(_key)
