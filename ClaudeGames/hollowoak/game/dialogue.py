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
                {"role": "user", "content": "(He has come down to you, on your loom in the great hollow, for the first "
                                            "time. You see him plainly now, and he sees you. Greet him - something "
                                            f"like: {opening})"}]

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
            if "next" not in node:
                break
            node_id = node["next"]
            node = nodes[node_id]
        text = " ".join(parts)
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
        line, choices = self._at(nxt)
        done(line, choices)

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
            if self.turns >= TURNS:
                msgs.append({"role": "user", "content": "(It is time to send him on: up to the gallery, to see your "
                                                        "guests. Answer him, and send him, in two sentences.)"})
                self.ended = "done"

            def back(reply):
                line = persona.clean(reply) or self.rng.choice(QUIET)   # (no answer from the model: she lets it lie)
                self.history.append(("her", line))
                done(line, [] if self.ended is None else None)
            self.voice.ask(msgs, back)
        self.voice.ask(persona.judge_messages(her_last, text, self.memory), judged, max_tokens=70, temperature=0.2)
