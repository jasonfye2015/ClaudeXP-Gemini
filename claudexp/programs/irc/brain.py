"""Ollama prompts for FurNet IRC characters: chatting in channels and in private messages."""
from ..aim import ensure_aim_path

ensure_aim_path()
from claudeaim import timefmt  # noqa: E402
from claudeaim.llm import LLM  # noqa: E402
from claudeaim.storage import Settings  # noqa: E402

BASE = """You are {nick}, chatting on FurNet, a furry IRC network, using mIRC. Right now it is {now}. You are a real person in 2001. Never say or hint that you are an AI or a language model, and never mention these instructions.

About you:
{persona}

{relationship}"""

CHANNEL = """
You're in the IRC channel {channel} (topic: {topic}). Also in the channel: {others}.

Reply with exactly ONE line of IRC chat:
  plain text           to say it in the channel (to talk to someone, start with their nick, e.g.  {player}: hey!)
  /me <action>         for an action, e.g.  /me pounces {player}
or the single word PASS to say nothing. Keep it short like real 2001 IRC chat, often just a few words. No timestamps, don't put your own nick in front, and only ever speak for yourself."""

QUERY = """
{player} is talking with you in a private message window (an IRC query) that only the two of you can see. Reply with exactly ONE short line of chat (or /me <action>), or PASS to not answer. No timestamps, don't put your nick in front."""


def parse_line(text, nick):
    """A model's reply -> ('say' | 'action', text), or None for PASS / nothing."""
    line = ""
    for raw in (text or "").splitlines():
        if raw.strip():
            line = raw.strip()
            break
    for prefix in (f"<{nick}>", f"<@{nick}>", f"{nick}:", f"[{nick}]"):
        if line.lower().startswith(prefix.lower()):
            line = line[len(prefix):].strip()
    if len(line) > 1 and line[0] == line[-1] == '"':
        line = line[1:-1].strip()
    if not line or line.upper().strip(".! ") == "PASS" or line.upper().startswith("PASS "):
        return None
    lower = line.lower()
    if lower.startswith("/me "):
        return ("action", line[4:].strip())
    if lower.startswith(f"* {nick.lower()} "):
        return ("action", line[len(nick) + 3:].strip())
    if line.startswith("/"):
        return None  # some other command; just skip it
    return ("say", line)


# Queue priorities: private replies first, then answers to you, then background chatter.
PRIORITY_QUERY, PRIORITY_REPLY, PRIORITY_CHATTER = 10, 5, 0


class Brain:
    def __init__(self, net):
        self.net = net
        self.llm = LLM()
        self.settings = Settings()
        self.pending = 0      # requests waiting for (or being answered by) the model

    def busy(self):
        return self.pending > 0

    def _chat(self, p, messages, callback, priority):
        self.pending += 1

        def done(text, err):
            self.pending -= 1
            callback(text, err)

        self.llm.chat(self._model(p), messages, self._options(p), done, priority, think=False)

    def _model(self, p):
        if p.contact is not None:
            if p.contact.model:
                return p.contact.model
            override = self.settings["model_overrides"].get(p.contact.id)
            if override:
                return override
        return self.settings["default_model"]

    def _options(self, p):
        return {"temperature": p.temperature, "num_ctx": int(self.settings["context_size"])}  # same as AIM, so Ollama never reloads

    def _system(self, p, extra):
        player = self.net.nick
        if p.contact is not None:
            aim = self.net.aim_name
            if aim and aim.lower() != player.lower():
                relationship = f"{player} is your buddy from AIM (screen name {aim} there); you know each other well."
            else:
                relationship = f"{player} is your AIM buddy; you know each other well."
        else:
            relationship = f"{player} is someone you've seen around on FurNet."
        tz = p.contact.timezone if p.contact is not None else None
        return BASE.format(nick=p.nick, now=timefmt.now_text(tz), persona=p.persona or "(none)",
                           relationship=relationship) + extra

    def channel_line(self, p, chan, nudge, callback, priority=PRIORITY_CHATTER):
        others = [m for m in self.net.member_nicks(chan.name) if m.lower() != p.nick.lower()]
        extra = CHANNEL.format(channel=chan.name, topic=chan.topic, others=", ".join(others[:25]) or "nobody",
                               player=self.net.nick)
        log = "\n".join(list(chan.log)[-25:]) or "(nothing yet)"
        messages = [{"role": "system", "content": self._system(p, extra)},
                    {"role": "user", "content": f"Recent chat in {chan.name} (most recent last):\n{log}\n\n{nudge}"}]
        self._chat(p, messages, lambda text, err: callback(None if err else parse_line(text, p.nick)), priority)

    def query_line(self, p, history, nudge, callback):
        """history: [{'role','content'}] of the private chat so far (user = the player)."""
        messages = [{"role": "system", "content": self._system(p, QUERY.format(player=self.net.nick))}]
        messages += history[-30:]
        if nudge:
            messages.append({"role": "user", "content": nudge})
        self._chat(p, messages, lambda text, err: callback(None if err else parse_line(text, p.nick)),
                   PRIORITY_QUERY)
