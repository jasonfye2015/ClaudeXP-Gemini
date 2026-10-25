"""Kithylin's words. A Kithylin model answers through the Timeline's broker like everyone else: an add-on
(kithylin-nemomix-*) rides on the residents' NemoMix base at scale 0 and is switched on just for his requests, so one
7.5 GB model on the card serves both sides of every conversation; a whole Kithylin model installed in the Timeline's
models folder (kithylin-v1 with --install-timeline) is asked directly; without either, the conversation model is
asked to be Kithylin from his character prompt alone.

    v = Voice("addon:kithylin-nemomix-recent")
    v.say(system, history, done, instruction="...")      # done(text) on the UI thread, "" if nothing came
"""
import re

from claudecore.ai import broker, llm_server

KITHYLIN = "Kithylin"


def choices():
    """[(key, label)] of the ways Kithylin can speak on this computer, best first."""
    from claudecore.ai import ai_models
    out = []
    usable = [a for a in llm_server.addons() if ai_models.get(a[3]) is not None]
    for _i, name, path, base in sorted(usable, key=lambda a: a[2].stat().st_mtime, reverse=True):   # newest first
        out.append((f"addon:{name}", f"{name}  (add-on for {base})"))
    for m in ai_models.installed():
        if m.info.get("kithylin"):
            out.append((f"model:{m.id}", f"{m.id}  (a whole Kithylin model)"))
    out.append(("plain", "The buddies' own model, asked to be Kithylin (not trained on you)"))
    return out


def persona(name="{name}"):
    """Who Kithylin is, as Kithylin AI has it (its Settings; the defaults until changed), with the other person's name."""
    try:
        from kithylinai import store
        s = store.Settings()
        character, codes = s["character"], s["codes_prompt"]
    except Exception:
        try:
            from kithylinai import defaults
            character = defaults.DEFAULT_CHARACTER
            codes = defaults.codes_prompt(defaults.KITHYLIN_FURCODE, defaults.KITHYLIN_YIFFCODE)
        except Exception:
            character, codes = ("You are Kithylin, an anthro husky, chatting online with {name}. Reply as yourself: "
                                "short, casual messages."), ""
    text = character.replace("{name}", name)
    return text + ("\n\n" + codes if codes else "")


def clean(text, max_lines=None):
    """A reply as it would be typed: no 'Kithylin:' prefix, no wrapping quotes, no stage directions in brackets."""
    text = (text or "").strip()
    text = re.sub(r"^\s*(\*\*)?kithylin(\*\*)?\s*[:>-]\s*", "", text, flags=re.I)
    text = re.sub(r"^\[[^\]]*\]\s*", "", text)
    text = text.replace("<|im_end|>", "").replace("<|im_start|>", "").strip()
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if max_lines:
        lines = lines[:max_lines]
    text = "\n".join(lines).strip()
    if len(text) > 1 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text


class Voice:
    def __init__(self, choice="auto"):
        self.choice = choice
        self.job = None

    def resolve(self):
        """(model id, options) for the chosen way of speaking; the first available if the choice is gone."""
        from claudecore.ai import ai_models
        keys = [k for k, _l in choices()]
        choice = self.choice if self.choice in keys else (keys[0] if keys else "plain")
        if choice.startswith("addon:"):
            name = choice[6:]
            for i, aname, _path, base in llm_server.addons():
                if aname == name:
                    return base, {"lora": [{"id": i, "scale": 1.0}]}
        if choice.startswith("model:"):
            return choice[6:], {}
        return ai_models.model_for("conversation"), {}

    def say(self, system, history, done, instruction=None, max_tokens=140, temperature=0.9, priority=None):
        """Ask Kithylin for his next line. history: [{"role": "user"|"assistant", "content"}] - the other side is
        "user", Kithylin's own lines "assistant". done(text) with the cleaned reply ("" on nothing / error)."""
        model, options = self.resolve()
        msgs = [{"role": "system", "content": system}] + list(history)
        if instruction:
            msgs.append({"role": "user", "content": f"[{instruction}]"})
        elif not msgs[-1:] or msgs[-1]["role"] != "user":
            msgs.append({"role": "user", "content": "[Say something.]"})
        options = dict(options, temperature=temperature, num_predict=max_tokens)

        def finished(text, err):
            self.job = None
            done("" if err else clean(text))
        self.job = broker.get().chat(model, msgs, options, finished, broker.AIM if priority is None else priority,
                                     think=False)
        return self.job

    def stop(self):
        if self.job is not None:
            try:
                self.job.stop()
            except Exception:
                pass
            self.job = None
