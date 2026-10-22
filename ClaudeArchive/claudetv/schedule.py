"""What's on: a live, wall-clock schedule for each channel, worked out the same way every time.

The schedule runs continuously from 6:00 AM on January 1 of the computer's year (2001 on ClaudeXP, 2011 on Claude7,
2025 on Claude11). Each time of
day draws from its own pool (Ren & Stimpy in the daytime, Mongrels in the evening, Aqua Teen late at night; movies
all day on the movie channel). A pool is a shuffled deck: every item airs once before anything repeats, then the
deck is reshuffled for its next cycle. Programs start on the :00/:15/:30/:45 (movies on any five minutes, like the
premium channels did) and the gaps between them hold 2-3 commercials, a short promo when one fits, and an
'Up Next' card. Commercials only ever air between programs.

Because every shuffle is seeded from the deck's name and cycle number, the schedule is the same on every run and
every PC with the same archive, so the TV Guide can show what's on next week."""
import random
from datetime import datetime, timedelta

from claudecore import host


def _era():
    try:
        return host.era()
    except Exception:
        return 2001


EPOCH = datetime(_era(), 1, 1, 6, 0)
DAY = 86400
MIN_AD = 5                  # seconds; shorter files are broken clips
CARD_MIN = 8                # an Up Next card shorter than this just gets folded into the ads


class Slot:
    """One thing on the air. kind: program | ad | promo | card. start/end are seconds from EPOCH."""
    __slots__ = ("start", "end", "kind", "media", "text", "next")

    def __init__(self, start, end, kind, media=None, text="", next_=None):
        self.start, self.end, self.kind, self.media, self.text, self.next = start, end, kind, media, text, next_

    def when(self):
        return EPOCH + timedelta(seconds=self.start)

    def until(self):
        return EPOCH + timedelta(seconds=self.end)


class Deck:
    """Each item once per cycle, in an order seeded by name and cycle."""

    def __init__(self, name, units):
        self.name, self.units, self.cycle, self.order = name, units, -1, []

    def peek(self, i=0):
        while len(self.order) <= i:
            self.cycle += 1
            more = list(self.units)
            random.Random(f"{self.name}:{self.cycle}").shuffle(more)
            if self.order and more and more[0] is self.order[-1] and len(more) > 1:
                more.append(more.pop(0))          # never the same thing twice in a row across a reshuffle
            self.order += more
        return self.order[i]

    def take(self, i=0):
        self.peek(i)
        return self.order.pop(i)

    def __bool__(self):
        return bool(self.units)


def _units(items):
    """Group two-part episodes (same season and episode, 'Part' in the title) so they air back to back."""
    groups, out = {}, []
    for m in items:
        if "part" in m.title.lower() and m.season and m.episode:
            key = (m.show_key, m.season, m.episode)
            if key not in groups:
                groups[key] = []
                out.append(groups[key])
            groups[key].append(m)
        else:
            out.append([m])
    for g in out:
        g.sort(key=lambda m: str(m.path))
    return out


def _bundle(items, n):
    """Very short episodes air n at a time, in order, back to back (one break per bundle, not per episode)."""
    ordered = sorted(items, key=lambda m: (str(m.season), int(m.episode) if str(m.episode).isdigit() else 0,
                                           str(m.path)))
    return [ordered[i:i + n] for i in range(0, len(ordered), n)]


class Channel:
    """number, call letters, slogan; blocks = [(hour from, hour to, pool name, block title)] in local time.
    pools = {name: [Media]}. promos = [Media] that may fill gaps in a block (by pool name)."""

    def __init__(self, number, call, slogan, blocks=(), pools=None, promos=None, ads=(), grid=15 * 60,
                 fine=None, grids=None, dead=False, bundles=None, fill=False):
        self.number, self.call, self.slogan, self.dead = number, call, slogan, dead
        self.fill = fill                      # a news channel: clips packed into half hours, 1-3 commercials between
        self.blocks = list(blocks)
        self.grid, self.fine, self.grids = grid, fine or grid, grids or {}
        bundles = bundles or {}
        self.decks = {name: Deck(f"{call}:{name}", _bundle(items, bundles[name]) if name in bundles else _units(items))
                      for name, items in (pools or {}).items()}
        self.promos = {name: Deck(f"{call}:{name}:promo", [[m] for m in items])
                       for name, items in (promos or {}).items()}
        self.ads = Deck(f"{call}:ads", [[m] for m in ads if m.secs >= MIN_AD])
        self.slots = []                       # built lazily, in order, from EPOCH
        self._built = 0
        self._rng = random.Random(f"{call}:breaks")

    def label(self):
        return f"{self.number} {self.call}" if self.call else str(self.number)

    # ---- building ---------------------------------------------------------------------------------------
    def _block_at(self, t):
        hour = ((EPOCH.hour * 3600 + t) % DAY) / 3600
        for start, end, pool, title in self.blocks:
            if (start <= hour < end) if start < end else (hour >= start or hour < end):
                if self.decks.get(pool):
                    return pool, title
        for _s, _e, pool, title in self.blocks:            # an empty pool falls back to any non-empty one
            if self.decks.get(pool):
                return pool, title
        return None, ""

    def _next_start(self, t, gap_min, grid):
        """The first start time after t + gap_min: a grid boundary if one comes soon, else a fine boundary."""
        earliest = t + gap_min
        coarse = -(-earliest // grid) * grid
        fine = -(-earliest // self.fine) * self.fine
        return coarse if coarse - earliest <= 4 * 60 else fine

    def _build_until(self, t_end):
        if not self.decks:
            return
        t = self._built
        while t < t_end:
            pool, block_title = self._block_at(t)
            if pool is None:
                return
            deck = self.decks[pool]
            unit = deck.take()
            for m in unit:
                self.slots.append(Slot(t, t + m.secs, "program", m, block_title))
                t += m.secs
            if self.fill:
                # a newscast: short clips run back to back while they fit in this half hour, then 1-3 commercials
                while True:
                    boundary = -(-(t + 30) // self.grid) * self.grid
                    following = deck.peek()
                    if t + sum(m.secs for m in following) + 60 > boundary:
                        break
                    for m in deck.take():
                        self.slots.append(Slot(t, t + m.secs, "program", m, block_title))
                        t += m.secs
                t = self._news_break(t)
            else:
                t = self._fill_break(t, pool, self._rng)
        self._built = t

    def _news_break(self, t):
        """1-3 commercials up to the next half hour (or, if the gap is long, to the next five minutes)."""
        coarse = -(-(t + 30) // self.grid) * self.grid
        n, run = 0, 0
        while self.ads and n < 3 and t + run + self.ads.peek(n)[0].secs + CARD_MIN <= coarse:
            run += self.ads.peek(n)[0].secs
            n += 1
        if n == 0 and self.ads:                           # always at least one between clips
            n, run = 1, self.ads.peek(0)[0].secs
        fine = -(-(t + run) // self.fine) * self.fine
        start = coarse if coarse >= t + run and coarse - (t + run) <= 4 * 60 else fine
        for _ in range(n):
            a = self.ads.take()[0]
            self.slots.append(Slot(t, t + a.secs, "ad", a))
            t += a.secs
        if start > t:
            self.slots.append(Slot(t, start, "card", text="Up Next"))
        return max(start, t)

    def _fill_break(self, t, pool, rng):
        """2 or 3 commercials, a promo if one fits, and an Up Next card to the next start time."""
        grid = self.grids.get(pool, self.grid)
        ads = [self.ads.peek(i)[0] for i in range(3)] if self.ads else []
        choices = []
        for n in ((3, 2) if rng.random() < 0.5 else (2, 3)) if ads else (0,):
            run = sum(a.secs for a in ads[:n])
            start = self._next_start(t, run, grid)
            choices.append((start - t - run, n, start))
        _card, n, start = min(choices, key=lambda c: (c[0] < 0, c[0]))
        for _ in range(n):
            a = self.ads.take()[0]
            self.slots.append(Slot(t, t + a.secs, "ad", a))
            t += a.secs
        promos = self.promos.get(pool)
        while promos and start - t >= promos.peek()[0].secs + CARD_MIN:
            p = promos.take()[0]
            self.slots.append(Slot(t, t + p.secs, "promo", p))
            t += p.secs
            if start - t < 90:
                break
        if start > t:
            self.slots.append(Slot(t, start, "card", text="Up Next"))
        return start

    # ---- queries ----------------------------------------------------------------------------------------
    def ensure(self, t):
        if self._built < t + 3 * 3600:
            self._build_until(t + 3 * 3600)

    def at(self, t):
        """The Slot on the air t seconds after EPOCH (None for a channel with nothing on it)."""
        if self.dead or not self.decks:
            return None
        self.ensure(t)
        lo, hi = 0, len(self.slots) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.slots[mid].start <= t:
                lo = mid
            else:
                hi = mid - 1
        slot = self.slots[lo] if self.slots else None
        if slot is not None and slot.kind == "card":
            slot.next = self.next_program(lo)
        return slot

    def next_program(self, index):
        for s in self.slots[index + 1:]:
            if s.kind == "program":
                return s
        return None

    def programs(self, t_from, t_to):
        """Programs overlapping [t_from, t_to), for the TV Guide."""
        if self.dead or not self.decks:
            return []
        self.ensure(t_to)
        return [s for s in self.slots if s.kind == "program" and s.end > t_from and s.start < t_to]


def seconds(when):
    return int((when - EPOCH).total_seconds())


KFUR_SHOWS = ("FOTP", "WOLFSRAIN", "DAMEKKO")
RAMSAY_SHOWS = ("KNUK", "KNUS", "HOTELHELL", "COOKALONG")
NEWS = (("NEWSCBS", 2, "WCBS", "CBS 2 News Archive", "CBS 2 News"),
        ("NEWSABC", 3, "WABC", "Eyewitness News Archive", "Eyewitness News"),
        ("NEWSWNBC", 4, "WNBC", "News 4 Archive", "News 4 New York"))
OWN_CHANNEL = ("REN", "ATHF", "MONGRELS", "COMEDY", "TOPGEAR", "WHEELER") + KFUR_SHOWS + RAMSAY_SHOWS + \
    tuple(n[0] for n in NEWS)
DEAD = (7, 12, 13)                     # no station: snow (the tuner's DEAD_STATIC picks each one's clip)


ARCHIVE_YEAR = 2001                    # the local news archives are old broadcasts: their breaks stay old too


def _ad_year(m):
    return int(m.year) if str(m.year).isdigit() else None


def era_ads(ads, era, at_least=40):
    """Each computer's own commercials: ClaudeXP the undated ones and everything up to 2001, Claude7 2002-2011,
    Claude11 2012 onward (every channel shows the same programs in every era - only the breaks age). When an era's
    own years are thin, the window opens backwards a few years at a time rather than falling back to everything."""
    if era <= ARCHIVE_YEAR:
        mine = [m for m in ads if _ad_year(m) is None or _ad_year(m) <= ARCHIVE_YEAR]
        return mine or ads
    windows = ((2002, 2011), (1996, 2011)) if era < 2012 else ((2012, 9999), (2008, 9999), (2002, 9999))
    for lo, hi in windows:
        mine = [m for m in ads if _ad_year(m) is not None and lo <= _ad_year(m) <= hi]
        if len(mine) >= at_least:
            return mine
    return mine or ads


def archive_ads(ads):
    """The breaks for the news archives, whatever the era: the old commercials that match the old broadcasts."""
    return era_ads(ads, ARCHIVE_YEAR)


def _one_each(movies):
    """A film that's in the archive twice (Idiocracy as .mp4 and .m4v) airs once."""
    seen, out = set(), []
    for m in movies:
        if m.title.lower() not in seen:
            seen.add(m.title.lower())
            out.append(m)
    return out


def build_channels(items, era=None):
    """The lineup, numbered the way cable was: the local news archives lowest (WCBS 2, WABC 3, WNBC 4), the series
    channels next (WAGG 5 cartoons, KFUR 6 animals and anime, KANI 8 anime with the Orangina commercials, KHAH 9
    stand-up, GRTV 10 Gordon Ramsay, TGTV 11 Top Gear, WDTV 14 Wheeler Dealers), the movie channels up high (KPAW 30,
    and the feature channels CINE 31, REEL 32 and FLIK 33), and dead channels in the gaps."""
    era = era or _era()
    by = {}
    for m in items:
        by.setdefault((m.kind, m.show_key), []).append(m)
    all_ads = by.get(("ad", ""), [])
    ads = era_ads(all_ads, era)
    news_ads = archive_ads(all_ads)

    def shows(*keys):
        return [m for k in keys for kind in ("episode", "special") for m in by.get((kind, k), [])]

    ren = shows("REN")
    athf_specials = by.get(("special", "ATHF"), [])
    athf = by.get(("episode", "ATHF"), []) + [m for m in athf_specials if m.secs <= 35 * 60]
    mongrels = by.get(("episode", "MONGRELS"), [])
    movies = by.get(("movie", ""), []) + [m for m in athf_specials if m.secs > 60 * 60 and "theater" in m.title.lower()]
    features = _one_each(by.get(("movie", "FEATURE"), []))
    other_shows = {}
    for (kind, key), ms in by.items():
        if kind in ("episode", "special") and key not in OWN_CHANNEL:
            other_shows.setdefault("other", []).extend(ms)
    channels = []
    for key, number, call, slogan, title in NEWS:
        channels.append(Channel(number, call, slogan, blocks=[(0, 24, "news", title)],
                                pools={"news": shows(key)}, ads=news_ads, grid=30 * 60, fine=5 * 60, fill=True))
    channels.append(Channel(5, "WAGG", "Cartoons & Comedy, Day and Night", blocks=[
        (6, 19, "ren", "Ren & Stimpy Marathon"),
        (19, 23, "mongrels", "Mongrels Prime Time"),
        (23, 6, "athf", "Late Night Aqua Teen"),
        (6, 19, "other", "Afternoon Cartoons"),
    ], pools={"ren": ren, "mongrels": mongrels, "athf": athf, **other_shows},
        promos={"athf": by.get(("promo", "ATHF"), [])}, ads=ads, grid=15 * 60, fine=5 * 60,
        grids={"mongrels": 30 * 60}))
    shorts = by.get(("episode", "DAMEKKO"), [])
    family = [m for m in movies if m.rating in ("G", "PG")]           # the animated features also air on KFUR
    channels.append(Channel(6, "KFUR", "Fur & Feather TV: Animals, Anime and Animated Features", blocks=[
        (6, 8, "damekko", "Useless Wolf Morning Shorts"),
        (8, 20, "family", "Fur & Feather Features"),
        (20, 23, "fotp", "Father of the Pride"),
        (23, 6, "wolfsrain", "Wolf's Rain After Dark"),
    ], pools={"damekko": shorts, "family": family, "fotp": by.get(("episode", "FOTP"), []),
              "wolfsrain": by.get(("episode", "WOLFSRAIN"), [])},
        promos={"damekko": by.get(("promo", "DAMEKKO"), [])}, ads=ads, grid=30 * 60, fine=5 * 60,
        grids={"damekko": 15 * 60}, bundles={"damekko": 3}))
    channels.append(Channel(8, "KANI", "Anime 8: Japanese Animation Around the Clock", blocks=[
        (6, 10, "damekko", "Useless Wolf Mornings"),
        (10, 16, "wolfsrain", "Wolf's Rain Marathon"),
        (16, 19, "damekko", "Useless Wolf After School"),
        (19, 6, "wolfsrain", "Wolf's Rain Nights"),
    ], pools={"damekko": shorts, "wolfsrain": by.get(("episode", "WOLFSRAIN"), [])},
        promos={"damekko": by.get(("promo", "DAMEKKO"), []), "wolfsrain": by.get(("promo", "WOLFSRAIN"), [])},
        ads=by.get(("ad", "ORANGINA"), []) or ads, grid=30 * 60, fine=5 * 60,
        grids={"damekko": 15 * 60}, bundles={"damekko": 3}))
    channels.append(Channel(9, "KHAH", "Ha-Ha 9: Comedy Around the Clock", blocks=[(0, 24, "comedy", "Ha-Ha 9 Comedy")],
                            pools={"comedy": by.get(("episode", "COMEDY"), [])}, ads=ads, grid=30 * 60, fine=5 * 60))
    ramsay_promos = [m for k in RAMSAY_SHOWS for m in by.get(("promo", k), [])]
    channels.append(Channel(10, "GRTV", "Gordon Ramsay TV: Kitchens, Hotels and Hell",
                            blocks=[(0, 24, "ramsay", "Gordon Ramsay")], pools={"ramsay": shows(*RAMSAY_SHOWS)},
                            promos={"ramsay": ramsay_promos}, ads=ads, grid=30 * 60, fine=5 * 60))
    channels.append(Channel(11, "TGTV", "Top Gear TV: Petrolheads Around the Clock",
                            blocks=[(0, 24, "topgear", "Top Gear")], pools={"topgear": shows("TOPGEAR")},
                            ads=ads, grid=30 * 60, fine=5 * 60))
    channels.append(Channel(14, "WDTV", "Wheeler Dealers: Buy It, Fix It, Sell It",
                            blocks=[(0, 24, "wheeler", "Wheeler Dealers")], pools={"wheeler": shows("WHEELER")},
                            ads=ads, grid=30 * 60, fine=5 * 60))
    channels.append(Channel(30, "KPAW", "Paw Pictures: Movies All Day", blocks=[(0, 24, "movies", "Paw Pictures Presents")],
                            pools={"movies": movies}, ads=ads, grid=30 * 60, fine=5 * 60))
    for number, call, slogan in ((31, "CINE", "Cinema 31: Feature Presentations"),
                                 (32, "REEL", "Reel 32: The Big Picture"),
                                 (33, "FLIK", "Flicks 33: Movies Without End")):
        channels.append(Channel(number, call, slogan, blocks=[(0, 24, "features", "Feature Presentation")],
                                pools={"features": features}, ads=ads, grid=30 * 60, fine=5 * 60))
    channels = [ch for ch in channels if ch.decks and any(ch.decks.values())]   # (a channel with nothing to air)
    taken = {c.number for c in channels}
    dead = [Channel(n, "", "", dead=True) for n in DEAD if n not in taken]
    return sorted(channels + dead, key=lambda c: c.number)
