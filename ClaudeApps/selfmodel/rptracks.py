"""RP tracks for Kithylin Autopilot: your own roleplay scenes from your Telegram chats, turned into tracks he can
follow - so in a roleplay he leads, the way you do, instead of two models waiting on each other.

    python -m selfmodel.rptracks [--count 36] [--per-contact 3] [--model nemomix-unleashed-12b]
                                 [--kinds adult,roleplay] [--min-turns 10] [--years 2022-2026] [--out FILE]

Reads Local Storage/Text Logs/telegram/result.json and writes Local Storage/LLM Models/selfmodel/rptracks.json,
which the autopilot's RP Tracks tab picks up.

  - The scenes: one-to-one conversations the training data calls roleplay or adult, where you wrote at least
    --min-turns times and a good share of the turns are *actions*; the best of them (long, rich in action, the more
    recent the better), at most --per-contact from any one person, --count in all.
  - Each scene is read by a model on the graphics card (nothing else should be using it) and written down as a
    track: a title, the setting, the premise, your role and theirs, the beats from the opening to the wind-down in
    order, the moves you make to lead it, and the tone. A few of your own action lines from it go with it.

Names stay out: the other person is "your partner" in everything the model reads, and contact names are filtered
out of what it writes and of your lines.
"""
import argparse
import hashlib
import json
import random
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import content
from .export import you
from .telegram import SOURCE, sessions
from .threads import LLM, Names, Server, say, turns_of

OUT = LLM / "selfmodel" / "rptracks.json"

TRACK_SYSTEM = ("You read a roleplay between {me} and his partner and write it down as a TRACK: a guide another "
                "writer can follow to play {me}'s side of a scene like it and lead it from start to finish. Refer "
                "to the other person only as 'your partner'. Write to {me} as 'you'. Answer with JSON only.")
TRACK_USER = """The roleplay ({when}):

{text}

Return JSON:
{{"title": "a short name for the scene, a few words",
"setting": "where and when it takes place, one sentence",
"premise": "the situation as it opens, one or two sentences",
"his_role": "who you ({me}) are in the scene, a few words",
"their_role": "who your partner is in the scene, a few words",
"beats": ["the scene from opening to wind-down in order, 8 to 12 beats, each one short sentence saying what
happens next - written as directions for you to lead it"],
"moves": ["3 to 5 things you do to lead and move the scene along"],
"tone": "a few words: playful, tender, rough, teasing..."}}"""


def scene_score(c):
    """Long, rich in action, recent."""
    mine = sum(1 for _ts, m, _t in c["rows"] if m)
    return min(mine, 80) * (0.5 + c["emote_share"]) * (1 + 0.15 * (c["year"] - 2022))


def transcript(rows, me, names, limit=7000):
    """The scene as lines, the partner unnamed; a long one keeps its opening, its middle and its end."""
    lines = [f"{me if mine else 'Partner'}: {names.hide(text, 'Partner')}" for _ts, mine, text in turns_of(rows)]
    text = "\n".join(lines)
    if len(text) <= limit:
        return text
    third = limit // 3
    mid = len(text) // 2
    return text[:third] + "\n[...]\n" + text[mid - third // 2: mid + third // 2] + "\n[...]\n" + text[-third:]


def his_lines(rows, names, n=4):
    """A few of his own action lines from the scene, for the flavour of how he plays it."""
    picks = [t for _ts, mine, t in rows if mine and content.EMOTE.search(t) and 25 <= len(t) <= 200]
    random.Random(len(rows)).shuffle(picks)
    return [names.hide(t, "you").replace("\n", " ") for t in picks[:n]]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default=str(SOURCE))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--count", type=int, default=36)
    ap.add_argument("--per-contact", type=int, default=3)
    ap.add_argument("--min-turns", type=int, default=10, help="your turns in the scene, at least")
    ap.add_argument("--kinds", default="adult,roleplay")
    ap.add_argument("--years", default="", help="only these years, e.g. 2023-2026")
    ap.add_argument("--model", default="nemomix-unleashed-12b")
    ap.add_argument("--engine", default="")
    ap.add_argument("--parallel", type=int, default=2)
    args = ap.parse_args(argv)
    started = time.time()
    lo, hi = 0, 9999
    if args.years:
        a, _, b = args.years.partition("-")
        lo, hi = int(a), int(b or a)
    kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
    say(f"Reading {Path(args.source).name}...")
    data = json.load(open(args.source, encoding="utf-8"))
    me_id = f"user{data['personal_information']['user_id']}"
    me = you()
    chats = [c for c in data.get("chats", {}).get("list", []) if c.get("type") == "personal_chat"]
    names = Names([c.get("name") for c in chats], keep=[me])
    found = []
    for chat in chats:
        for rows in sessions(chat, me_id):
            year = time.localtime(rows[0][0]).tm_year if rows[0][0] else 0
            if not (lo <= year <= hi) or sum(1 for r in rows if r[1]) < args.min_turns:
                continue
            msgs = [{"role": "assistant" if m else "user", "content": t} for _ts, m, t in turns_of(rows)]
            kind = content.kind(msgs)
            if kind not in kinds:
                continue
            sc = content.scores(msgs)
            if sc["emote_share"] < 0.3:
                continue
            found.append({"rows": rows, "kind": kind, "year": year, "contact": chat.get("name") or "",
                          "emote_share": sc["emote_share"]})
    del data
    found.sort(key=scene_score, reverse=True)
    per = defaultdict(int)
    picked = []
    for c in found:
        if per[c["contact"]] >= args.per_contact:
            continue
        per[c["contact"]] += 1
        picked.append(c)
        if len(picked) >= args.count:
            break
    say(f"{len(found)} roleplay scenes; taking the best {len(picked)} "
        f"({sum(1 for c in picked if c['kind'] == 'adult')} adult) from {len(per)} people.")
    if not picked:
        return 1
    srv = Server(args.model, args.engine, max(1, args.parallel), slot=12288)
    system = TRACK_SYSTEM.format(me=me)

    def one(c):
        when = time.strftime("%B %Y", time.localtime(c["rows"][0][0]))
        return srv.ask(system, TRACK_USER.format(when=when, text=transcript(c["rows"], me, names), me=me),
                       max_tokens=1200, temperature=0.3)

    tracks = []
    try:
        with ThreadPoolExecutor(max(1, args.parallel)) as pool:
            for i, (c, t) in enumerate(zip(picked, pool.map(one, picked)), 1):
                beats = [names.hide(str(b), "your partner") for b in (t.get("beats") or []) if str(b).strip()]
                ok = bool(t.get("title")) and len(beats) >= 4
                if ok:
                    clean = lambda k: names.hide(str(t.get(k) or ""), "your partner").strip()
                    tracks.append({
                        "id": hashlib.sha1(str(c["rows"][0][0]).encode() + c["contact"].encode()).hexdigest()[:12],
                        "title": clean("title")[:1].upper() + clean("title")[1:], "kind": c["kind"], "setting": clean("setting"),
                        "premise": clean("premise"), "his_role": clean("his_role"),
                        "their_role": clean("their_role"), "beats": beats[:12],
                        "moves": [names.hide(str(m), "your partner") for m in (t.get("moves") or [])][:5],
                        "tone": clean("tone"), "lines": his_lines(c["rows"], names),
                        "turns": sum(1 for r in c["rows"] if r[1]), "year": c["year"]})
                say(f"  {i} of {len(picked)}: " + (tracks[-1]["title"] if ok else "(no track came of it)"))
    finally:
        srv.stop()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"built": time.strftime("%Y-%m-%d %H:%M"), "source": "Telegram", "model": args.model,
                               "tracks": tracks}, indent=1, ensure_ascii=False), encoding="utf-8")
    say(f"Done in {int(time.time() - started)} s: {len(tracks)} tracks in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
