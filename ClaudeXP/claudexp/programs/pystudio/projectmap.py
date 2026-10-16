"""Project awareness for the AI Helper: a compact map of the other files in the project folder (classes, functions,
assets), plus the full text of the few files most relevant to a question. Pure Python, no Qt."""
import ast
import os
import re

SKIP_DIRS = {".history", "__pycache__", "Built Programs", "build", "dist", ".git", "venv", ".venv", "Assets"}
MAX_FILES = 60
MAX_FILE_BYTES = 200_000
MAP_LIMIT = 3500
RELEVANT_LIMIT = 7000
ASSET_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".wav", ".ogg", ".mp3", ".csv", ".json", ".tmx", ".ttf"}


def project_root(current_path, default):
    """The folder of the file being edited, or the default programs folder for an unsaved file."""
    if current_path and os.path.isfile(current_path):
        return os.path.dirname(current_path)
    return str(default)


def python_files(root):
    found = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(files):
            if name.lower().endswith(".py"):
                path = os.path.join(base, name)
                try:
                    if os.path.getsize(path) <= MAX_FILE_BYTES:
                        found.append(path)
                except OSError:
                    pass
        if len(found) >= MAX_FILES:
            break
    return found[:MAX_FILES]


def _signature(node):
    args = [a.arg for a in node.args.posonlyargs + node.args.args]
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    args += [a.arg for a in node.args.kwonlyargs]
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return f"{node.name}({', '.join(args)})"


def outline(text):
    """(classes, functions, constants, imports) found at the top level of the source; empty on a syntax error."""
    classes, functions, constants, imports = [], [], [], []
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return classes, functions, constants, imports
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [_signature(n) for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append((node.name, methods))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_signature(node))
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    constants.append(t.id)
        elif isinstance(node, ast.Import):
            imports += [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            imports.append(node.module.split(".")[0])
    return classes, functions, constants, imports


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def describe(root, path, text):
    classes, functions, constants, _ = outline(text)
    rel = os.path.relpath(path, root).replace("\\", "/")
    parts = []
    for name, methods in classes:
        shown = ", ".join(m.split("(")[0] for m in methods[:8])
        parts.append(f"class {name}" + (f" [{shown}{', ...' if len(methods) > 8 else ''}]" if shown else ""))
    parts += [f"def {f}" for f in functions[:12]]
    if constants:
        parts.append("constants " + ", ".join(constants[:8]))
    return f"- {rel}: " + ("; ".join(parts) if parts else "(no top-level definitions)")


def asset_summary(root):
    folder = os.path.join(root, "Assets")
    if not os.path.isdir(folder):
        folder = root
    counts, samples = {}, []
    for base, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS - {"Assets"} and not d.startswith(".")]
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in ASSET_EXT:
                counts[ext] = counts.get(ext, 0) + 1
                if len(samples) < 12 and base != folder:
                    samples.append(os.path.relpath(os.path.join(base, name), root).replace("\\", "/"))
    if not counts:
        return ""
    kinds = ", ".join(f"{n} {ext}" for ext, n in sorted(counts.items()))
    return f"Asset files near the project: {kinds}." + (" Examples: " + ", ".join(samples[:8]) if samples else "")


def local_imports(text, names):
    """Which project module names (file stems) a file imports."""
    return [m for m in outline(text)[3] if m in names]


def relevance(question, stem, text):
    """Score how likely a file is needed to answer the question: file name, class/function names and the
    word overlap with the question."""
    words = {w.lower() for w in re.findall(r"[A-Za-z_]{3,}", question)}
    if not words:
        return 0
    score = 0
    if stem.lower() in words:
        score += 10
    classes, functions, constants, _ = outline(text)
    names = [c[0] for c in classes] + [f.split("(")[0] for f in functions]
    for n in names:
        parts = {p.lower() for p in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", n)} | {n.lower()}
        score += 3 * len(parts & words)
    return score


def build_context(root, current_path, question, limit_map=MAP_LIMIT, limit_files=RELEVANT_LIMIT, skip=()):
    """Text for the prompt: a map of the other files plus the full text of the most relevant ones.
    `skip` holds paths already sent another way. Returns "" when the project has no other Python files."""
    files = python_files(root)
    current = os.path.normcase(os.path.abspath(current_path)) if current_path else None
    skipped = {os.path.normcase(os.path.abspath(p)) for p in skip}
    others = [p for p in files if os.path.normcase(os.path.abspath(p)) != current]
    if not others:
        return ""
    texts = {p: read(p) for p in others}
    stems = {os.path.splitext(os.path.basename(p))[0] for p in others}
    lines = [describe(root, p, texts[p]) for p in others]
    block, used = [], 0
    for line in lines:
        if used + len(line) > limit_map:
            block.append(f"- ... and {len(lines) - len(block)} more files")
            break
        block.append(line)
        used += len(line) + 1
    out = ["Other files in this project (name: what they define):\n" + "\n".join(block)]
    assets = asset_summary(root)
    if assets:
        out.append(assets)

    # a file the current one imports, or that the question mentions, is worth sending in full
    imported = set(local_imports(read(current_path), stems)) if current_path else set()
    scored = []
    for p in others:
        if os.path.normcase(os.path.abspath(p)) in skipped:
            continue
        stem = os.path.splitext(os.path.basename(p))[0]
        s = relevance(question, stem, texts[p]) + (6 if stem in imported else 0)
        if s > 0:
            scored.append((s, p))
    scored.sort(key=lambda t: (-t[0], t[1]))
    budget = limit_files
    for _score, p in scored[:4]:
        if budget < 400:
            break
        text = texts[p][:budget]
        budget -= len(text)
        rel = os.path.relpath(p, root).replace("\\", "/")
        cut = "\n# ... (cut)\n" if len(text) < len(texts[p]) else ""
        out.append(f"Project file {rel} (likely relevant):\n```python\n{text}{cut}\n```")
    return "\n\n".join(out)
