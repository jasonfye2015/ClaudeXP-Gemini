"""His satchel (phase 6a): small - four things - and what's in it doesn't keep. The mouse kicks a while, and then it
doesn't; the moths get out, one by one; the honey drips, and her small ones follow it. One thing at a time in his
left hand (the mouse wheel), held out to her in her scenes; G puts it down where he stands (a live mouse, or moths,
are gone the moment he lets them go). And what she made of each thing he gave her, he writes beside it - kept across
nights, like his notes.

    SLOTS
    items(night)                 -> what he carries, in order (night.pack)
    take(night, item) -> bool    into the satchel, if there's room
    put_down(night) -> item      what's in his hand, set down at his feet (or let go)
    choose(night, step)          the wheel: the next (or last) thing into his hand - or nothing
    step(night, dt) -> events    the mouse tiring, moths escaping, honey dripping
    state(night, item)           its state: "kicking"/"still" for the mouse, how many moths are left
    learned_line(item, tier, night)    what he writes, once he's seen what she made of it
    WHERE                        where each thing was found, as he'd write it
Plain Python: the tests fill it and empty it."""
import math

SLOTS = 4
MOUSE_LIFE = 210.0             # (seconds it kicks, in his fist)
MOTHS = 6
MOTH_EVERY = 45.0              # (one gets out)
HONEY_EVERY = 55.0             # (her small ones find it on his fingers)
WHERE = {"ring": "Found in the mud of her roots, among old bones.",
         "mouse": "Caught where the roots open into the hollow.",
         "moths": "Caught about the low fungus, in my cupped hands.",
         "string": "From under Orrin Vale, where his lute broke.",
         "journal": "From under Maudren Hale. Every page is her words.",
         "honey": "Her own, from her larder wall.",
         "antidote": "Her phial, from behind her stores. It takes her venom out."}


def items(night):
    return night.pack


def state(night, item):
    return night.items.get(item, {})


def take(night, item):
    """Into the satchel, if there's room: -> False if it's full."""
    if len(night.pack) >= SLOTS and item not in night.pack:
        return False
    night.items[item] = {"got": night.time, "moths": MOTHS if item == "moths" else 0, "still": False,
                         "drip": night.time + HONEY_EVERY}
    if night.held is None:
        night.held = item                                     # (an empty hand takes it)
    return True


def gone(night, item):
    """Out of his satchel (given, drunk, let go)."""
    if item in night.pack:
        night.pack.remove(item)
    night.items.pop(item, None)
    if night.held == item:
        night.held = None


def choose(night, step):
    """The wheel: through what he carries, and an empty hand between the last and the first."""
    order = [None] + list(night.pack)
    k = order.index(night.held) if night.held in order else 0
    night.held = order[(k + step) % len(order)]
    return night.held


def put_down(night):
    """G: what's in his hand, set down at his feet - a live mouse runs, moths fly; the rest lie where he left them."""
    item = night.held
    if item is None:
        return None
    st = night.items.get(item, {})
    gone(night, item)
    if (item == "mouse" and not st.get("still")) or item == "moths":
        return item                                           # (let go: gone)
    fx, fz = math.sin(night.yaw), -math.cos(night.yaw)
    x, z = night.x + fx * 0.45, night.z + fz * 0.45
    night.finds.dropped[item] = (x, night.floor_at(x, z, night.y + 0.3) + 0.02, z)
    night.items_left[item] = st                               # (as it was: a still mouse stays still)
    return item


def step(night, dt):
    out = []
    t = night.time
    for item in list(night.pack):
        st = night.items.setdefault(item, {"got": t, "moths": MOTHS if item == "moths" else 0, "still": False,
                                           "drip": t + HONEY_EVERY})
        if item == "mouse" and not st["still"] and t - st["got"] > MOUSE_LIFE:
            st["still"] = True
            out.append(("satchel", "mouse_still"))
        elif item == "moths" and st["moths"] > 0 and t - st["got"] > MOTH_EVERY * (MOTHS - st["moths"] + 1):
            st["moths"] -= 1
            if st["moths"] <= 0:
                gone(night, "moths")
                out.append(("satchel", "moths_gone"))
            else:
                out.append(("satchel", "moth_out"))
        elif item == "honey" and t >= st["drip"]:
            st["drip"] = t + HONEY_EVERY
            out.append(("satchel", "honey"))
    return out


# what he writes beside a thing, once he's seen what she made of it: (item, tier) -> a line; {when} is filled in
LEARNED = {
    ("ring", "delight"): "She wore it on her thought of me - once she thought well of me.",
    ("ring", "insult"): "From a stranger, it was a bribe. She has to think well of me first.",
    ("mouse", "delight"): "Warm and kicking, and she was hungry: it delighted her.",
    ("mouse", "plain"): "She kept it for later. She wasn't hungry enough to care.",
    ("mouse", "insult"): "Fed, she was insulted: \"I am not a cat.\"",
    ("mouse", "still"): "Dead in my fist, it was nothing to her. She likes them kicking.",
    ("moths", "delight"): "Moths delighted her {when}.",
    ("moths", "plain"): "Moths, {when}, were only a kindness.",
    ("moths", "insult"): "Starving, she called them crumbs.",
    ("moths", "few"): "Two or three moths were hardly a gift at all.",
    ("string", "delight"): "Orrin's string moved her - when she was taken with me.",
    ("string", "insult"): "To her it was theft from her guests. Like Wick.",
    ("journal", "delight"): "Maudren's book softened her doubt, {when}.",
    ("journal", "plain"): "Maudren's book, {when}: she knew what was in it.",
    ("honey", "delight"): "Her own honey amused her - when she was taken with me.",
    ("honey", "insult"): "Her own honey, given back: she said I'd stolen it.",
}


def learned_line(item, tier, night):
    when = "late in the night" if night.sky.clock % 1440 < 7 * 60 else "early in the night"
    line = LEARNED.get((item, tier))
    return line.format(when=when) if line else None
