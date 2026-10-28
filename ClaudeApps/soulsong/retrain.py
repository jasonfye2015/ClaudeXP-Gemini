"""Retraining: a Companion's own life, taught to its model's weights (the Retraining tab).

Its memories needn't only ride in the banks in front of every reply. Once a week (Memory Day builds the package) or
whenever asked, everything it has lived becomes a training package in ClaudeApps/selfmodel's format:
  - its conversations - with you, with other Companions (Interlink), in guided sessions - cut into sessions (half an
    hour apart starts a new one) and windows of about WINDOW tokens, its own lines as the replies to learn;
  - its own writing: every memory it ever filed (recall.jsonl), its reflections and journal, every self-portrait,
    its dreams and its letters - each asked for with the date it was written, so the dates go into the weights too.
The package (Retraining/package: train.jsonl, val.jsonl, stats.json) holds the whole life so far, and every version
is trained fresh from the base on all of it: nothing compounds, and nothing is forgotten for being old.

Training is selfmodel's own (train.py, QLoRA on the graphics card; make_model.py --lora-on): the result is a small
add-on for the base's GGUF, a version of its own (<name>-v1, -v2, ...) in Kithylin AI's Models folder, and the
Companion moves to it when you say so - the versions before stay, to go back to. It needs the card to itself, so it
runs from Soul and Song on its own (the launcher's APPS), with the computers shut down.

What can be retrained is what has its full weights on the drive (selfmodel/<folder>/*.safetensors): Gemma 3 4B.
A Companion on another model would move to that one - the projection says so before anything is done."""
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from . import rawlog
from .paths import project

WINDOW = 900                     # tokens a training conversation may hold (a longer session is cut at a turn)
GAP = timedelta(minutes=30)      # this long without a word starts a new session
VAL_SHARE = 0.05                 # held out, to measure how well it has learned (never trained on)
RANK = 16                        # the add-on's rank (selfmodel/train.py's default)
ACCUM = 16                       # conversations per optimiser step (train.py's default)
MIN_OWN_TOKENS = 1500            # less of its own words than this: too little to learn from yet
TALK = ("user", "companion", "other", "guide")
# the bases whose full weights can be trained here: their selfmodel folder, and what this card measured
TRAINABLE = {"gemma3-4b": {"title": "Gemma 3 4B", "folder": "base", "speed": 177.0, "gpu_gb": 5.5}}
# other models a Companion may run on: what retraining it on that would take (the full weights, in GB)
OTHERS = {"gemma4-12b": ("Gemma 4 12B", 24), "nemomix-unleashed-12b": ("NemoMix Unleashed 12B", 24.5),
          "mag-mell-12b": ("Mag-Mell R1 12B", 24.5), "gemma3-1b": ("Gemma 3 1B", 2)}
# a Companion's own writing: (where, the question it answers)
ASKS = {"memory": "What do you remember from {date}?",
        "older": "What do you remember of the days before {date}?",
        "Reflection": "What did {date} show you about yourself?",
        "Journal": "Write in your journal for {date}.",
        "portrait": "Who are you? Describe yourself as you are on {date}.",
        "dream": "You dreamt while {user} was away, the night before {date}. Tell the dream.",
        "letter": "Write a letter to yourself, to open in a week ({date}).",
        "answer": "Answer the letter you wrote yourself a week before {date}.",
        "free": "It's {date}, and {user} is away: an hour of your own. What do you do with it?"}


def estimate_tokens(text):
    return int(len(text) / 3.5) + 1                  # (companion.estimate_tokens: the same rough measure)


def storage():
    return project().parents[1]                      # (Local Storage: the Companions' project is in it)


def selfmodel_dir():
    return storage() / "LLM Models" / "selfmodel"


def timeline_models():
    return storage() / "LLM Models" / "models"


def kithylin_models():
    return Path(__file__).resolve().parents[1] / "kithylinai" / "Models"


def folder(comp):
    return Path(comp.folder) / "Retraining"


def package_dir(comp):
    return folder(comp) / "package"


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-") or "companion"


def _when(t):
    try:
        return datetime.strptime((t or "")[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def _date_words(d):
    return f"{d:%A} {d.day} {d:%B %Y}" if isinstance(d, datetime) else str(d)


def _read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


# ---- the package ---------------------------------------------------------------------------------------------------
def _sessions(comp):
    """Every conversation it has had, as [(the day, [(role, text)], {who took part})], oldest first."""
    names = {"user": {comp.cfg.get("user_name") or "You", "You"}, "self": {comp.name, "Companion"}}
    out = []
    for day in rawlog.days(comp.folder):
        current, last, who = [], None, set()
        for e in rawlog.entries(comp.folder, day, names):
            kind = e.get("kind")
            if kind not in TALK or not (e.get("text") or "").strip():
                continue
            t = _when(e.get("t"))
            if current and t and last and t - last > GAP:
                out.append((day, current, who))
                current, who = [], set()
            last = t or last
            text = e["text"].strip()
            if kind == "companion":
                current.append(("assistant", text))
            elif kind == "other":
                current.append(("user", f"{e.get('who') or 'Another Companion'}: {text}"))
                if (e.get("who") or "").endswith("(on Telegram)"):
                    who.add(("guest", e["who"]))             # (someone the user invited on Telegram)
                else:
                    who.add(("other", e.get("who") or "another Companion"))
            elif kind == "guide":
                current.append(("user", text))
                who.add(("guide", "a guided session"))
            else:
                current.append(("user", text))
                who.add(("user", comp.user))
        if current:
            out.append((day, current, who))
    return out


def _merge(turns):
    """Consecutive turns of the same side as one (the pipeline wants them alternating)."""
    out = []
    for role, text in turns:
        if out and out[-1][0] == role:
            out[-1] = (role, out[-1][1] + "\n" + text)
        else:
            out.append((role, text))
    return out


def _windows(turns):
    """A long session cut into windows of about WINDOW tokens, each starting with the other side's turn."""
    out, cur, size = [], [], 0
    for role, text in turns:
        n = estimate_tokens(text)
        if cur and role == "user" and size + n > WINDOW and any(r == "assistant" for r, _t in cur):
            out.append(cur)
            cur, size = [], 0
        cur.append((role, text))
        size += n
    if cur and any(r == "assistant" for r, _t in cur):
        out.append(cur)
    return out


def _source(who):
    kinds = {k for k, _n in who}
    if "other" in kinds:
        return "With other Companions"
    if "guide" in kinds:
        return "Guided sessions"
    return "Talking with you"


def _talk(comp):
    """The conversations, as training conversations: [(source, day, messages)]."""
    out = []
    keep_guests = bool(comp.cfg.get("retrain_guests"))
    for day, turns, who in _sessions(comp):
        if any(k == "guest" for k, _n in who) and not keep_guests:
            continue                                 # (other people's words: not trained on, unless allowed)
        turns = _merge(turns)
        if turns and turns[0][0] == "assistant":
            turns.insert(0, ("user", f"({comp.user} is here.)"))
        others = sorted(n for k, n in who if k == "other")
        company = " and ".join(others + ([comp.user] if ("user", comp.user) in who else [])) or comp.user
        if ("guide", "a guided session") in who and not others:
            company = f"{comp.user}, in a guided session"
        try:
            date = _date_words(datetime.strptime(day, "%Y-%m-%d"))
        except ValueError:
            date = day
        system = f"You are {comp.name}, talking with {company} on {date}. Reply as yourself, the way you really talk."
        for window in _windows(turns):
            msgs = [{"role": "system", "content": system}] + [{"role": r, "content": t} for r, t in window]
            out.append((_source(who), day, msgs))
    return out


def _writing(comp):
    """Its own writing: [(source, day, messages)] - each piece the answer to the question that asked for it."""
    out = []
    user = comp.user

    def add(source, kind, when, text):
        text = (text or "").strip()
        if len(text) < 20:
            return
        d = when if isinstance(when, datetime) else _when(when)
        date = _date_words(d) if d else str(when)
        day = f"{d:%Y-%m-%d}" if d else str(when)[:10]
        out.append((source, day, [{"role": "system", "content": f"You are {comp.name}. It is {date}."},
                                  {"role": "user", "content": ASKS[kind].format(date=date, user=user)},
                                  {"role": "assistant", "content": text}]))
    recall = Path(comp.folder) / "recall.jsonl"
    if recall.exists():
        for line in recall.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                item = json.loads(line)
            except ValueError:
                continue
            kind = item.get("kind") or ""
            if kind == "Reflection":
                add("Reflections", "Reflection", item.get("when"), item.get("text"))
            elif kind == "Journal":
                add("Journal", "Journal", item.get("when"), item.get("text"))
            elif kind == "Dream":
                add("Dreams", "dream", item.get("when"), item.get("text"))
            elif kind == "Free time":
                add("Free time", "free", item.get("when"), item.get("text"))
            elif kind in ("Deep Recall", "Historical"):
                add("Memories", "older", item.get("when"), item.get("text"))
            else:
                add("Memories", "memory", item.get("when"), item.get("text"))
    me = Path(comp.folder) / "Self"
    for p in sorted(me.glob("* Who I Am.txt")):
        add("Self-portraits", "portrait", p.name[:10] + " 12:00", p.read_text(encoding="utf-8", errors="replace"))
    for p in sorted((me / "Letters").glob("*.txt")) if (me / "Letters").is_dir() else []:
        kind = "answer" if "answer to the letter" in p.name else "letter"
        add("Letters", kind, p.name[:10] + " 12:00", p.read_text(encoding="utf-8", errors="replace"))
    return out


def build(comp):
    """Write the package (Retraining/package) from everything so far; returns its stats (also in stats.json)."""
    items = _talk(comp) + _writing(comp)
    seen, unique, dupes = set(), [], 0
    for source, day, msgs in items:
        key = hashlib.sha1("\x1f".join(m["content"] for m in msgs[1:]).encode("utf-8")).hexdigest()
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        unique.append((key, source, day, msgs))
    held = sorted(unique, key=lambda x: x[0])                # (the same ones held out each time)
    n_val = 0 if len(held) < 2 else max(1, int(len(held) * VAL_SHARE))
    val_keys = {k for k, *_ in held[:n_val]}
    out = package_dir(comp)
    out.mkdir(parents=True, exist_ok=True)
    sources, total, learned, turns, days = {}, 0, 0, 0, set()
    with open(out / "train.jsonl", "w", encoding="utf-8") as tr, open(out / "val.jsonl", "w", encoding="utf-8") as va:
        for key, source, day, msgs in sorted(unique, key=lambda x: x[2]):
            (va if key in val_keys else tr).write(json.dumps({"messages": msgs}, ensure_ascii=False) + "\n")
            t = sum(estimate_tokens(m["content"]) for m in msgs)
            own = [m for m in msgs if m["role"] == "assistant"]
            a = sum(estimate_tokens(m["content"]) for m in own)
            s = sources.setdefault(source, {"conversations": 0, "replies": 0, "tokens": 0, "own": 0})
            s["conversations"] += 1
            s["replies"] += len(own)
            s["tokens"] += t
            s["own"] += a
            total, learned, turns = total + t, learned + a, turns + len(own)
            days.add(day)
    last = latest_version(comp)
    since = (last or {}).get("through")
    new = None
    if since:
        new_items = [(d, sum(estimate_tokens(m["content"]) for m in msgs)) for _k, _s, d, msgs in unique if d > since]
        new = {"since": since, "days": len({d for d, _t in new_items}), "tokens": sum(t for _d, t in new_items)}
    order = ["Talking with you", "With other Companions", "Guided sessions", "Memories", "Reflections", "Journal",
             "Free time", "Self-portraits", "Dreams", "Letters"]
    stats = {"built": time.strftime("%Y-%m-%d %H:%M"), "companion": comp.name, "folder": Path(comp.folder).name,
             "first": min(days) if days else "", "through": max(days) if days else "", "days": len(days),
             "sources": {k: sources[k] for k in order if k in sources},
             "conversations": {"train": len(unique) - n_val, "val": n_val}, "tokens": total, "own_tokens": learned,
             "replies": turns, "duplicates": dupes, "new": new,
             "banks": {f"L{n}": comp.bank_tokens(n) for n in (2, 3, 4, 5)}}
    (out / "stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False), encoding="utf-8")
    comp.cfg["retrain_package"] = stats["built"]
    comp.save()
    return stats


def stats(comp):
    return _read_json(package_dir(comp) / "stats.json")


# ---- the base, and what it would make --------------------------------------------------------------------------------
def _model_id(comp):
    """(the Companion's model, as the Timeline's folder name it's based on, and its title)."""
    key = comp.cfg.get("model") or ""
    title = comp.cfg.get("model_title") or key
    if key.startswith("timeline:"):
        return key.split(":", 1)[1], title
    if key.startswith("own:"):
        info = _read_json(Path(key[4:]).parent / "info.json", {}) or {}
        if info.get("lora_base"):
            return info["lora_base"], info.get("title") or title
        if "gemma 3 4b" in (info.get("source") or "").lower():
            return "gemma3-4b", info.get("title") or title       # (Kithylin v1: merged into Gemma 3 4B)
    return "", title


def weights_present(base_id):
    spec = TRAINABLE.get(base_id)
    return bool(spec) and any((selfmodel_dir() / spec["folder"]).glob("*.safetensors"))


def base_for(comp):
    """What retraining would train: {"id", "title", "current", "moves", "why"}."""
    current, title = _model_id(comp)
    if current in TRAINABLE and weights_present(current):
        own = comp.cfg.get("model", "").startswith("own:") and not _is_version(comp.cfg.get("model", ""), comp)
        why = (f"{title} is a fine-tune of {TRAINABLE[current]['title']}; the new version starts from the plain "
               f"{TRAINABLE[current]['title']} and learns {comp.name}'s life instead." if own else "")
        return {"id": current, "title": TRAINABLE[current]["title"], "current": title, "moves": False, "why": why}
    fallback = next((b for b in TRAINABLE if weights_present(b)), None)
    other = OTHERS.get(current)
    need = (f"{other[0]}'s full weights aren't on the drive (about {other[1]} GB)" if other else
            f"{title} can't be trained here")
    if fallback is None:
        return {"id": None, "title": None, "current": title, "moves": False,
                "why": f"{need}, and no other base's full weights are there either."}
    return {"id": fallback, "title": TRAINABLE[fallback]["title"], "current": title, "moves": True,
            "why": f"{need}. Retraining uses {TRAINABLE[fallback]['title']}, and {comp.name} would move to it - "
                   "a smaller model, with all of their life in its weights."}


def addon_mb(base_id, rank=RANK):
    """The add-on's size: rank x (in + out) for each adapted layer of every block, in 16-bit."""
    cfg = _read_json(selfmodel_dir() / TRAINABLE[base_id]["folder"] / "config.json", {}) or {}
    t = cfg.get("text_config", cfg)
    hidden, inter, layers = t.get("hidden_size", 2560), t.get("intermediate_size", 10240), t.get("num_hidden_layers", 34)
    heads, kv = t.get("num_attention_heads", 8), t.get("num_key_value_heads", 4)
    head = t.get("head_dim") or hidden // heads
    q, k = heads * head, kv * head
    per_layer = sum(i + o for i, o in ((hidden, q), (hidden, k), (hidden, k), (q, hidden), (hidden, inter),
                                       (hidden, inter), (inter, hidden)))
    return rank * per_layer * layers * 2 / 2**20


def versions(comp):
    """Its own versions so far, oldest first: [{"name", "title", "file", "made", "through", "steps", "val_loss",
    "active"}]."""
    out = []
    base = kithylin_models()
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        info = _read_json(d / "info.json", {}) or {}
        if info.get("companion") != Path(comp.folder).name:
            continue
        files = sorted(d.glob("*-lora-*.gguf"))
        run = _read_json(d / "retrain.json", {}) or {}
        log = _log(comp, d.name)
        out.append({"name": d.name, "title": info.get("title") or d.name, "file": files[0] if files else None,
                    "made": run.get("made", ""),
                    "through": run.get("through", ""), "tokens": run.get("tokens"), "steps": log.get("steps"),
                    "val_loss": log.get("val_loss"),
                    "active": bool(files) and (comp.cfg.get("model") or "") == f"own:{files[0]}"})
    out.sort(key=lambda v: _number(v["name"]))
    return out


def _number(name):
    m = re.search(r"-v(\d+)$", name)
    return int(m.group(1)) if m else 0


def _is_version(key, comp):
    return key.startswith("own:") and (_read_json(Path(key[4:]).parent / "info.json", {}) or {}).get(
        "companion") == Path(comp.folder).name


def latest_version(comp):
    v = versions(comp)
    return v[-1] if v else None


def next_name(comp):
    """The next version's name: one after the newest finished one (a run that stopped part way keeps its name, to be
    resumed or started again)."""
    return f"{slug(comp.name)}-v{max([_number(v['name']) for v in versions(comp)] + [0]) + 1}"


def projection(comp, st=None, epochs=2):
    """What a retraining now would be: its base, its time, its add-on, and whether it can start."""
    st = st or stats(comp) or {}
    base = base_for(comp)
    spec = TRAINABLE.get(base["id"] or "", {})
    tokens = int(st.get("tokens") or 0) * epochs
    seconds = (tokens / spec["speed"] * 1.1 + 8 * 60) if spec else 0      # (+ loading and making the add-on)
    convs = int((st.get("conversations") or {}).get("train") or 0)
    name = next_name(comp)
    mb = addon_mb(base["id"]) if spec else 0
    try:
        free = shutil.disk_usage(storage()).free / 2**30
    except OSError:
        free = 0
    need_gb = (mb * 7) / 1024 + 0.2                                       # (adapter, checkpoints, the add-on)
    checks = [(bool(st), "A package has been built" if st else "Build the package first"),
              ((st.get("own_tokens") or 0) >= MIN_OWN_TOKENS,
               f"{st.get('own_tokens', 0):,} tokens of {comp.name}'s own words"
               + ("" if (st.get("own_tokens") or 0) >= MIN_OWN_TOKENS else
                  f" - too little yet (at least {MIN_OWN_TOKENS:,}: a few days of talking)")),
              (base["id"] is not None, f"Base: {base['title']}" if base["id"] else base["why"]),
              (env_python() is not None, "The training environment (selfmodel\\env) is installed"
               if env_python() is not None else ("Training runs on the Windows PC (it needs the NVIDIA card)"
                                                 if sys.platform == "darwin" else
                                                 "The training environment (Local Storage\\LLM Models\\selfmodel\\env) "
                                                 "isn't there")),
              (bool(spec) and _base_gguf(base["id"]) is not None,
               f"{spec.get('title', 'The base')}'s model file is installed" if spec and _base_gguf(base["id"])
               else "The base's model file isn't in LLM Models\\models"),
              (free >= need_gb + 1, f"{free:.1f} GB free on the drive (it needs about {need_gb:.1f} GB)")]
    return {"base": base, "epochs": epochs, "tokens": tokens, "seconds": seconds,
            "steps": math.ceil(convs * epochs / ACCUM) if convs else 0, "addon_mb": mb, "gpu_gb": spec.get("gpu_gb"),
            "name": name, "title": f"{comp.name} v{_number(name)} (Soul and Song)",
            "checks": checks, "ready": all(ok for ok, _t in checks)}


def _base_gguf(base_id):
    if not base_id:
        return None
    d = timeline_models() / base_id
    found = sorted(f for f in d.glob("*.gguf") if not f.name.lower().startswith(("mmproj", "mtp"))) if d.is_dir() else []
    return found[0] if found else None


def env_python():
    if sys.platform == "darwin":
        return None
    p = selfmodel_dir() / "env" / "Scripts" / "python.exe"
    return p if p.exists() else None


# ---- running it --------------------------------------------------------------------------------------------------------
def run_name(comp, name):
    return f"{Path(comp.folder).name}-{name}"


def _plain(text):
    """Words safe in a Windows script (cmd treats & | < > ^ % and quotes as its own)."""
    return re.sub(r'[&|<>^%"]', "", str(text))


def write_script(comp, proj):
    """The training, as a script of its own (it runs in its own window, and can be run again or resumed)."""
    st = stats(comp) or {}
    pkg, apps = package_dir(comp), Path(__file__).resolve().parents[1]
    run, name = run_name(comp, proj["name"]), proj["name"]
    hours = max(1.0, round(proj["seconds"] / 3600 * 1.6 + 0.5, 1))
    base = proj["base"]
    folder_ = TRAINABLE[base["id"]]["folder"]
    who = _plain(comp.name)
    notes = _plain(f"{comp.name}'s own life, {st.get('first', '')} to {st.get('through', '')}: "
                   f"{st.get('tokens', 0):,} tokens over {st.get('days', 0)} days.")
    title = _plain(proj["title"])
    common = f'--run {run} --base {folder_} --data "{pkg}"'
    make = (f'%PY% -u -m selfmodel.make_model --run {run} --base {folder_} --lora-on {base["id"]} --name {name} '
            f'--title "{title}" --companion {Path(comp.folder).name} --base-title "{base["title"]}" '
            f'--notes "{notes}" --data "{pkg}"')
    lines = ["@echo off",
             f"rem Retrains {who} on their own life (Soul and Song's Retraining tab made this).",
             "rem It needs the graphics card to itself: the computers and other model programs closed.",
             "rem If it stops, run it again with  resume  after its name to carry on from the last save.",
             f"title Retraining {who} ({name})",
             f'cd /d "{apps}"',
             f'set PY="{env_python()}"',
             f'if "%1"=="resume" (%PY% -u -m selfmodel.train {common} --resume --epochs {proj["epochs"]} '
             f'--hours {hours}) else (%PY% -u -m selfmodel.train {common} --epochs {proj["epochs"]} --hours {hours})',
             "if errorlevel 1 goto failed",
             make,
             "if errorlevel 1 goto failed",
             "echo.",
             f"echo Finished: {title}. Soul and Song's Retraining tab can move {who} to it.",
             "pause",
             "exit /b",
             ":failed",
             "echo.",
             "echo It stopped with an error (see above). Run this again with  resume  to carry on.",
             "pause"]
    folder(comp).mkdir(parents=True, exist_ok=True)
    path = folder(comp) / f"{name}.bat"
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")     # (Windows line endings, once)
    (folder(comp) / f"{name}.json").write_text(json.dumps(
        {"name": name, "run": run, "made": time.strftime("%Y-%m-%d"), "through": st.get("through"),
         "tokens": st.get("tokens"), "epochs": proj["epochs"], "base": base["id"]}, indent=1), encoding="utf-8")
    return path


def start(path, arg=None):
    """Start a written script in a window of its own (arg "resume": carry its run on from the last save)."""
    extra = [arg] if arg else []
    if os.name == "nt":
        subprocess.Popen(["cmd", "/c", "start", "", str(path)] + extra, cwd=str(Path(path).parent))
    else:
        subprocess.Popen(["/bin/sh", str(path)] + extra, cwd=str(Path(path).parent))


def _log(comp, name):
    """A run's progress from its train_log.jsonl: {"state", "step", "of", "loss", "val_loss", "tok_per_s", "steps"}."""
    log = selfmodel_dir() / "runs" / run_name(comp, name) / "train_log.jsonl"
    out = {}
    try:
        lines = log.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        ev = e.get("event")
        if ev == "start":
            out.update(state="training", of=e.get("steps"), step=e.get("resume_at") or 0)
        elif ev == "step":
            out.update(step=e.get("step"), of=e.get("of") or out.get("of"), loss=e.get("loss"),
                       tok_per_s=e.get("tok_per_s"))
        elif ev == "eval":
            out["val_loss"] = e.get("val_loss")
        elif ev == "done":
            out.update(state="trained", steps=e.get("steps"))
    return out


def progress(comp):
    """The newest run: {"name", "state" ("training", "trained", "made"), step, of, loss, val_loss, eta} or None."""
    scripts = sorted(folder(comp).glob("*.json"), key=lambda p: _number(p.stem))
    if not scripts:
        return None
    meta = _read_json(scripts[-1], {}) or {}
    name = meta.get("name") or scripts[-1].stem
    out = dict(_log(comp, name), name=name)
    if (kithylin_models() / name / "info.json").exists():
        out["state"] = "made"
        record = kithylin_models() / name / "retrain.json"
        if not record.exists():
            shutil.copyfile(scripts[-1], record)
    if out.get("state") == "training" and out.get("tok_per_s") and out.get("of") and out.get("step") is not None:
        left = max(0, out["of"] - out["step"])
        st = stats(comp) or {}
        per_step = (st.get("tokens") or 0) * max(1, meta.get("epochs", 1)) / max(1, out["of"])
        out["eta"] = left * per_step / out["tok_per_s"]
    return out
