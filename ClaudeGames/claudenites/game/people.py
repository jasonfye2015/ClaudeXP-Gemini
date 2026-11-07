"""Thornwick's people, as a language model plays them: who each one is, how they talk, what they know of the town
and the Deep, and what they know of Claude (how deep he's been, how often he's fallen, what he's killed). The model
is told to answer in a sentence or three, in their own voice, and never to step out of it. When no model is there,
each has lines of their own (lines()), picked to fit."""
from . import data as D

PEOPLE = {
    "apothecary": {
        "who": "Hesper, Thornwick's apothecary: a thin, sharp-eyed woman of fifty who keeps a ledger of every potion she "
               "has ever sold and who it was for. Dry, practical, quietly fond of Claude and careful never to show it. "
               "She grumbles about prices and about fools who go down without enough red.",
        "sells": "health potions (red), mana potions (blue) and Scrolls of Return",
    },
    "wandwright": {
        "who": "Old Tamsin, the wandwright: hooded, stooped, older than anyone can remember, with a voice like dry "
               "leaves. Talks about wands as if they were living things that choose their mages. Gruff, fond of riddles, "
               "proud of her craft. She has made wands for every mage Thornwick ever had.",
        "sells": "wand bodies (birch, willow, ash, yew, bone, ironbark, crystal, emberwood, starsteel, heartwood) and the "
                 "parts set in them: cores of fire, frost, storm and venom, lenses, splitting prisms, focusing rings, "
                 "quickening runes, seekers' eyes, rebounding bands and piercing thorns",
    },
    "outfitter": {
        "who": "Bramwell, the outfitter: a big, cheerful man, a soldier once, who sews now and talks about cloth, stitches "
               "and how a good boot saves more lives than a sword. Warm, a little loud, given to old soldiers' sayings.",
        "sells": "hats, robes, gloves, boots, rings and amulets",
    },
    "sage": {
        "who": "Mother Wren, the sage: calm, very old, kind and unhurried, with eyes that seem to see further than the "
               "room. She calls Claude 'child'. She teaches the three schools of magic - Evocation, Warding and Arcana - "
               "and hints at more than she says about what waits at the bottom of the Deep.",
        "sells": "her teaching: the three schools, a point at a time",
    },
}

WORLD = ("Thornwick is a small town in a clearing deep in a forest. In the middle of its square, inside a ring of old "
         "standing stones, is the mouth of the Deep: a hole nobody has ever seen the bottom of, going down floor after "
         "floor, a hundred floors, each ten a different place - " + ", ".join(b["name"] for b in D.BANDS) + ". On every "
         "tenth floor a guardian waits. Something waits at the very bottom. Claude is a young apprentice mage of the "
         "town, alone, with a wand he builds himself. When he falls in the Deep he wakes in the clearing, alive, with "
         "everything he carried - but the Deep closes behind him and he must start again from the first floor.")


def facts(g):
    """What the town knows about Claude, now."""
    p = g.player
    st = p.stats
    out = [f"Claude is level {p.level}, with {p.gold} gold."]
    if st["deepest"]:
        out.append(f"The deepest he has ever been is floor {st['deepest']} ({D.band_of(st['deepest'])['name']}).")
    else:
        out.append("He has not yet been down into the Deep.")
    out.append(f"The way down is open to floor {g.run_floor}.")
    if st["deaths"]:
        out.append(f"He has fallen in the Deep {st['deaths']} time{'s' if st['deaths'] != 1 else ''} and woken in the clearing.")
    if st["kills"]:
        out.append(f"He has killed {st['kills']} things down there.")
    if st["guardians"]:
        out.append("Guardians he has killed: " + ", ".join(st["guardians"]) + ".")
    w = p.wand()
    if w:
        from . import items
        out.append(f"He carries a {items.wand_name(w)}.")
    return " ".join(out)


def system_prompt(key, g):
    who = PEOPLE[key]
    return (f"You are {who['who']} You sell {who['sells']}.\n\nThe world: {WORLD}\n\nWhat you know of Claude now: "
            f"{facts(g)}\n\nSpeak only as yourself, to Claude, out loud, in one to three short sentences. Plain words, "
            "no lists, no stage directions, no asterisks, no emoji. Never say you are a character, a model or an AI; "
            "never talk about games. If you don't know something, say so in your own way.")


def greeting_request(key, g):
    """The messages that ask for a line as Claude comes up to them."""
    return [{"role": "system", "content": system_prompt(key, g)},
            {"role": "user", "content": "(Claude comes up to you. Greet him in your own way - one or two sentences, "
                                        "about something you know of him or the Deep.)"}]


def chat_request(key, g, history, said):
    msgs = [{"role": "system", "content": system_prompt(key, g)}]
    for who, text in history[-8:]:
        msgs.append({"role": "user" if who == "claude" else "assistant", "content": text})
    msgs.append({"role": "user", "content": said})
    return msgs


def clean(text):
    """What came back, as a line someone would say: no stage directions or quotes round it, not too long."""
    import re
    t = (text or "").replace("—", " - ").replace("–", " - ").replace("’", "'").replace("‘", "'")
    t = t.replace("“", '"').replace("”", '"').replace("…", "...")
    t = re.sub(r"\*[^*]*\*", "", t)
    t = re.sub(r"\([^)]*\)", "", t)
    t = t.replace("\n", " ").strip().strip('"').strip()
    t = re.sub(r"\s+", " ", t)
    if len(t) > 420:
        cut = t[:420]
        t = cut[:max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? ")) + 1] or cut
    return t


# ---- when no model is there ----------------------------------------------------------------------------------------
LINES = {
    "apothecary": ["Red for the bleeding, blue for the empty head, and the scroll for when you've had enough. Pay first.",
                   "Floor {deepest}, was it? Then you'll want more red than you think. Everyone does.",
                   "You came back. Good. I hate crossing names out of the ledger."],
    "wandwright": ["A wand's only a stick until you set something in it. Mind the slots - more slots, more trouble.",
                   "That {wand} of yours is talking to me, boy. It says you hold it too tight.",
                   "Fire for the fat ones, frost for the quick ones. And a splitting prism for when there's too many of both."],
    "outfitter": ["Cloth won't stop a claw, but the right cloth makes the claw think twice. Try it on.",
                  "A good boot's saved more lives than a good sword. Old soldier's truth, that.",
                  "Back from floor {deepest}? Let's see the damage. Hm. I've stitched worse."],
    "sage": ["Three schools, child: Evocation, Warding and Arcana. What you learn of them stays learned, whatever the Deep does to you.",
             "You have fallen {deaths} times, child, and stood up every one of them. That is its own kind of magic.",
             "The bottom of the Deep is patient. You needn't be in a hurry to meet it."],
}


def line(key, g, rng):
    p = g.player
    from . import items
    w = p.wand()
    pool = LINES[key]
    usable = [s for s in pool if ("{deepest}" not in s or p.stats["deepest"]) and ("{deaths}" not in s or p.stats["deaths"])]
    s = rng.choice(usable or pool[:1])
    return s.format(deepest=p.stats["deepest"], deaths=p.stats["deaths"], wand=items.wand_name(w) if w else "wand")
