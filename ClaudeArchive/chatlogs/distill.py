"""The Log Distiller: what the chat log archive says about how people talked, as numbers - never as quotes.

It reads the index (Text Logs/_Index/chatlogs.sqlite, read-only) and writes Text Logs/_Distilled/:
  culture.json      each service, and each service by year: message length, capitals and punctuation, emoticons,
                    chat shorthand, roleplay emotes (and the verbs in them), bursts, reply times, busy hours; topics
  archetypes.json   voice archetypes: groups of people who typed alike, each described only by its averages and the
                    habits its members share - the raw material for giving a fictional resident a steady voice
  you.json          how people talked with you: how chats opened and closed, what you were called, how fast they
                    answered - and how you write
  report.md         all of it, readable

Bots and system lines (file servers, scripted objects, "has quit", "user not online") are left out: a speaker whose
messages are mostly repeats is treated as a bot. Adult words are kept out of topics and emote verbs.

Privacy: nothing is quoted. A word, phrase, emoticon, greeting or topic is only kept if at least MIN_PEOPLE different
people used it, and every archetype is the average of at least MIN_PEOPLE people.

    python -m chatlogs.distill            (from ClaudeArchive)"""
import json
import math
import random
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from .index import db_path, norm_name

OUT_DIR = "_Distilled"
MIN_PEOPLE = 15                  # how many different people must share something before it's kept
ARCHETYPE_MIN_MESSAGES = 400     # people with this much to go on are grouped into archetypes
ARCHETYPES = 12
SESSION_GAP = 30 * 60            # a quiet half hour ends a conversation
BURST_GAP = 60                   # messages within a minute of each other, from the same side, are one burst
REPLY_CAP = 30 * 60

EMOTICON = re.compile(r"(?<![\w/])(?:[:;=8][-o^'`]?[)(DPpOo3*|\\/\]\[@$#]+|\^[_.\-~]?\^|[xX]D+|<3+|[oO0][_.][oO0]"
                      r"|[>][._][<]|[TQ][_.][TQ]|[oOuU][wW][oOuU]|:'\(|\(:|\(=|-_-)(?![\w])")
EMOTE = re.compile(r"^\s*/me\b|^\s*\*[^*\s][^*]{1,80}\*|^\s*::[^:]{2,80}::|\s\*[^*\s][^*]{1,60}\*")
WORD = re.compile(r"[a-z][a-z']{1,24}")
URL = re.compile(r"https?://|www\.", re.I)
REPEAT = re.compile(r"([a-z])\1{2,}")
SHORTHAND = {"lol", "lmao", "lmfao", "rofl", "roflmao", "brb", "bbl", "bbs", "afk", "omg", "omfg", "ttyl", "btw",
             "imo", "imho", "np", "ty", "thx", "tyvm", "k", "kk", "u", "ur", "r", "y", "cuz", "cus", "wat", "nvm",
             "idk", "jk", "ikr", "gtg", "g2g", "nm", "wb", "hehe", "heh", "haha", "hah", "teh", "pls", "plz",
             "srsly", "tho", "wtf", "ftw", "ppl", "gonna", "wanna", "dunno", "yea", "ya", "yup", "nope", "mmhm",
             "murr", "rawr", "yay", "aww", "awww", "hiya", "heya", "sup", "o.o", "x3", "<3", "*hugs*"}
GREETINGS = {"hi", "hey", "hello", "heya", "hiya", "yo", "sup", "howdy", "morning", "mornin", "evening", "afternoon",
             "hai", "hay", "heyy", "hii", "ello", "greetings", "wb", "*hugs*", "*glomps*", "*pounces*"}
STOP = set("""the and you that for are with this have was but not your what all just can about there they them
then than out get got like one when will would could should yeah yes its it's i'm im don't dont that's thats know
going been some how him her his she he who why where which were did does doing done from into over more much very
really think make made too also our only well any back now see say said way ok okay lol haha hehe what's here
gonna wanna let's lets let i'll ill i've ive you're youre we're were they're theyre can't cant didn't didnt won't
wont isn't isnt aren't arent wasn't wasnt hey hi hello yea yup nope maybe though thing things stuff something
anything nothing everything someone anyone everyone time day night today tonight tomorrow yesterday good bad nice
cool sure right still even just yeah mean try trying want need take come came go went goes off them those these
other another again always never ever every each lot little big great sorry thanks thank please because cause
cuz while after before since until around through under down being ill mmm hmm hmmm umm uhh ahh heh lmao omg brb
afk gtg btw rofl wtf idk nvm hah hahaha hahah heheh ttyl</""".split())
EXPLICIT = set("""yiff yiffing yiffy sex sexy cock dick penis pussy cum cumming fuck fucking fucked fucker shit
porn horny boobs tits ass anal knot knotting murr sheath moans moan moaning humps humping hump suck sucks sucking
licks lick licking strokes stroke stroking thrust thrusts thrusting grinds grinding naked nude nipple nipples
balls butt rump tailhole breed breeding mounts mounting climax orgasm lust lustful arousal aroused erect
throbbing pants panting squeezes squeezing rubbing rubs tight tightly deeply deep slides inside wet
spank spanks spanking bite bites biting nips gropes grope groping fondles fondling""".split())
SYSTEM = re.compile(r"has (quit|joined|left)|is now known as|user (is )?not online|offline message|auto-?reply|"
                    r"^\*\*\*|^-[a-z]+-|^\[[^\]]*\]|xdcc|#\d+\s+\d+x|\bdelivered\b|\binventory\b|\bsession\b|"
                    r"\bbytes\b|\bobject\b|\bscript|\bpong\b|\bping\b|\bmotd\b|\bquit\b.*\(", re.I)
BOT_NAME = re.compile(r"bot\b|serv\b|xdcc|^global$|^ircop|^\*|^-|chanserv|nickserv|memoserv|operserv|hostserv|"
                      r"botserv|seen$|^trivia|^quiz", re.I)
BOT_REPEATS = 0.45               # a speaker with fewer than this share of different messages is a bot
SYSTEM_WORDS = set("""gets current file files record sends queues various served active offered motd password
login packs bandwidth users sysreset triggers rcps port accessed addendum usage portfolio quality genus delivered
stored commands attached session summary functions bytes items owner joined quit seconds timeout peer reset read
ping pong channel server nick mode topic kicked banned offline online view ding""".split())
HOURS = 24


def _new_stats():
    return Counter()


def message_features(text):
    """The countable habits of one message."""
    f = {}
    letters = [c for c in text if c.isalpha()]
    f["chars"] = len(text)
    words = text.split()
    f["words"] = len(words)
    if letters:
        upper = sum(c.isupper() for c in letters)
        f["lowercase"] = int(upper == 0)
        f["allcaps"] = int(len(letters) >= 4 and upper == len(letters))
        f["capital_start"] = int(text.lstrip()[:1].isupper())
    f["end_punct"] = int(text.rstrip()[-1:] in ".!?")
    f["question"] = int("?" in text)
    f["exclaim"] = int("!" in text)
    f["ellipsis"] = int("..." in text)
    f["url"] = int(bool(URL.search(text)))
    emo = EMOTICON.findall(text)
    f["emoticon"] = int(bool(emo))
    f["emote"] = int(bool(EMOTE.search(text)))
    low = text.lower()
    toks = re.findall(r"[a-z0-9<>*'.]+", low)
    f["shorthand"] = int(any(t.strip(".") in SHORTHAND for t in toks))
    f["stretched"] = int(bool(REPEAT.search(low)))
    return f, emo, [t.strip(".") for t in toks if t.strip(".") in SHORTHAND]


class People:
    """Counts that remember how many different people used each thing (up to MIN_PEOPLE, to keep it small)."""

    def __init__(self):
        self.count = Counter()
        self.who = {}

    def add(self, key, person):
        self.count[key] += 1
        s = self.who.get(key)
        if s is True:
            return
        if s is None:
            s = self.who[key] = set()
        s.add(person)
        if len(s) >= MIN_PEOPLE:
            self.who[key] = True

    def shared(self, top=None):
        """[(key, count)] for things enough people used, most used first."""
        out = [(k, c) for k, c in self.count.most_common() if self.who.get(k) is True]
        return out[:top] if top else out


def collapse(word):
    return REPEAT.sub(r"\1\1", word)


def phrase(text, words=3):
    text = re.sub(r"https?://\S+|www\.\S+", "<link>", text, flags=re.I)
    toks = re.findall(r"<link>|[a-z']+|<3|:\)|:d|:p|:3|\^\^|\*[a-z]+\*", text.lower())
    return " ".join(collapse(t) for t in toks[:words])


def summarise(stats):
    """Averages from a Counter of feature totals (with "n" messages)."""
    n = stats["n"] or 1
    out = {"messages": stats["n"], "avg_chars": round(stats["chars"] / n, 1), "avg_words": round(stats["words"] / n, 1)}
    for k in ("lowercase", "allcaps", "capital_start", "end_punct", "question", "exclaim", "ellipsis", "url",
              "emoticon", "emote", "shorthand", "stretched"):
        out[k] = round(stats[k] / n, 3)
    if stats["bursts"]:
        out["avg_burst"] = round(stats["burst_msgs"] / stats["bursts"], 2)
        out["multi_burst"] = round(stats["multi_bursts"] / stats["bursts"], 3)
    if stats["replies"]:
        out["median_reply_s"] = stats.get("median_reply_s")
        out["avg_reply_s"] = round(stats["reply_s"] / stats["replies"], 1)
    return out


# ---- the pass over the archive ------------------------------------------------------------------------------
def distill(root, log=lambda m: print(m, flush=True)):
    root = Path(root)
    src = db_path(root)
    if not src.exists():
        raise FileNotFoundError(f"No index at {src} - build it first (python -m chatlogs.index)")
    db = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    total = db.execute("select count(*) from messages").fetchone()[0]
    log(f"Distilling {total:,} messages...")
    own = set((db.execute("select value from info where key='own_names'").fetchone() or [""])[0].split())
    names = set()                                       # everyone's names, kept out of topics and phrases
    for (c,) in db.execute("select distinct contact from messages"):
        names.update(WORD.findall((c or "").lower()))
    for (s,) in db.execute("select distinct speaker from messages"):
        names.update(WORD.findall((s or "").lower()))
    names |= own
    bots = set()
    for svc, sp, n, distinct in db.execute("select service, speaker, count(*), count(distinct text) from messages "
                                            "where outgoing=0 group by service, speaker"):
        if BOT_NAME.search(sp or "") or (n >= 150 and distinct / n < BOT_REPEATS):
            bots.add((svc, norm_name(sp or "")))
    log(f"  {len(bots):,} bots and scripted speakers left out")

    service = defaultdict(_new_stats)                   # service -> totals
    service_year = defaultdict(_new_stats)              # (service, year) -> totals
    service_kind = defaultdict(_new_stats)              # (service, "1:1"/"room") -> totals
    hours = defaultdict(Counter)                        # service -> hour of day -> messages
    emoticons = defaultdict(People)                     # service -> emoticon
    shorthand = defaultdict(People)
    topics = defaultdict(People)                        # service -> word
    emote_verbs = defaultdict(People)                   # service -> the first word of a roleplay emote
    year_topics = defaultdict(People)                   # (service, year) -> word
    person = defaultdict(_new_stats)                    # (service, speaker) -> totals
    person_emo = defaultdict(Counter)
    person_short = defaultdict(Counter)
    person_replies = defaultdict(list)
    you = _new_stats()
    you_replies = []
    their_replies = []
    openers_them, openers_you = People(), People()
    closers_them, closers_you = People(), People()
    called = People()                                   # words right after a greeting, in their openers
    room_address = Counter()                            # rooms: messages that name someone / all

    q = db.execute("select service, account, contact, room, ts, approx, outgoing, speaker, text from messages "
                   "order by service, account, contact, ts, id")
    conv = None
    last = None                                         # (ts, outgoing, speaker) of the previous message here
    burst = None                                        # (who, count, ts)
    session_first = True
    session_last = None
    session_count = 0
    room_speakers = set()
    done = 0
    started = time.time()

    def end_burst():
        if burst is None:
            return
        who, n_, _ts = burst
        tgt = you if who == "@you" else person[who]
        tgt["bursts"] += 1
        tgt["burst_msgs"] += n_
        tgt["multi_bursts"] += int(n_ > 1)

    def end_session():
        if session_last is None or session_count < 4:
            return
        out_, text_, contact_ = session_last
        p = phrase(text_)
        if p:
            (closers_you if out_ else closers_them).add(p, contact_)

    for svc, account, contact, room, ts, approx, outgoing, speaker, text in q:
        done += 1
        if done % 250000 == 0:
            log(f"  {done:,} / {total:,}  ({time.time() - started:.0f}s)")
        text = (text or "").strip()
        if not text:
            continue
        if SYSTEM.search(text):
            continue
        if not outgoing and (svc, norm_name(speaker or contact or "")) in bots:
            continue
        key = (svc, account, contact)
        if key != conv:
            end_burst()
            end_session()
            conv, last, burst, session_first, session_last, session_count = key, None, None, True, None, 0
            if room:
                room_speakers = {norm_name(s) for (s,) in db.execute(
                    "select distinct speaker from messages where service=? and account=? and contact=? limit 400",
                    key)} - {""}
        f, emo, short = message_features(text)
        year = time.strftime("%Y", time.gmtime(ts)) if ts else "?"
        sp = norm_name(speaker or contact or "")
        who = "@you" if outgoing else (svc, sp or norm_name(contact or ""))
        kind = "room" if room else "1:1"
        for bucket in (service[svc], service_year[(svc, year)], service_kind[(svc, kind)],
                       you if outgoing else person[who]):
            bucket["n"] += 1
            for k, v in f.items():
                bucket[k] += v
        if not approx and ts:
            hours[svc][time.gmtime(ts).tm_hour] += 1
        pid = who if outgoing else who[1]
        if not outgoing:
            for e in emo:
                emoticons[svc].add(e, pid)
                person_emo[who][e] += 1
            for s in short:
                shorthand[svc].add(s, pid)
                person_short[who][s] += 1
            if f["emote"]:                              # an action: its verb is vocabulary, not a topic
                m = re.search(r"(?:/me\s+|\*|::)\s*([a-z]+)", text.lower())
                if m:
                    verb = collapse(m.group(1))
                    if verb not in EXPLICIT and verb not in names and len(verb) > 2:
                        emote_verbs[svc].add(verb, pid)
            else:
                for w in set(WORD.findall(URL.sub(" ", text.lower()))):
                    w = collapse(w)
                    if len(w) < 4 or w in STOP or w in names or w in EXPLICIT or w in SYSTEM_WORDS:
                        continue
                    topics[svc].add(w, pid)
                    year_topics[(svc, year)].add(w, pid)
        if room and not outgoing:
            room_address["all"] += 1
            first = text.split()[0].lower().rstrip(":,") if text.split() else ""
            if first in room_speakers or any(norm_name(t.rstrip(":,")) in room_speakers for t in text.split()[:1]):
                room_address["named"] += 1
        # one-to-one rhythm: bursts, replies, how conversations open and close
        if not room and ts and not approx:
            gap = ts - last[0] if last else None
            if gap is None or gap > SESSION_GAP:
                end_burst()
                end_session()
                burst = None
                session_first = True
                session_count = 0
            if session_first:
                p = phrase(text)
                if p:
                    (openers_you if outgoing else openers_them).add(p, contact)
                if not outgoing:
                    toks = re.findall(r"[a-z*']+", text.lower())
                    for i, t in enumerate(toks[:-1]):
                        if collapse(t) in GREETINGS and len(toks[i + 1]) > 1:
                            nxt = collapse(toks[i + 1])
                            if nxt not in GREETINGS and nxt not in STOP and len(nxt) > 2 and nxt not in (
                                    "there", "again", "how", "what", "you", "all", "guys", "everyone"):
                                called.add(nxt, contact)
                            break
                session_first = False
            session_last = (outgoing, text, contact)
            session_count += 1
            if last is not None and gap is not None and gap <= SESSION_GAP:
                same_side = (last[1] == outgoing)
                if same_side and burst is not None and burst[0] == who and ts - burst[2] <= BURST_GAP:
                    burst = (who, burst[1] + 1, ts)
                else:
                    end_burst()
                    burst = (who, 1, ts)
                if not same_side and gap <= REPLY_CAP:
                    if outgoing:
                        you["replies"] += 1
                        you["reply_s"] += gap
                        you_replies.append(gap)
                    else:
                        tgt = person[who]
                        tgt["replies"] += 1
                        tgt["reply_s"] += gap
                        if len(person_replies[who]) < 400:
                            person_replies[who].append(gap)
                        their_replies.append(gap)
            else:
                end_burst()
                burst = (who, 1, ts)
            last = (ts, outgoing, sp)
    end_burst()
    end_session()
    log(f"  read everything in {time.time() - started:.0f}s; summarising...")

    def median(xs):
        if not xs:
            return None
        xs = sorted(xs)
        return xs[len(xs) // 2]

    # ---- culture ----
    culture = {"services": {}, "min_people": MIN_PEOPLE}
    for svc, st in sorted(service.items(), key=lambda kv: -kv[1]["n"]):
        if st["n"] < 2000:
            continue
        total_h = sum(hours[svc].values()) or 1
        entry = summarise(st)
        entry["kinds"] = {k: summarise(service_kind[(svc, k)]) for k in ("1:1", "room")
                          if service_kind[(svc, k)]["n"] >= 500}
        entry["busy_hours_utc"] = [h for h, _c in hours[svc].most_common(6)]
        entry["hour_share_utc"] = [round(hours[svc][h] / total_h, 3) for h in range(HOURS)]
        entry["emoticons"] = emoticons[svc].shared(25)
        entry["shorthand_words"] = shorthand[svc].shared(25)
        entry["topics"] = _distinctive(topics[svc], topics, svc, 60)
        entry["emote_verbs"] = emote_verbs[svc].shared(40)
        entry["years"] = {}
        for (s2, y), yst in sorted(service_year.items()):
            if s2 == svc and yst["n"] >= 1000:
                ye = summarise(yst)
                ye["topics"] = _distinctive(year_topics[(svc, y)], year_topics, (svc, y), 25)
                entry["years"][y] = ye
        culture["services"][svc] = entry
    if room_address["all"]:
        culture["rooms_named_someone"] = round(room_address["named"] / room_address["all"], 3)

    # ---- archetypes ----
    archetypes = _archetypes(person, person_emo, person_short, person_replies, emoticons, shorthand, log)

    # ---- you ----
    you["median_reply_s"] = median(you_replies)
    them = _new_stats()
    for p_, st in person.items():
        for k, v in st.items():
            if isinstance(v, (int, float)):
                them[k] += v
    them["median_reply_s"] = median(their_replies)
    yours = {"how_you_write": summarise(you), "how_they_wrote_to_you": summarise(them),
             "their_openers": openers_them.shared(40), "your_openers": openers_you.shared(25),
             "their_closers": closers_them.shared(30), "your_closers": closers_you.shared(25),
             "what_they_called_you": [(w, c) for w, c in called.shared(40) if w not in EXPLICIT],
             "median_reply_s": {"them": median(their_replies), "you": median(you_replies)}}
    return culture, archetypes, yours


def _distinctive(people, all_people, own_key, top):
    """The words this place used much more than everywhere else (and that enough people used)."""
    shared = people.shared()
    if not shared:
        return []
    total = sum(c for _w, c in shared) or 1
    overall = Counter()
    for k, p in all_people.items():
        for w, c in p.count.items():
            overall[w] += c
    grand = sum(overall.values()) or 1
    scored = []
    for w, c in shared:
        if c < 20:
            continue
        here = c / total
        everywhere = overall[w] / grand
        scored.append((here * math.log(here / everywhere + 1.0), w, c))
    scored.sort(reverse=True)
    return [(w, c) for _s, w, c in scored[:top]]


FEATURES = ["avg_words", "lowercase", "capital_start", "end_punct", "question", "exclaim", "ellipsis", "emoticon",
            "emote", "shorthand", "stretched", "allcaps", "avg_burst", "median_reply_s"]
LABELS = {"avg_words": ("writes long messages", "writes short messages"),
          "lowercase": ("all lowercase", "uses capitals"),
          "capital_start": ("starts sentences with a capital", "rarely capitalises"),
          "end_punct": ("ends with punctuation", "rarely punctuates"),
          "question": ("asks lots of questions", "rarely asks questions"),
          "exclaim": ("exclamation-happy!", "calm, few exclamations"),
          "ellipsis": ("trails off a lot...", None),
          "emoticon": ("emoticon-heavy", "hardly any emoticons"),
          "emote": ("roleplay emotes (*hugs*)", None),
          "shorthand": ("chat shorthand (lol, brb, u)", "spells things out"),
          "stretched": ("stretches words (sooo, heyyy)", None),
          "allcaps": ("SHOUTS sometimes", None),
          "avg_burst": ("sends rapid bursts of short messages", "one message at a time"),
          "median_reply_s": ("takes their time replying", "replies fast")}


def _archetypes(person, person_emo, person_short, person_replies, emoticons, shorthand, log):
    people = []
    for who, st in person.items():
        if st["n"] < ARCHETYPE_MIN_MESSAGES:
            continue
        s = summarise(st)
        reps = sorted(person_replies.get(who) or [])
        s["median_reply_s"] = reps[len(reps) // 2] if reps else None
        people.append((who, s))
    log(f"  {len(people):,} people with {ARCHETYPE_MIN_MESSAGES}+ messages")
    if len(people) < MIN_PEOPLE * 2:
        return {"archetypes": [], "note": "not enough people to group"}
    # standardise the features (filling gaps with the average)
    cols = {}
    for f in FEATURES:
        vals = [s.get(f) for _w, s in people if s.get(f) is not None]
        mean = sum(vals) / len(vals) if vals else 0.0
        sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals)) if vals else 1.0
        cols[f] = (mean, sd or 1.0)
    vecs = [[((s.get(f) if s.get(f) is not None else cols[f][0]) - cols[f][0]) / cols[f][1] for f in FEATURES]
            for _w, s in people]
    groups = _kmeans(vecs, ARCHETYPES)
    # small groups join their nearest big one
    sizes = Counter(groups)
    centres = _centres(vecs, groups)
    big = [g for g in centres if sizes[g] >= MIN_PEOPLE]
    for i, g in enumerate(groups):
        if sizes[g] < MIN_PEOPLE:
            groups[i] = min(big, key=lambda b: _dist(vecs[i], centres[b]))
    centres = _centres(vecs, groups)
    out = []
    for n_, g in enumerate(sorted(set(groups), key=lambda g: -groups.count(g))):
        members = [i for i, x in enumerate(groups) if x == g]
        avg = {}
        for f in FEATURES:
            vals = [people[i][1].get(f) for i in members if people[i][1].get(f) is not None]
            avg[f] = round(sum(vals) / len(vals), 3) if vals else None
        z = centres[g]
        traits = []
        for f, zv in sorted(zip(FEATURES, z), key=lambda t: -abs(t[1])):
            hi, lo = LABELS[f]
            if zv > 0.55 and hi:
                traits.append(hi)
            elif zv < -0.55 and lo:
                traits.append(lo)
        # habits the members share (and that enough people anywhere use)
        emo, short = Counter(), Counter()
        for i in members:
            who = people[i][0]
            for e, c in person_emo[who].items():
                emo[e] += c
            for s, c in person_short[who].items():
                short[s] += c
        ok_emo = {e for svc in emoticons.values() for e, _c in svc.shared()}
        ok_short = {s for svc in shorthand.values() for s, _c in svc.shared()}
        services = Counter(people[i][0][0] for i in members)
        out.append({"id": f"A{n_ + 1:02d}", "people": len(members), "traits": traits[:6] or ["middle of the road"],
                    "averages": avg, "services": services.most_common(),
                    "emoticons": [(e, c) for e, c in emo.most_common(40) if e in ok_emo][:10],
                    "shorthand": [(s, c) for s, c in short.most_common(40) if s in ok_short][:10]})
    return {"archetypes": out, "features": FEATURES, "min_people": MIN_PEOPLE,
            "from_people": len(people)}


def _dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _centres(vecs, groups):
    sums, counts = {}, Counter(groups)
    for v, g in zip(vecs, groups):
        s = sums.setdefault(g, [0.0] * len(v))
        for k, x in enumerate(v):
            s[k] += x
    return {g: [x / counts[g] for x in s] for g, s in sums.items()}


def _kmeans(vecs, k, rounds=40, seed=7):
    rng = random.Random(seed)
    centres = [vecs[rng.randrange(len(vecs))]]
    while len(centres) < k:                             # k-means++ start
        d = [min(_dist(v, c) for c in centres) for v in vecs]
        total = sum(d) or 1
        r = rng.random() * total
        acc = 0.0
        for v, dv in zip(vecs, d):
            acc += dv
            if acc >= r:
                centres.append(v)
                break
    groups = [0] * len(vecs)
    for _ in range(rounds):
        new = [min(range(k), key=lambda g: _dist(v, centres[g])) for v in vecs]
        if new == groups:
            break
        groups = new
        cs = _centres(vecs, groups)
        centres = [cs.get(g, centres[g]) for g in range(k)]
    return groups


# ---- writing it down ------------------------------------------------------------------------------------------
def report(culture, archetypes, yours):
    def pct(v):
        return "-" if v is None else f"{v * 100:.0f}%"

    def secs(v):
        return "-" if v is None else (f"{v:.0f}s" if v < 90 else f"{v / 60:.1f} min")

    lines = ["# What the chat logs say", "",
             f"Everything here is counted, never quoted, and only kept if at least {MIN_PEOPLE} different people "
             "shared it.", "", "## Services", ""]
    lines.append("| Service | Messages | Avg words | lowercase | punctuated | emoticons | shorthand | emotes | burst |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for svc, e in culture["services"].items():
        lines.append(f"| {svc} | {e['messages']:,} | {e['avg_words']} | {pct(e['lowercase'])} | {pct(e['end_punct'])} "
                     f"| {pct(e['emoticon'])} | {pct(e['shorthand'])} | {pct(e['emote'])} | {e.get('avg_burst', '-')} |")
    for svc, e in culture["services"].items():
        lines += ["", f"### {svc}", "",
                  "Emoticons: " + ", ".join(f"`{x}`" for x, _c in e["emoticons"][:15]),
                  "", "Shorthand: " + ", ".join(f"`{x}`" for x, _c in e["shorthand_words"][:15]),
                  "", "Distinctive words: " + ", ".join(w for w, _c in e["topics"][:40]),
                  "", "Emote verbs: " + ", ".join(f"*{w}*" for w, _c in e["emote_verbs"][:25]),
                  "", "Busiest hours (UTC): " + ", ".join(str(h) for h in e["busy_hours_utc"])]
        if e["years"]:
            lines += ["", "| Year | Messages | Avg words | lowercase | emoticons | distinctive words |",
                      "|---|---|---|---|---|---|"]
            for y, ye in e["years"].items():
                lines.append(f"| {y} | {ye['messages']:,} | {ye['avg_words']} | {pct(ye['lowercase'])} | "
                             f"{pct(ye['emoticon'])} | {', '.join(w for w, _c in ye['topics'][:8])} |")
    lines += ["", "## Voice archetypes", "",
              f"From {archetypes.get('from_people', 0):,} people with {ARCHETYPE_MIN_MESSAGES}+ messages, grouped by "
              "how they typed. Each is an average of everyone in it.", ""]
    for a in archetypes.get("archetypes", []):
        av = a["averages"]
        lines += [f"### {a['id']} - {'; '.join(a['traits'])}  ({a['people']} people)", "",
                  f"Avg {av['avg_words']} words, lowercase {pct(av['lowercase'])}, punctuated {pct(av['end_punct'])}, "
                  f"emoticons {pct(av['emoticon'])}, shorthand {pct(av['shorthand'])}, emotes {pct(av['emote'])}, "
                  f"bursts of {av['avg_burst'] or '-'}, replies in {secs(av['median_reply_s'])}.",
                  "", "Emoticons: " + (", ".join(f"`{x}`" for x, _c in a["emoticons"]) or "-"),
                  "", "Shorthand: " + (", ".join(f"`{x}`" for x, _c in a["shorthand"]) or "-"),
                  "", "Mostly on: " + ", ".join(f"{s} ({c})" for s, c in a["services"][:4]), ""]
    h, t = yours["how_you_write"], yours["how_they_wrote_to_you"]
    lines += ["## You and them", "",
              f"They wrote {t['avg_words']} words a message on average ({pct(t['lowercase'])} lowercase, "
              f"{pct(t['emoticon'])} with emoticons); you wrote {h['avg_words']} ({pct(h['lowercase'])} lowercase, "
              f"{pct(h['emoticon'])} with emoticons).",
              f"Median reply: them {secs(yours['median_reply_s']['them'])}, you {secs(yours['median_reply_s']['you'])}.",
              "", "How they opened chats: " + ", ".join(f"`{p}`" for p, _c in yours["their_openers"][:30]),
              "", "How you opened chats: " + ", ".join(f"`{p}`" for p, _c in yours["your_openers"][:20]),
              "", "How they signed off: " + ", ".join(f"`{p}`" for p, _c in yours["their_closers"][:25]),
              "", "What they called you after a greeting: " +
              ", ".join(f"`{w}`" for w, _c in yours["what_they_called_you"][:30]), ""]
    return "\n".join(lines)


def main(argv=None):
    from .index import __file__ as index_file
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0]) if argv else Path(index_file).resolve().parents[2] / "Local Storage" / "Text Logs"
    culture, archetypes, yours = distill(root)
    out = root / OUT_DIR
    out.mkdir(exist_ok=True)
    built = time.strftime("%Y-%m-%d %H:%M")
    for name, data in (("culture", culture), ("archetypes", archetypes), ("you", yours)):
        data = dict(data, built=built)
        (out / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "report.md").write_text(report(culture, archetypes, yours), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

