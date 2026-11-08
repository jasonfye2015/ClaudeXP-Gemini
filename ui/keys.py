"""His keys: what each does, and which key does it - set to the player's own in Options (records.options["keys"]).
Esc (his notebook), the arrows (walking and turning), F3/F4 and F9/F10/Enter stay as they are.

    ACTIONS                 [(id, what it does, the key it's on as made)]
    bound(options)          -> {id: key}
    name(key)               the key, as words
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

ACTIONS = (
    ("forward", "Walk forward", int(Qt.Key_W)), ("back", "Walk back", int(Qt.Key_S)),
    ("left", "Step left", int(Qt.Key_A)), ("right", "Step right", int(Qt.Key_D)),
    ("run", "Run", int(Qt.Key_Shift)), ("jump", "Jump", int(Qt.Key_Space)),
    ("look", "Look closer, take", int(Qt.Key_F)), ("lantern", "Shake the lantern", int(Qt.Key_E)),
    ("satchel", "Open the satchel", int(Qt.Key_Tab)), ("put_down", "Put down what's in his hand", int(Qt.Key_G)),
    ("drink", "Drink the antidote", int(Qt.Key_Q)),
    ("light", "Light", int(Qt.Key_1)), ("warmth", "Warmth", int(Qt.Key_2)), ("illusion", "Illusion", int(Qt.Key_3)),
    ("memory", "Memory", int(Qt.Key_4)),
    ("save", "Save here", int(Qt.Key_F5)), ("wait", "Wait for the light", int(Qt.Key_T)),
    ("pause", "Pause", int(Qt.Key_P)),
)


def bound(options):
    mine = options.get("keys") or {}
    return {aid: int(mine.get(aid, default)) for aid, _label, default in ACTIONS}


def name(key):
    if int(key) == int(Qt.Key_Shift):
        return "Shift"
    if int(key) == int(Qt.Key_Space):
        return "Space"
    return QKeySequence(int(key)).toString() or str(key)
