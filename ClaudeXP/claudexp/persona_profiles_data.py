"""What Fur Persona Profiles shows: one Contact Persona Style's residents and prompting, in the same shape whatever
the style - {"id", "meta", "contacts": {name: AIM contact}, "prompts": {name: sample AIM system prompt},
"prompting": {module: {name: {"kind", "value"}}}, "voices": {name: {...}}}.

A frozen style is read from its folder. The Development style is worked out in a fresh process
(python -m claudexp.persona_profiles_data dev OUT.json), because on a computer set up with a frozen style that
style's prompting is loaded over the live code, and the Development style would come out looking like it."""
import json
import sys
from pathlib import Path

from . import persona_style


def _load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def frozen_view(sid):
    d = persona_style.folder(sid)
    contacts = {f.stem: _load(f) for f in sorted((d / "generated" / "ClaudeAIM" / "contacts").glob("*.json"))}
    prompts = {f.stem: f.read_text(encoding="utf-8")
               for f in sorted((d / "prompts" / "AIM system prompts").glob("*.txt"))}
    return {"id": sid, "meta": _load(d / "style.json"), "contacts": contacts, "prompts": prompts,
            "prompting": _load(d / "prompting.json"), "voices": _load(d / "voices.json")}


def dev_view():
    """The Development style as the code and Residents/ have it now (run in a process of its own)."""
    from . import realism
    realism._paths()
    from claudeaim.contacts import Contact

    from . import residents_sync, voices
    persona_style.testing(persona_style.DEV)
    contacts = {}
    R = residents_sync._residents()
    for name in R.names(residents_sync.ERA) if R else []:
        r = R.load(name, residents_sync.ERA)
        aim = residents_sync.aim_contact(r) if r else None
        if aim:
            contacts[name] = aim
    prompts = persona_style.sample_aim_prompts(contacts=[Contact.from_dict(n, c) for n, c in contacts.items()])
    meta = next(s for s in persona_style.available() if s["id"] == persona_style.DEV)
    return {"id": persona_style.DEV, "meta": dict(meta, features=["voice"]), "contacts": contacts,
            "prompts": prompts, "prompting": persona_style.capture(),
            "voices": {n: voices.describe(n) for n in contacts}}


def latest_evals():
    """The newest realism test of each style: {style id: result (without the replies)}."""
    out = {}
    for f in sorted((persona_style.styles_dir() / "evals").glob("*.json")):
        res = _load(f)
        if res.get("style"):
            res.pop("replies_detail", None)
            res["file"] = str(f.with_suffix(".md"))
            out[res["style"]] = res
    return out


if __name__ == "__main__":
    out = Path(sys.argv[2])
    out.write_text(json.dumps(dev_view() if sys.argv[1] == persona_style.DEV else frozen_view(sys.argv[1]),
                              ensure_ascii=False), encoding="utf-8")
