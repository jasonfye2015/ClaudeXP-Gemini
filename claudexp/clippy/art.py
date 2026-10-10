"""Clippy himself: a bent paperclip with big eyes and bushy eyebrows, sitting on a sheet of yellow paper.
Everything is drawn in code; Pose holds the animated bits (bounce, blink, eyebrows, where he's looking...)."""
import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

W, H = 96, 152          # the widget's size: his 80 x 120 box sits at the bottom, with headroom for jumping


@dataclass
class Pose:
    lift: float = 0.0          # pixels up (bouncing, jumping)
    squash: float = 0.0        # -1 stretched tall .. 1 squashed flat
    tilt: float = 0.0          # degrees, leaning
    scale: float = 1.0         # 'tapping on the glass' grows him
    blink: float = 0.0         # 0 open .. 1 shut
    brows: float = 0.0         # -1 frowning .. 1 raised high
    sulk: float = 0.0          # 0 .. 1: brows slant down, eyes half shut
    droop: float = 0.0         # 0 .. 1: sad brows (inner ends up, outer ends down)
    lid: float = 0.0           # 0 .. 1: eyelids resting half shut (bored, sad, smug)
    brow2: float = 0.0         # extra lift of the right eyebrow only (the arched, snarky brow)
    blush: float = 0.0         # pink cheeks
    tear: float = -1.0         # 0..1: a tear running down his left cheek; negative: none
    look: tuple = (0.0, 0.0)   # pupils, -1..1 each way
    paper: bool = True
    wire: tuple = ("#9AA0AA", "#F2F4F8", "#7A808C")      # shadow, highlight, edge colours of the wire
    accessory: str = "none"
    mood: str = "happy"


def _clip_path():

    """The wire: three nested U bends, like a real paperclip standing on end."""
    p = QPainterPath()
    p.moveTo(46, 84)
    p.lineTo(46, 42)
    p.arcTo(QRectF(34, 34, 12, 12), 0, 180)          # small inner bend at the top
    p.lineTo(34, 100)
    p.arcTo(QRectF(34, 88, 24, 24), 180, 180)        # bend at the bottom
    p.lineTo(58, 30)
    p.arcTo(QRectF(22, 12, 36, 36), 0, 180)          # the big outer bend at the top
    p.lineTo(22, 92)
    return p


def paint(p: QPainter, pose: Pose, rect=None):
    """Draw Clippy in pose, fitted into rect (default: the whole W x H widget)."""
    rect = rect or QRectF(0, 0, W, H)
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    sx, sy = rect.width() / W, rect.height() / H
    p.translate(rect.x(), rect.y())
    p.scale(sx, sy)
    p.translate(0, H - 132)
    if pose.paper:
        _paper(p)
    # his body moves; the paper stays put
    p.translate(W / 2, 118 - pose.lift)
    p.rotate(pose.tilt)
    stretch = 1 - 0.12 * pose.squash
    p.scale(pose.scale * (1 + 0.08 * pose.squash), pose.scale * stretch)
    p.translate(-40, -112)
    path = _clip_path()
    for width, colour in ((7.5, QColor("#3C4048")), (5.5, None), (1.6, QColor(255, 255, 255, 200))):
        if colour is None:
            g = QLinearGradient(20, 0, 60, 0)
            g.setColorAt(0, QColor(pose.wire[0]))
            g.setColorAt(0.45, QColor(pose.wire[1]))
            g.setColorAt(1, QColor(pose.wire[2]))
            pen = QPen(g, width)
        else:
            pen = QPen(colour, width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        if width < 2:
            p.save()
            p.translate(-1.2, -0.8)
            p.drawPath(path)
            p.restore()
        else:
            p.drawPath(path)
    _eyes(p, pose)
    _accessory(p, pose)
    p.restore()


def _accessory(p, pose):
    """Hats and glasses, in the same coordinates as the wire (eyes at (31, 36) and (50, 36); the top of the clip is
    y = 12)."""
    kind = pose.accessory
    if kind in ("none", "", None):
        return
    p.save()
    ink = QPen(QColor("#202020"), 1.2)
    if kind == "glasses":
        p.setPen(QPen(QColor("#2A2A30"), 1.8))
        p.setBrush(QColor(200, 225, 255, 70))
        for cx in (31, 50):
            p.drawEllipse(QPointF(cx, 37), 11, 12.5)
        p.drawLine(QPointF(41.6, 35), QPointF(39.4, 35))
    elif kind == "shades":
        p.setPen(ink)
        p.setBrush(QColor("#15151A"))
        for cx in (31, 50):
            p.drawRoundedRect(QRectF(cx - 11, 27, 22, 17), 6, 6)
        p.setPen(QPen(QColor("#15151A"), 2))
        p.drawLine(QPointF(42, 32), QPointF(39, 32))
        p.setPen(QPen(QColor(255, 255, 255, 120), 1.6))
        for cx in (31, 50):
            p.drawLine(QPointF(cx - 6, 30), QPointF(cx - 2, 30))
    elif kind == "tophat":
        p.setPen(ink)
        p.setBrush(QColor("#1C1C20"))
        p.drawRect(QRectF(29, -4, 22, 18))
        p.setBrush(QColor("#B02A2A"))
        p.drawRect(QRectF(29, 8, 22, 4))
        p.setBrush(QColor("#1C1C20"))
        p.drawEllipse(QPointF(40, 14), 19, 4)
    elif kind == "party":
        p.translate(40, 14)
        p.rotate(10)
        cone = QPainterPath()
        cone.moveTo(-10, 0)
        cone.lineTo(0, -22)
        cone.lineTo(10, 0)
        cone.closeSubpath()
        p.setPen(ink)
        p.setBrush(QColor("#E0489A"))
        p.drawPath(cone)
        p.setPen(QPen(QColor("#FFE24A"), 2))
        p.drawLine(QPointF(-7, -5), QPointF(7, -9))
        p.drawLine(QPointF(-4, -12), QPointF(4, -14))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FFE24A"))
        p.drawEllipse(QPointF(0, -22), 3, 3)
    elif kind == "wizard":
        p.translate(40, 14)
        p.rotate(-6)
        cone = QPainterPath()
        cone.moveTo(-15, 0)
        cone.quadTo(-8, -10, 2, -26)
        cone.quadTo(8, -20, 13, -16)
        cone.quadTo(11, -8, 15, 0)
        cone.closeSubpath()
        p.setPen(ink)
        p.setBrush(QColor("#2E3F9E"))
        p.drawPath(cone)
        p.setBrush(QColor("#FFE24A"))
        p.setPen(Qt.NoPen)
        for x, y, r in ((-3, -9, 1.8), (4, -15, 1.4), (-7, -3, 1.2)):
            p.drawEllipse(QPointF(x, y), r, r)
        p.setPen(ink)
        p.setBrush(QColor("#2E3F9E"))
        p.drawEllipse(QPointF(0, 0), 19, 4)
    elif kind == "grad":
        p.setPen(ink)
        p.setBrush(QColor("#1D2750"))
        p.drawRoundedRect(QRectF(30, 8, 20, 8), 3, 3)
        board = QPolygonF([QPointF(40, -1), QPointF(61, 8), QPointF(40, 15), QPointF(19, 8)])
        p.drawPolygon(board)
        p.setPen(QPen(QColor("#F2C230"), 1.4))
        p.drawLine(QPointF(40, 8), QPointF(57, 12))
        p.drawLine(QPointF(57, 12), QPointF(57, 19))
    elif kind == "santa":
        p.translate(40, 14)
        p.rotate(-8)
        cap = QPainterPath()
        cap.moveTo(-14, 0)
        cap.quadTo(-12, -16, 6, -18)
        cap.quadTo(16, -16, 18, -8)
        cap.lineTo(14, 0)
        cap.closeSubpath()
        p.setPen(ink)
        p.setBrush(QColor("#C8242B"))
        p.drawPath(cap)
        p.setBrush(QColor("#F6F6F6"))
        p.drawRoundedRect(QRectF(-16, -3, 32, 6), 3, 3)
        p.drawEllipse(QPointF(18, -9), 4, 4)
    p.restore()


def _eyes(p, pose):
    lx, ly = pose.look
    shut = max(pose.blink, 0.45 * pose.sulk, pose.lid)
    for cx, side in ((31, -1), (50, 1)):
        cy = 36
        eye = QRectF(cx - 8, cy - 10, 16, 20)
        if pose.blush > 0.01:                              # rosy cheeks
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 120, 140, int(90 * pose.blush)))
            p.drawEllipse(QPointF(cx + 8 * side, cy + 15), 5.5, 3.2)
        p.setPen(QPen(QColor("#202020"), 1.4))
        p.setBrush(QColor("white"))
        if pose.blink >= 0.95:
            p.drawLine(QPointF(cx - 7, cy + 2), QPointF(cx + 7, cy + 2))
        else:
            p.drawEllipse(eye)
            pupil = QPointF(cx + 3.5 * lx, cy + 2 + 4.5 * ly)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#101010"))
            p.drawEllipse(pupil, 3.6, 4.2)
            p.setBrush(QColor("white"))
            p.drawEllipse(pupil + QPointF(-1.2, -1.6), 1.1, 1.1)
            if shut > 0:                                   # the lid coming down
                lid = QRectF(eye.x() - 1, eye.y() - 1, eye.width() + 2, (eye.height() + 2) * shut)
                p.setBrush(QColor("#C8CCD4"))
                p.setPen(QPen(QColor("#202020"), 1.2))
                p.drawChord(QRectF(lid.x(), lid.y() - lid.height(), lid.width(), lid.height() * 2), 180 * 16,
                            180 * 16)
        # eyebrows: thick black arcs; raised, frowning, sulking or drooping
        raise_ = 3.5 * pose.brows + (4.5 * pose.brow2 if side == 1 else 0.0)
        slant = 4.5 * pose.sulk - 2.5 * min(0.0, pose.brows)
        inner_y = cy - 13 - raise_ + slant * 0.4 * (1 if pose.sulk > 0 else -1) - 3.5 * pose.droop
        outer_y = cy - 14 - raise_ - slant * 0.6 + 3.0 * pose.droop
        if pose.droop and shut:
            inner_y += 2.0 * shut                           # the lid pushes the brow down a little
        pen = QPen(QColor("#151515"), 3.2)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        brow = QPainterPath()
        inner, outer = cx - 6 * side, cx + 8 * side
        brow.moveTo(inner, inner_y)
        brow.quadTo((inner + outer) / 2, min(inner_y, outer_y) - 4, outer, outer_y)
        p.drawPath(brow)
    if pose.tear >= 0:                                      # a tear from his left eye
        f = pose.tear
        y = 47 + 24 * f
        p.setPen(QPen(QColor(70, 120, 200, int(230 * (1 - f * f))), 1))
        p.setBrush(QColor(150, 200, 255, int(220 * (1 - f * f))))
        drop = QPainterPath()
        drop.moveTo(27.5, y - 3.5)
        drop.cubicTo(25.5, y, 25.5, y + 3, 27.5, y + 3)
        drop.cubicTo(29.5, y + 3, 29.5, y, 27.5, y - 3.5)
        p.drawPath(drop)

def _paper(p):
    page = QPainterPath()
    page.addRoundedRect(QRectF(8, 104, 80, 24), 2, 2)
    p.save()
    p.translate(48, 116)
    p.rotate(-4)
    p.translate(-48, -116)
    p.setPen(QPen(QColor("#B8A860"), 1))
    p.setBrush(QColor("#FFF6B0"))
    p.drawPath(page)
    p.setPen(QPen(QColor("#9DB8E0"), 1))
    for y in (111, 117, 123):
        p.drawLine(QPointF(12, y), QPointF(84, y))
    p.setPen(QPen(QColor("#E8A0A0"), 1))
    p.drawLine(QPointF(20, 105), QPointF(20, 127))
    p.restore()


def icon_pixmap(size=32, pose=None):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    h = size
    w = size * W / H
    if pose is None:
        pose = Pose(paper=False)
    paint(p, pose, QRectF((size - w) / 2, -h * 0.2, w, h * 1.35))
    p.end()
    return pm


def still_pose(mood="happy", wire="silver", accessory="none"):
    """A resting pose for icons and previews (the tray icon wears his mood)."""
    a = Animator()
    a.set_style(mood, wire, accessory)
    pose = a.step(0.0)
    pose.paper = False
    pose.lift = pose.tilt = 0.0
    pose.blink = 0.0
    return pose


class Animator:
    """Turns named animations into poses over time. step(dt) -> Pose."""
    LENGTHS = {"idle": None, "appear": 0.7, "wave": 1.4, "tap": 1.6, "jump": 1.2, "think": None, "sulk": 1.6,
               "leave": 0.6, "look_around": 2.2, "eyebrows": 1.2, "spin": 1.0, "sigh": 2.4, "eyeroll": 1.8}

    def __init__(self):
        from . import moods
        self.t = 0.0
        self.name = "idle"
        self.start = 0.0
        self.next_blink = 2.5
        self.blink_until = 0.0
        self.look_target = (0.0, 0.0)
        self.look = [0.0, 0.0]
        self.mood = "happy"
        self.face = moods.MOODS["happy"]["face"]
        self.wire_key = "silver"
        self.accessory = "none"
        self.next_gag = 25.0
        self.gags_on = True

    def set_style(self, mood, wire="silver", accessory="none"):
        """mood: a key of moods.MOODS. wire/accessory: keys of moods.WIRES / ACCESSORIES ('mood' and 'seasonal'
        are resolved here)."""
        from . import moods
        self.mood = mood if mood in moods.MOODS else "happy"
        self.face = moods.MOODS[self.mood]["face"]
        self.wire_key = moods.MOODS[self.mood]["wire"] if wire == "mood" else wire
        if self.wire_key not in moods.WIRES:
            self.wire_key = "silver"
        self.accessory = moods.seasonal_accessory() if accessory == "seasonal" else accessory
        self.next_gag = self.t + 8

    def _wire(self):
        from . import moods
        colours = moods.WIRES[self.wire_key][1]
        if colours is None:                                        # rainbow
            h = (self.t * 0.12) % 1.0
            return (QColor.fromHsvF(h, 0.7, 0.7).name(), QColor.fromHsvF(h, 0.25, 1.0).name(),
                    QColor.fromHsvF(h, 0.85, 0.5).name())
        return colours

    def play(self, name):
        self.name, self.start = name, self.t

    def busy(self):
        n = self.LENGTHS.get(self.name)
        return n is not None and self.t - self.start < n

    def step(self, dt):
        self.t += dt
        t, k = self.t, self.t - self.start
        face = self.face
        pose = Pose()
        amp, speed = face["bob"]
        pose.lift = amp * math.sin(t * speed * 2.2 / 1.8 + 0.0)   # idle bob: bouncy when happy, barely when glum
        if self.t > self.next_blink:
            self.blink_until = self.t + 0.14
            self.next_blink = self.t + 2.5 + (math.sin(t * 7.3) + 1) * 2.2
        if self.t < self.blink_until:
            pose.blink = 1.0
        n = self.LENGTHS.get(self.name)
        if n is not None and k >= n:
            self.name = "idle"
        name = self.name
        if name == "idle" and self.gags_on and self.t > self.next_gag:       # what he does when he's bored
            self.next_gag = self.t + 18 + 27 * ((math.sin(t * 12.9) + 1) / 2)
            self.play(face["gags"][int(t * 1000) % len(face["gags"])])
            name, k = self.name, 0.0
        rest_look = face["look"]
        if name == "appear":
            f = min(1.0, k / 0.7)
            pose.scale = 0.2 + 0.8 * f + 0.15 * math.sin(f * math.pi)
            pose.lift += 10 * math.sin(f * math.pi)
        elif name == "leave":
            f = min(1.0, k / 0.6)
            pose.scale = max(0.05, 1 - f)
            pose.lift += 20 * f
        elif name == "wave":
            pose.tilt = 10 * math.sin(k * 9)
            pose.brows = 0.8
        elif name == "tap":                                        # leans in close and knocks on the screen
            f = min(1.0, k / 1.6)
            pose.scale = 1 + 0.35 * math.sin(f * math.pi)
            pose.tilt = 4 * math.sin(k * 30) * (0.3 < f < 0.8)
            pose.brows = 1.0
            self.look_target = (0.0, -0.2)
        elif name == "jump":
            for start in (0.0, 0.6):
                if start <= k < start + 0.5:
                    f = (k - start) / 0.5
                    pose.lift += 22 * math.sin(f * math.pi)
                    pose.squash = -0.6 * math.sin(f * math.pi)
            pose.brows = 1.0
        elif name == "think":
            pose.brows = 0.5 + 0.3 * math.sin(k * 3)
            self.look_target = (0.7 * math.sin(k * 1.4), -0.8)
            pose.tilt = 3 * math.sin(k * 1.3)
        elif name == "sulk":
            pose.sulk = min(1.0, k / 0.4)
            pose.lift -= 3
            pose.tilt = -6
            self.look_target = (-0.6, 0.7)
        elif name == "look_around":
            self.look_target = ((-1.0, 0.0), (1.0, 0.0), (0.0, -0.8), (0.0, 0.0))[min(3, int(k / 0.55))]
        elif name == "eyebrows":
            pose.brows = 1.0 if int(k * 5) % 2 == 0 else -0.2
        elif name == "spin":
            pose.tilt = 360 * min(1.0, k / 1.0)
            pose.brows = 0.6
        elif name == "sigh":                                       # a long breath: sags, then recovers
            f = min(1.0, k / 2.4)
            pose.squash = 0.55 * math.sin(f * math.pi)
            pose.lift -= 4 * math.sin(f * math.pi)
            pose.blink = 1.0 if 0.35 < f < 0.6 else pose.blink
            self.look_target = (0.0, 0.8)
        elif name == "eyeroll":                                    # eyes round the clock, brow up
            f = min(1.0, k / 1.8)
            if 0.15 < f < 0.85:
                a = (f - 0.15) / 0.7 * 2 * math.pi
                self.look_target = (0.9 * math.sin(a + math.pi), 0.9 * math.cos(a + math.pi) * -1)
            pose.brow2 = 1.0 * math.sin(f * math.pi)
            pose.tilt = -3 * math.sin(f * math.pi)
        # his mood, underneath whatever he's doing
        pose.brows = max(-1.0, min(1.0, pose.brows + face["brows"]))
        pose.sulk = max(pose.sulk, face["sulk"])
        pose.droop, pose.lid, pose.blush = face["droop"], face["lid"], face["blush"]
        pose.brow2 = max(pose.brow2, face["brow2"])
        pose.tilt += face["tilt"]
        if face["tear"]:
            phase = (t % 4.0) / 4.0
            pose.tear = (phase - 0.55) / 0.45 if phase > 0.55 else -1.0
        if name in ("idle", "wave", "jump", "eyebrows", "appear", "spin", "sigh") and k > 0.3 and name != "sigh":
            self.look_target = rest_look
        for i in (0, 1):                                            # eyes glide towards where he's looking
            self.look[i] += (self.look_target[i] - self.look[i]) * min(1.0, dt * 8)
        pose.look = tuple(self.look)
        pose.wire = self._wire()
        pose.accessory = self.accessory
        pose.mood = self.mood
        return pose
