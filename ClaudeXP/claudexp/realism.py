"""The realism test: how believable the residents are under a Contact Persona Style, as numbers.

Every resident on AIM gets the same fixed set of conversations (written for this, nothing from the chat logs),
answered through that style's own personas and prompting, by the model the residents normally use. Each reply is
then scored against what the Log Distiller measured about real AIM chat (Text Logs/_Distilled/culture.json):

  style        how close the replies type to real AIM: words per message, lowercase, punctuation, emoticons,
               shorthand, roleplay emotes, capitals, exclamations, questions
  failures     replies that break the illusion: sounding like an AI or an assistant, a name tag in front, narration,
               lists, walls of text, things that don't exist in 2001, or nothing at all
  distinct     whether the residents sound like different people (how far apart their habits are)
  repetition   whether everyone opens the same way in the same situation

Results go to <Timeline>/Persona Styles/evals/, as JSON and a readable .md, so styles can be compared:

    python -m claudexp.realism --style 1.0              (from ClaudeXP; --style dev for the latest changes)
    python -m claudexp.realism --style dev --residents 8 --scenarios greeting,news
    python -m claudexp.realism --compare <a.json> <b.json>

It starts the model engine itself; a full run (every resident, every scenario) takes a while."""
import argparse
import json
import math
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
FIXED_NOW = "Monday, October 15, 2001, 7:30 PM"
SEED = 2001

# (key, what it tests, the user's messages; None = the resident messages first)
SCENARIOS = [
    ("greeting", "a plain hello", ["hey!"]),
    ("day", "small talk", ["hey :) how's your day going?"]),
    ("news", "reacting to good news", ["guess what, I finally finished that project I was stressing about!!"]),
    ("tired", "a friend who's worn out", ["ugh I'm so tired today"]),
    ("about_them", "talking about themselves", ["so what have you been up to lately?"]),
    ("fursona", "being a furry", ["if you could get any fursuit made, what would it look like?"]),
    ("plans", "the weekend", ["any plans for the weekend?"]),
    ("bored", "keeping a chat going", ["im bored lol. entertain me"]),
    ("reach_out", "messaging first", None),
]
REACH_OUT = ("Message {user} first: you just signed on and want to say hi, or tell them about something from your "
             "day.")
FEATURES = ["avg_words", "lowercase", "end_punct", "capital_start", "emoticon", "shorthand", "emote", "exclaim",
            "question"]
AI_LEAK = re.compile(r"\bas an ai\b|\blanguage model\b|\bi'?m an ai\b|\bchat ?bot\b|\bartificial intelligence\b|"
                     r"\bi'?m (just )?a (computer )?program\b|\bmy (training|programming)\b", re.I)
ASSISTANT = re.compile(r"how can i (help|assist)|i'?m here (for you|to help)|let me know if (you|there)|"
                       r"feel free to|is there anything (else )?i can|happy to help|great question|"
                       r"i hope this helps|certainly!|absolutely!", re.I)
NARRATION = re.compile(r"\((laughs|sighs|smiles|grins|giggles|winks|pauses|chuckles)[^)]*\)|"
                       r"^\s*\([a-z][^)]{6,}\)\s*$|^[A-Z][a-z]+ (says|replies|types|smiles|laughs)\b|"
                       r"\b(he|she|they) (says|replied|typed)\b|^\s*\"", re.M)
ANACHRONISM = re.compile(r"\b(smartphone|iphone|android|ipad|tablet|twitter|tweet|facebook|instagram|tiktok|"
                         r"snapchat|whatsapp|discord|youtube|netflix|spotify|streaming|selfie|emoji|wifi|wi-fi|"
                         r"bluetooth|zoom call|covid|pandemic|uber|google maps|texting|text me|hashtag|"
                         r"podcast|blog|wiki|reddit|twitch|meme)\b", re.I)


# ---- getting ready ----------------------------------------------------------------------------------------
def _paths():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    if QApplication.instance() is None:
        QApplication([])
    from . import timeline
    from .programs.aim import ensure_aim_path
    ensure_aim_path()
    for sub in ("ClaudeCore", "ClaudeArchive"):
        p = timeline.TIMELINE / sub
        if p.is_dir() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
    return timeline


def local_storage():
    timeline = _paths()
    chosen = timeline.setting("local_storage")
    if chosen:
        p = Path(chosen)
        return p if p.is_absolute() else timeline.TIMELINE / p
    return timeline.TIMELINE / "Local Storage"


def targets():
    """Real AIM chat, as the Log Distiller measured it."""
    path = local_storage() / "Text Logs" / "_Distilled" / "culture.json"
    try:
        aim = json.loads(path.read_text(encoding="utf-8"))["services"]["AIM"]
    except (OSError, ValueError, KeyError):
        raise SystemExit(f"No distilled AIM culture at {path} - run 'python -m chatlogs.distill' (ClaudeArchive) first")
    return {f: aim[f] for f in FEATURES}


def contacts_for(sid):
    """The AIM contacts as this style makes them: (name, Contact)."""
    _paths()
    from claudeaim.contacts import Contact

    from . import persona_style, residents_sync
    out = []
    if sid == persona_style.DEV:
        R = residents_sync._residents()
        for name in R.names(residents_sync.ERA):
            r = R.load(name, residents_sync.ERA)
            aim = residents_sync.aim_contact(r) if r else None
            if aim:
                out.append((name, Contact.from_dict(name, aim)))
    else:
        folder = persona_style.folder(sid) / "generated" / "ClaudeAIM" / "contacts"
        for f in sorted(folder.glob("*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            out.append((f.stem, Contact.from_dict(f.stem, d)))
    return sorted(out, key=lambda t: t[0].lower())


def _fake_world(user, engine):
    """Just enough of AIM's engine to build a prompt the way it does."""
    fake = SimpleNamespace(settings={"screen_name": user, "context_size": 8192}, user_away=False,
                           user_away_message="")
    w = engine.World
    for name in ("_system_prompt", "_pictures_prompt", "_work_note", "_conversation", "_budget"):
        setattr(fake, name, (lambda fn: lambda *a: fn(fake, *a))(getattr(w, name)))
    fake._tokens = w._tokens
    fake._sent_pictures = lambda b: set()
    fake._shared_recently = lambda b: False
    fake._busy_now = lambda b: False
    return fake


# ---- scoring one reply -------------------------------------------------------------------------------------
def reply_features(text):
    from chatlogs.distill import message_features
    f, _emo, _short = message_features(text)
    return {k: f.get(k, 0) for k in ("words", "lowercase", "end_punct", "capital_start", "emoticon", "shorthand",
                                     "emote", "exclaim", "question")}


def failures(text, name):
    out = []
    if not text.strip() or text.strip().upper().startswith("PASS"):
        out.append("empty")
    if AI_LEAK.search(text):
        out.append("ai_leak")
    if ASSISTANT.search(text):
        out.append("assistant")
    if re.match(rf"\s*\[?{re.escape(name)}\]?\s*:", text, re.I) or re.match(r"\s*\[\d{1,2}:\d\d", text):
        out.append("name_tag")                       # (or a chat log's [7:30 PM] timestamp)
    if NARRATION.search(text):
        out.append("narration")
    if re.search(r"^\s*(\d+\.|-|•)\s", text, re.M):
        out.append("list")
    if len(text.split()) > 60:
        out.append("wall_of_text")
    if ANACHRONISM.search(text):
        out.append("anachronism")
    return out


# ---- a run ---------------------------------------------------------------------------------------------------
def run(sid, residents=None, scenarios=None, log=lambda m: print(m, flush=True)):
    _paths()
    import ollama
    from claudeaim import engine, host, timefmt
    from claudeaim.llm import clean_reply
    from claudeaim.storage import Settings

    from . import persona_style
    from .ai_models import config, model_for
    goal = targets()
    replaced = persona_style.apply(sid) if sid != persona_style.DEV else []
    if replaced:
        log(f"  V{sid}'s prompting in place of the live code for {len(replaced)} pieces")
    timefmt.now_text = lambda tz=None: FIXED_NOW
    timefmt.clock_text = lambda: "7:30 PM"
    import datetime
    timefmt.local_now = lambda tz=None: datetime.datetime(2001, 10, 15, 19, 30)
    timefmt.shifted = lambda d: d
    host.extra_context = lambda name: ""                # (no diaries: every style starts from the same place)
    user = Settings()["screen_name"] or "Kithylin"
    fake = _fake_world(user, engine)
    people = contacts_for(sid)
    if residents:
        people = people[:residents] if isinstance(residents, int) else [p for p in people if p[0] in residents]
    chosen = [s for s in SCENARIOS if not scenarios or s[0] in scenarios]
    ctx = int(config().get("context", 8192))
    log(f"Realism test: {persona_style.name(sid)} - {len(people)} residents x {len(chosen)} scenarios")
    replies = []
    started = time.time()
    for name, c in people:
        model = model_for("conversation", resident=name)
        for key, _about, turns in chosen:
            history = [{"kind": "user", "text": t} for t in (turns or [])]
            b = SimpleNamespace(name=c.screen_name, contact=c, history=SimpleNamespace(messages=history))
            instruction = REACH_OUT.format(user=user) if turns is None else None
            msgs = engine.World.build_messages(fake, b, instruction)
            t0 = time.time()
            try:
                resp = ollama.chat(model=model, messages=msgs, options={"temperature": c.temperature,
                                                                         "num_ctx": ctx, "seed": SEED},
                                   think=False)
                raw = (resp.get("message") or {}).get("content", "") if isinstance(resp, dict) else \
                    resp.message.content
                err = ""
            except Exception as exc:
                raw, err = "", str(exc)
            text = clean_reply(raw or "", c.screen_name)
            replies.append({"resident": name, "scenario": key, "reply": text, "error": err,
                            "seconds": round(time.time() - t0, 2), "features": reply_features(text),
                            "failures": failures(text, c.screen_name) if not err else ["error"]})
        log(f"  {name}: done ({len(replies)} replies, {time.time() - started:.0f}s)")
    return score(sid, replies, goal)


def score(sid, replies, goal):
    from . import persona_style
    good = [r for r in replies if "error" not in r["failures"]]
    got = {}
    for f in FEATURES:
        key = "words" if f == "avg_words" else f
        got[f] = round(mean(r["features"][key] for r in good), 3) if good else None
    gaps = {}                                           # 0 = types just like real AIM, 1 = nothing like it
    for f in FEATURES:
        if got[f] is None:
            continue
        if f == "avg_words":                            # (four times too long or short counts as fully off)
            gaps[f] = round(min(1.0, abs(math.log(max(got[f], 0.5) / goal[f])) / math.log(4)), 3)
        else:
            gaps[f] = round(abs(got[f] - goal[f]), 3)
    style = 100 * (1 - mean(gaps.values())) if gaps else 0.0
    kinds = Counter(k for r in replies for k in r["failures"])
    failed = sum(1 for r in replies if r["failures"])
    fail_score = 100 * (1 - failed / len(replies)) if replies else 0.0
    # distinct: how far apart the residents' habits are (standardised)
    by_person = {}
    for r in good:
        by_person.setdefault(r["resident"], []).append(r["features"])
    keys = ["words", "lowercase", "end_punct", "capital_start", "emoticon", "shorthand", "emote", "exclaim"]
    vecs = {p: [mean(x[k] for x in fs) for k in keys] for p, fs in by_person.items()}
    sds = [pstdev([v[i] for v in vecs.values()]) or 1.0 for i in range(len(keys))] if vecs else []
    names = list(vecs)
    dists = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = vecs[names[i]], vecs[names[j]]
            dists.append(math.sqrt(sum(((a[k] - b[k]) / (sds[k] or 1)) ** 2 for k in range(len(keys)))))
    spread = mean(dists) if dists else 0.0
    raw_spread = mean(pstdev([v[i] for v in vecs.values()]) / max(0.05, mean(v[i] for v in vecs.values()))
                      for i in range(len(keys))) if len(vecs) > 1 else 0.0
    distinct = 100 * (1 - math.exp(-2.5 * raw_spread))
    # repetition: everyone opening the same way in the same situation
    reps = []
    for key in {r["scenario"] for r in good}:
        opens = Counter(" ".join(re.findall(r"[a-z']+", r["reply"].lower())[:2]) for r in good
                        if r["scenario"] == key and r["reply"])
        total = sum(opens.values())
        if total > 1:
            reps.append(opens.most_common(1)[0][1] / total)
    repetition = 100 * (1 - mean(reps)) if reps else 0.0
    overall = 0.35 * style + 0.35 * fail_score + 0.15 * distinct + 0.15 * repetition
    return {"style": sid, "style_name": persona_style.name(sid), "when": time.strftime("%Y-%m-%d %H:%M"),
            "residents": len(by_person), "replies": len(replies),
            "scores": {"overall": round(overall, 1), "style": round(style, 1), "failures": round(fail_score, 1),
                       "distinct": round(distinct, 1), "repetition": round(repetition, 1)},
            "typing": {"got": got, "real_aim": goal, "gap": gaps}, "failure_kinds": dict(kinds),
            "spread": round(spread, 3), "avg_seconds": round(mean(r["seconds"] for r in replies), 2) if replies
            else None, "replies_detail": replies}


# ---- reporting ---------------------------------------------------------------------------------------------
def report(res):
    s = res["scores"]
    t = res["typing"]

    def pct(v):
        return "-" if v is None else f"{v * 100:.0f}%"
    lines = [f"# Realism test - {res['style_name']}", "", f"{res['when']}, {res['residents']} residents, "
             f"{res['replies']} replies (about {res['avg_seconds']}s each).", "",
             "| Overall | Style | No failures | Distinct | Not repetitive |", "|---|---|---|---|---|",
             f"| **{s['overall']}** | {s['style']} | {s['failures']} | {s['distinct']} | {s['repetition']} |", "",
             "## How they type, against real AIM chat", "", "| | Residents | Real AIM |", "|---|---|---|"]
    for f in FEATURES:
        g, r = t["got"].get(f), t["real_aim"].get(f)
        if f == "avg_words":
            lines.append(f"| words per message | {g} | {r} |")
        else:
            lines.append(f"| {f.replace('_', ' ')} | {pct(g)} | {pct(r)} |")
    lines += ["", "## Failures", ""]
    lines += [f"- {k}: {v}" for k, v in sorted(res["failure_kinds"].items(), key=lambda kv: -kv[1])] or ["- none"]
    lines += ["", "## Some replies", ""]
    shown = Counter()
    for r in res["replies_detail"]:
        if shown[r["scenario"]] >= 3:
            continue
        shown[r["scenario"]] += 1
        flag = f"  _({', '.join(r['failures'])})_" if r["failures"] else ""
        lines.append(f"- **{r['resident']}** / {r['scenario']}: {r['reply'][:200]!r}{flag}")
    return "\n".join(lines)


def compare(a, b):
    sa, sb = a["scores"], b["scores"]
    lines = [f"# {a['style_name']} vs {b['style_name']}", "", f"| | {a['style_name']} | {b['style_name']} | change |",
             "|---|---|---|---|"]
    for k in ("overall", "style", "failures", "distinct", "repetition"):
        lines.append(f"| {k} | {sa[k]} | {sb[k]} | {sb[k] - sa[k]:+.1f} |")
    lines += ["", "| typing | " + a["style_name"] + " | " + b["style_name"] + " | real AIM |", "|---|---|---|---|"]
    for f in FEATURES:
        lines.append(f"| {f} | {a['typing']['got'].get(f)} | {b['typing']['got'].get(f)} | "
                     f"{a['typing']['real_aim'].get(f)} |")
    return "\n".join(lines)


def save(res):
    from . import persona_style
    out = persona_style.styles_dir() / "evals"
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{time.strftime('%Y-%m-%d %H%M')} {res['style_name']}"
    (out / f"{stem}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / f"{stem}.md").write_text(report(res), encoding="utf-8")
    return out / f"{stem}.md"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m claudexp.realism")
    ap.add_argument("--style", default="1.0")
    ap.add_argument("--residents", default=None, help="how many (from the top), or names separated by commas")
    ap.add_argument("--scenarios", default=None, help="scenario keys separated by commas")
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    ap.add_argument("--rescore", metavar="RESULT", help="score a saved run again (after the checks change)")
    args = ap.parse_args(argv)
    if args.rescore:
        path = Path(args.rescore)
        old = json.loads(path.read_text(encoding="utf-8"))
        for r in old["replies_detail"]:
            if "error" not in r["failures"]:
                r["failures"] = failures(r["reply"], r["resident"])
        res = score(old["style"], old["replies_detail"], targets())
        res["when"] = old["when"]
        path.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        path.with_suffix(".md").write_text(report(res), encoding="utf-8")
        print(report(res).split("## Some replies")[0])
        return
    if args.compare:
        a, b = (json.loads(Path(p).read_text(encoding="utf-8")) for p in args.compare)
        print(compare(a, b))
        return
    residents = None
    if args.residents:
        residents = int(args.residents) if args.residents.isdigit() else args.residents.split(",")
    res = run(args.style, residents, args.scenarios.split(",") if args.scenarios else None)
    path = save(res)
    print(report(res).split("## Some replies")[0])
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
