"""Code tidying for Copilot Python Studio: format, tidy imports, and rename a symbol. Uses the offline `ruff`
installed in the studio runtime; renaming uses Python's own tokenizer. No Qt in this module."""
import ast
import io
import keyword
import os
import subprocess
import sys
import tokenize

SAFE_RULES = "I,F401"          # sort imports, remove unused imports (both safe, never change behaviour)
LINE_LENGTH = 100


class TidyError(Exception):
    pass


def _env():
    env = dict(os.environ)
    for var in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(var, None)
    env["PYTHONUTF8"] = "1"
    return env


def _ruff(python, args, text, name="program.py"):
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        r = subprocess.run([str(python), "-m", "ruff", *args, "--stdin-filename", name, "-"], input=text,
                           capture_output=True, text=True, encoding="utf-8", timeout=30, env=_env(),
                           creationflags=flags)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise TidyError(f"Could not run the formatter: {e}")
    if "No module named ruff" in r.stderr:
        raise TidyError("The formatter (ruff) is not installed. Use Tools > Install Package and type: ruff")
    return r


def available(python):
    try:
        return "No module named" not in _ruff(python, ["--version"], "").stderr
    except TidyError:
        return False


def _check_syntax(text, what):
    try:
        ast.parse(text)
    except SyntaxError as e:
        raise TidyError(f"Fix the syntax error on line {e.lineno} first ({e.msg}); then {what}.")
    except ValueError as e:
        raise TidyError(str(e))


def format_code(python, text):
    """The text laid out in the standard Black-compatible style (spacing, quotes, wrapping)."""
    _check_syntax(text, "the code can be formatted")
    r = _ruff(python, ["format", "--line-length", str(LINE_LENGTH)], text)
    if r.returncode != 0:
        raise TidyError(_first_error(r.stderr) or "The code could not be formatted.")
    return r.stdout


def tidy_imports(python, text):
    """Imports sorted and unused ones removed. Nothing else changes."""
    _check_syntax(text, "imports can be tidied")
    r = _ruff(python, ["check", "--select", SAFE_RULES, "--fix", "--exit-zero", "--quiet",
                       "--line-length", str(LINE_LENGTH)], text)
    if r.returncode != 0 or (not r.stdout.strip() and text.strip()):
        raise TidyError(_first_error(r.stderr) or "The imports could not be tidied.")
    return r.stdout


def tidy_all(python, text):
    return format_code(python, tidy_imports(python, text))


def _first_error(stderr):
    for line in stderr.splitlines():
        line = line.strip()
        if line and not line.startswith("warning"):
            return line.replace("error: ", "")[:200]
    return ""


def valid_name(name):
    return name.isidentifier() and not keyword.iskeyword(name)


def identifier_at(text, offset):
    """The identifier under the cursor offset, or ''."""
    if not text:
        return ""
    i = min(max(offset, 0), len(text))
    start = i
    while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
        start -= 1
    end = i
    while end < len(text) and (text[end].isalnum() or text[end] == "_"):
        end += 1
    word = text[start:end]
    return word if word.isidentifier() and not keyword.iskeyword(word) else ""


def count_uses(text, name):
    return len(_name_tokens(text, name))


def _name_tokens(text, name):
    """(line, column) of every NAME token equal to `name` that is not an attribute of something else (obj.name) and
    not a keyword argument name in a call to something unknown. Strings and comments are never touched."""
    found = []
    previous = None
    depth_calls = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return found
    for i, tok in enumerate(tokens):
        if tok.type == tokenize.NAME and tok.string == name:
            after_dot = previous is not None and previous.type == tokenize.OP and previous.string == "."
            if not after_dot:
                found.append(tok.start)
        if tok.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT):
            previous = tok
    return found


def rename(text, old, new):
    """Rename every use of the identifier `old` to `new`. Returns (new_text, number_replaced).
    Skips strings, comments and obj.attribute names, so it renames variables, functions, classes and parameters."""
    if not valid_name(new):
        raise TidyError(f"\"{new}\" is not a valid Python name.")
    spots = _name_tokens(text, old)
    if not spots:
        return text, 0
    lines = text.split("\n")
    for row, col in sorted(spots, reverse=True):
        line = lines[row - 1]
        lines[row - 1] = line[:col] + new + line[col + len(old):]
    return "\n".join(lines), len(spots)


def clashes(text, new):
    """True when `new` is already used as a name in the file, so a rename may merge two things."""
    return bool(_name_tokens(text, new))
