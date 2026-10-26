"""Fingerprinting your recent Telegram chats for Kithylin Autopilot: the threads that run through them and the way
you write, as suggestions the autopilot's Threads tab offers (nothing is used until it's ticked).

    python -m selfmodel.threads [--months 12] [--model qwen3-4b-instruct] [--sessions 300] [--no-model]
                                [--kinds general,roleplay] [--engine cuda|vulkan] [--out FILE]

Reads Local Storage/Text Logs/telegram/result.json (the same export selfmodel.telegram trains on) and writes
Local Storage/LLM Models/selfmodel/threads.json:

  - the style card, from every one-to-one conversation in the last --months (no model needed): the lines you open
    and close with, how many words a message runs at each time of day (work, lunch, evening, late, weekend), your
    habits - laughs, emoticons, *actions*, lowercase, bursts of short messages
  - the threads (with a model, run on the graphics card - nothing else should be using it): a sample of the longer
    conversations is summarised one by one (how it opened, what it was about, how it went, how it ended, what it
    says about your life), then the summaries are grouped into recurring threads - life arcs, openers, running
    bits, roleplay seeds - each with its facts, a few beats for a life arc, how often it came up and when

Names are left out: the other side is "a friend" in everything the model sees, and contact names are filtered out
of what it writes. --no-model makes the style card alone, in a minute or so.
"""
import argparse
import hashlib
import json
import os
import re
import socket
import statistics
import subprocess
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import content
from .export import you
from .telegram import SOURCE, TIMELINE, sessions

LLM = TIMELINE / "Local Storage" / "LLM Models"
OUT = LLM / "selfmodel" / "threads.json"
LOG = LLM / "selfmodel" / "threads-server.log"
SUMMARIES = LLM / "selfmodel" / "threads-summaries.json"   # kept, so --reuse can regroup without summarising again

LAUGH = re.compile(r"\b(?:he(?:h|he)+e?h?|ha(?:ha)+h?|hehe+|lo+l|lmao+|rofl|xd+|kek)\b", re.I)
EMOTICON = re.compile(r"(?<!\w)(?:[:;=xX8][-']?[)(DPp3Oo/\\|\]\[]+|<3+|\^\^|\^_\^|o\.o|;_;|T_T|uwu|owo|:3)(?!\w)")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿❤️]+")
ACTION = re.compile(r"\*([^*\n]{2,40})\*")


def say(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


# ---- names out --------------------------------------------------------------------------------------------------
class Names:
    """Every contact's name, and the first word of it, for keeping names out of what's written."""

    def __init__(self, names):
        words = set()
        for n in names:
            n = (n or "").strip()
            if len(n) >= 3:
                words.add(n)
            first = re.split(r"[\s(|\-]", n)[0].strip()
            if len(first) >= 3 and first[:1].isupper():
                words.add(first)
        self.words = sorted(words, key=len, reverse=True)
        self.pattern = re.compile("|".join(re.escape(w) for w in self.words)) if self.words else None

    def hide(self, text, as_="a friend"):
        if not text or self.pattern is None:
            return text
        return self.pattern.sub(as_, text)

    def hide_ci(self, text, as_="{name}"):
        """For short lines (openers): case-insensitive, whole words."""
        for w in self.words:
            text = re.sub(rf"(?<!\w){re.escape(w)}(?!\w)", as_, text, flags=re.I)
        return text


# ---- the style card ---------------------------------------------------------------------------------------------
def style_block(t):
    """Matches the autopilot's default week: work Mon-Fri 9:30-18:30 with lunch 14:30-15:30, asleep 23-7."""
    mins = t.tm_hour * 60 + t.tm_min
    if t.tm_wday >= 5 and 7 <= t.tm_hour < 23:
        return "weekend"
    if t.tm_wday < 5 and 14 * 60 + 30 <= mins < 15 * 60 + 30:
        return "lunch"
    if t.tm_wday < 5 and 9 * 60 + 30 <= mins < 18 * 60 + 30:
        return "work"
    if 5 <= t.tm_hour < 12:
        return "morning"
    if 12 <= t.tm_hour < 23:
        return "evening"
    return "late"


BREAK = 6 * 3600          # a gap this long before (or after) a conversation: a real start (or end)


def short_line(text, names, max_words=8):
    text = " ".join((text or "").split())
    if not text or "<link>" in text or "<email>" in text or "<phone>" in text:
        return ""
    bare = EMOJI.sub("", EMOTICON.sub("", LAUGH.sub("", text))).strip(" !?.~*")
    if len(bare) < 2:
        return ""                                   # only a laugh or a smiley: a reaction, not an opener
    if len(text.split()) > max_words:
        return ""
    return names.hide_ci(text).lower()


def style_card(convs, names):
    openers, closers, habits, actions = Counter(), Counter(), Counter(), Counter()
    words = defaultdict(list)
    by_hour = [0] * 24
    lower = msgs = bursts = turns_n = 0
    for c in convs:
        rows = c["rows"]
        by_hour[time.localtime(rows[0][0]).tm_hour] += 1
        if rows[0][1] and c.get("gap_before", BREAK) >= BREAK:
            line = short_line(rows[0][2], names)
            if line:
                openers[line] += 1
        mine = [r for r in rows if r[1]]
        if mine and mine[-1] in rows[-2:] and c.get("gap_after", BREAK) >= BREAK:
            line = short_line(mine[-1][2], names)
            if line:
                closers[line] += 1
        run = []                                    # his messages back to back: one turn
        for ts, is_me, text in rows + [(0, False, "")]:
            if is_me:
                run.append((ts, text))
                continue
            if run:
                turns_n += 1
                bursts += len(run)
                joined = " ".join(t for _ts, t in run)
                words[style_block(time.localtime(run[0][0]))].append(len(joined.split()))
                run = []
        for _ts, is_me, text in rows:
            if not is_me:
                continue
            msgs += 1
            if text[:1].islower():
                lower += 1
            for m in LAUGH.findall(text):
                m = m.lower()
                habits["hehehe" if re.fullmatch(r"h?(?:eh)+e?h?|he+", m) else
                       "hahaha" if m.startswith("ha") else m[:8]] += 1
            for m in EMOTICON.findall(text):
                habits[m] += 1
            for m in EMOJI.findall(text):
                habits[m[:2]] += 1
            for a in ACTION.findall(text):
                a = names.hide(a.strip().lower(), "them")
                if len(a.split()) <= 4:
                    actions[f"*{a}*"] += 1
    common = lambda counter, n, least: [k for k, v in counter.most_common(n) if v >= least]
    hab, seen = [], set()
    for h in common(habits, 16, 5) + common(actions, 6, 4):
        if h.lower() not in seen:                   # xd / XD: one habit
            seen.add(h.lower())
            hab.append(h)
    if msgs and lower / msgs > 0.6:
        hab.append("mostly lowercase")
    if turns_n and bursts / turns_n > 1.6:
        hab.append("several short messages in a row rather than one long one")
    return {
        "openers": common(openers, 12, 2),
        "closers": common(closers, 12, 2),
        "words_by_block": {k: round(statistics.median(v), 1) for k, v in sorted(words.items()) if len(v) >= 20},
        "habits": hab,
        "sessions_by_hour": by_hour,
        "messages": msgs,
    }


# ---- the model --------------------------------------------------------------------------------------------------
def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Server:
    def __init__(self, model, engine, parallel):
        folder = LLM / "models" / model
        ggufs = sorted(f for f in folder.glob("*.gguf") if not f.name.lower().startswith(("mmproj", "mtp")))
        if not ggufs:
            raise SystemExit(f"No model called {model} in {LLM / 'models'}")
        exe = None
        for e in ([engine] if engine else ["cuda", "vulkan"]):
            cand = LLM / "llama.cpp" / e / ("llama-server.exe" if os.name == "nt" else "llama-server")
            if cand.exists():
                exe = cand
                break
        if exe is None:
            raise SystemExit("No llama-server found in Local Storage/LLM Models/llama.cpp")
        self.port = _free_port()
        args = [str(exe), "--host", "127.0.0.1", "--port", str(self.port), "-m", str(ggufs[0]), "-c",
                str(8192 * parallel), "--parallel", str(parallel), "-ngl", "99", "--jinja", "--flash-attn", "on"]
        say(f"Starting {model} on the {exe.parent.name} engine...")
        self.log = open(LOG, "w", encoding="utf-8", errors="replace")
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.proc = subprocess.Popen(args, stdout=self.log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                     cwd=str(exe.parent), creationflags=flags)
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise SystemExit(f"The engine stopped while loading (see {LOG})")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=2) as r:
                    if r.status == 200:
                        return
            except Exception:
                pass
            time.sleep(0.5)
        self.stop()
        raise SystemExit("The engine took too long to load")

    def ask(self, system, user, max_tokens=400, temperature=0.2):
        body = {"messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": temperature, "max_tokens": max_tokens, "response_format": {"type": "json_object"}}
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/chat/completions",
                                     data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                out = json.loads(r.read())["choices"][0]["message"]["content"] or ""
        except Exception as e:
            say(f"  (a request failed: {e})")
            return {}
        m = re.search(r"\{.*\}", out, re.S)
        try:
            return json.loads(m.group(0)) if m else {}
        except ValueError:
            say(f"  (an answer wasn't JSON: {out[:80]!r} ... {out[-80:]!r})")
            return {}

    def stop(self):
        try:
            self.proc.terminate()
            self.proc.wait(10)
        except Exception:
            pass
        self.log.close()


SUMMARY_SYSTEM = ("You read one chat conversation between {me} and a friend and describe it briefly. Never use "
                  "anyone's name: say {me} and 'a friend' (or 'his roommate', 'his partner'). Answer with JSON only.")
SUMMARY_USER = """The conversation ({when}):

{text}

Return JSON:
{{"opener": "how it started, a few words",
"topic": "what it was mostly about, 3-8 words",
"arc": "how it went, one short sentence",
"closer": "how it ended, a few words",
"kind": "life" (news and happenings in {me}'s life), "bit" (a running joke or playful routine), "roleplay" (a
pretend scene in *asterisks*), "opener" (mostly a greeting, good morning / good night) or "other",
"life_facts": ["facts about {me}'s own life it mentions - job, home, pets, health, plans, hobbies - a few words
each, no names; [] if none"]}}"""

GROUP_SYSTEM = ("You find the recurring threads in a person's chats. Never use anyone's name except {me}. Answer "
                "with JSON only.")
GROUP_USER = """Here are summaries of {me}'s conversations, numbered:

{items}

Group them into recurring THREADS - things that come up again and again: his job, a move, a pet, his health, a
hobby or project, a running joke, a kind of roleplay he likes, the way he says good morning. Only threads at least
two summaries share. Write each thread to {me} as "you".
Return JSON: {{"threads": [{{"title": "a few words", "kind": "life" | "bit" | "roleplay" | "opener",
"facts": "what's true about it, one or two sentences, to {me} as 'you', no names",
"items": [the numbers of the summaries in it]}}]}}"""

MERGE_USER = """These threads were found in different batches of {me}'s conversations; several are the same thread.

{items}

Merge the duplicates into one list of at most {limit} threads, most frequent first. For a "life" thread that
naturally moves on over days (a move, an illness, a project, a trip), add 2-4 short "beats" - how it might develop,
one per day. Write to {me} as "you", no names.
Return JSON: {{"threads": [{{"title": "...", "kind": "life" | "bit" | "roleplay" | "opener", "facts": "...",
"beats": ["...", "..."], "from": [the numbers of the threads merged into it]}}]}}"""


def transcript(rows, me, names, limit=2400):
    lines = []
    for _ts, mine, text in turns_of(rows):
        lines.append(f"{me if mine else 'Friend'}: {names.hide(text, 'Friend')}")
    text = "\n".join(lines)
    if len(text) > limit:
        text = text[: int(limit * 0.7)] + "\n[...]\n" + text[-int(limit * 0.3):]
    return text


def turns_of(rows):
    out = []
    for ts, mine, text in rows:
        if out and out[-1][1] == mine:
            out[-1] = (out[-1][0], mine, out[-1][2] + "\n" + text)
        else:
            out.append((ts, mine, text))
    return out


def part_of_day(hours):
    if not hours:
        return ""
    h = statistics.median(hours)
    return ("in the morning" if 5 <= h < 12 else "in the afternoon" if 12 <= h < 17 else
            "in the evening" if 17 <= h < 22 else "late at night")


def _numbers(values, top):
    out = []
    for v in values if isinstance(values, list) else []:
        try:
            n = int(str(v).strip().strip("#."))
        except ValueError:
            continue
        if 1 <= n <= top:
            out.append(n)
    return out


def summarise(srv, convs, me, names, sample, workers):
    long = [c for c in convs if len(turns_of(c["rows"])) >= 6]
    long.sort(key=lambda c: c["rows"][0][0])
    step = max(1, len(long) / max(1, sample))
    picked = [long[int(i * step)] for i in range(min(sample, len(long)))]
    say(f"Summarising {len(picked)} of {len(long)} longer conversations...")
    system = SUMMARY_SYSTEM.format(me=me)

    def one(c):
        when = time.strftime("%A %B %Y, %H:%M", time.localtime(c["rows"][0][0]))
        return srv.ask(system, SUMMARY_USER.format(when=when, text=transcript(c["rows"], me, names), me=me))

    summaries = []
    with ThreadPoolExecutor(workers) as pool:
        for i, (c, s) in enumerate(zip(picked, pool.map(one, picked)), 1):
            if s.get("topic"):
                s["hour"] = time.localtime(c["rows"][0][0]).tm_hour
                summaries.append(s)
            if i % 20 == 0 or i == len(picked):
                say(f"  summarised {i} of {len(picked)}")
    SUMMARIES.write_text(json.dumps(summaries, indent=1, ensure_ascii=False), encoding="utf-8")
    return summaries


def group_threads(srv, summaries, me, names, workers):
    say(f"Grouping {len(summaries)} summaries into threads...")
    found = []
    batch = 40
    batches = [summaries[i:i + batch] for i in range(0, len(summaries), batch)]

    def group(chunk):
        items = "\n".join(f"{n}. [{s.get('kind', 'other')}] {s.get('topic', '')} - {s.get('arc', '')}"
                          + (f" (life: {'; '.join(s.get('life_facts') or [])})" if s.get("life_facts") else "")
                          for n, s in enumerate(chunk, 1))
        return chunk, srv.ask(GROUP_SYSTEM.format(me=me), GROUP_USER.format(me=me, items=items), max_tokens=2500)

    with ThreadPoolExecutor(workers) as pool:
        for chunk, out in pool.map(group, batches):
            for t in out.get("threads", []) if isinstance(out.get("threads"), list) else []:
                nums = _numbers(t.get("items"), len(chunk))
                if len(nums) < 2 or not t.get("title"):
                    continue
                found.append({"title": str(t["title"]), "kind": str(t.get("kind", "life")),
                              "facts": str(t.get("facts", "")), "support": len(nums),
                              "hours": [chunk[n - 1]["hour"] for n in nums]})
    say(f"  {len(found)} threads in {len(batches)} batches; merging...")
    if not found:
        return []
    items = "\n".join(f"{n}. [{t['kind']}] {t['title']} - {t['facts']} (seen {t['support']}x)"
                      for n, t in enumerate(found, 1))
    out = srv.ask(GROUP_SYSTEM.format(me=me), MERGE_USER.format(me=me, items=items, limit=30), max_tokens=3000)
    merged = []
    for t in out.get("threads", []) if isinstance(out.get("threads"), list) else []:
        src = [found[n - 1] for n in _numbers(t.get("from"), len(found))]
        if not t.get("title"):
            continue
        support = sum(s["support"] for s in src) or 2
        hours = [h for s in src for h in s["hours"]]
        kind = t.get("kind") if t.get("kind") in ("life", "bit", "roleplay", "opener") else "life"
        merged.append({"title": names.hide(str(t["title"])), "kind": kind,
                       "facts": names.hide(str(t.get("facts", ""))),
                       "beats": [names.hide(str(b)) for b in (t.get("beats") or [])][:4] if kind == "life" else [],
                       "support": support, "when": part_of_day(hours)})
    merged.sort(key=lambda t: -t["support"])
    for t in merged:
        t["id"] = hashlib.sha1((t["kind"] + t["title"].lower()).encode()).hexdigest()[:12]
    return merged


# ---- the run ----------------------------------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default=str(SOURCE))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--months", type=int, default=12, help="how far back from the newest message (default 12)")
    ap.add_argument("--model", default="qwen3-4b-instruct", help="a folder in Local Storage/LLM Models/models")
    ap.add_argument("--engine", default="", help="cuda or vulkan (default: whichever is there, cuda first)")
    ap.add_argument("--sessions", type=int, default=300, help="how many conversations to summarise")
    ap.add_argument("--kinds", default="general,roleplay", help="which kinds of conversation to summarise")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--no-model", action="store_true", help="the style card only")
    ap.add_argument("--reuse", action="store_true", help="regroup the summaries kept from the last run")
    args = ap.parse_args(argv)
    started = time.time()
    say(f"Reading {Path(args.source).name}...")
    data = json.load(open(args.source, encoding="utf-8"))
    me_id = f"user{data['personal_information']['user_id']}"
    me = you()
    chats = [c for c in data.get("chats", {}).get("list", []) if c.get("type") == "personal_chat"]
    newest = max((int(m.get("date_unixtime") or 0) for c in chats for m in c.get("messages", [])[-1:]), default=0)
    since = newest - args.months * 30 * 86400
    names = Names([c.get("name") for c in chats] + [me])
    convs = []
    for chat in chats:
        prev = None
        for rows in sessions(chat, me_id):
            gap = rows[0][0] - prev["rows"][-1][0] if prev is not None else BREAK
            if prev is not None:
                prev["gap_after"] = gap
            prev = {"rows": rows, "gap_before": gap}
            if rows[0][0] < since or sum(1 for r in rows if r[1]) < 2:
                continue
            convs.append(prev)
    del data
    say(f"{len(convs)} conversations since {time.strftime('%B %Y', time.localtime(since))}.")
    style = style_card(convs, names)
    style["sessions"] = len(convs)
    style["since"] = time.strftime("%B %Y", time.localtime(since))
    say(f"Style card: {len(style['openers'])} openers, {len(style['closers'])} closers, "
        f"{len(style['habits'])} habits.")
    threads = []
    if not args.no_model:
        kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
        pool = [c for c in convs if not kinds or content.kind(
            [{"role": "assistant" if m else "user", "content": t} for _ts, m, t in c["rows"]]) in kinds]
        srv = Server(args.model, args.engine, max(1, args.parallel))
        try:
            summaries = None
            if args.reuse:
                try:
                    summaries = json.loads(SUMMARIES.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    say("No summaries kept from before; summarising.")
            if not summaries:
                summaries = summarise(srv, pool, me, names, args.sessions, max(1, args.parallel))
            threads = group_threads(srv, summaries, me, names, max(1, args.parallel))
        finally:
            srv.stop()
    out = Path(args.out)
    previous = {}
    try:
        previous = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    if args.no_model and previous.get("threads"):
        threads = previous["threads"]                       # a style-only run keeps the threads found before
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"built": time.strftime("%Y-%m-%d %H:%M"), "source": "Telegram",
                               "months": args.months, "model": "" if args.no_model else args.model,
                               "style": style, "threads": threads}, indent=1, ensure_ascii=False),
                   encoding="utf-8")
    say(f"Done in {int(time.time() - started)} s: {len(threads)} threads and the style card in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
