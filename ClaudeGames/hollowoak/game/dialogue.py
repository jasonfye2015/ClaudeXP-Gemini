"""Talking with her: one night's conversation, whichever way her words are written - by a language model (he types),
or by the script (he chooses from the lines offered). Either way what he says moves her moods (game/moods.py), and
what matters is remembered.

    talk = Conversation(night, voice, reputation, rng)
    talk.mode                         "model" or "script"
    talk.murmur(kind, done)           one short unasked line: done(text) (from a thread, with a model)
    talk.open(scene, done)            her first line of a scene: done(text, choices) - choices [] when he types
    talk.say(text, done, interrupting=False)   his typed words: judged, remembered, answered: done(text, [])
    talk.choose(i, done)              his chosen line (the script): done(text, choices), or done(text, None) at the end
    talk.memory                       what she remembers of him tonight ("He ...")
    talk.lies, talk.ended             tallies for the night's record; how the scene ended
"""
import difflib
import random

from . import persona, script

MODERN = (" ai", "a.i", "system prompt", "prompt", "instruction", "model", "computer", "game", "chatbot", "robot")
OPENINGS = {
    "audience": "(He has come down to you, on your loom in the great hollow, for the first time. You see him plainly now, "
                "and he sees you. Greet him - something like: {line})",
    "supper": "(He has come down into your larder, where your stores hang wrapped. It is late, and your hunger is at its "
              "height. Ask him why you should not begin with him - something like: {line})",
    "crown": "(He has climbed to the crown of your oak, onto your web under the moon and the open sky. This is the "
             "deepest of your talks. Ask him what he wants of you - something like: {line})",
}
CLOSINGS = {
    "audience": "(It is time to send him on: up to the gallery, to see your guests. Answer him, and send him, in two "
                "sentences.)",
    "supper:guest": "(You have decided: he will be your guest at this table, not your meal - tonight. Tell him so, in one "
                    "or two sentences, and send him up to wait until you call.)",
    "supper:meal": "(You have decided: you will bite him. Tell him so, in one or two sentences - sorry, and very "
                   "hungry.)",
    "crown": "(Ask him to wait with you for the light, in one or two sentences.)",
}
QUIET = ("Hm.", "Go on.", "Say that again. Slowly.", "I am listening.")
TURNS = 9                        # (a scene's length, typed: then she sends him on)
PLACES = {"tunnel": "the roots", "hollow": "the great hollow", "gallery": "the gallery", "larder": "the larder",
          "high hollow": "the high hollow", "crown": "the crown of the oak"}


class Conversation:
    def __init__(self, night, voice, reputation=None, rng=None):
        self.night, self.voice = night, voice
        self.reputation = reputation or {}
        self.rng = rng or random.Random()
        self.mode = "model" if voice is not None and voice.speaking() else "script"
        self.memory = []
        self.history = []                         # [(who, text)]: "her" / "him"
        self.said = {k: [] for k in script.MURMURS}
        self.scene = None
        self.node = None
        self.turns = 0
        self.lies = 0
        self.ended = None
        self.visited = []                         # (the script's lines she's said, in order: for his notes)
        self.flags = night.flags if hasattr(night, "flags") else {}     # (what he's chosen: to stay; to ask...)

    # ---- what she knows, now -------------------------------------------------------------------------------------
    def context(self):
        n = self.night
        return {"place": PLACES.get(n.where(), "the Hollow"), "time": n.clock_words(), "moods": n.moods.values(),
                "manner": n.manner(), "dark": (not n.lantern) or n.lamp.state == "out", "bitten": n.moods.bites > 0,
                "memory": self.memory, "reputation": self.reputation}

    def _keep(self, fact):
        if fact and any(w in fact.lower() for w in MODERN):                # (nothing from outside the night)
            return
        if fact and fact not in self.memory:
            self.memory.append(fact)

    def _heard(self, kinds):
        for k in kinds:
            self.night.moods.heard(k)
            if k == "lie":
                self.lies += 1

    # ---- unasked -------------------------------------------------------------------------------------------------
    def _scripted_murmur(self, kind):
        lines = script.MURMURS.get(kind) or script.MURMURS["glimpse"]
        fresh = [m for m in lines if m not in self.said.get(kind, [])] or list(lines)
        line = self.rng.choice(fresh)
        self.said.setdefault(kind, []).append(line)
        return line

    def murmur(self, kind, done):
        if self.mode != "model":
            done(self._scripted_murmur(kind))
            return

        def back(text):
            line = persona.clean(text)
            done(line if len(line) > 3 else self._scripted_murmur(kind))
        self.voice.ask(persona.murmur_prompt(kind, self.context()), back, max_tokens=50)

    # ---- a scene -------------------------------------------------------------------------------------------------
    def open(self, scene, done):
        self.scene, self.turns, self.ended = scene, 0, None
        sc = script.SCENES[scene]
        if self.mode == "script":
            self.node = sc["start"]
            text, choices = self._at(self.node)
            done(text, choices)
            return
        opening = sc["nodes"][sc["start"]]["her"]                     # (her first words are hers to choose; the
        msgs = [{"role": "system", "content": persona.system(self.context())},   # script's are a guide)
                {"role": "user", "content": OPENINGS[scene].format(line=opening)}]

        def back(text):
            line = persona.clean(text) or opening
            self.history.append(("her", line))
            done(line, [])
        self.voice.ask(msgs, back)

    def _at(self, node_id):
        """Her line at a node (running on through any that lead straight to the next): -> (text, choices or None)."""
        nodes = script.SCENES[self.scene]["nodes"]
        parts = []
        node = nodes[node_id]
        while True:
            parts.append(node["her"])
            self.visited.append(node_id)
            if "next" not in node:
                break
            node_id = node["next"]
            node = nodes[node_id]
        text = " ".join(parts)
        if node.get("end") == "judge":                                # (her larder: guest, or meal - her moods decide)
            self.ended = self.supper()
            text += " " + script.SCENES[self.scene]["outcomes"][self.ended]
            self.history.append(("her", text))
            return text, None
        self.history.append(("her", text))
        if "end" in node:
            self.ended = node["end"]
            return text, None
        self.node = node_id
        return text, [c[0] for c in node["choices"]]

    def choose(self, i, done):
        node = script.SCENES[self.scene]["nodes"][self.node]
        choice = node["choices"][i]
        text, kinds, nxt = choice[0], choice[1], choice[2]
        self.history.append(("him", text))
        self._heard(kinds)
        if len(choice) > 3:
            self._keep(choice[3])
        if len(choice) > 4 and choice[4]:
            if choice[4].startswith("un"):
                self.flags.pop(choice[4][2:], None)
            else:
                self.flags[choice[4]] = True
        line, choices = self._at(nxt)
        done(line, choices)

    FEEL = {"delight": "It delights you", "plain": "It is a small thing to you, but kindly meant",
            "insult": "It insults you"}

    def offer(self, item, done):
        """He offers her something from his pack: her moods move as its worth decides; she answers - from the script
        (and the talk goes on where it was), or the model, told how it lands. done(text, choices)."""
        from . import offerings
        tier, scripted = offerings.give(item, self.night)
        name, said, _where = offerings.ITEMS[item]
        self.history.append(("him", f"(offers {name})"))
        if self.mode != "model":
            self.history.append(("her", scripted))
            node = script.SCENES[self.scene]["nodes"].get(self.node, {})
            done(scripted, [c[0] for c in node.get("choices", [])] if self.ended is None else None)
            return
        msgs = [{"role": "system", "content": persona.system(self.context())}]
        for who, t in self.history[-14:-1]:
            msgs.append({"role": "assistant" if who == "her" else "user", "content": t})
        msgs.append({"role": "user", "content": f"({said} {self.FEEL[tier]}. Answer him - one to three sentences.)"})

        def back(reply):
            line = persona.clean(reply) or scripted
            self.history.append(("her", line))
            done(line, [])
        self.voice.ask(msgs, back)

    def supper(self):
        """Guest, or meal: her hunger against what she's come to think of him."""
        m = self.night.moods
        score = m.hunger - 0.5 * m.fascination - 0.8 * m.regard + (25.0 if m.suspicion > 60 else 0.0)
        return "meal" if score > 25.0 else "guest"

    # ---- typed ---------------------------------------------------------------------------------------------------
    def _repeats(self, text):
        mine = [t for who, t in self.history if who == "him"]
        return any(difflib.SequenceMatcher(None, text.lower(), m.lower()).ratio() > 0.82 for m in mine)

    def say(self, text, done, interrupting=False):
        text = text.strip()[:400]
        her_last = next((t for who, t in reversed(self.history) if who == "her"), "")
        local = []
        if self._repeats(text):
            local.append("repeat")
        if interrupting:
            local.append("interrupt")
        self.history.append(("him", text))
        self.turns += 1

        def judged(verdict):
            kinds, remember = persona.read_judgement(verdict)
            self._heard(local + [k for k in kinds if k != "none"])
            self._keep(remember)
            msgs = [{"role": "system", "content": persona.system(self.context())}]
            for who, t in self.history[-14:]:
                msgs.append({"role": "assistant" if who == "her" else "user", "content": t})
            if "stay" in kinds:
                self.flags["stay"] = True
            if self.turns >= TURNS:
                if self.scene == "supper":
                    self.ended = self.supper()
                    msgs.append({"role": "user", "content": CLOSINGS["supper:" + self.ended]})
                else:
                    msgs.append({"role": "user", "content": CLOSINGS[self.scene]})
                    self.ended = "done"

            def back(reply):
                line = persona.clean(reply) or self.rng.choice(QUIET)   # (no answer from the model: she lets it lie)
                self.history.append(("her", line))
                done(line, [] if self.ended is None else None)
            self.voice.ask(msgs, back)
        self.voice.ask(persona.judge_messages(her_last, text, self.memory), judged, max_tokens=70, temperature=0.2)
