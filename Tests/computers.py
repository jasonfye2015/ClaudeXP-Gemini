"""Booting one of the three computers for a test - for real, through its power-on screens, offscreen - in a sandbox:

  - its data folder, its Program Files (Windows 7 and 11) and ClaudeAIM's chats are scratch folders;
  - its E: drive (Local Storage) is an empty scratch folder, so no program can change the archive, the Companions or
    your projects - and the computers are shown coping with an empty drive;
  - no language model server starts, Kithylin AI loads no model, and the Bluesky watcher stays off;
  - Kithylin AI keeps its chats in a scratch folder (KITHYLINAI_DATA).

One computer per process (they replace each other's modules): each computer has a test file of its own."""
import importlib
import os
import sys
import time
import traceback

import support

ERAS = {2001: ("ClaudeXP", "claudexp", "EPOCH-2001"), 2011: ("Claude7", "claude7", "SYSTEM-2011"),
        2025: ("Claude11", "claude11", "WORKSTATION-2025")}
# programs a sweep leaves alone: the autopilot takes the computer over; on XP, the ones that keep their data in XP's
# own Program Files, which a sandbox can't stand in for (Windows 7 and 11 run the same programs with theirs sandboxed)
NEVER = {"autopilot"}
XP_OWN_FILES = {"aim", "irc", "muck", "navigator", "iexplore", "furdir"}
# what a quick run opens on each computer (the ones it has): the shared programs and a few of each kind
QUICK = ["mycomputer", "notepad", "calc", "soulsong", "qbstudio", "pystudio", "kithylinai", "manual", "backup",
         "claudeai", "copilotwidgets", "claudejeweled", "minesweeper", "comix", "tv", "stickynotes"]


class Computer:
    def __init__(self, era):
        self.era = era
        self.folder, self.pkg, self.name = ERAS[era]
        self.sandbox = support.scratch("computer")
        self.storage = support.scratch("computer", "Local Storage")
        self.errors = support.catch_errors()
        self.app = None
        self.current = "starting up"
        self.dialogs = []

    def _watchdog(self):
        """A dialog left waiting for a click would wait forever - there's no one to click it. Every half second, one
        that's open is closed, and noted."""
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        def check():
            w = QApplication.activeModalWidget()
            if w is not None:
                self.dialogs.append(f"{self.current}: \"{w.windowTitle() or type(w).__name__}\"")
                print(f"closed a dialog: {self.dialogs[-1]}", flush=True)
                try:
                    w.reject()
                except Exception:
                    w.close()
        self._dog = QTimer()
        self._dog.timeout.connect(check)
        self._dog.start(500)

    # ---- before the computer exists ----
    def prepare(self):
        root = support.TIMELINE / self.folder
        sys.path.insert(0, str(root))
        os.environ["KITHYLINAI_DATA"] = str(support.scratch("computer", "Kithylin AI data"))
        os.environ.setdefault("CLAUDE7_SETUP_SPEED", "50")
        empty = self.storage
        if self.era == 2001:
            import claudexp.paths as P
            P.DATA = self.sandbox / "data"
            from claudexp.explorer import vfs
            vfs.local_storage = lambda: empty
            from claudexp import realism
            realism.local_storage = lambda: empty
            from claudexp.programs.aim import ensure_aim_path
            ensure_aim_path()
            import claudeaim.paths as AP
            AP.DATA = self.sandbox / "ClaudeAIM data"
            AP.HISTORY = AP.DATA / "history"
            AP.HISTORY.mkdir(parents=True, exist_ok=True)
        else:
            P = importlib.import_module(f"{self.pkg}.paths")
            P.DATA = self.sandbox / "data"
            P.PROGRAM_FILES = self.sandbox / "Program Files"
            vfs = importlib.import_module(f"{self.pkg}.vfs")
            vfs.local_storage = lambda: empty
            xpcompat = importlib.import_module(f"{self.pkg}.xpcompat")
            xpcompat.install()
            xpcompat.program_files_ready()
            import claudexp.paths as XP
            assert str(XP.DATA).startswith(str(self.sandbox)), f"XP's code would write to {XP.DATA}"
            importlib.import_module(f"{self.pkg}.residents_sync").sync()       # (into the sandbox's Program Files)
        support.no_model_server()
        from claudexp import bsky
        bsky.install = lambda desktop=None: None
        from kithylinai import engine
        engine.Engine.load = lambda self, *a, **k: self.status.emit("(no models while testing)")

    def make(self):
        qapp = support.qapp()
        style = importlib.import_module(f"{self.pkg}.style")
        sound = importlib.import_module(f"{self.pkg}.sound")
        style.apply(qapp)
        sound.set_muted(True)
        if self.era == 2001:
            from claudexp import persona_style
            persona_style.apply()                       # (as main.py does: the computer's frozen style)
        user = importlib.import_module(f"{self.pkg}.user")
        setup = importlib.import_module(f"{self.pkg}.setup")
        user.new_account("Tester", computer=self.name)
        setup.finished()
        if self.era != 2001:
            importlib.import_module(f"{self.pkg}.programs")          # (installs that era's registry)
        App = getattr(importlib.import_module(f"{self.pkg}.app"),
                      {2001: "ClaudeXP", 2011: "Claude7", 2025: "Claude11"}[self.era])
        self._watchdog()
        self.app = App()
        self.app.resize(1366, 768)
        return self.app

    # ---- running it ----
    @property
    def screen(self):
        return self.app.stack.currentWidget()

    @property
    def desktop(self):
        return self.app.desktop

    def wait_for(self, widget, seconds):
        return support.pump(seconds, until=lambda: self.screen is widget)

    def power_on(self):
        """From the power button to the desktop, through every screen in between."""
        app = self.app
        app.start()
        sign_in = app.welcome if self.era == 2001 else app.logon
        assert self.wait_for(sign_in, 90), f"it never reached the sign-in screen (stuck on {type(self.screen).__name__})"
        support.pump(0.5)
        if self.era == 2001:
            app.welcome._log_on()
        elif self.era == 2011:
            app.logon._submit()
        else:
            app.logon._wake()
            support.pump(1.0)
            app.logon._submit()
        assert self.wait_for(app.desktop, 30), f"it never reached the desktop (stuck on {type(self.screen).__name__})"
        support.pump(6)                                  # (what starts with Windows)

    def registry(self):
        import claudexp.programs as xp
        return xp

    def close_all(self):
        for win in list(self.desktop.windows):
            try:
                win.request_close() if hasattr(win, "request_close") else self.desktop.close_window(win)
            except Exception:
                pass
        support.pump(0.3)
        try:
            self.registry().shutdown_all()
        except Exception:
            pass
        support.pump(0.2)

    def sweep(self, keys):
        """Open each program in turn, then close it. Returns [problems]."""
        xp = self.registry()
        have = [p.key for p in xp.PROGRAMS]
        problems = []
        for key in keys:
            if key not in have or key in NEVER or (self.era == 2001 and key in XP_OWN_FILES):
                continue
            before = len(self.errors)
            asked = len(self.dialogs)
            t = time.monotonic()
            self.current = key
            print(f"opening {key}", flush=True)                # (if it hangs, the report's last lines say where)
            try:
                xp.launch(self.desktop, key)
                support.pump(1.0)
            except Exception:
                problems.append(f"{key}: " + traceback.format_exc().strip().splitlines()[-1])
            if time.monotonic() - t > 30:
                problems.append(f"{key}: took {time.monotonic() - t:.0f} s to open")
            self.close_all()
            support.pump(0.5)                                 # (what closing sets off a moment later is its too)
            if len(self.errors) > before:
                problems.append(f"{key}: " + self.errors[before].strip().splitlines()[-1])
                del self.errors[before:]
            for d in self.dialogs[asked:]:                    # (opened and closed untouched: nothing to ask about)
                problems.append(f"a dialog was left waiting - {d}")
        self.current = "after the programs"
        return problems

    def everything(self):
        return [p.key for p in self.registry().PROGRAMS]


def run_computer_tests(era, namespace):
    """The tests every computer gets, made into test_ functions in the calling file's globals."""
    pc = Computer(era)

    def test_boots():
        """It boots in a sandbox: power on, the BIOS, Windows starting, signing in, the desktop"""
        pc.prepare()
        pc.make()
        pc.power_on()
        support.no_errors(pc.errors, "while it started")

    def test_start_menu():
        """The Start menu opens and closes"""
        if pc.app is None:
            support.skip("it didn't boot")
        pc.desktop.toggle_start_menu()
        support.pump(0.5)
        pc.desktop.hide_start_menu()
        support.pump(0.2)
        support.no_errors(pc.errors)

    def test_programs_open():
        """The shared programs and a few of every kind open and close (all of them with --all-programs)"""
        if pc.app is None:
            support.skip("it didn't boot")
        keys = pc.everything() if os.environ.get("TIMELINE_TEST_ALL_PROGRAMS") == "1" else QUICK
        problems = pc.sweep(keys)
        assert not problems, "\n".join(problems)

    def test_log_off_and_shut_down():
        """Log off, sign in again, then shut down"""
        if pc.app is None:
            support.skip("it didn't boot")
        app = pc.app
        app.log_off()
        sign_in = app.welcome if era == 2001 else app.logon
        assert pc.wait_for(sign_in, 30), "it didn't come back to the sign-in screen"
        support.pump(0.5)
        app.shut_down()
        support.pump(4)
        support.no_errors(pc.errors)

    for fn in (test_boots, test_start_menu, test_programs_open, test_log_off_and_shut_down):
        namespace[fn.__name__] = fn
    return pc
