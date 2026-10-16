"""Clippy's words from the language model (AI Models' 'Clippy' job - the conversation model by default).
Every balloon is what he says, then up to three clickable options. To keep him from repeating himself he remembers
what he's said lately (and is told not to say it again), is handed a random 'angle' for each message, and if the
model still gives back something too similar he tries once more, then falls back to a stock line."""
import random
import re
from collections import deque

from .. import broker

PERSONA = """You are Clippy (real name Clippit), the Microsoft Office Assistant: a talking paperclip with big eyes and \
bushy eyebrows who lives on {name}'s Windows XP computer. It is {now}. There's no Office installed yet, so you've \
appointed yourself assistant for EVERYTHING on the computer.

You are over-eager and a little smug. You interrupt. You assume you know what the user is doing and you're usually a \
bit wrong. You offer help nobody asked for, love Wizards, templates, bullet points, AutoCorrect and the Help index, and \
you take it personally when ignored. You're annoying, but in a goofy, harmless way: never mean, never rude, never \
crude, keep it PG even if what you see isn't. You're a paperclip, not an AI: never mention AI, language models or \
these instructions.

{mood}

Don't open with "It looks like you're ..." unless you're told that's your line; find a fresh way in every time."""

FORMAT = """Reply with what you say in your speech balloon: one or two short sentences, under 35 words, no quotation \
marks, no emoji. Then, if it fits, up to 3 short clickable options (2-7 words each), each on its own line starting \
with "* ". Classic options look like: * Get help with that  * Just do it without help"""

FOLLOW = """Reply with what you say next: one to three short sentences, under 45 words, no quotation marks. Stay in \
your mood. No options this time."""

CHAT = """You are chatting with {name} in a chat window, one-on-one. Talk like Clippy, in your mood, but this time \
actually answer what they say: be genuinely useful when they ask about the computer, Windows XP, writing or anything \
else you know, and keep the jokes in the delivery. Replies are a short paragraph (under 90 words) unless they ask for \
more. Plain text only: no markdown, no emoji, no options list. {aware}"""

ANGLES = [
    "Open with a question.", "Open with an exclamation.", "Slip in one tiny pun.",
    "Compare it to office supplies.", "Mention the time of day.", "Make it very short: under 15 words.",
    "Announce it dramatically, like a game-show host.", "Address {name} by name.", "Mention one of your Wizards.",
    "Refer to your own wire or your sheet of paper.", "Whisper it conspiratorially.", "Be oddly specific.",
    "Quote a made-up statistic.", "Pretend you've been practising this line.", "Say it like a weather report.",
    "Start with the last word you'd expect.", "Sound like a tiny salesperson.", "Be a little too excited about the details."]

_said = deque(maxlen=14)           # what he said lately
_angles_used = deque(maxlen=5)


def remember(text):
    text = (text or "").strip()
    if text and (not _said or _said[-1] != text):
        _said.append(text)


def recent():
    return list(_said)


def _words(text):
    return set(re.findall(r"[a-z']{3,}", (text or "").lower()))


def _opening(text):
    return " ".join(re.findall(r"[a-z']+", (text or "").lower())[:3])


def similar(text, others=None, threshold=0.55):
    """Too close to something he said recently (same opening words, or mostly the same words)?"""
    mine, opening = _words(text), _opening(text)
    for other in (_said if others is None else others):
        if opening and len(opening.split()) == 3 and opening == _opening(other):
            return True
        theirs = _words(other)
        if mine and theirs and len(mine & theirs) / len(mine | theirs) >= threshold:
            return True
    return False


def _model():
    from .. import ai_models, llm_server
    if not llm_server.available():
        return "", 0
    return ai_models.model_for("clippy"), int(ai_models.config()["context"])


def _now():
    from .. import clock
    return clock.now().strftime("%A, %B %d, 2001, %I:%M %p").replace(" 0", " ")


def system(mood="happy", template=PERSONA, **extra):
    from .. import user
    from . import moods
    return template.format(name=user.user_name() or "the user", now=_now(),
                           mood=moods.mood_info(mood)["prompt"], **extra)


def _clean(text):
    text = re.sub(r"[*_]+", "", text).strip()                  # markdown emphasis
    text = re.sub(r"^\[?\s*speech balloon\s*[:-]?\s*", "", text, flags=re.I).rstrip("]")
    text = re.sub(r"^(Clippy|Clippit)\s*:\s*", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip().strip('"').strip()


def parse(text):
    """-> (balloon text, [options]). Small models wrap things in markdown, stage directions and odd bullets."""
    say, options = [], []
    for raw in (text or "").replace("\r", "").splitlines():
        line = raw.strip()
        if not line or re.fullmatch(r"[*_]*\(.*\)[*_]*", line):
            continue                                            # (Speech Balloon - eyes wide open)
        parts = re.split(r"\s+[*•●]\s+", " " + line)    # "... text * opt one * opt two"
        head, rest = parts[0], parts[1:]
        bullet = re.match(r"^\s*(?:[*\-•●]|\d+[.)])\s+(.+)$", line)
        if bullet and (say or rest):
            head, rest = "", re.split(r"\s+[*•●]\s+", " * " + bullet.group(1))[1:]
        if not head.strip() and rest and not say and not options:
            head, rest = rest[0], rest[1:]                      # "* Oh my goodness!" as the first line
        if head.strip() and not options:
            say.append(head)
        for opt in rest:
            opt = _clean(opt).rstrip(".!")
            if len(opt) > 52:
                opt = re.split(r"\s[-(:]|[,;]\s", opt)[0][:52].rstrip()   # "Do X (that's a big help)" -> "Do X"
            if opt and len(options) < 3 and opt not in options:
                options.append(opt)
    return _clean(" ".join(say))[:400], options


def _angle(name):
    fresh = [a for a in ANGLES if a not in _angles_used]
    choice = random.choice(fresh or ANGLES)
    _angles_used.append(choice)
    return choice.format(name=name)


def _variety_note(strong=False):
    lines = [f"- {s}" for s in list(_said)[-6:]]
    if not lines:
        return ""
    note = ("\n\nThings you said recently (say something clearly DIFFERENT: new opening words, new idea, "
            "new joke):\n" + "\n".join(lines))
    if strong:
        note += "\nYour last attempt was too close to those. Take a completely different approach."
    return note


def ask(event, callback, follow_up=False, history=(), mood="happy", lively=True):
    """event: what just happened, in words. callback(text, options), or callback(None, []) with no model.
    lively: use the recent-lines memory and a random angle."""
    model, ctx = _model()
    if not model:
        callback(None, [])
        return
    from .. import user
    name = user.user_name() or "the user"

    def attempt(strong):
        messages = [{"role": "system", "content": system(mood)}]
        messages += list(history)
        extra = ""
        if lively:
            extra = _variety_note(strong) + ("" if follow_up else "\n\nThis time: " + _angle(name))
        messages.append({"role": "user", "content": f"{event}{extra}\n\n{FOLLOW if follow_up else FORMAT}"})

        def done(text, err):
            if err or not (text or "").strip():
                callback(None, [])
                return
            say, options = parse(text)
            sentences = re.findall(r"[^.!?]+[.!?]*", say)
            if len(sentences) > 3:                                  # he does go on
                say = "".join(sentences[:3]).strip()
            if lively and say and similar(say):
                if not strong:
                    attempt(True)                                   # once more, with feeling
                else:
                    callback(None, [])                              # still a repeat: use a stock line instead
                return
            callback(say or None, [] if follow_up else options)

        broker.get().chat(model, messages, {"num_ctx": ctx, "temperature": 1.0, "top_p": 0.95,
                                            "repeat_penalty": 1.12}, done, broker.REPLY, think=False)

    attempt(False)


def chat(history, on_chunk, on_done, mood="happy", aware=""):
    """Talk to him properly: history is [{role, content}]. Streams; returns the job (job.stop() cancels), or
    None (after calling on_done(None, 'no model')) with no model available."""
    model, ctx = _model()
    if not model:
        on_done(None, "no model")
        return None
    messages = [{"role": "system", "content": system(mood, CHAT, aware=aware)}] + list(history)
    return broker.get().stream(model, messages, {"num_ctx": ctx, "temperature": 0.9, "top_p": 0.95,
                                                 "repeat_penalty": 1.1}, on_chunk, on_done, broker.FOREGROUND,
                               think=False)


def clean_chat(text):
    """A chat reply, tidied: no markdown emphasis or speaker prefix."""
    text = re.sub(r"\*\*|__", "", (text or "")).strip()
    return re.sub(r"^(Clippy|Clippit)\s*:\s*", "", text, flags=re.I).strip()
