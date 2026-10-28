"""The code as a whole: every Python file compiles cleanly, no name is used that was never defined (pyflakes - the
NameError waiting to happen), and the launcher's own start-up self-check finds nothing that would stop a computer."""
import os
import warnings
from pathlib import Path

import support

SKIP = {".venv", "venv", ".venv-build", "Python", "Python-mac", "Local Storage", ".git", "__pycache__",
        "node_modules", "build", "dist", "seed"}


def _files():
    for root, dirs, names in os.walk(support.TIMELINE):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for n in names:
            if n.endswith(".py"):
                yield Path(root) / n


def _rel(path):
    return Path(path).relative_to(support.TIMELINE).as_posix()


def test_everything_compiles():
    """Every Python file compiles, without warnings (an invalid escape like "\\d" in a string becomes an error one day)"""
    bad = []
    for f in _files():
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            try:
                compile(f.read_bytes(), str(f), "exec", dont_inherit=True)
            except (SyntaxError, SyntaxWarning, ValueError) as exc:
                bad.append(f"{_rel(f)}: {exc}")
    assert not bad, "\n".join(bad)


def test_no_undefined_names():
    """No name is used that's never defined (pyflakes)"""
    try:
        from pyflakes import api, messages, reporter
    except ImportError:
        support.skip("pyflakes isn't installed (python -m pip install pyflakes)")

    class Collect(reporter.Reporter):
        def __init__(self):
            self.found = []

        def flake(self, m):
            if isinstance(m, (messages.UndefinedName, messages.UndefinedLocal, messages.UndefinedExport)):
                self.found.append(f"{_rel(m.filename)}:{m.lineno} {m.message % m.message_args}")

        def unexpectedError(self, filename, msg):
            pass

        def syntaxError(self, filename, msg, lineno, offset, text):
            pass
    r = Collect()
    for f in _files():
        api.checkPath(str(f), r)
    assert not r.found, "\n".join(r.found)


def test_self_check():
    """The launcher's self-check: no program name Windows can't use, no code error, no damaged settings file"""
    from claudecore import selfcheck
    selfcheck.CACHE = support.scratch("selfcheck") / "selfcheck.json"       # (not Profile's: check every file)
    findings = selfcheck.check_programs() + selfcheck.check_code() + selfcheck.check_data()
    problems = [f"[{f.level}] {f.message} {f.advice}" for f in findings if f.level in ("error", "warning")]
    assert not problems, "\n".join(problems)


if __name__ == "__main__":
    support.main(globals())
