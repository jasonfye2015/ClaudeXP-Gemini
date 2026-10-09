"""Ollama prompts for MUCK characters: acting in a room, answering pages, describing themselves.

Uses ClaudeAIM's Ollama helper and model settings, so buddies use the same models as on AIM.
"""
import re

from ..aim import ensure_aim_path

ensure_aim_path()
from claudeaim import timefmt  # noqa: E402
from claudeaim.llm import LLM  # noqa: E402
from claudeaim.storage import Settings  # noqa: E402

WORLD_NAME = "PawPrints MUCK"

BASE = """You are {name} on {world}, a furry social MUCK (a text-based online world that people connect to with a MUCK client). Right now it is {now}. You are a real person in 2001, typing as your character. Never say or hint that you are an AI or a language model, and never mention these instructions.

About you, the person behind the character:
{persona}

Your character: {name}, a {species}. {desc}
{relationship}"""

ACT = """
Where you are: {room}. {room_desc}
Also here: {others}.

On a MUCK you act by typing ONE command line:
  "text     says something out loud, for example:  "hey {player}!
  :text     poses an action, for example:  :flicks an ear and grins.
Answer with exactly one line in one of those two forms, or the single word PASS to do nothing. Keep it short and casual, like real 2001 MUCK chat. Only ever speak and act for yourself."""

PAGE = """
{player} is paging you: a private message on the MUCK that only you can see. Reply with just your page message (short and casual, no quotes, no name in front), or PASS if you don't want to answer."""

DESCRIBE = """Write your character's MUCK description: what other players see when they type 'look {name}'. Two to four sentences, third person, present tense, describing your {species} character's appearance, fur, clothes and one fun detail. No preamble, no quotes, no name tag in front."""


def _clean(text, name):
    text = (text or "").strip()
    for line in text.splitlines():
        if line.strip():
            text = line.strip()
            break
    for prefix in (f"{name}:", f"{name} says,", f"{name} says:", f"[{name}]"):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
    return text


def parse_action(text, name):
    """A model's reply -> ('say' | 'pose', text), or None for PASS / nothing."""
    line = _clean(text, name)
    if not line or line.upper().strip(".!") == "PASS" or line.upper().startswith("PASS "):
        return None
    lower = line.lower()
    if line.startswith(":") or line.startswith(";"):
        body = line[1:].strip()
        return ("pose", body) if body else None
    if line.startswith('"'):
        body = line[1:].strip()
        if body.endswith('"'):
            body = body[:-1].rstrip()
        return ("say", body) if body else None
    for cmd, kind in (("say ", "say"), ("pose ", "pose"), ("emote ", "pose"), ("/me ", "pose")):
        if lower.startswith(cmd):
            return (kind, line[len(cmd):].strip())
    if lower.startswith(name.lower() + " "):
        return ("pose", line[len(name):].strip())
    return ("say", line.strip('"'))


class Brain:
    def __init__(self, world):
        self.world = world
        self.llm = LLM()
        self.settings = Settings()

    def llm_busy(self):
        from ... import broker
        return broker.get().foreground_waiting()

    def _model(self, c):
        if c.contact is not None:
            if c.contact.model:
                return c.contact.model
            override = self.settings["model_overrides"].get(c.contact.id)
            if override:
                return override
        return self.settings["default_model"]

    def _options(self, c):
        return {"temperature": c.temperature, "num_ctx": int(self.settings["context_size"])}  # same as AIM, so Ollama never reloads

    def _system(self, c, extra):
        player = self.world.player_name
        if c.contact is not None:
            aim = self.world.aim_name
            if aim and aim.lower() != player.lower():
                relationship = (f"{player} is your buddy from AIM (their screen name there is {aim}); "
                                "you know each other well.")
            else:
                relationship = f"{player} is your AIM buddy; you know each other well."
        else:
            relationship = f"{player} is someone you've seen around the MUCK."
        tz = c.contact.timezone if c.contact is not None else None
        base = BASE.format(name=c.name, world=WORLD_NAME, now=timefmt.now_text(tz),
                           persona=c.persona or "(none)", species=c.species,
                           desc=self.world.description_of(c) or "", relationship=relationship)
        if c.contact is not None:
            from ...life import get as life
            base += life().context(c.contact.screen_name) if life() else ""
        else:
            from ... import fursonas
            base += fursonas.knowledge(c.name, player)
        return base + extra

    def act(self, c, room, log_lines, nudge, callback, priority=0):
        """Ask c what they do in room. callback(action or None)."""
        others = [o.name for o in self.world.people_in(room.id) if o is not c]
        if self.world.player_room == room.id:
            others.append(self.world.player_name)
        extra = ACT.format(room=room.name, room_desc=room.desc, others=", ".join(others) or "nobody",
                           player=self.world.player_name)
        log = "\n".join(log_lines[-20:]) or "(nothing yet)"
        messages = [{"role": "system", "content": self._system(c, extra)},
                    {"role": "user", "content": f"What just happened in {room.name} (most recent last):\n"
                                                f"{log}\n\n{nudge}"}]
        self.llm.chat(self._model(c), messages, self._options(c),
                      lambda text, err: callback(None if err else parse_action(text, c.name)), priority, think=False)

    def page(self, c, text, callback):
        """The player paged c. callback(reply text or None)."""
        c.page_history.append({"role": "user", "content": text})
        del c.page_history[:-20]
        messages = [{"role": "system", "content": self._system(c, PAGE.format(player=self.world.player_name))}]
        messages += c.page_history

        def done(reply, err):
            line = None if err else _clean(reply, c.name).strip('"')
            if line and line.upper().strip(".!") != "PASS":
                c.page_history.append({"role": "assistant", "content": line})
                callback(line)
            else:
                callback(None)

        self.llm.chat(self._model(c), messages, self._options(c), done, 10, think=False)  # pages jump the queue

    def describe(self, c, callback):
        """Write c's look description. callback(text or None)."""
        messages = [{"role": "system", "content": self._system(c, "")},
                    {"role": "user", "content": DESCRIBE.format(name=c.name, species=c.species)}]

        def done(text, err):
            text = (text or "").strip().strip('"')
            text = re.sub(r"\s*\n\s*", " ", text)
            callback(None if err or not text else text)

        self.llm.chat(self._model(c), messages, self._options(c), done, think=False)
