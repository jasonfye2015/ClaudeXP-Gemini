"""Turning a Telegram Desktop export (result.json, "Machine-readable JSON") into training conversations, in the same
format as export.py's: the other person's turns are "user", yours are "assistant", with a system line saying who you
were talking to and when ("You are Kithylin, chatting on Telegram with <name> in 2025...").

    python -m selfmodel.telegram [--years 2022-2026] [--min-avg-words 8] [--kinds general,roleplay,adult]
                                 [--tokens 3200000] [--per-contact 6000] [--groups] [--out DIR]

Reads Local Storage/Text Logs/telegram/result.json by default and writes train.jsonl, val.jsonl and stats.json to
Local Storage/LLM Models/selfmodel/data-telegram. One-to-one chats only, unless --groups.

How it's cut and cleaned (as export.py does for the old logs):
  - a chat splits into sessions at gaps of more than 30 minutes; back-to-back messages from the same side become one
    turn (Telegram invites firing off several short messages in a row)
  - links, e-mail addresses and phone numbers become <link>, <email>, <phone>
  - their stickers, photos, videos, voice messages and GIFs become short notes ("(sends a sticker: 😊)") so the
    conversation still makes sense; yours are left out (the model should learn to write, not to send stickers)
  - forwarded messages are left out (they're someone else's words)
  - sessions are cut into windows of about --window-tokens that open with their turn
"""
import argparse
import json
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

from . import content
from .export import CHARS_PER_TOKEN, MAX_TURN_CHARS, VAL_SHARE, clean, tokens, windows, you

TIMELINE = Path(__file__).resolve().parents[2]
SOURCE = TIMELINE / "Local Storage" / "Text Logs" / "telegram" / "result.json"
OUT = TIMELINE / "Local Storage" / "LLM Models" / "selfmodel" / "data-telegram"
SESSION_GAP = 30 * 60
MEDIA_NOTES = {"sticker": "sends a sticker", "animation": "sends a GIF", "video_file": "sends a video",
               "voice_message": "sends a voice message", "video_message": "sends a video message",
               "audio_file": "sends a song"}


def text_of(m):
    t = m.get("text", "")
    if isinstance(t, list):
        return "".join(x if isinstance(x, str) else x.get("text", "") for x in t)
    return t or ""


def note_for(m):
    """Their media as words, or ''."""
    if "photo" in m:
        return "(sends a photo)"
    mt = m.get("media_type")
    if mt:
        note = MEDIA_NOTES.get(mt, "sends a file")
        if mt == "sticker" and m.get("sticker_emoji"):
            note += f": {m['sticker_emoji']}"
        return f"({note})"
    if m.get("file"):
        return "(sends a file)"
    return ""


def sessions(chat, me):
    """A chat's messages cut into sessions: [(ts, mine, text)] each."""
    current, last = [], None
    for m in chat.get("messages", []):
        if m.get("type") != "message" or m.get("forwarded_from"):
            continue
        try:
            ts = int(m.get("date_unixtime") or 0)
        except ValueError:
            ts = 0
        mine = m.get("from_id") == me
        text = clean(text_of(m)).strip()
        if not text and not mine:
            text = note_for(m)
        if not text:
            continue
        if last is not None and ts - last > SESSION_GAP and current:
            yield current
            current = []
        current.append((ts, mine, text))
        last = ts
    if current:
        yield current


def turns(rows):
    out = []
    for _ts, mine, text in rows:
        role = "assistant" if mine else "user"
        if out and out[-1][0] == role:
            out[-1] = (role, "", out[-1][2] + "\n" + text)
        else:
            out.append((role, "", text))
    return [(r, s, t if len(t) <= MAX_TURN_CHARS else t[:MAX_TURN_CHARS].rstrip() + " ...") for r, s, t in out]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default=str(SOURCE))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--years", default="", help="only these years, e.g. 2022-2026")
    ap.add_argument("--tokens", type=int, default=7_000_000, help="stop at about this many tokens in all")
    ap.add_argument("--per-contact", type=int, default=6000, help="at most this many of your turns per contact")
    ap.add_argument("--kinds", default="", help="only sessions of these kinds: general, roleplay, adult")
    ap.add_argument("--min-turns", type=int, default=2, help="only sessions where you wrote at least this many turns")
    ap.add_argument("--min-avg-words", type=float, default=0, help="only windows where your replies average this many words")
    ap.add_argument("--window-tokens", type=int, default=650)
    ap.add_argument("--max-window-tokens", type=int, default=900)
    ap.add_argument("--groups", action="store_true", help="include group chats")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args(argv)
    lo, hi = 0, 9999
    if args.years:
        a, _, b = args.years.partition("-")
        lo, hi = int(a), int(b or a)
    kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
    started = time.time()
    data = json.load(open(args.source, encoding="utf-8"))
    me = f"user{data['personal_information']['user_id']}"
    name = you()
    by_contact = defaultdict(list)
    for chat in data.get("chats", {}).get("list", []):
        group = chat.get("type") != "personal_chat"
        if group and not args.groups:
            continue
        who = chat.get("name") or "someone"
        for rows in sessions(chat, me):
            year = time.gmtime(rows[0][0]).tm_year if rows[0][0] else 0
            if not (lo <= year <= hi):
                continue
            ts = turns(rows)
            if sum(1 for t in ts if t[0] == "assistant") < max(2, args.min_turns):
                continue
            kind = content.kind([{"role": r, "content": t} for r, _s, t in ts])
            if kinds and kind not in kinds:
                continue
            for w in windows(ts, args.window_tokens):
                mine = [t for t in w if t[0] == "assistant"]
                if not mine or sum(len(t[2]) for t in mine) < 12:
                    continue
                if args.min_avg_words and sum(len(t[2].split()) for t in mine) / len(mine) < args.min_avg_words:
                    continue
                place = f"in the {who} group on Telegram" if group else "on Telegram"
                system = (f"You are {name}, chatting {place}" + ("" if group else f" with {who}") +
                          (f" in {year}" if year else "") + ". Reply as yourself, the way you really talk.")
                msgs = [{"role": "system", "content": system}]
                if w[0][0] == "assistant":
                    msgs.append({"role": "user", "content": f"({who} is online.)" if not group else "(The chat is quiet.)"})
                for role, _speaker, text in w:
                    msgs.append({"role": role, "content": text})
                n = sum(tokens(m["content"]) for m in msgs)
                if n > args.max_window_tokens:
                    continue
                by_contact[who].append({"messages": msgs, "meta": {"service": "Telegram", "contact": who, "year": year,
                                                                   "room": group, "your_turns": len(mine), "tokens": n,
                                                                   "session_kind": kind}})
    rnd = random.Random(args.seed)
    pool = []
    for who, examples in by_contact.items():
        rnd.shuffle(examples)
        mine = 0
        for ex in examples:
            if mine >= args.per_contact:
                break
            pool.append(ex)
            mine += ex["meta"]["your_turns"]
    rnd.shuffle(pool)
    chosen, total = [], 0
    for ex in pool:
        if total + ex["meta"]["tokens"] > args.tokens:
            continue
        chosen.append(ex)
        total += ex["meta"]["tokens"]
    n_val = max(50, int(len(chosen) * VAL_SHARE))
    val, train = chosen[:n_val], chosen[n_val:]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for fname, rows in (("train.jsonl", train), ("val.jsonl", val)):
        with open(out / fname, "w", encoding="utf-8") as f:
            for ex in rows:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    stats = {"built": time.strftime("%Y-%m-%d %H:%M"), "you": name, "source": "Telegram", "token_budget": args.tokens,
             "years": args.years or "all", "rooms": args.groups, "per_contact": args.per_contact,
             "kinds": sorted(kinds) or "all", "min_turns": args.min_turns, "min_avg_words": args.min_avg_words,
             "window_tokens": args.window_tokens, "conversations": {"train": len(train), "val": len(val)},
             "tokens": total, "your_turns": sum(e["meta"]["your_turns"] for e in chosen),
             "available_windows": sum(len(v) for v in by_contact.values()),
             "by_service": {"Telegram": len(chosen)},
             "by_year": dict(sorted(Counter(e["meta"]["year"] for e in chosen).items())),
             "by_session_kind": dict(Counter(e["meta"]["session_kind"] for e in chosen).most_common()),
             "top_contacts": Counter(e["meta"]["contact"] for e in chosen).most_common(25),
             "seconds": round(time.time() - started)}
    (out / "stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "top_contacts"}, indent=1))
    return stats


if __name__ == "__main__":
    main()
