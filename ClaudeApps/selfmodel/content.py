"""What kind of conversation a training example is: general chat, roleplay, or adult.

Used by the model details card (card.py) and available to the exporter for choosing what a model is trained on.

    kind(messages) -> "general" | "roleplay" | "adult"
    scores(messages) -> {"turns", "emote_turns", "emote_share", "adult_hits"}

Roleplay: a good share of the turns are actions - *wags*, *hugs you*, /me ..., or ':nuzzles' - not just a *hug* hello.
Adult: several explicit words across the conversation (one stray word doesn't make a chat adult). Adult wins over
roleplay when both apply; most adult chats are roleplayed anyway."""
import re

EMOTE = re.compile(r"(^|\s)\*[^*\n]{2,}\*|^/me\s|^:[a-z]", re.I | re.M)
ADULT = re.compile(r"\b(cock|cocks|dick|knot|knots|knotted|knotting|sheath|cum|cumming|cums|precum|jizz|yiff|yiffing|"
                   r"yiffed|fuck|fucks|fucking|fucked|horny|naked|nude|balls|tailhole|tail\s?hole|butthole|anus|"
                   r"breed|breeding|bred|mount|mounts|mounting|mounted|suck|sucks|sucking|sucked|stroke|stroking|"
                   r"erect|erection|throb|throbbing|hump|humping|humps|orgasm|climax|thrust|thrusts|thrusting|"
                   r"pussy|slit|nipple|nipples|moan|moans|moaning|lube|condom|69|blowjob|rimming|rim|spank|spanking|"
                   r"bondage|collar\s?and\s?leash|piss|watersports|squirt|squirts|squirting)\b", re.I)

ROLEPLAY_SHARE = 0.35     # of all turns with an action in them
ROLEPLAY_MIN = 4          # and at least this many action turns
ADULT_MIN = 4             # explicit words in the conversation

KINDS = ("general", "roleplay", "adult")
LABELS = {"general": "General chatting", "roleplay": "Roleplay", "adult": "Adult roleplay and chat"}


def scores(messages):
    turns = [m["content"] for m in messages if m.get("role") in ("user", "assistant") and m.get("content")]
    emotes = sum(1 for t in turns if EMOTE.search(t))
    adult = sum(len(ADULT.findall(t)) for t in turns)
    return {"turns": len(turns), "emote_turns": emotes, "emote_share": emotes / max(1, len(turns)),
            "adult_hits": adult}


def kind(messages):
    s = scores(messages)
    if s["adult_hits"] >= ADULT_MIN:
        return "adult"
    if s["emote_turns"] >= ROLEPLAY_MIN and s["emote_share"] >= ROLEPLAY_SHARE:
        return "roleplay"
    return "general"
