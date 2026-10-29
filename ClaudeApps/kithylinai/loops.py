"""A model going round in circles: where its writing starts repeating itself, and the writing without the repeats.

A model asked for more than it knows how to write - one made from chat logs, asked to reflect at length - can fall
into a loop: the same sentence, or the same few, over and over until it runs out of room. Each answer it gives is in
front of it for the next, so a loop that's kept spreads.

A loop here is the same sentence, or the same few, said ROUNDS times in a row with nothing new between; what's kept
is everything before the second time. A refrain isn't a loop - a chorus after each verse (or twice at the end), a line
said again later - because something new comes between; nor is "hehe" or "I love you" said over (sentences shorter
than SHORT don't count). Sentences are split at . ! ? and line ends, and compared without case, punctuation or
doubled letters ("suppose" is "supose"). If it varies a line now and then, the loop is found a little later, but cut
from the same place."""
import re

SHORT = 15              # a sentence shorter than this (letters and spaces) is never counted as a repeat
ROUNDS = 3              # the same sentences this many times in a row: a loop

_SENTENCE = re.compile(r"[^.!?\n]+[.!?]*")


def _key(sentence):
    return re.sub(r"(.)\1+", r"\1", " ".join(re.findall(r"[a-z0-9]+", sentence.lower())))


def loop_at(text, finished=True):
    """Where text starts going round in circles - the start of its first repeat - or None.
    finished=False: it's still being written, so its last sentence, if it isn't finished yet, doesn't count."""
    text = text or ""
    found = list(_SENTENCE.finditer(text))
    if not finished and found and not found[-1].group().rstrip().endswith((".", "!", "?")) \
            and not text[found[-1].end():].startswith("\n"):
        found.pop()
    said, second, order, run, start = {}, {}, [], [], 0
    for m in found:
        key = _key(m.group())
        if len(key) < SHORT:
            continue
        order.append(key)
        said[key] = said.get(key, 0) + 1
        if said[key] == 1:
            run = []                            # (something new: whatever came round before wasn't a loop)
            continue
        second.setdefault(key, m.start())
        if not run:
            start = len(order) - 1
        run.append(key)
        cycle = set(run)
        just_before = set(order[max(0, start - len(cycle)):start])
        rounds = len(run) / len(cycle) + (just_before == cycle)     # (the first time counts if it came just before)
        if rounds >= ROUNDS:
            return min(second[k] for k in cycle)
    return None


def unloop(text):
    """The text without its loop (everything before the first repeat), or as it is if it hasn't one."""
    at = loop_at(text)
    return text if at is None else text[:at].rstrip()
