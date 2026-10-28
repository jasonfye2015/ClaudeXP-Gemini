"""Check everything: run the Claude Timeline's tests and say what passed.

    python Tests\\run.py                  all of them but the slow ones (a couple of minutes)
    python Tests\\run.py --slow           and boot each computer in a sandbox too (several minutes more)
    python Tests\\run.py --all-programs   with --slow: launch every program on each computer (half an hour or so)
    python Tests\\run.py qbasic soul      only the files whose names have these words
    python Tests\\run.py --keep           keep the scratch folders the tests wrote to (their path is printed)

Each test file runs in its own process, offscreen, with a scratch folder of its own: one that crashes outright is
reported as crashed and the rest still run. The files are Tests\\test_*.py and ClaudeCore\\tests\\test_*.py.
The whole report is also written to Tests\\last run.txt."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMELINE = HERE.parent
FOLDERS = [HERE, TIMELINE / "ClaudeCore" / "tests"]
REPORT = HERE / "last run.txt"
TIMEOUT = 180
# a process that ends with these didn't fail a test, it crashed
CRASHES = {0xC0000409: "Qt aborted it (often a QThread let go of while still running)",
           0xC0000005: "an access violation", 0xC00000FD: "a stack overflow", 3: "abort()"}


def _servers():
    """The language-model servers running now (their process ids) - a test must never start one."""
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq llama-server.exe", "/FO", "CSV", "/NH"],
                                 capture_output=True, text=True, timeout=10).stdout
            return {int(row.split('","')[1]) for row in out.splitlines() if row.startswith('"llama-server')}
        out = subprocess.run(["pgrep", "-x", "llama-server"], capture_output=True, text=True, timeout=10).stdout
        return {int(x) for x in out.split()}
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return set()


def files(words):
    found = [p for folder in FOLDERS if folder.is_dir() for p in sorted(folder.glob("test_*.py"))]
    if words:
        found = [p for p in found if any(w.lower() in p.stem.lower() for w in words)]
    return found


def _settings(path):
    """SLOW and TIMEOUT from a test file, read without importing it."""
    text = path.read_text(encoding="utf-8")
    slow = re.search(r"^SLOW\s*=\s*True", text, re.M) is not None
    m = re.search(r"^TIMEOUT\s*=\s*(\d+)", text, re.M)
    return slow, int(m.group(1)) if m else TIMEOUT


def child(path):
    """Run one file's tests in this process (run.py starts itself like this for each file)."""
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(path.parent))
    import support
    import importlib.util
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    try:
        spec.loader.exec_module(module)
    except support.Skip as exc:
        support._report(f"  skip  the whole file  ({exc})")
        support._report("RESULT 0 0 1")
        os._exit(0)
    _p, failed, _s = support.run_tests(vars(module))
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1 if failed else 0)


def main(argv):
    if argv[:1] == ["--child"]:
        return child(Path(argv[1]))
    flags = {a for a in argv if a.startswith("--")}
    words = [a for a in argv if not a.startswith("--")]
    slow = "--slow" in flags or "--all-programs" in flags
    root = Path(tempfile.mkdtemp(prefix="timeline-tests-"))
    out = []

    def say(line=""):
        print(line, flush=True)
        out.append(line)

    say(f"Claude Timeline tests - {time.strftime('%d %B %Y %H:%M')} - Python {sys.version.split()[0]}")
    totals = {"passed": 0, "failed": 0, "skipped": 0}
    trouble = []
    started = time.monotonic()
    for path in files(words):
        is_slow, timeout = _settings(path)
        if is_slow and "--all-programs" in flags:
            timeout *= 4                                 # (every program, not a dozen)
        name = path.relative_to(TIMELINE).as_posix()
        if is_slow and not slow:
            say(f"{name}  - slow, left out (add --slow)")
            continue
        say(name)
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1", QT_QPA_PLATFORM="offscreen",
                   TIMELINE_TEST_RUNNER="1",
                   TIMELINE_TEST_TMP=str(root / path.stem), TIMELINE_TEST_SLOW="1" if slow else "0",
                   TIMELINE_TEST_ALL_PROGRAMS="1" if "--all-programs" in flags else "0")
        if os.name == "nt":
            env.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")
        proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--child", str(path)],
                                cwd=str(TIMELINE), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace")
        result, noise = None, []
        timer = threading.Timer(timeout, proc.kill)
        timer.start()
        before, started_servers = _servers(), set()

        def watch():                                     # (any model server that appears while it runs)
            while proc.poll() is None:
                started_servers.update(_servers() - before)
                time.sleep(1)
        threading.Thread(target=watch, daemon=True).start()
        t = time.monotonic()
        for line in proc.stdout:
            line = line.rstrip("\n")
            if line.startswith("@@RESULT "):
                result = [int(x) for x in line.split()[1:4]]
            elif line.startswith("@@"):
                say(line[2:])
            elif line.strip():
                noise.append(line)                       # (what the programs print along the way: shown on failure)
        code = proc.wait()
        timer.cancel()
        took = time.monotonic() - t
        started_servers.update(_servers() - before)
        if started_servers:
            still = started_servers & _servers()
            say(f"  FAIL   it started a language-model server (process {', '.join(map(str, sorted(started_servers)))})"
                " - a test must never use the graphics card" + (f"; still running: {', '.join(map(str, still))}"
                                                                 if still else ""))
            totals["failed"] += 1
            trouble.append(name)
        if result is None:
            why = ("timed out after %d s" % timeout if took >= timeout - 1 else
                   "crashed: " + CRASHES.get(code & 0xFFFFFFFF, f"exit code {code}"))
            say(f"  FAIL   the file {why}")
            for line in noise[-15:]:
                say("        " + line)
            totals["failed"] += 1
            trouble.append(name)
            continue
        p, f, s = result
        totals["passed"] += p
        totals["failed"] += f
        totals["skipped"] += s
        if f:
            trouble.append(name)
            for line in noise[-10:]:
                say("        | " + line)
    say()
    say(f"{totals['passed']} passed, {totals['failed']} failed, {totals['skipped']} skipped "
        f"in {time.monotonic() - started:.0f} s" + (f" - look at: {', '.join(trouble)}" if trouble else ""))
    if "--keep" in flags:
        say(f"The scratch folders are kept in {root}")
    else:
        shutil.rmtree(root, ignore_errors=True)
    try:
        REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
    except OSError:
        pass
    return 1 if totals["failed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
