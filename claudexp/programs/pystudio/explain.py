"""Plain-English explanations for Python Studio: builds the questions sent to the AI Helper. No Qt here."""
import ast
import re

TRACE_FILE = re.compile(r'File "([^"]+)", line (\d+)')
SKIP_PARTS = ("site-packages", "python312", "\\lib\\", "/lib/", "<frozen", "<string>")
STYLE = ("I am a beginner. Explain in simple words, short sentences and no jargon. Say what it does or why it "
         "happened. Do not rewrite my whole program. If something should change, show only the few lines.")


def scope_at(source, line):
    """First and last line (1-based) of the function or class around `line`, or just that line."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return line, line
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            if start <= line <= node.end_lineno and (best is None or start >= best[0]):
                best = (start, node.end_lineno)
    return best or (line, line)


def code_prompt(code, name="my program", first=None, last=None, whole=False):
    where = ""
    if first:
        where = f" (lines {first}-{last})" if last and last != first else f" (line {first})"
    if whole:
        where = " (the whole file)"
    return (f"Explain this code from {name}{where}. {STYLE}\n\n```python\n{code.strip()}\n```")


def traceback_at(text, line_index=None):
    """The error text to explain. With a line index (0-based, in `text`) it is the traceback around that line;
    otherwise the last traceback. Returns '' if there is none."""
    lines = text.split("\n")
    marker = "Traceback (most recent call last)"
    starts = [i for i, ln in enumerate(lines) if marker in ln]
    if not starts:
        err = [i for i, ln in enumerate(lines) if re.match(r"^\w*(Error|Exception)\b.*:", ln)]
        if line_index is None and err:
            return lines[err[-1]]
        return ""
    if line_index is None:
        begin = starts[-1]
    else:
        before = [s for s in starts if s <= line_index]
        begin = before[-1] if before else starts[0]
    stop = len(lines)
    for i in range(begin + 1, len(lines)):
        if lines[i].startswith(("Finished with", "Stopped after", ">>>")):
            stop = i
            break
    return "\n".join(lines[begin:stop]).strip()


def failing_frame(trace):
    """(path, line) of the last frame in the user's own code, or None."""
    found = None
    for path, line in TRACE_FILE.findall(trace):
        if not any(part in path.lower() for part in SKIP_PARTS):
            found = (path, int(line))
    return found


def snippet(read, path, line, around=3):
    """A few numbered lines of source around `line`. `read(path)` returns the file's text or None."""
    text = read(path)
    if not text:
        return ""
    rows = text.splitlines()
    lo, hi = max(0, line - 1 - around), min(len(rows), line + around)
    return "\n".join(f"{n + 1:>4}: {rows[n]}" for n in range(lo, hi))


def error_prompt(trace, read=None):
    frame = failing_frame(trace)
    code = ""
    if frame and read:
        code = snippet(read, *frame)
    out = f"My program stopped with this error. {STYLE} Tell me what the error message means, which line caused " \
          f"it and the most likely fix.\n\n```\n{trace.strip()[-3500:]}\n```"
    if code:
        out += f"\n\nThe code near line {frame[1]} of {frame[0].split(chr(92))[-1].split('/')[-1]}:\n```python\n{code}\n```"
    return out


def problem_prompt(code_line, message, name="my program", line=None):
    return (f"My editor underlined a problem in {name}. {STYLE} What does this message mean and how do I fix it?\n\n"
            f"Message: {message}\n" + (f"Line {line}: " if line else "") + f"`{code_line.strip()}`")
