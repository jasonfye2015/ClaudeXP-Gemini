"""NES Emulator: FCE Ultra (the FCEUmm libretro core in assets/emulators) in an XP window.

The game list shows the user's own ROMs from E:\\Emulation\\NES... (not in git). Picking one runs it at 2x with
sound; battery saves (Zelda and friends) are kept in data/nes/saves, save states in data/nes/states (ten slots).

Controls: arrows = D-pad, X = A, Z = B, Enter = Start, Space or Shift = Select.
F5 save state, F7 load state, 0-9 pick a slot, P or Pause to pause, F1 reset, Esc back to the game list."""
import os
import re
import time
from pathlib import Path

from PySide6.QtCore import QByteArray, QElapsedTimer, QRectF, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QIcon, QImage, QKeySequence, QPainter, QPixmap
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices
from PySide6.QtWidgets import (QAbstractItemView, QLabel, QListWidget, QListWidgetItem, QMenuBar, QStackedWidget,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from ... import sound
from ...paths import DATA, ROOT, pixmap
from ...wm import XPWindow
from ..people import load_json, save_json
from . import libretro as L

CORE_DLL = ROOT / "assets" / "emulators" / "fceumm_libretro.dll"
NES_DATA = DATA / "nes"
STATE_FILE = NES_DATA / "settings.json"
ROM_EXTS = {".nes", ".fds", ".unf", ".unif"}
KEYS = {Qt.Key_Up: L.UP, Qt.Key_Down: L.DOWN, Qt.Key_Left: L.LEFT, Qt.Key_Right: L.RIGHT, Qt.Key_X: L.A,
        Qt.Key_Z: L.B, Qt.Key_Return: L.START, Qt.Key_Enter: L.START, Qt.Key_Space: L.SELECT, Qt.Key_Shift: L.SELECT}
NES_W, NES_H = 256, 240

_core = None                     # one core per process (cores keep global state)


def nes_icon():
    pm = pixmap("nes_icon.png")
    return QIcon(pm) if not pm.isNull() else QIcon()


def core():
    global _core
    if _core is None:
        (NES_DATA / "system").mkdir(parents=True, exist_ok=True)
        (NES_DATA / "saves").mkdir(parents=True, exist_ok=True)
        _core = L.Core(CORE_DLL, NES_DATA / "system", NES_DATA / "saves")
    return _core


def rom_folders():
    """NES folders under E:\\Emulation (e.g. 'NES (36 Roms)')."""
    from ...explorer.vfs import local_storage
    emu = next((d for d in local_storage().iterdir() if d.is_dir() and d.name.lower().startswith("emulat")), None)
    if emu is None:
        return []
    return [d for d in sorted(emu.iterdir()) if d.is_dir() and re.match(r"(nes|famicom|nintendo)\b", d.name.lower())]


def game_title(path):
    """'Legend of Zelda, The (U) (PRG 0).nes' -> 'The Legend of Zelda'."""
    t = re.sub(r"\s*[\[(][^\])]*[\])]", "", Path(path).stem).strip()
    m = re.match(r"(.+?), The(\s*-.*)?$", t)
    if m:
        t = "The " + m.group(1) + (m.group(2) or "")
    return t


class Screen(QWidget):
    """The NES picture, pixel-sharp, letterboxed in black, with FCE Ultra-style messages in the corner."""

    def __init__(self, emu):
        super().__init__()
        self.emu = emu
        self.image = QImage()
        self.message = ""
        self.message_until = 0.0
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(NES_W, NES_H)

    def say(self, text, seconds=2.0):
        self.message, self.message_until = text, time.monotonic() + seconds
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.black)
        if not self.image.isNull():
            aspect = (4 / 3) if self.emu.state.get("tv_aspect") else NES_W / NES_H
            w, h = self.width(), self.height()
            if w / h > aspect:
                w = int(h * aspect)
            else:
                h = int(w / aspect)
            if not self.emu.state.get("tv_aspect"):                # whole-number scaling keeps pixels square
                k = max(1, min(self.width() // NES_W, self.height() // NES_H))
                w, h = NES_W * k, NES_H * k
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
        core().buttons.clear()                     # never leave a button stuck down
        super().focusOutEvent(event)


class Emulator(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = load_json(STATE_FILE, {"scale": 2, "sound": True, "tv_aspect": False, "pause_inactive": True,
                                            "recent": []})
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
        self.games.setIconSize(pixmap("nes_icon.png").size().scaled(24, 24, Qt.KeepAspectRatio))
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
        n = bar.addMenu("&NES")
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
        h.addAction("&About FCE Ultra...", self.about)
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
        icon = nes_icon()
        roms = []
        for folder in rom_folders():
            for f in folder.iterdir():
                if f.suffix.lower() in ROM_EXTS:
                    roms.append(f)
        for f in sorted(roms, key=lambda p: game_title(p).lower()):
            item = QListWidgetItem(icon, game_title(f))
            item.setData(Qt.UserRole, str(f))
            item.setToolTip(f.name)
            self.games.addItem(item)
        if not roms:
            item = QListWidgetItem("No games found. Put your NES ROMs (.nes) in E:\\Emulation\\NES, then choose "
                                   "File > Game List.")
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
        c = core()
        if not c.load(path):
            from ...explorer.dialogs import msgbox
            msgbox(self.desktop, "FCE Ultra", f"{path.name} couldn't be loaded. It may be damaged or use a "
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
            self.frame.set_title(f"FCE Ultra - {game_title(path)}")
        self.screen.say(f"Loaded {game_title(path)}")

    def close_game(self):
        if self.game is None:
            return
        self._save_sram()
        self.timer.stop()
        self.sram_timer.stop()
        core().unload()
        core().buttons.clear()
        self._stop_audio()
        self.game = None
        self.screen.image = QImage()
        self.stack.setCurrentWidget(self.games)
        self.fill_games()
        if self.frame is not None:
            self.frame.set_title("FCE Ultra")

    def _tick(self):
        if self.game is None:
            return
        active = self.frame is not None and self.frame.isVisible() and (
            not self.state.get("pause_inactive") or self.desktop.is_active(self.frame))
        if not active and not self.auto_paused and not self.paused:
            self.auto_paused = True
            core().buttons.clear()
            self.screen.update()
        elif active and self.auto_paused:
            self.auto_paused = False
            self.next_frame = self.clock.elapsed() / 1000
        if self.paused or self.auto_paused or self.stack.currentWidget() is not self.screen:
            return
        c = core()
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
            return event.key() in KEYS
        k = event.key()
        if k in KEYS:
            (core().buttons.add if down else core().buttons.discard)(KEYS[k])
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

    # ---- NES menu ---------------------------------------------------------------------------------------
    def pause(self, on):
        self.paused = on and self.game is not None
        self.pause_action.setChecked(self.paused)
        if not self.paused:
            self.next_frame = self.clock.elapsed() / 1000
        core().buttons.clear() if _core else None
        self.screen.update()

    def toggle_pause(self):
        self.pause(not self.paused)

    def reset(self):
        if self.game is not None:
            core().reset()
            self.screen.say("Reset")

    def power(self):
        if self.game is not None:
            self.play(self.game)
            self.screen.say("Power cycled")

    # ---- states and battery saves ------------------------------------------------------------------------
    def _sram_file(self):
        return NES_DATA / "saves" / (self.game.stem + ".srm")

    def _state_file(self, slot):
        return NES_DATA / "states" / f"{self.game.stem}.st{slot}"

    def _save_sram(self):
        if self.game is None:
            return
        data = core().save_ram()
        if data and data != self.last_sram:
            try:
                self._sram_file().write_bytes(data)
                self.last_sram = data
            except OSError:
                pass

    def save_state(self):
        if self.game is None:
            return
        data = core().save_state()
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
        self.screen.say(f"State {self.slot} loaded" if core().load_state(f.read_bytes())
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
        chrome = self.frame.size() - self.size()
        extra_h = self.height() - self.stack.height()
        area = self.desktop.work_area()
        while k > 1 and (NES_H * k + extra_h + chrome.height() > area.height()
                         or NES_W * k + chrome.width() > area.width()):
            k -= 1                                          # 3x doesn't fit on a 1024x768 screen
        self.frame.resize(NES_W * k + chrome.width(), NES_H * k + extra_h + chrome.height())
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
        save_json(STATE_FILE, self.state)

    # ---- help ---------------------------------------------------------------------------------------------
    def show_controls(self):
        from ...explorer.dialogs import msgbox
        msgbox(self.desktop, "Controls",
               "D-pad:  Arrow keys\nA:  X\nB:  Z\nStart:  Enter\nSelect:  Space or Shift\n\n"
               "Save state:  F5\nLoad state:  F7\nState slot:  0 - 9\nPause:  P or Pause\nReset:  F1\n"
               "Game list:  Esc", "info")

    def about(self):
        from ...explorer.dialogs import msgbox
        c = core()
        msgbox(self.desktop, "About FCE Ultra",
               f"FCE Ultra NES Emulator\n\nEmulation core: {c.name} {c.version}\n"
               "FCE Ultra by Bero, Xodnizel and the FCEUmm team. Free software under the GNU GPL.", "info")

    def closeEvent(self, event):
        self.close_game()
        self._save_settings()
        event.accept()


_open = {}


def open_nes(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        if not CORE_DLL.exists():
            from ...explorer.dialogs import msgbox
            msgbox(desktop, "FCE Ultra", "The emulator core (fceumm_libretro.dll) is missing from "
                   "assets\\emulators.", "error")
            return None
        body = Emulator(desktop)
        win = XPWindow(desktop, "FCE Ultra", body, nes_icon(), (NES_W * 2 + 16, NES_H * 2 + 90))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    global _core
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.close_game()
    if _core is not None:
        _core.close()
        _core = None
