"""The Hollow Oak, inside: its shape, and what can be walked.

One tall hollow, its axis the y axis (y up), the trunk's inner wall a ring about it - wider at the roots, narrowing as
it climbs, fluted and lumpy as old heartwood is. A ledge spirals up the wall from the floor to the crown (the way up
for anything without eight legs), flattening into landings where chambers open into the wood: the gallery, the
larder, the high hollow, and at the top the crown, open to the sky. A tunnel through the roots is the way in.
Knot-holes let the moon in, in narrow shafts.

Units: one unit is about two and a half metres (Claude's eye is 0.62 above his feet, as in the rest of the Timeline's
first-person games). All of it is plain Python and numpy: the renderer builds its meshes from these same functions,
and the tests walk it.

    tree = Tree()
    tree.wall_r(theta, y)            the inner wall's distance from the axis
    tree.floor_at(x, z, feet)        the highest ground under (x, z) a walker with feet at `feet` can stand on
    tree.can_stand(x, z, feet, r)    whether a walker of radius r fits there
"""
import math

TOP = 30.0                      # where the trunk ends, broken open to the sky
R0 = 7.0                        # the hollow's radius at the roots, give or take
LEDGE_W = 1.6                   # how far the ledge stands out from the wall
PITCH = 6.4                     # how much the ledge climbs in one turn
STEP = 0.45                     # the highest step a walker takes without climbing
THETA_IN = 0.0                  # where the root tunnel comes in (angle = atan2(z, x))
TUNNEL_LEN = 9.0
TUNNEL_HALF = 0.78
TUNNEL_CEIL = 1.7
CHAMBER_DEPTH = 2.6
CHAMBER_HIGH = 2.6
# the landings: (name, how far round the spiral they start (radians), how far round they run) - flat, a chamber
# opening off each into the wood
LANDINGS = (("gallery", 1.7 * math.tau, 0.55), ("larder", 2.75 * math.tau, 0.5), ("high hollow", 3.6 * math.tau, 0.45),
            ("crown", 4.35 * math.tau, 0.9))
# knot-holes: (angle, height, radius) - the moon comes in through them
OUT_LEN, OUT_HALF = 28.0, 14.0   # (outside: the glade beyond the roots' mouth, in the tunnel's own frame)
OUT_TREES = ((6.0, -9.5, 0.7), (11.0, 10.5, 0.9), (16.0, -12.0, 0.8), (20.5, 8.0, 0.75), (25.0, -6.0, 0.95),
             (26.5, 11.5, 0.7), (14.0, -4.5, 0.55), (9.0, 6.5, 0.6), (23.0, 2.5, 0.65), (3.5, 12.0, 0.8),
             (18.0, 13.0, 0.85), (27.0, -12.5, 0.75))      # ((along past the mouth, across, trunk radius): the forest)
KNOTS = ((1.1, 6.0, 0.55), (3.9, 10.5, 0.45), (2.4, 15.0, 0.6), (5.2, 19.5, 0.5), (0.4, 23.5, 0.55), (4.4, 26.5, 0.5))
# the glowing fungus: (angle, height, size) shelves on the wall
FUNGI = ((0.7, 1.2, 1.0), (2.3, 0.6, 1.3), (3.7, 1.8, 0.8), (5.0, 0.9, 1.1), (1.6, 4.0, 0.9), (4.3, 5.5, 1.2),
         (0.2, 7.5, 0.8), (2.9, 9.0, 1.0), (5.6, 11.0, 0.9), (1.2, 13.5, 1.1), (3.5, 14.8, 0.8), (5.9, 17.0, 1.0),
         (2.0, 18.5, 0.9), (4.0, 21.0, 1.1), (0.9, 22.5, 0.8), (3.0, 24.8, 1.0), (5.3, 27.0, 0.9))


def _wrap(a):
    return a % math.tau


class Tree:
    def __init__(self):
        # the spiral, as a table of (s0, s1, h0, h1): from s0 to s1 radians round it, from height h0 to h1
        self.segments = []
        s, h = 0.0, 0.0
        k = PITCH / math.tau                                   # (height per radian on a rising stretch)
        for name, start, run in LANDINGS:
            self.segments.append((s, start, h, h + (start - s) * k))
            h += (start - s) * k
            self.segments.append((start, start + run, h, h))      # (a landing: flat)
            s = start + run
        self.s_end = s
        self.top_h = h
        self.landing_h = {}
        for (name, start, run), seg in zip(LANDINGS, [g for g in self.segments if g[2] == g[3]]):
            self.landing_h[name] = seg[2]
        # the start: in the root tunnel, its far end, looking in; or (a new night) out in the glade, at dusk
        self.start = self.tunnel_point(TUNNEL_LEN - 1.2, 0.0) + (THETA_IN + math.pi,)
        self.start_outside = self.tunnel_point(TUNNEL_LEN + 21.0, 0.6) + (THETA_IN + math.pi,)

    # ---- the wall --------------------------------------------------------------------------------------------
    def base_r(self, theta, y):
        """The wall without its chambers: fluted, lumpy, narrowing as it climbs, flaring at the roots."""
        r = R0 * (1 + 0.045 * math.sin(13 * theta + 0.7 * math.sin(3 * theta)) + 0.035 * math.sin(5 * theta + 1.3)
                  + 0.03 * math.sin(2 * theta + y * 0.21) + 0.02 * math.sin(7 * theta - y * 0.37))
        r *= 1.0 - 0.16 * min(1.0, max(0.0, y) / TOP)
        r -= 1.1 * math.exp(-max(0.0, y) / 1.1) * max(0.0, math.sin(6 * theta + 0.8)) ** 3      # (root buttresses)
        return r

    def wall_r(self, theta, y):
        """The inner wall's distance from the axis at this angle and height, chambers and all."""
        r = self.base_r(theta, y)
        for name, start, run in LANDINGS[:-1]:
            h = self.landing_h[name]
            if h <= y <= h + CHAMBER_HIGH:
                mid = self.theta_of(start + run / 2)
                d = abs((_wrap(theta) - mid + math.pi) % math.tau - math.pi)
                half = run / 2
                if d < half:
                    across = math.cos(d / half * math.pi / 2)
                    up = math.sin(min(1.0, (y - h) / CHAMBER_HIGH) * math.pi) ** 0.35
                    r += CHAMBER_DEPTH * across * up
        return r

    def knot_at(self, theta, y):
        """Whether the wall is open here (a knot-hole)."""
        for a, h, rad in KNOTS:
            da = abs((_wrap(theta) - a + math.pi) % math.tau - math.pi) * self.base_r(a, h)
            if da * da + (y - h) ** 2 < rad * rad:
                return True
        return False

    # ---- the ledge -------------------------------------------------------------------------------------------
    def ledge_h(self, s):
        """The ledge's height s radians round the spiral from its foot."""
        for s0, s1, h0, h1 in self.segments:
            if s0 <= s <= s1:
                return h0 + (h1 - h0) * (s - s0) / max(1e-9, s1 - s0)
        return None

    def ledge_turns(self, theta):
        """Every place round the spiral at this angle: -> [s]."""
        base = _wrap(theta - THETA_IN - 0.35)
        return [base + k * math.tau for k in range(int(self.s_end / math.tau) + 2) if base + k * math.tau <= self.s_end]

    def theta_of(self, s):
        return _wrap(s + THETA_IN + 0.35)

    # ---- the floor -------------------------------------------------------------------------------------------
    def ground(self, x, z):
        """The hollow's floor: a shallow bowl, roots ridging it toward the wall."""
        d = math.hypot(x, z)
        th = math.atan2(z, x)
        ridge = 0.32 * max(0.0, math.sin(6 * th + 0.8)) ** 2 * min(1.0, max(0.0, d / R0 - 0.45) * 2.2)
        bowl = -0.25 * math.exp(-(d / 3.0) ** 2)
        return ridge + bowl + 0.04 * math.sin(x * 1.7) * math.cos(z * 1.3)

    def tunnel_point(self, along, across):
        """A point in the root tunnel: `along` from the hollow's wall outward, `across` from its middle."""
        r = self.base_r(THETA_IN, 0.0) - 0.3 + along
        cx, cz = math.cos(THETA_IN), math.sin(THETA_IN)
        return (cx * r - cz * across, cz * r + cx * across)

    def in_tunnel(self, x, z):
        """-> (along, across) if (x, z) is in the root tunnel's ground plan, else None."""
        cx, cz = math.cos(THETA_IN), math.sin(THETA_IN)
        along = x * cx + z * cz - (self.base_r(THETA_IN, 0.0) - 0.3)
        across = -x * cz + z * cx
        if -1.0 <= along <= TUNNEL_LEN and abs(across) <= TUNNEL_HALF:
            return along, across
        return None

    def tunnel_floor(self, along):
        return 0.05 + 0.12 * min(TUNNEL_LEN, max(0.0, along)) / TUNNEL_LEN

    # ---- outside -----------------------------------------------------------------------------------------------
    def outside(self, x, z):
        """-> (past the mouth, across) if (x, z) is out in the glade beyond the roots, else None."""
        cx, cz = math.cos(THETA_IN), math.sin(THETA_IN)
        along = x * cx + z * cz - (self.base_r(THETA_IN, 0.0) - 0.3) - TUNNEL_LEN
        across = -x * cz + z * cx
        if -0.05 <= along <= OUT_LEN and abs(across) <= OUT_HALF:
            return along, across
        return None

    def out_ground(self, past, across):
        """The glade's floor: up from the roots' mouth, a little uneven."""
        return self.tunnel_floor(TUNNEL_LEN) + min(0.35, past * 0.06) + 0.06 * math.sin(past * 0.7 + across * 0.4) \
            * min(1.0, past / 3.0)

    def out_open(self, past, across, radius):
        """Room to stand out there: not inside the mound over the roots, not in a tree."""
        if past < 0.5 and abs(across) > TUNNEL_HALF - radius + past * 2.0:          # (the mound's flanks, at the mouth)
            return False
        if abs(across) > OUT_HALF - radius or past > OUT_LEN - radius:
            return False
        return all(math.hypot(past - a, across - c) > r + radius for a, c, r in OUT_TREES)

    def floor_at(self, x, z, feet):
        """The highest thing to stand on under (x, z) that a walker with feet at `feet` can step onto (or fall to)."""
        best = None
        out = self.outside(x, z)
        if out:
            return self.out_ground(*out)
        tun = self.in_tunnel(x, z)
        d = math.hypot(x, z)
        th = math.atan2(z, x)
        if tun and tun[0] > 0.2:
            return self.tunnel_floor(tun[0])
        g = self.ground(x, z)
        if g <= feet + STEP:
            best = g
        for s in self.ledge_turns(th):
            h = self.ledge_h(s)
            if h is None or h < 0.2:
                continue
            inner = self.base_r(th, h + 0.5) - LEDGE_W
            if d >= inner and h <= feet + STEP and (best is None or h > best):
                best = h
        return best if best is not None else g

    def ceiling_at(self, x, z, feet):
        """The lowest thing overhead (the next turn of the ledge, the tunnel's roof) - None if only sky."""
        if self.outside(x, z):
            return None                                            # (the sky)
        tun = self.in_tunnel(x, z)
        if tun and tun[0] > 0.2:
            return self.tunnel_floor(tun[0]) + TUNNEL_CEIL
        d, th = math.hypot(x, z), math.atan2(z, x)
        best = None
        for s in self.ledge_turns(th):
            h = self.ledge_h(s)
            if h is None:
                continue
            under = h - 0.35
            if under > feet + 0.1 and d >= self.base_r(th, h) - LEDGE_W and (best is None or under < best):
                best = under
        return best

    def can_stand(self, x, z, feet, radius=0.24, height=0.75):
        """Whether a walker fits here: inside the wall (or in the tunnel), and room for his head."""
        out = self.outside(x, z)
        if out:
            return self.out_open(out[0], out[1], radius)
        tun = self.in_tunnel(x, z)
        if tun:
            along, across = tun
            if along > 0.2:
                return abs(across) <= TUNNEL_HALF - radius
        d, th = math.hypot(x, z), math.atan2(z, x)
        for y in (feet + 0.15, feet + height * 0.8):
            if d + radius > self.wall_r(th, y):
                if not (tun and abs(tun[1]) <= TUNNEL_HALF - radius and y < TUNNEL_CEIL):
                    return False
        ceil = self.ceiling_at(x, z, feet)
        return ceil is None or ceil - feet >= height

    def landing_at(self, x, z, feet):
        """Which landing (or chamber) he stands on, if any."""
        th = math.atan2(z, x)
        for s in self.ledge_turns(th):
            for name, start, run in LANDINGS:
                if start <= s <= start + run and abs(self.ledge_h(s) - feet) < 0.3 and \
                        math.hypot(x, z) >= self.base_r(th, feet) - LEDGE_W:
                    return name
        return None
