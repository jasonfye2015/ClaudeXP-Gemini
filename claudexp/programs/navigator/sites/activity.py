"""The residents use FurAffinity while you're logged on: now and then one of them favourites some art, shouts on a
friend's page, comments on a picture, writes a journal or links a site they like (social.py stores it).

Tiered, as the user asked: Main furs (AIM buddies) are the most active and write the most, Support furs post now
and then, Background furs mostly just favourite art. Writing uses the background language model at the lowest
priority; without a model they still favourite art and share links."""
import random
import re

from PySide6.QtCore import QObject, QTimer

from .... import broker

FIRST_DELAY_S = 45                  # after logon
EVERY_MINUTES = (6, 14)             # between actions
CATCH_UP = 4                        # actions right after logon (the site moved on while the PC was off)
TIER_WEIGHT = {"main": 6, "support": 3, "background": 1}
# action -> weight, per tier
ACTIONS = {"main": {"journal": 14, "shout": 30, "comment": 24, "fave": 27, "link": 5},
           "support": {"journal": 8, "shout": 24, "comment": 18, "fave": 45, "link": 5},
           "background": {"journal": 0, "shout": 8, "comment": 8, "fave": 84, "link": 0}}
STYLE = ("Write like a real person online in 2001: casual, in your own voice, plain text, no hashtags, no emoji "
         "(old-school smileys like :) are fine). Keep it friendly and keep it clean: nothing sexually explicit.")

_runner = None


def start(desktop):
    global _runner
    if _runner is None:
        _runner = Activity(desktop)
    return _runner


class Activity(QObject):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.tick)
        self.pending = CATCH_UP
        self.busy = False
        self.timer.start(FIRST_DELAY_S * 1000)

    def site(self):
        from . import sites
        fa = next((s for s in sites() if s.host == "www.furaffinity.net"), None)
        return fa if fa is not None and fa.installed() else None

    def tick(self):
        try:
            if not self.busy:
                self.act()
        finally:
            if self.pending > 0:
                self.pending -= 1
                self.timer.start(20 * 1000)
            else:
                self.timer.start(int(random.uniform(*EVERY_MINUTES) * 60 * 1000))

    # ---- one action -----------------------------------------------------------------------------------------
    def act(self):
        fa = self.site()
        if fa is None:
            return
        people = [(n, r) for n, r in fa.residents().values() if r.tier in TIER_WEIGHT]
        if not people:
            return
        name, r = random.choices(people, weights=[TIER_WEIGHT[r.tier] for _n, r in people])[0]
        acts = ACTIONS[r.tier]
        action = random.choices(list(acts), weights=list(acts.values()))[0]
        soc = fa.social()
        if action in ("journal", "shout", "comment") and not self._model():
            action = "fave"
        if action == "fave":
            pool = [s.id for s in fa._visible(fa.index().newest[:4000])]
            for sid in random.sample(pool, min(len(pool), random.randint(1, 3))):
                soc.add_fave(name, sid)
        elif action == "link":
            from .social import SITE_LINKS
            have = {u for u, _t in soc.links(name)}
            choice = [x for x in SITE_LINKS if x[0] not in have]
            if choice:
                soc.add_link(name, random.choice(choice))
        elif action == "shout":
            self._shout(fa, name, r, people)
        elif action == "comment":
            self._comment(fa, name, r)
        elif action == "journal":
            self._journal(fa, name, r)

    def _model(self):
        from .... import ai_models, llm_server
        if not llm_server.available():
            return ""
        return ai_models.model_for("background")

    def _ask(self, prompt, done):
        model = self._model()
        if not model:
            return
        from .... import ai_models
        self.busy = True

        def finished(text, err):
            self.busy = False
            text = (text or "").strip()
            if not err and text:
                done(text)
        broker.get().chat(model, [{"role": "user", "content": prompt}],
                          {"num_ctx": int(ai_models.config()["context"]), "temperature": 0.9}, finished,
                          broker.BACKGROUND, think=False)

    @staticmethod
    def _who(name, r):
        """Who they are, for the prompt."""
        persona = ((r.aim or {}).get("persona") or (r.irc or {}).get("persona") or (r.muck or {}).get("persona")
                   or "")
        rec = r.record or {}
        if not persona:
            persona = " ".join(x for x in (rec.get("summary", ""), rec.get("personality", "")) if x)
        from .... import clock
        now = clock.now()
        return (f"You are {name}, a furry with an account on FurAffinity, the furry art site. It is "
                f"{now:%B} {now.year}.\nAbout you: {persona.strip()[:1500]}\n")

    def _shout(self, fa, name, r, people):
        friends = [f for f in (r.record or {}).get("friends", []) if isinstance(f, str)]
        known = {n.lower(): n for n, _r in people}
        targets = [known[f.lower()] for f in friends if f.lower() in known]
        if not targets:
            targets = [n for n, rr in people if n != name and (rr.tier == "main" or random.random() < 0.15)]
        if not targets:
            return
        target = random.choice(targets)
        prompt = (self._who(name, r) + f"\nWrite a short 'shout' to leave on {target}'s FurAffinity userpage: one or "
                  "two sentences, like a quick hello, a compliment, an inside joke, or asking how they've been. "
                  f"{STYLE}\nReply with only the shout.")
        self._ask(prompt, lambda text: fa.social().add_shout(target, name, _clean(text, 300)))

    def _comment(self, fa, name, r):
        pool = fa._visible(fa.index().newest[:3000])
        if not pool:
            return
        s = random.choice(pool)
        prompt = (self._who(name, r) + f"\nYou're looking at a picture on FurAffinity called \"{s.title}\" by the "
                  f"artist {s.artist}. Write a short comment to leave under it: one or two sentences, the kind people "
                  f"really leave (praise, what you like about it, a friendly question). {STYLE}\n"
                  "Reply with only the comment.")

        def done(text):
            fa.social().add_comment(s.id, name, _clean(text, 300))
            fa.social().add_fave(name, s.id) if random.random() < 0.5 else None
        self._ask(prompt, done)

    def _journal(self, fa, name, r):
        from ....life import get as life
        recent = ""
        if life() is not None:
            try:
                recent = life().context(name)
            except Exception:
                recent = ""
        prompt = (self._who(name, r) + (f"\nWhat's been happening in your life lately:\n{recent[:1500]}\n" if recent
                                        else "") +
                  "\nWrite a FurAffinity journal entry about what's going on with you lately (your week, something "
                  "you're excited about, a con, art you're working on or saw, a rant, whatever fits you). The first "
                  "line is the journal's title (under 8 words). Then two to four short paragraphs, under 170 words "
                  f"in all. {STYLE}\nReply with only the title line and the entry.")

        def done(text):
            lines = [l.strip() for l in text.splitlines()]
            lines = [l for l in lines if l]
            if len(lines) < 2:
                return
            title = _clean(re.sub(r"^(title\s*:\s*)", "", lines[0], flags=re.I), 80)
            body = "\n\n".join(_clean(l, 1200) for l in lines[1:])
            fa.social().add_journal(name, title, body[:1600])
        self._ask(prompt, done)


def _clean(text, limit):
    text = re.sub(r"[*_#`]+", "", text).strip().strip('"“”‘’').strip()
    text = re.sub(r"^(shout|comment|journal)\s*:\s*", "", text, flags=re.I)
    return text[:limit]
