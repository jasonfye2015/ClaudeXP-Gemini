"""The model details card: what a Kithylin model was trained on and how the training went, with sample snippets of
the conversations, written as card.json beside the model (Kithylin AI shows it on its Model Details tab).

    env\\Scripts\\python.exe -m selfmodel.card MODEL_FOLDER [--data DATA_FOLDER] [--adapter ADAPTER] [--notes "..."]

make_model.py writes one automatically. The card is built from the training data folder (train.jsonl, stats.json)
and the training log (train_log.jsonl: the run that made the adapter). It holds snippets of your real conversations,
so like the model it's personal: it stays in kithylinai/Models (not in git)."""
import argparse
import json
import random
import re
import time
from collections import Counter
from pathlib import Path

from . import content

ROOT = Path(__file__).resolve().parents[2] / "Local Storage" / "LLM Models" / "selfmodel"
SNIPPETS_PER_KIND = 4
SNIPPET_TURNS = 8
SNIPPET_CHARS = 280


def _rows(data):
    with open(data / "train.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _name_pattern(rows):
    """A regex for every contact's name in the data: the full screen name, and the parts of it people actually
    call someone ('Aesar' for Aesar19, 'Snowpaw' for Woof Snowpaw, 'fluffyroo' for fluffyroo@mac.com). A part that's
    an everyday word in the chats (woof, puppy, wolf...) is left alone, so the snippets stay readable."""
    names, parts = set(), {}
    for r in rows:
        contact = ((r.get("meta") or {}).get("contact") or "").strip()
        if not contact:
            continue
        names.add(contact.lower())
        local = contact.split("@")[0]
        names.add(local.lower())
        for part in re.findall(r"[A-Za-z]{4,}", local):
            parts.setdefault(part.lower(), set()).add(contact)
    # how many conversations use each part, other than those with its owner: a common word is in lots of them
    common = Counter()
    word = re.compile(r"[a-z]{4,}")
    for r in rows:
        contact = ((r.get("meta") or {}).get("contact") or "")
        seen = set(word.findall(" ".join(m["content"].lower() for m in r["messages"] if m["role"] != "system")))
        for w in seen & parts.keys():
            if contact not in parts[w]:
                common[w] += 1
    names |= {p for p in parts if common[p] < 15}
    names = sorted((n for n in names if len(n) >= 3), key=len, reverse=True)
    return re.compile(r"(?<![\w@.])(" + "|".join(re.escape(n) for n in names) + r")(?![\w@])", re.I) if names else None


def _snippet(row, rng, hide=None):
    """A run of up to SNIPPET_TURNS turns from the conversation, as [(who, text)]. hide: a pattern of names to
    replace with [name] (and the other person is called 'Them')."""
    meta = row.get("meta") or {}
    who = "Them" if hide else (meta.get("contact") or "them")
    turns = [m for m in row["messages"] if m["role"] in ("user", "assistant")
             and not (m["role"] == "user" and m["content"].endswith("is online.)"))]
    if len(turns) > SNIPPET_TURNS:
        start = rng.randrange(0, len(turns) - SNIPPET_TURNS + 1)
        turns = turns[start:start + SNIPPET_TURNS]
    out = []
    for m in turns:
        text = m["content"].strip()
        if len(text) > SNIPPET_CHARS:
            text = text[:SNIPPET_CHARS].rstrip() + "…"
        if hide is not None:
            text = hide.sub("[name]", text)
        out.append(["Kithylin" if m["role"] == "assistant" else who, text])
    return {"service": meta.get("service", ""), "contact": "" if hide else who, "year": meta.get("year"), "turns": out}


def _training(log_path, adapter):
    """The training run that made the adapter: from its last start (not a benchmark) up to the adapter's step."""
    if not log_path.exists():
        return {}
    entries = []
    for line in open(log_path, encoding="utf-8"):
        try:
            entries.append(json.loads(line))
        except ValueError:
            pass
    starts = [i for i, e in enumerate(entries) if e.get("event") == "start" and not e.get("bench")]
    if not starts:
        return {}
    first = starts[-1]
    while first > 0 and entries[first].get("resume_at"):          # a resumed run: go back to where it began
        earlier = [i for i in starts if i < first]
        if not earlier:
            break
        first = earlier[-1]
    run = entries[first:]
    upto = None
    try:
        upto = json.loads((adapter / "state.json").read_text()).get("step")
    except (OSError, ValueError, TypeError):
        pass
    if upto is not None:
        run = [e for e in run if e.get("step") is None or e["step"] <= upto or e.get("event") in ("start", "done")]
    steps = [e for e in run if e.get("event") == "step"]
    evals = [e for e in run if e.get("event") == "eval"]
    start = run[0]
    last = steps[-1] if steps else {}
    t0 = time.mktime(time.strptime(start["time"], "%Y-%m-%d %H:%M:%S"))
    t1 = time.mktime(time.strptime((steps[-1] if steps else start)["time"], "%Y-%m-%d %H:%M:%S"))
    return {"started": start["time"], "hours": round((t1 - t0) / 3600, 2),
            "steps": last.get("step", 0), "of": start.get("steps"),
            "conversations_in_set": start.get("train"),
            "speed_tok_s": last.get("tok_per_s"), "gpu_gb": last.get("gpu_gb"),
            "train_loss_last": last.get("loss"),
            "val_loss": [[e["step"], e["val_loss"]] for e in evals]}


def build(model_dir, data=ROOT / "data", adapter=ROOT / "adapter", log=ROOT / "train_log.jsonl", notes="",
          base="Gemma 3 4B instruct (unsloth/gemma-3-4b-it, Google's Gemma 3)", settings=None, keep_names=False):
    model_dir, data, adapter = Path(model_dir), Path(data), Path(adapter)
    rows = _rows(data)
    stats = json.loads((data / "stats.json").read_text(encoding="utf-8")) if (data / "stats.json").exists() else {}
    kinds, tokens, turns = Counter(), Counter(), Counter()
    by_kind = {k: [] for k in content.KINDS}
    lengths = []
    for r in rows:
        k = content.kind(r["messages"])
        meta = r.get("meta") or {}
        kinds[k] += 1
        tokens[k] += meta.get("tokens", 0)
        turns[k] += meta.get("your_turns", 0)
        by_kind[k].append(r)
        lengths.append(meta.get("tokens", 0))
    total_tokens = sum(tokens.values()) or 1
    rng = random.Random(f"{model_dir.name}")
    hide = None if keep_names else _name_pattern(rows)
    snippets = {}
    for k, pool in by_kind.items():
        good = [r for r in pool if 6 <= len(r["messages"]) and (r.get("meta") or {}).get("tokens", 0) <= 900]
        rng.shuffle(good)
        snippets[k] = [_snippet(r, rng, hide) for r in good[:SNIPPETS_PER_KIND]]
    lengths.sort()
    card = {
        "name": model_dir.name, "made": time.strftime("%Y-%m-%d %H:%M"), "base": base, "notes": notes,
        "you": stats.get("you", "Kithylin"),
        "data": {"conversations": len(rows), "your_turns": sum(turns.values()), "tokens": sum(tokens.values()),
                 "years": stats.get("years", "all"), "rooms": stats.get("rooms", False),
                 "per_contact": stats.get("per_contact"), "exported": stats.get("built"),
                 "by_service": stats.get("by_service", {}), "by_year": stats.get("by_year", {}),
                 "contacts": len({(r.get("meta") or {}).get("contact") for r in rows}),
                 "top_contacts": stats.get("top_contacts", [])[:12] if keep_names else [],
                 "names_hidden": not keep_names,
                 "median_tokens": lengths[len(lengths) // 2] if lengths else 0},
        "mix": {k: {"label": content.LABELS[k], "conversations": kinds[k], "tokens": tokens[k], "your_turns": turns[k],
                    "share_tokens": round(100 * tokens[k] / total_tokens, 1),
                    "share_conversations": round(100 * kinds[k] / max(1, len(rows)), 1)} for k in content.KINDS},
        "training": _training(Path(log), adapter),
        "settings": settings or {},
        "snippets": snippets,
    }
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "card.json").write_text(json.dumps(card, indent=1, ensure_ascii=False), encoding="utf-8")
    return card


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model_dir", type=Path)
    ap.add_argument("--data", type=Path, default=ROOT / "data")
    ap.add_argument("--adapter", type=Path, default=ROOT / "adapter")
    ap.add_argument("--log", type=Path, default=ROOT / "train_log.jsonl")
    ap.add_argument("--notes", default="")
    ap.add_argument("--keep-names", action="store_true", help="keep other people's names in the card (hidden by default)")
    args = ap.parse_args(argv)
    card = build(args.model_dir, args.data, args.adapter, args.log, args.notes, keep_names=args.keep_names)
    mix = ", ".join(f"{v['label']} {v['share_tokens']}%" for v in card["mix"].values())
    print(f"wrote {args.model_dir / 'card.json'}: {card['data']['conversations']} conversations; {mix}")


if __name__ == "__main__":
    main()
