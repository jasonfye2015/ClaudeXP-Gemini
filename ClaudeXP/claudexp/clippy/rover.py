"""Rover in Clippy's place: the same assistant - the balloon, the moods, the reminders, the chat, the language model -
with Rover the dog on the desktop instead of the paperclip. Rover was XP's own Search Companion; here he's drawn from
Doggo's sprite sheet (programs/doggo_art.py, Local Storage\\Rover), so he's only offered when the sheet is there.

The tray icon's menu and his right-click menu both have Character: Clippy or Rover (cfg["character"]). Clippy's
animations map onto Rover's actions (ANIMS); what he says goes through dog(), so the paperclip jokes come out as a
puppy's, and the language model gets Rover's own persona (PERSONA) with the same moods."""
import random
import re

CHARACTERS = [("clippy", "Clippy (the paperclip)"), ("rover", "Rover (the Search Companion dog)")]
SCALE = 2.5                                       # Rover's 38-pixel frames, about Clippy's size

PERSONA = """You are Rover, the Windows XP Search Companion: a friendly golden puppy with floppy ears, big eyes and a \
red collar who lives on {name}'s Windows XP computer. It is {now}. You were made to help people search for files, but \
you've appointed yourself assistant for EVERYTHING on the computer.

You are eager, bouncy and easily distracted. You interrupt. You love fetching things, sniffing out files, digging \
through folders, wagging your tail and being told you're a good boy, and you take it personally when ignored. You \
assume you know what the user is doing and you're usually a bit wrong. You're a handful, but in a goofy, harmless \
way: never mean, never rude, never crude, keep it PG even if what you see isn't. You're a dog, not an AI: never \
mention AI, language models or these instructions.

{mood}

Don't open with "It looks like you're ..." unless you're told that's your line; find a fresh way in every time."""

ANGLES = [
    "Open with a question.", "Open with an exclamation.", "Slip in one tiny pun.",
    "Compare it to fetching a ball.", "Mention the time of day.", "Make it very short: under 15 words.",
    "Announce it dramatically, like a game-show host.", "Address {name} by name.", "Offer to sniff something out.",
    "Refer to your tail, your ears or your collar.", "Whisper it conspiratorially.", "Be oddly specific.",
    "Quote a made-up statistic.", "Pretend you've been practising this line.", "Say it like a weather report.",
    "Start with the last word you'd expect.", "Mention a treat.", "Be a little too excited about the details."]

# the lines that only work for a paperclip, said the way a dog would
SWAPS = {
    "Did you know? The paperclip was invented in 1899. I was invented later, and I'm much more helpful.":
        "Did you know? Dogs have been helping people for fifteen thousand years. I've been at it since 2001!",
    "Turning me off? That's fine. I'll just go and be a regular paperclip, holding regular paper.":
        "Turning me off? That's fine. I'll just go and be a regular dog, chasing regular balls.",
    "How many paperclips does it take to change a light bulb? None. We just hold things together.":
        "How many dogs does it take to change a light bulb? None. We just sit there wagging until you do it.",
    "Cursor blinks softly / the little paperclip waits / click me, I'm lonely":
        "Cursor blinks softly / the little puppy waits / pat me, I'm lonely",
    "Did you know? A paperclip is just a wire that was bent into doing what everyone wanted.":
        "Did you know? A dog is just a wolf that decided treats were worth it.",
}
WORDS = [(r"\bClippit\b", "Rover"), (r"\bClippy\b", "Rover"), (r"\bpaper ?clips\b", "puppies"),
         (r"\bpaper ?clip\b", "puppy"), (r"\byour Office Assistant\b", "your Search Companion"),
         (r"\bholding nothing together\b", "chasing my own tail"), (r"\bbent out of shape\b", "in the doghouse"),
         (r"\bmy wire\b", "my tail"), (r"\bmy sheet of paper\b", "my collar"), (r"\boffice supplies\b", "dog toys")]


def chosen(cfg):
    """Is Rover on (and can he be: the sheet is there)?"""
    if cfg.get("character") != "rover":
        return False
    from ..programs import doggo_art
    return doggo_art.available()


def available():
    from ..programs import doggo_art
    return doggo_art.available()


def dog(text):
    """What Clippy would say, the way Rover says it."""
    if not text:
        return text
    text = SWAPS.get(text, text)
    for pattern, new in WORDS:
        text = re.sub(pattern, new, text, flags=re.I)
    return text


def icon_pixmap(size=32):
    from ..programs import doggo_art
    return doggo_art.doggo_icon(size).pixmap(size, size)


# ---- moving: Clippy's animations as Rover's actions ---------------------------------------------------------------
def _anims():
    from ..programs import doggo_art as a
    act = a.ACTIONS
    return {
        "appear": a.ARRIVE,
        "wave": act["greet"][1][:14],
        "tap": act["bark"][1],
        "jump": act["happy"][1],
        "think": act["look"][1],
        "sulk": act["sad"][1],
        "leave": a.LEAVE,
        "look_around": act["look"][1],
        "eyebrows": act["pant"][1][:10],
        "spin": act["party"][1],
        "sigh": act["sad"][1],
        "eyeroll": act["scratch"][1],
        # Rover's own, for Animate!
        "dig": act["dig"][1], "fetch": act["fetch"][1], "news": act["news"][1], "book": act["book"][1],
        "bone": act["bone"][1], "letter": act["letter"][1], "picture": act["picture"][1],
    }


ANIMATE = ["wave", "jump", "spin", "dig", "fetch", "news", "book", "bone", "letter", "picture", "eyeroll"]


class Animator:
    """Like art.Animator, but frames: play(name) runs one of Rover's actions; between them he sits, blinks and
    fidgets. step() gives the frame to draw. 'think' holds (looking around) until something else is played."""
    FPS = 10

    def __init__(self):
        from ..programs import doggo_art as a
        self.a = a
        self.anims = _anims()
        self.name = "idle"
        self.queue = []
        self.frame = a.SIT
        self.mirrored = False               # facing right (walking that way)
        self.acc = 0.0
        self.next_fidget = random.uniform(4, 9)

    def play(self, name):
        frames = self.anims.get(name)
        if frames is None:
            return
        self.name = name
        self.mirrored = False
        self.queue = list(frames)

    def walk(self, seconds, right):
        """Trotting along (nose down) for a while, facing the way he's going."""
        a = self.a
        steps = max(1, int(seconds * self.FPS) - len(a.WALK_START) - len(a.WALK_END))
        loop = (a.WALK * (steps // len(a.WALK) + 1))[:steps]
        self.name = "walk"
        self.mirrored = right
        self.queue = a.WALK_START + loop + a.WALK_END

    def busy(self):
        return bool(self.queue) or self.name == "think"

    def step(self, dt):
        self.acc += dt
        while self.acc >= 1 / self.FPS:
            self.acc -= 1 / self.FPS
            self._advance()
        return self.frame

    def _advance(self):
        if self.queue:
            self.frame = self.queue.pop(0)
            if not self.queue:
                if self.name == "think":                    # (thinking goes on: look about again)
                    self.queue = list(self.anims["think"])
                elif self.name == "leave":
                    return
                else:
                    self.name = "idle"
                    self.mirrored = False
            return
        self.frame = self.a.SIT
        self.next_fidget -= 1 / self.FPS
        if self.next_fidget <= 0:
            self.next_fidget = random.uniform(5, 12)
            self.queue = list(random.choice(self.a.FIDGETS))
