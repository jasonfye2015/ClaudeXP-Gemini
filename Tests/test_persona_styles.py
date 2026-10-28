"""Contact Persona Styles: the frozen V1.0 and V1.1 put their old prompting code back over today's code at every start.
That breaks quietly when today's code calls one of those old functions in a new way - on 26 October 2026 every AIM
reply failed for hours because the code passed clean_reply four arguments and V1.0's takes two. These check that each
frozen function still takes what today's code gives it, and that each style loads cleanly (in a process of its own,
on a scratch data folder) with the buddies' replies still tidied the way they should be."""
import ast
import inspect
import json
import os
import subprocess
import sys
import textwrap

import support

sys.path.insert(0, str(support.XP))
STYLES = support.TIMELINE / "Persona Styles"
support.needs(STYLES / "V1.0" / "prompting.json", "the frozen Persona Styles")
# a frozen function that takes different arguments from today's, and how today's code copes with it
HANDLED = {"claudeaim.llm.clean_reply": "llm.tidy_reply calls it the way the loaded one takes it"}


def _setup():
    support.qapp()
    import claudexp.paths as P
    P.DATA = support.scratch("xp data")
    from claudexp import persona_style as S
    S._ready()
    return S


def _params(fn=None, source=None):
    if source is not None:
        node = next(n for n in ast.parse(textwrap.dedent(source)).body if isinstance(n, ast.FunctionDef))
        a = node.args
        return ([x.arg for x in a.posonlyargs + a.args], [x.arg for x in a.kwonlyargs], bool(a.vararg),
                bool(a.kwarg))
    fn = fn.__func__ if isinstance(fn, (staticmethod, classmethod)) else fn
    ps = inspect.signature(fn).parameters.values()
    return ([p.name for p in ps if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)],
            [p.name for p in ps if p.kind == p.KEYWORD_ONLY], any(p.kind == p.VAR_POSITIONAL for p in ps),
            any(p.kind == p.VAR_KEYWORD for p in ps))


def test_frozen_functions_take_what_the_code_gives():
    """Every frozen function takes the same arguments as today's (or how the difference is handled is known)"""
    S = _setup()
    problems = []
    for style in [s for s in S.available() if s["id"] != S.DEV]:
        data = json.loads((S.folder(style["id"]) / "prompting.json").read_text(encoding="utf-8"))
        for modname, entry in data.items():
            mod = S._import(modname)
            for name, v in entry.items():
                if v["kind"] != "code":
                    continue
                parts = name.split(".")
                owner = S._get(mod, ".".join(parts[:-1])) if len(parts) > 1 else mod
                live = owner.__dict__.get(parts[-1])
                key = f"{modname}.{name}"
                if live is None:
                    problems.append(f"V{style['id']} {key}: no longer in the code")
                elif _params(source=v["value"]) != _params(live) and key not in HANDLED:
                    problems.append(f"V{style['id']} {key}: frozen {_params(source=v['value'])[0]}, "
                                    f"today {_params(live)[0]}")
    assert not problems, "\n".join(problems)


def test_clean_reply_called_the_frozen_way():
    """Nothing but llm.tidy_reply calls clean_reply with more than the frozen styles' two arguments"""
    calls = []
    for folder in (support.XP / "claudexp", support.XP / "Program Files" / "ClaudeAIM" / "claudeaim",
                   support.W7 / "claude7", support.W11 / "claude11"):
        for path in folder.rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == \
                        "clean_reply" and len(node.args) + len(node.keywords) > 2:
                    if not (path.name == "llm.py" and "claudeaim" in path.parts):
                        calls.append(f"{path.relative_to(support.TIMELINE)}:{node.lineno}")
    assert not calls, "clean_reply called with more than two arguments (use tidy_reply): " + ", ".join(calls)


def _apply(sid):
    env = dict(os.environ, TIMELINE_TEST_TMP=str(support.scratch(f"style {sid}")))
    env.pop("TIMELINE_TEST_RUNNER", None)
    done = subprocess.run([sys.executable, __file__, "--apply", sid], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, timeout=120)
    out = done.stdout + done.stderr
    assert done.returncode == 0 and "APPLIED" in out, out[-1500:]
    noise = [ln for ln in out.splitlines() if ln.startswith("Persona style:")]
    assert not noise, "\n".join(noise)
    return out


def test_styles_load():
    """Each style loads over today's code without a complaint, and the buddies' replies are still tidied"""
    S = _setup()
    for style in S.available():
        _apply(style["id"])


def _check_in_this_process(sid):
    """(run as: test_persona_styles.py --apply <id>) Load the style, then tidy some replies the ways the code does."""
    S = _setup()
    replaced = S.apply(sid) if sid != S.DEV else []
    from claudeaim import llm
    tidy = llm.tidy_reply
    assert tidy("Brass: hey there!", "Brass", "Kithylin", "hi") == "hey there!", tidy("Brass: hey there!", "Brass")
    assert "Kithylin:" not in tidy("Kithylin: so anyway\nhey! how was the con?", "Brass", "Kithylin", "so anyway")
    assert tidy("so how are you", "Brass", "Kithylin", "so how are you") == "", "an echo wasn't refused"
    assert llm.clean_reply("Brass: hello", "Brass") == "hello"                 # (the two-argument callers)
    print("APPLIED", len(replaced), "replaced", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--apply"]:
        _check_in_this_process(sys.argv[2])
        sys.stdout.flush()
        os._exit(0)
    support.main(globals())
