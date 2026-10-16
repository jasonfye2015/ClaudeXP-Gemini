"""The residents' life on FurAffinity: favourites, shouts, journals, comments and the sites they link to.

Kept in data/furaffinity.json. Favourites start out seeded (each resident likes a handful of pieces, Main furs more
than Support, Support more than Background); what they write - journals, shouts, comments - is added over time by
the life sim (see activity.py). Thread-safe: the web server reads it while the life sim writes."""
import json
import random
import threading

from ....paths import DATA

FILE = DATA / "furaffinity.json"
SEED_FAVES = {"main": (25, 50), "support": (10, 25), "background": (3, 12), "user": (0, 0)}
SITE_LINKS = [("http://www.housepetscomic.com/", "Housepets!"), ("http://www.clubstripes.com/", "Club Stripes"),
              ("http://www.jaynaylor.com/", "Jay Naylor"), ("http://www.yiffstar.com/", "YiffStar"),
              ("http://www.sexyfur.com/", "SexyFur"), ("http://www.hardblush.com/", "Hardblush")]

_store = None
_lock = threading.RLock()


class Social:
    def __init__(self, site):
        self.site = site
        try:
            self.data = json.loads(FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {}
        for key in ("faves", "shouts", "journals", "comments", "links", "active"):
            self.data.setdefault(key, {})
        if not self.data.get("seeded"):
            self._seed()

    def save(self):
        with _lock:
            FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp = FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data), encoding="utf-8")
            tmp.replace(FILE)

    # ---- the first visit: everyone already likes some art and some sites -------------------------------------------
    def _seed(self):
        idx = self.site.index()
        pool = [s.id for s in self.site._visible(idx.newest)]
        if not pool:
            return
        for low, (name, r) in self.site.residents().items():
            rng = random.Random(f"fa-seed:{low}")
            lo, hi = SEED_FAVES.get(r.tier, (3, 12))
            if hi:
                self.data["faves"][name] = rng.sample(pool, min(len(pool), rng.randint(lo, hi)))
            if r.tier in ("main", "support") and rng.random() < (0.7 if r.tier == "main" else 0.35):
                self.data["links"][name] = [list(x) for x in rng.sample(SITE_LINKS, rng.randint(1, 3))]
        self.data["seeded"] = True
        self.save()

    # ---- reading ------------------------------------------------------------------------------------------------
    def faves(self, name):
        return list(self.data["faves"].get(self._key(self.data["faves"], name), []))

    def favers(self, sid):
        with _lock:
            return [n for n, ids in self.data["faves"].items() if sid in ids]

    def shouts(self, name):
        return list(self.data["shouts"].get(self._key(self.data["shouts"], name), []))

    def journals(self, name):
        return list(self.data["journals"].get(self._key(self.data["journals"], name), []))

    def comments(self, sid):
        return list(self.data["comments"].get(str(sid), []))

    def links(self, name):
        return [tuple(x) for x in self.data["links"].get(self._key(self.data["links"], name), [])]

    def latest_journals(self, n):
        out = []
        with _lock:
            for user, js in self.data["journals"].items():
                for i, j in enumerate(js, 1):
                    out.append({**j, "user": user, "n": i})
        out.sort(key=lambda j: j.get("t", 0), reverse=True)
        return out[:n]

    def recently_active(self, n):
        with _lock:
            return [u for u, _t in sorted(self.data["active"].items(), key=lambda kv: kv[1], reverse=True)[:n]]

    @staticmethod
    def _key(table, name):
        if name in table:
            return name
        low = name.lower()
        return next((k for k in table if k.lower() == low), name)

    # ---- writing ------------------------------------------------------------------------------------------------
    def _stamp(self, user):
        from .... import clock
        now = clock.now()
        self.data["active"][user] = now.timestamp()
        return now.strftime("%b %d, %Y %I:%M %p"), now.timestamp()

    def toggle_fave(self, user, sid):
        with _lock:
            ids = self.data["faves"].setdefault(self._key(self.data["faves"], user), [])
            if sid in ids:
                ids.remove(sid)
            else:
                ids.append(sid)
            self._stamp(user)
            self.save()

    def add_fave(self, user, sid):
        with _lock:
            ids = self.data["faves"].setdefault(self._key(self.data["faves"], user), [])
            if sid not in ids:
                ids.append(sid)
                self._stamp(user)
                self.save()

    def add_shout(self, to, sender, text):
        with _lock:
            when, t = self._stamp(sender)
            self.data["shouts"].setdefault(self._key(self.data["shouts"], to), []).append(
                {"from": sender, "text": text, "when": when, "t": t})
            self.save()

    def add_journal(self, user, title, text):
        with _lock:
            when, t = self._stamp(user)
            self.data["journals"].setdefault(self._key(self.data["journals"], user), []).append(
                {"title": title, "text": text, "when": when, "t": t})
            self.save()

    def add_link(self, user, link):
        with _lock:
            self.data["links"].setdefault(self._key(self.data["links"], user), []).append(list(link))
            self._stamp(user)
            self.save()

    def add_comment(self, sid, sender, text):
        with _lock:
            when, t = self._stamp(sender)
            self.data["comments"].setdefault(str(sid), []).append({"from": sender, "text": text, "when": when, "t": t})
            self.save()


def get(site):
    global _store
    with _lock:
        if _store is None:
            _store = Social(site)
        return _store
