"""Turning the chat-log index into training conversations for a model of you.

Reads Local Storage/Text Logs/_Index/chatlogs.sqlite (built by ClaudeArchive/chatlogs) and writes chat-format JSONL
to Local Storage/LLM Models/selfmodel/data/:

    train.jsonl, val.jsonl   {"messages": [{"role": "system"|"user"|"assistant", "content": ...}, ...],
                              "meta": {"service", "contact", "year", "your_turns", "tokens"}}
    stats.json               what went in, by service, year and contact

Each conversation is a stretch of one chat: the other person's turns are "user", yours are "assistant", so training
learns your replies (loss on the assistant turns) with what you were answering as context. The system line says who
you are, where, with whom and when - so the model can later be asked for "you on AIM in 2005" as well as "you".

How it's cut and cleaned:
  - a chat splits into sessions at gaps of more than SESSION_GAP; runs of lines from the same side become one turn
  - auto-replies, "test" lines, file-bot lines and empty lines go; links, e-mail addresses and phone numbers are
    replaced with <link>, <email>, <phone>
  - sessions are cut into windows of about WINDOW_TOKENS; a window always opens with their turn (or a note that you
    started the conversation)
  - group rooms (IRC channels, Second Life local chat) are off by default: they're mostly other people and bots
  - each contact gives at most PER_CONTACT of your turns, so one long friendship doesn't drown out the rest, and
    the whole set stops at about --tokens (default sized for an overnight run on a GTX 1080 Ti)

    python -m selfmodel.export [--tokens 7000000] [--years 2004-2011] [--rooms] [--per-contact 3000]
           [--kinds adult,roleplay] [--min-turns 20] [--window-tokens 900] [--max-window-tokens 1600] [--out DIR]

--kinds keeps only sessions of those kinds (content.py: general, roleplay, adult - judged on the whole session, so
every window of an adult session comes along, build-up included); --min-turns keeps only sessions where you wrote at
least that many turns (the longer ones).
"""
import argparse
import json
import random
import re
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path

from . import content

TIMELINE = Path(__file__).resolve().parents[2]
INDEX = TIMELINE / "Local Storage" / "Text Logs" / "_Index" / "chatlogs.sqlite"
OUT = TIMELINE / "Local Storage" / "LLM Models" / "selfmodel" / "data"
SESSION_GAP = 30 * 60
WINDOW_TOKENS = 900
PER_CONTACT = 3000
VAL_SHARE = 0.01
CHARS_PER_TOKEN = 3.6           # chat text with emotes and short words; good enough for sizing
MAX_TURN_CHARS = 1200           # a pasted wall of text is cut down to this
MAX_WINDOW_TOKENS = 1600        # longer windows are left out (they'd blow the memory budget in training)

LINK = re.compile(r"(?i)\b(?:https?://|ftp://|www\.)\S+")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)")
BOT = re.compile(r"^\*\*|^#\d+\s|xdcc|^\[\d+:\d+\]|has (joined|left|quit)|is now known as|sets mode", re.I)
JUNK = {"test", "testing", "test test", ".", "..", "..."}
SERVICE_NAMES = {"Yahoo! Messenger": "Yahoo! Messenger", "AIM": "AIM", "MSN Messenger": "MSN Messenger",
                 "Second Life": "Second Life", "IRC": "IRC", "ICQ": "ICQ", "Google Talk": "Google Talk",
                 "Jabber": "Jabber", "Skype": "Skype"}


def you():
    try:
        prof = json.loads((TIMELINE / "Profile" / "profile.json").read_text(encoding="utf-8"))
        return prof.get("handle") or prof.get("name") or "Kithylin"
    except (OSError, ValueError):
        return "Kithylin"


def clean(text):
    text = (text or "").replace("\r", "").strip()
    if not text:
        return ""
    text = LINK.sub("<link>", text)
    text = EMAIL.sub("<email>", text)
    text = PHONE.sub("<phone>", text)
    return text


def tokens(text):
    return int(len(text) / CHARS_PER_TOKEN) + 4


def sessions(con, rooms):
    """Yield (service, account, contact, room, [(ts, outgoing, speaker, text)]) per session, chat by chat."""
    where = "" if rooms else "WHERE room = 0"
    chats = con.execute(f"SELECT service, account, contact, room FROM messages {where} "
                        "GROUP BY service, account, contact, room HAVING SUM(outgoing = 1) >= 5").fetchall()
    for service, account, contact, room in chats:
        rows = con.execute("SELECT ts, outgoing, speaker, text FROM messages WHERE service = ? AND account = ? AND "
                           "contact = ? AND room = ? ORDER BY ts, id", (service, account, contact, room)).fetchall()
        current, last = [], None
        for row in rows:
            if last is not None and row[0] - last > SESSION_GAP and current:
                yield service, account, contact, room, current
                current = []
            current.append(row)
            last = row[0]
        if current:
            yield service, account, contact, room, current


def turns(rows, room):
    """A session's lines as turns: [(role, speaker, text)], same-side runs merged, junk dropped."""
    out = []
    for ts, outgoing, speaker, text in rows:
        speaker = speaker or ""
        if "auto-reply" in speaker.lower() or "<auto" in (text or "").lower():
            continue
        text = clean(text)
        if not text or text.lower() in JUNK or (not outgoing and BOT.search(text)):
            continue
        role = "assistant" if outgoing else "user"
        line = f"{speaker}: {text}" if room and not outgoing else text
        if out and out[-1][0] == role:          # one side's run of lines (in a room, several speakers) is one turn
            out[-1] = (role, out[-1][1], out[-1][2] + "\n" + line)
        else:
            out.append((role, speaker, line))
    return [(r, s, t if len(t) <= MAX_TURN_CHARS else t[:MAX_TURN_CHARS].rstrip() + " ...") for r, s, t in out]


def windows(ts, size_limit=WINDOW_TOKENS):
    """Cut a session's turns into windows of about size_limit tokens that open with their turn."""
    out, current, size = [], [], 0
    for t in ts:
        n = tokens(t[2])
        if current and size + n > size_limit and current[-1][0] == "assistant":
            out.append(current)
            current, size = [], 0
        current.append(t)
        size += n
    if current:
        out.append(current)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tokens", type=int, default=7_000_000, help="stop at about this many tokens in all")
    ap.add_argument("--years", default="", help="only these years, e.g. 2004-2007")
    ap.add_argument("--rooms", action="store_true", help="include group rooms (IRC, Second Life local chat)")
    ap.add_argument("--per-contact", type=int, default=PER_CONTACT, help="at most this many of your turns per contact")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--kinds", default="", help="only sessions of these kinds: general, roleplay, adult (comma-separated)")
    ap.add_argument("--min-turns", type=int, default=2, help="only sessions where you wrote at least this many turns")
    ap.add_argument("--min-avg-words", type=float, default=0,
                    help="only windows where your replies average at least this many words (the wordier you)")
    ap.add_argument("--window-tokens", type=int, default=WINDOW_TOKENS)
    ap.add_argument("--max-window-tokens", type=int, default=MAX_WINDOW_TOKENS)
    args = ap.parse_args(argv)
    kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
    lo, hi = 0, 9999
    if args.years:
        a, _, b = args.years.partition("-")
        lo, hi = int(a), int(b or a)
    name = you()
    con = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)
    started = time.time()
    by_contact = defaultdict(list)              # contact key -> [example]
    seen = 0
    for service, account, contact, room, rows in sessions(con, args.rooms):
        year = time.gmtime(rows[0][0]).tm_year if rows[0][0] else 0
        if not (lo <= year <= hi):
            continue
        ts = turns(rows, room)
        if sum(1 for t in ts if t[0] == "assistant") < max(2, args.min_turns):
            continue
        kind = content.kind([{"role": r, "content": t} for r, _s, t in ts])
        if kinds and kind not in kinds:
            continue
        theirs = Counter(t[1] for t in ts if t[0] == "user" and t[1])
        who = contact if room else (theirs.most_common(1)[0][0] if theirs else contact)
        where = SERVICE_NAMES.get(service, service)
        place = f"in {contact} on {where}" if room else f"on {where}"
        for w in windows(ts, args.window_tokens):
            mine = [t for t in w if t[0] == "assistant"]
            if not mine or sum(len(t[2]) for t in mine) < 12:
                continue
            if args.min_avg_words and sum(len(t[2].split()) for t in mine) / len(mine) < args.min_avg_words:
                continue
            system = (f"You are {name}, chatting {place}" + ("" if room else f" with {who}") +
                      (f" in {year}" if year else "") + ". Reply as yourself, the way you really talk.")
            msgs = [{"role": "system", "content": system}]
            if w[0][0] == "assistant":
                msgs.append({"role": "user", "content": f"({who} is online.)" if not room else "(The room is quiet.)"})
            for role, _speaker, text in w:
                msgs.append({"role": role, "content": text})
            n = sum(tokens(m["content"]) for m in msgs)
            if n > args.max_window_tokens:
                continue
            by_contact[(service, contact)].append({
                "messages": msgs,
                "meta": {"service": where, "contact": who, "year": year, "room": bool(room),
                         "your_turns": len(mine), "tokens": n, "session_kind": kind}})
        seen += 1
        if seen % 2000 == 0:
            print(f"  {seen} sessions, {sum(len(v) for v in by_contact.values())} windows...", flush=True)
    # each contact's windows, capped and shuffled; then everything shuffled and cut to the token budget
    rnd = random.Random(args.seed)
    pool = []
    for key, examples in by_contact.items():
        rnd.shuffle(examples)
        kept, mine = [], 0
        for ex in examples:
            if mine >= args.per_contact:
                break
            kept.append(ex)
            mine += ex["meta"]["your_turns"]
        pool.extend(kept)
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
    stats = {
        "built": time.strftime("%Y-%m-%d %H:%M"), "you": name, "token_budget": args.tokens,
        "years": args.years or "all", "rooms": args.rooms, "per_contact": args.per_contact,
        "kinds": sorted(kinds) or "all", "min_turns": args.min_turns, "window_tokens": args.window_tokens,
        "min_avg_words": args.min_avg_words,
        "by_session_kind": dict(Counter(e["meta"]["session_kind"] for e in chosen).most_common()),
        "conversations": {"train": len(train), "val": len(val)},
        "tokens": total, "your_turns": sum(e["meta"]["your_turns"] for e in chosen),
        "available_windows": sum(len(v) for v in by_contact.values()),
        "by_service": dict(Counter(e["meta"]["service"] for e in chosen).most_common()),
        "by_year": dict(sorted(Counter(e["meta"]["year"] for e in chosen).items())),
        "top_contacts": Counter(e["meta"]["contact"] for e in chosen).most_common(25),
        "seconds": round(time.time() - started)}
    (out / "stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "top_contacts"}, indent=1))
    return stats


if __name__ == "__main__":
    main()
