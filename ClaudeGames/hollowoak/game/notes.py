"""Claude's notes: what he learns of her, written down as he learns it, and kept - across nights, across deaths -
so each night begins knowing what the last ones learned. (The notebook: Esc > Notes.)

    PAGES                       every page there is: id -> (section, title, text)
    unlock_for(event, night)    which pages a thing that happened writes: [ids]
    for_line(text)              which pages her words write (her name spoken, fire feared...): [ids]
    for_node(node)              which pages a line of the script writes: [ids]
The writing down and keeping is game/records.py's (rec.note(id))."""

SECTIONS = ("The invitation", "Her", "Her ways", "Her guests")

PAGES = {
    # ---- the invitation
    "letter": ("The invitation", "The letter",
               "Silk, not paper - finer than anything woven in Thornwick, and written in a hand that seems to move when "
               "I look away. Come at dusk. Come alone. Come hungry for knowing. Signed only: Y."),
    "silk": ("The invitation", "What the silk is soaked in",
             "My fingertips have been numb since I first touched it. It smells sweet, and faintly bitter. Venom, I "
             "think - and something else beneath it, something that keeps turning my thoughts to the oak."),
    # ---- her
    "name": ("Her", "Her name",
             "She calls herself Ysmeine. The Weaver Below."),
    "hidden": ("Her", "What she hides",
               "Ysmeine is what she is called. It is not what she is, she says - and told me not to ask the difference. "
               "Not yet."),
    "what": ("Her", "What she is",
             "A predator, and she does not pretend otherwise. Her hunger is never hidden - only set aside, for as long "
             "as she chooses."),
    "old": ("Her", "How old",
            "She lived in the oak before it was hollow. She is older than Thornwick."),
    "wants": ("Her", "What she wants",
              "To be surprised. To be interesting to someone, and to find someone interesting. She has outlived every "
              "conversation she ever had."),
    "journal": ("Her", "Maudren's journal",
                "Half of it is Ysmeine's words, copied down. On the last page, in a shaking hand: Not her name. She "
                "took it the night the oak went hollow. The one she will not speak of knew her before."),
    "fire": ("Her", "What she fears",
             "Fire. Everything that lives in silk fears it, she said - and that it is not a thing she tells."),
    # ---- her ways
    "silk_sense": ("Her ways", "She feels the silk",
                   "Every step I take on her silk, she feels - wherever she is. A careful step, and she lets me be. A "
                   "scramble, and she turns."),
    "edge": ("Her ways", "At the edge of the light",
             "She comes to the very edge of my lantern's light, and leans out of the dark toward me - and holds there, "
             "a long moment, and is gone."),
    "dark": ("Her ways", "In the dark",
             "When my lantern goes out she comes close, and stays close. The dark is her house with the lamp put out."),
    "hunger_tell": ("Her ways", "The fungus warms",
                    "The fungus-light warms toward amber when she is hungry, and the silk hums higher. Learn to watch "
                    "the light."),
    "fascination_tell": ("Her ways", "The fungus brightens",
                         "When I please her - when she is curious about me - the fungus burns brighter."),
    "suspicion_tell": ("Her ways", "The fungus dims",
                       "When she doubts me, the fungus dims and goes cold."),
    "small_ones": ("Her ways", "Her small ones",
                   "The little ones are hers - her children, and her eyes. They drop on threads, run across my face, "
                   "and come for my lantern when it's out."),
    "bite": ("Her ways", "Her bite",
             "She bit me. The venom burns, and then it doesn't, which is worse. One bite she forgives. I do not think "
             "she forgives two."),
    "hunt": ("Her ways", "When she hunts",
             "When her patience is gone, or her hunger too much, she stops talking and comes straight for me, light or "
             "no light. The middle of the floor is the only place she cannot reach."),
    # ---- her guests: the suitors, wrapped
    "orrin": ("Her guests", "Orrin Vale, the bard",
              "Wrapped by the roots, a lute broken under him. He sang to her for nine nights. On the tenth he ran out "
              "of songs."),
    "aldric": ("Her guests", "Ser Aldric, the knight",
               "Hung in his armour, his sword beneath him. He called her the wisest creature in the forest. She "
               "says he said it best."),
    "wick": ("Her guests", "Wick, the thief",
             "Small, bound tight, his picks still in his fist. He came for her larder, not for her."),
    "maudren": ("Her guests", "Maudren Hale, the scholar",
                "A book under her, every page filled. She wrote down everything Ysmeine said - and still did not "
                "understand her."),
    "fennick": ("Her guests", "Brother Fennick, the hermit",
                "A holy man from the hills. He came to save her. His prayer beads are still wound in the silk."),
    "isolde": ("Her guests", "Isolde of the Marr, the huntress",
               "She came with a bow and arrows tipped in fire. Not one was loosed. The arrows lie under her, unburnt."),
    "unnamed": ("Her guests", "The one she will not speak of",
                "High in the crown, wrapped tighter than the rest, and nothing beneath it at all. When I touched it, "
                "the whole oak went still."),
}
SUITORS = ("orrin", "aldric", "wick", "maudren", "fennick", "isolde", "unnamed")


def unlock_for(event, night=None):
    """Pages a thing that happened writes."""
    kind = event[0]
    if kind == "her":
        return {"glimpse": ["edge"], "near": ["dark"], "turn": ["silk_sense"], "hunts": ["hunt"],
                "bite": ["bite"]}.get(event[1], [])
    if kind == "crawler" or kind == "dangler" or kind == "swarm":
        return ["small_ones"]
    return []


def for_moods(moods):
    """Pages her moods, shown in the den, write - once he's seen them clearly enough."""
    out = []
    if moods.hunger > 60:
        out.append("hunger_tell")
    if moods.fascination > 60:
        out.append("fascination_tell")
    if moods.suspicion > 55:
        out.append("suspicion_tell")
    return out


def for_line(text):
    """Pages her words write: her name, said; fire, feared; her age, told."""
    t = (text or "").lower()
    out = []
    if "ysmeine" in t:
        out.append("name")
    if "fire" in t and ("fright" in t or "fear" in t or "afraid" in t):
        out.append("fire")
    if "not what i am" in t or "true name" in t:
        out.append("hidden")
    if "before it was hollow" in t or "older than thornwick" in t:
        out.append("old")
    if "surprise" in t:
        out.append("wants")
    if "hunger" in t and ("flesh" in t or "eat" in t):
        out.append("what")
    return out


NODES = {"hername": ["name", "hidden"], "herhunger": ["what"], "eatme": ["what"], "want": ["wants"],
         "fear": ["fire"], "flame": ["fire"], "orrin": ["orrin"], "meantit": ["aldric"]}


def for_node(node):
    return NODES.get(node, [])
