"""What the tests share: where everything is, a scratch folder, the offscreen Qt application, waiting for events,
and running a test file's tests (run.py starts each file in its own process; a file also runs on its own:
python Tests\\test_qbasic.py).

A test is a function named test_...; its docstring's first line is what the report calls it. It passes by returning,
fails by raising (assert), and is skipped with support.skip("why") - say, when Local Storage isn't there. A file that
sets SLOW = True runs only with --slow; TIMEOUT = seconds raises the time it's allowed (3 minutes otherwise).

The one rule: a test never touches the real data - the computers' data folders, Program Files, the Companions,
Kithylin AI's chats, the game saves, Profile. Everything a test writes goes under scratch()."""
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[1]
CORE = TIMELINE / "ClaudeCore"
APPS = TIMELINE / "ClaudeApps"
XP = TIMELINE / "ClaudeXP"
W7 = TIMELINE / "Claude7"
W11 = TIMELINE / "Claude11"
LOCAL_STORAGE = TIMELINE / "Local Storage"

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt" and Path(r"C:\Windows\Fonts").is_dir():
    os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")          # (without it, text renders as boxes)
for _p in (str(APPS), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


class Skip(Exception):
    pass


def skip(why):
    raise Skip(why)


def needs(path, what=None):
    """Skip unless this file or folder (in Local Storage, usually) is there."""
    path = Path(path)
    if not path.exists():
        skip("needs " + (what or str(path.relative_to(TIMELINE) if path.is_relative_to(TIMELINE) else path)))
    return path


_tmp = {}


def scratch(*parts):
    """A folder of this test file's own (run.py deletes it afterwards unless --keep)."""
    if "root" not in _tmp:
        given = os.environ.get("TIMELINE_TEST_TMP")
        _tmp["root"] = Path(given) if given else Path(tempfile.mkdtemp(prefix="timeline-test-"))
    path = _tmp["root"].joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def slow():
    return os.environ.get("TIMELINE_TEST_SLOW") == "1"


# ---- Qt ------------------------------------------------------------------------------------------------------------
def qapp():
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
        app = QApplication([sys.argv[0]])
    return app


def pump(seconds=0.0, until=None):
    """Let Qt run for this long, or until until() is true (then True; False if the time ran out first)."""
    app = qapp()
    end = time.monotonic() + seconds
    while True:
        app.processEvents()
        if until is not None and until():
            return True
        if time.monotonic() >= end:
            return until is None
        time.sleep(0.005)


# ---- no language models ------------------------------------------------------------------------------------------
def no_model_server():
    """Nothing starts a llama-server or loads a model: the computers act as if no models were installed (their
    'no model' mode), so a test never uses the graphics card."""
    from claudecore.ai import llm_server as L

    def refuse(*_a, **_k):
        raise RuntimeError("no language models while testing")
    L.status = lambda: "No language models while testing."
    L.available = lambda: False
    L.ready = lambda: False
    L.recheck = lambda desktop=None: False
    L.ensure_started = refuse
    L.restart = refuse
    L.load = refuse
    L.start_in_background = lambda: None


# ---- errors that don't raise ---------------------------------------------------------------------------------------
def catch_errors():
    """Errors in Qt callbacks, timers and threads only print; this collects them (a list of tracebacks) so a test can
    say there were none."""
    import threading
    caught = []

    def hook(kind, value, tb):
        caught.append("".join(traceback.format_exception(kind, value, tb)))
    sys.excepthook = hook
    threading.excepthook = lambda a: hook(a.exc_type, a.exc_value, a.exc_traceback)
    return caught


def no_errors(caught, what="while it ran"):
    assert not caught, f"{len(caught)} error(s) {what}:\n" + "\n".join(caught[:3])


# ---- running a file's tests ---------------------------------------------------------------------------------------
def _report(line):
    """A line of the report (run.py tells them from whatever the programs print by the mark in front)."""
    print(("@@" if os.environ.get("TIMELINE_TEST_RUNNER") else "") + line, flush=True)


def _title(fn):
    doc = (fn.__doc__ or "").strip().splitlines()
    return doc[0].rstrip(".") if doc else fn.__name__[5:].replace("_", " ")


def _short(tb_text):
    """The traceback without the runner's own frames."""
    lines = tb_text.rstrip().splitlines()
    keep = []
    skipping = False
    for line in lines:
        if line.startswith('  File "') and __file__ in line:
            skipping = True
            continue
        if skipping and line.startswith("    "):
            continue
        skipping = False
        keep.append(line)
    return "\n".join(keep)


def run_tests(namespace, only=()):
    """Run the test_ functions of a module (its globals), in order. Prints a line each and a RESULT line for run.py.
    Returns (passed, failed, skipped)."""
    tests = [(k, v) for k, v in namespace.items() if k.startswith("test_") and callable(v)]
    if not tests and callable(namespace.get("run")):
        tests = [("run", namespace["run"])]                  # (ClaudeCore's older tests have a run())
    if only:
        tests = [(k, v) for k, v in tests if any(w.lower() in (k + " " + _title(v)).lower() for w in only)]
    passed = failed = skipped = 0
    for name, fn in tests:
        t = time.perf_counter()
        try:
            fn()
            passed += 1
            mark, extra = "ok   ", ""
        except Skip as exc:
            skipped += 1
            mark, extra = "skip ", f"  ({exc})"
        except BaseException as exc:                       # (an assert, an error, or SystemExit from deep down)
            failed += 1
            mark, extra = "FAIL ", "\n" + "\n".join("        " + ln for ln in _short(traceback.format_exc()).splitlines())
            if isinstance(exc, KeyboardInterrupt):
                raise
        for line in f"  {mark} {_title(fn)}  ({time.perf_counter() - t:.1f} s){extra}".splitlines():
            _report(line)
    _report(f"RESULT {passed} {failed} {skipped}")
    return passed, failed, skipped


def main(namespace):
    """For a test file run on its own: run its tests (or those whose names have the words given) and exit."""
    _passed, failed, _skipped = run_tests(namespace, sys.argv[1:])
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1 if failed else 0)                  # (straight out: a Qt app's threads can't hang the exit)
