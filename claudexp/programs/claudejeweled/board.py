"""Claudejeweled's rules: an 8 x 8 board of gems. Swap two neighbours to line up three or more of a colour.

Four in a line makes a Flame Gem (it blows up its 3 x 3 neighbourhood when matched), an L or T shape makes a
Star Gem (it clears its whole row and column), and five in a line makes a Hypercube - swap it with any gem to
clear every gem of that colour. Cleared gems leave holes, everything above falls, new gems drop in, and any
matches that makes are cascades worth more and more.

Cells are (row, col) with row 0 at the top.
"""
import random

N = 8
COLOURS = 7                              # red, orange, yellow, green, blue, purple, white
NAMES = ["Ruby", "Amber", "Topaz", "Emerald", "Sapphire", "Amethyst", "Diamond"]


class Gem:
    __slots__ = ("colour", "special", "dx", "dy", "vy")

    def __init__(self, colour, special=None):
        self.colour, self.special = colour, special
        self.dx = self.dy = 0.0                # where it's drawn, in cells away from its square (for sliding)
        self.vy = 0.0                          # falling speed


class Board:
    def __init__(self, rnd=None):
        self.rnd = rnd or random.Random()
        self.grid = []
        self.hyper_swap = None
        self.swapped = ()
        self.cascade = 0
        self.fill_fresh()

    # ---- setting up ---------------------------------------------------------------------------------------------
    def fill_fresh(self):
        """A new board with no matches on it and at least one move."""
        while True:
            self.grid = [[None] * N for _ in range(N)]
            for r in range(N):
                for c in range(N):
                    while True:
                        col = self.rnd.randrange(COLOURS)
                        if c >= 2 and self.colour(r, c - 1) == col == self.colour(r, c - 2):
                            continue
                        if r >= 2 and self.colour(r - 1, c) == col == self.colour(r - 2, c):
                            continue
                        break
                    self.grid[r][c] = Gem(col)
            if self.find_move():
                return

    def shuffle(self):
        """Mix the gems up (keeping the specials) until there's a move and no ready-made matches."""
        gems = [g for row in self.grid for g in row]
        for _ in range(200):
            self.rnd.shuffle(gems)
            self.grid = [gems[r * N:(r + 1) * N] for r in range(N)]
            if not self.runs() and self.find_move():
                return
        self.fill_fresh()

    # ---- looking at the board -------------------------------------------------------------------------------------
    def get(self, cell):
        return self.grid[cell[0]][cell[1]]

    def colour(self, r, c):
        g = self.grid[r][c]
        return None if g is None or g.special == "hyper" else g.colour

    def runs(self):
        """Every straight line of three or more of one colour, as lists of cells."""
        out = []
        for r in range(N):
            c = 0
            while c < N:
                col, e = self.colour(r, c), c + 1
                while col is not None and e < N and self.colour(r, e) == col:
                    e += 1
                if col is not None and e - c >= 3:
                    out.append([(r, x) for x in range(c, e)])
                c = e
        for c in range(N):
            r = 0
            while r < N:
                col, e = self.colour(r, c), r + 1
                while col is not None and e < N and self.colour(e, c) == col:
                    e += 1
                if col is not None and e - r >= 3:
                    out.append([(y, c) for y in range(r, e)])
                r = e
        return out

    @staticmethod
    def groups(runs):
        """Runs that share a cell (an L, a T or a cross) are one group."""
        groups = []
        for run in runs:
            cells, longest = set(run), len(run)
            for g in [g for g in groups if g[0] & cells]:
                groups.remove(g)
                cells |= g[0]
                longest = max(longest, g[1])
            groups.append((cells, longest))
        return groups

    def find_move(self):
        """A swap that makes a match, or None."""
        for r in range(N):
            for c in range(N):
                for dr, dc in ((0, 1), (1, 0)):
                    r2, c2 = r + dr, c + dc
                    if r2 >= N or c2 >= N:
                        continue
                    a, b = (r, c), (r2, c2)
                    if self.get(a).special == "hyper" or self.get(b).special == "hyper":
                        return a, b
                    self.swap(a, b)
                    ok = self._makes_run(a) or self._makes_run(b)
                    self.swap(a, b)
                    if ok:
                        return a, b
        return None

    def _makes_run(self, cell):
        r, c = cell
        col = self.colour(r, c)
        if col is None:
            return False
        n = 1
        x = c - 1
        while x >= 0 and self.colour(r, x) == col:
            n, x = n + 1, x - 1
        x = c + 1
        while x < N and self.colour(r, x) == col:
            n, x = n + 1, x + 1
        if n >= 3:
            return True
        n = 1
        y = r - 1
        while y >= 0 and self.colour(y, c) == col:
            n, y = n + 1, y - 1
        y = r + 1
        while y < N and self.colour(y, c) == col:
            n, y = n + 1, y + 1
        return n >= 3

    # ---- moves ----------------------------------------------------------------------------------------------------
    def swap(self, a, b):
        ga, gb = self.get(a), self.get(b)
        self.grid[a[0]][a[1]], self.grid[b[0]][b[1]] = gb, ga

    def productive(self, a, b):
        """After swapping a and b: does it do anything? (Arms a hypercube if one was swapped.)"""
        ga, gb = self.get(a), self.get(b)
        self.cascade = 0
        if ga.special == "hyper" or gb.special == "hyper":
            self.hyper_swap = (a, b)
            return True
        if self._makes_run(a) or self._makes_run(b):
            self.swapped = (a, b)
            return True
        return False

    def clear_step(self):
        """Clear whatever matches are on the board, set off any special gems caught in it and make new ones.

        Returns None when nothing matched, otherwise a dict: cleared [(cell, gem)], made [(cell, gem)],
        blasts [(kind, cell)], zaps [(from_cell, [cells])], score, cascade, biggest (longest line)."""
        cleared = set()
        made, blasts, zaps = [], [], []
        score = 0
        biggest = 0
        self.cascade += 1
        if self.hyper_swap:
            a, b = self.hyper_swap
            self.hyper_swap = None
            ga, gb = self.get(a), self.get(b)
            if ga.special == "hyper" and gb.special == "hyper":
                cells = [(r, c) for r in range(N) for c in range(N)]
                zaps.append((a, cells))
                cleared |= set(cells)
                score += 2500
            else:
                h, other = (a, b) if ga.special == "hyper" else (b, a)
                colour = self.get(other).colour
                cells = [(r, c) for r in range(N) for c in range(N)
                         if self.grid[r][c].colour == colour and self.grid[r][c].special != "hyper"]
                zaps.append((h, cells))
                cleared |= set(cells) | {h}
                score += 50 * len(cells)
        for cells, longest in self.groups(self.runs()):
            n = len(cells)
            biggest = max(biggest, longest)
            straight = len({r for r, _c in cells}) == 1 or len({c for _r, c in cells}) == 1
            special = "hyper" if longest >= 5 else "star" if not straight else "flame" if n == 4 else None
            score += {3: 50, 4: 100}.get(n, 150 + (n - 5) * 50) if straight else 150 + (n - 5) * 30
            cleared |= cells
            if special:
                spot = next((c for c in self.swapped if c in cells), None) if self.cascade == 1 else None
                if spot is None:
                    ordered = sorted(cells)
                    spot = ordered[len(ordered) // 2]
                made.append((spot, Gem(self.get(spot).colour, special)))
        if not cleared:
            self.cascade -= 1
            return None
        # set off the special gems caught in it (and the ones they catch)
        queue = [c for c in cleared if self.get(c).special]
        done = set()
        extra = 0
        while queue:
            cell = queue.pop()
            if cell in done:
                continue
            done.add(cell)
            g = self.get(cell)
            r, c = cell
            if g.special == "flame":
                area = [(y, x) for y in range(r - 1, r + 2) for x in range(c - 1, c + 2) if 0 <= y < N and 0 <= x < N]
                blasts.append(("flame", cell))
            elif g.special == "star":
                area = [(r, x) for x in range(N)] + [(y, c) for y in range(N)]
                blasts.append(("star", cell))
            elif g.special == "hyper" and not zaps:
                colours = [self.grid[y][x].colour for y in range(N) for x in range(N) if self.grid[y][x].special != "hyper"]
                colour = self.rnd.choice(colours) if colours else 0
                area = [(y, x) for y in range(N) for x in range(N) if self.grid[y][x].colour == colour]
                zaps.append((cell, area))
            else:
                continue
            for a in area:
                if a not in cleared:
                    cleared.add(a)
                    extra += 1
                    if self.get(a).special:
                        queue.append(a)
        score += extra * 20
        out = []
        for (r, c) in cleared:
            out.append(((r, c), self.grid[r][c]))
            self.grid[r][c] = None
        for (r, c), gem in made:
            self.grid[r][c] = gem
        self.swapped = ()
        score *= self.cascade
        return {"cleared": out, "made": made, "blasts": blasts, "zaps": zaps, "score": score,
                "cascade": self.cascade, "biggest": biggest}

    def collapse(self):
        """Gems fall into the holes and new ones drop in from above. Sets each moved gem's dy (negative: it's
        drawn above its square and falls into place)."""
        for c in range(N):
            gems = [self.grid[r][c] for r in range(N - 1, -1, -1) if self.grid[r][c] is not None]
            rows = [r for r in range(N - 1, -1, -1) if self.grid[r][c] is not None]
            missing = N - len(gems)
            for i in range(N):
                r = N - 1 - i
                if i < len(gems):
                    g = gems[i]
                    g.dy += rows[i] - r
                else:
                    g = Gem(self.rnd.randrange(COLOURS))
                    g.dy = -missing - 0.3
                self.grid[r][c] = g
