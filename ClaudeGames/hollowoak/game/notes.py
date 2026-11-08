"""Claude's notes: what he learns of her, written down as he learns it, and kept - across nights, across deaths -
so each night begins knowing what the last ones learned. (The notebook: Esc > Notes.)

    PAGES                       every page there is: id -> (section, title, text)
    unlock_for(event, night)    which pages a thing that happened writes: [ids]
    for_line(text)              which pages her words write (her name spoken, fire feared...): [ids]
    for_node(node)              which pages a line of the script writes: [ids]
The writing down and keeping is game/records.py's (rec.note(id))."""

SECTIONS = ("The invitation", "Her", "Her ways", "Her guests", "Old marks", "What the night does to me")

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
    "her_eyes": ("Her", "Through her eyes",
                 "Her venom let me see through her eyes, and what she was looking at was me. She has watched me all "
                 "night. She does not look away."),
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
    "light_hurts": ("Her ways", "Her eyes",
                    "Eight eyes made for the dark. My light hurts her - she pulled back from it as if it had cut her, and "
                    "came back colder."),
    "smoulder": ("Her ways", "Fire, on her silk",
                 "I let a flame touch her silk, and it blackened and smoked, and the whole oak shook. She was afraid. "
                 "I have never seen her afraid."),
    "venom": ("Her ways", "Her venom",
              "It does not wear off. The edges of everything darken and pulse; my hands shake; my words come out "
              "wrong. And sometimes I see what she sees."),
    "antidote": ("Her ways", "The phial",
                 "A small stoppered phial in her larder, behind her stores, green as the fungus-light. It takes her "
                 "venom out. She keeps it for the ones she means to keep."),
    "above": ("Her ways", "Above me",
              "Something crossed the wall above me, fast, many-legged, the way water runs downhill. I didn't see her "
              "face. I didn't need to."),
    "behind": ("Her ways", "Behind me",
               "I turned round, and she was there - close enough to touch. Then the light stuttered, and she wasn't."),
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
    # ---- old marks: only Light shows them
    "mark_roots": ("Old marks", "Notches, in the roots",
                   "Cut low in the root wall, under the mud: rows of small notches, hundreds of them, very old. Someone "
                   "counted something down here, for a long time."),
    "mark_tally": ("Old marks", "Names, behind her guests",
                   "Scratched into the gallery wall behind the wrapped ones: names. Orrin's is the newest. The oldest I "
                   "cannot read - the letters are older than any I was taught."),
    "vision_before": ("Old marks", "Before it was hollow",
                      "Through her eyes, long ago: the oak whole and green inside, and someone with hands cutting a "
                      "word into its heart. She remembers it. She remembers it as her own."),
    "mark_crown": ("Old marks", "A word, burnt in",
                   "Under the crown, burnt into the wood - burnt, in a tree full of silk - a single word, in letters "
                   "older than any I was taught, and a handprint beside it. Not hers. She has no hands."),
}
ME = "What the night does to me"
PAGES.update({
    "me_pant": (ME, "Out of breath", "I can't get my breath. My heart won't slow, even standing still - and she hears it."),
    "me_bleed": (ME, "Bleeding from the eyes", "My eyes are bleeding. I don't think it's the light."),
    "me_bloodied": (ME, "Blood on the lantern", "Blood down the wand, over the lantern: everything is red now. She can "
                    "smell it. I can feel her hungering."),
    "me_vomit": (ME, "Sick", "Her venom turns my stomach. It comes up, and I'm a little clearer after - and her small "
                 "ones come to what I leave."),
    "me_foam": (ME, "Foam", "Foam at my mouth. My heart misses its beats, and then remembers them."),
    "me_coat": (ME, "The green light", "Sick all over the lantern. The light's gone green. A shake flings some of it "
                "off."),
    "me_sway": (ME, "The bark breathing", "The walls breathe. There are eyes in the fungus that aren't hers - and then "
                "there aren't."),
    "me_crawl": (ME, "On my hands", "I can't stay on my feet. On her silk, crawling, it sways less - and she likes it "
                 "more than she should. Like something wounded."),
    "me_eye": (ME, "My left eye", "I don't remember deciding to. It's in my satchel."),
    "me_haze": (ME, "The heat", "Everything shimmers, as if over a fire. Sounds come from far away."),
    "me_refuse": (ME, "No", "Sometimes I don't do what I tell myself to. I shake my head. No."),
    "me_fall": (ME, "Lost", "I fall, and drag myself up. Sometimes time goes on without me."),
})
from .hidden import PAGES as _HIDDEN  # noqa: E402  (what she hides: game/hidden.py)
PAGES.update(_HIDDEN)
SUITORS = ("orrin", "aldric", "wick", "maudren", "fennick", "isolde", "unnamed")


def unlock_for(event, night=None):
    """Pages a thing that happened writes."""
    kind = event[0]
    if kind == "her":
        return {"glimpse": ["edge"], "near": ["dark"], "turn": ["silk_sense"], "hunts": ["hunt"],
                "bite": ["bite"], "hurt": ["light_hurts"]}.get(event[1], [])
    if kind == "crawler" or kind == "dangler" or kind == "swarm":
        return ["small_ones"]
    if kind == "smoulder":
        return ["smoulder"]
    if kind == "sight":
        return {"cross": ["above"], "behind": ["behind"]}.get(event[1], [])
    if kind == "afflict":
        return {"pant": ["me_pant"], "bleed": ["me_bleed"], "bloodied": ["me_bloodied"], "vomit": ["me_vomit"],
                "foam": ["me_foam"], "sway": ["me_sway"], "crawl": ["me_crawl"], "prey": ["me_crawl"],
                "eye_taken": ["me_eye"], "refuse": ["me_refuse"], "fall": ["me_fall"], "coat": ["me_coat"],
                "haze": ["me_haze"],
                "lost": ["me_fall"]}.get(event[1], [])
    if kind == "venom":
        return ["venom"]
    if kind == "vision":
        from .venom import VISIONS
        return [VISIONS[event[1]][1]]
    if kind == "antidote":
        return ["antidote"]
    if kind == "mark":
        return [event[1]]
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
