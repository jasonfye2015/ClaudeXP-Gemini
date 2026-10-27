"""The QBasic screen: one palette-indexed framebuffer per page, for every SCREEN mode (0 text, 1 2 7 8 9 11 12 13
graphics), with QBasic's own text cursor, colours, scrolling, and the graphics statements. The program's thread draws;
the studio's screen view copies the visible page out under the lock and shows it. And the sound: BEEP, SOUND, PLAY.

Characters are code page 437, drawn from a monospaced font rendered once into 8-pixel-wide bitmaps - except the box
lines and shade blocks (176-223), which are drawn by hand so frames join up the way they did on a real VGA."""
import math
import threading
import time

# mode: (width, height, columns, rows, cell height, colours, pages)
MODES = {0: (640, 400, 80, 25, 16, 16, 8), 1: (320, 200, 40, 25, 8, 4, 1), 2: (640, 200, 80, 25, 8, 2, 1),
         7: (320, 200, 40, 25, 8, 16, 8), 8: (640, 200, 80, 25, 8, 16, 4), 9: (640, 350, 80, 25, 14, 16, 2),
         11: (640, 480, 80, 30, 16, 2, 1), 12: (640, 480, 80, 30, 16, 16, 1), 13: (320, 200, 40, 25, 8, 256, 1)}
EGA = [0x000000, 0x0000AA, 0x00AA00, 0x00AAAA, 0xAA0000, 0xAA00AA, 0xAA5500, 0xAAAAAA,
       0x555555, 0x5555FF, 0x55FF55, 0x55FFFF, 0xFF5555, 0xFF55FF, 0xFFFF55, 0xFFFFFF]


def vga_palette():
    """VGA's 256 default colours (mode 13h): the 16 EGA colours, 16 greys, then 9 runs of 24 hues."""
    pal = list(EGA)
    for i in range(16):
        g = [0, 5, 8, 11, 14, 17, 20, 24, 28, 32, 36, 40, 45, 50, 56, 63][i] * 255 // 63
        pal.append(g << 16 | g << 8 | g)
    for hi, lo in ((63, 0), (63, 31), (63, 45), (28, 0), (28, 14), (28, 20), (16, 0), (16, 8), (16, 11)):
        steps = [lo + (hi - lo) * k // 4 for k in range(5)]
        ramp = []
        # blue -> magenta -> red -> yellow -> green -> cyan -> (back to) blue, 24 steps
        for k in range(4):
            ramp.append((steps[k], lo, hi))
        for k in range(4):
            ramp.append((hi, lo, steps[4 - k]))
        for k in range(4):
            ramp.append((hi, steps[k], lo))
        for k in range(4):
            ramp.append((steps[4 - k], hi, lo))
        for k in range(4):
            ramp.append((lo, hi, steps[k]))
        for k in range(4):
            ramp.append((lo, steps[4 - k], hi))
        for r, g, b in ramp:
            pal.append((r * 255 // 63) << 16 | (g * 255 // 63) << 8 | (b * 255 // 63))
    pal += [0] * (256 - len(pal))
    return pal[:256]


VGA = vga_palette()
EGA64 = [((((c >> 2) & 1) * 2 + ((c >> 5) & 1)) * 85) << 16 | ((((c >> 1) & 1) * 2 + ((c >> 4) & 1)) * 85) << 8 |
         ((c & 1) * 2 + ((c >> 3) & 1)) * 85 for c in range(64)]

# ---- the font --------------------------------------------------------------------------------------------------------
GLYPHS = {}                     # cell height -> [256 glyphs], each a tuple of row bitmasks (bit 7 = left pixel)
# box drawing, 179-218: (up, down, left, right) with 1 single, 2 double
BOX = {179: (1, 1, 0, 0), 180: (1, 1, 1, 0), 181: (1, 1, 2, 0), 182: (2, 2, 1, 0), 183: (0, 2, 1, 0),
       184: (0, 1, 2, 0), 185: (2, 2, 2, 0), 186: (2, 2, 0, 0), 187: (0, 2, 2, 0), 188: (2, 0, 2, 0),
       189: (2, 0, 1, 0), 190: (1, 0, 2, 0), 191: (0, 1, 1, 0), 192: (1, 0, 0, 1), 193: (1, 0, 1, 1),
       194: (0, 1, 1, 1), 195: (1, 1, 0, 1), 196: (0, 0, 1, 1), 197: (1, 1, 1, 1), 198: (1, 1, 0, 2),
       199: (2, 2, 0, 1), 200: (2, 0, 0, 2), 201: (0, 2, 0, 2), 202: (2, 0, 2, 2), 203: (0, 2, 2, 2),
       204: (2, 2, 0, 2), 205: (0, 0, 2, 2), 206: (2, 2, 2, 2), 207: (1, 0, 2, 2), 208: (2, 0, 1, 1),
       209: (0, 1, 2, 2), 210: (0, 2, 1, 1), 211: (2, 0, 0, 1), 212: (1, 0, 0, 2), 213: (0, 1, 0, 2),
       214: (0, 2, 0, 1), 215: (2, 2, 1, 1), 216: (1, 1, 2, 2), 217: (1, 0, 1, 0), 218: (0, 1, 0, 1)}


def _box_glyph(code, h):
    up, down, left, right = BOX[code]
    rows = [0] * h
    my = h // 2 - 1
    vx = [3, 4]                                         # single vertical: columns 3-4 ... drawn as one column 3
    for y in range(h):
        bits = 0
        above, below = y < my, y > my
        for kind, active in ((up, above or y == my), (down, below or y == my)):
            if kind and active:
                if kind == 1:
                    bits |= 1 << (7 - 3)
                else:
                    bits |= (1 << (7 - 2)) | (1 << (7 - 5))
        rows[y] = bits
    for kind, xs in ((left, range(0, 4)), (right, range(3, 8))):
        if not kind:
            continue
        ys = [my] if kind == 1 else [my - 1, my + 1]
        for yy in ys:
            for x in xs:
                rows[yy] |= 1 << (7 - x)
    # double lines meeting: open the inner corners so ╔ looks right
    if 2 in (up, down) and 2 in (left, right):
        for yy in (my - 1, my + 1):
            pass
    _ = vx
    return tuple(rows)


def _shade_glyph(code, h):
    rows = []
    for y in range(h):
        if code == 176:
            rows.append(0x22 if y % 4 == 0 else 0x88 if y % 4 == 2 else 0)
        elif code == 177:
            rows.append(0x55 if y % 2 == 0 else 0xAA)
        elif code == 178:
            rows.append(0xDD if y % 2 == 0 else 0x77)
        elif code == 219:
            rows.append(0xFF)
        elif code == 220:
            rows.append(0xFF if y >= h // 2 else 0)
        elif code == 221:
            rows.append(0xF0)
        elif code == 222:
            rows.append(0x0F)
        elif code == 223:
            rows.append(0xFF if y < h // 2 else 0)
        else:
            rows.append(0)
    return tuple(rows)


def _fon_glyphs(path):
    """The glyphs of a Windows bitmap font (.fon: an NE file with FNT resources) - DOS's own code page 437 faces,
    still shipped with Windows: {code: rows}, height."""
    import struct
    data = open(path, "rb").read()
    ne = struct.unpack_from("<I", data, 0x3C)[0]
    if data[ne:ne + 2] != b"NE":
        return None, 0
    rtab = ne + struct.unpack_from("<H", data, ne + 0x24)[0]
    shift = struct.unpack_from("<H", data, rtab)[0]
    p = rtab + 2
    while True:
        tid, count = struct.unpack_from("<HH", data, p)
        if tid == 0:
            return None, 0
        p += 8
        for _ in range(count):
            off, length = struct.unpack_from("<HH", data, p)
            p += 12
            if tid != 0x8008:
                continue
            fnt = data[off << shift:(off << shift) + (length << shift)]
            ver = struct.unpack_from("<H", fnt, 0)[0]
            width, height = struct.unpack_from("<HH", fnt, 86)
            first, last = fnt[95], fnt[96]
            if width != 8 or fnt[85] != 255:
                continue
            table, step = (118, 4) if ver == 0x200 else (148, 6)
            glyphs = {}
            for code in range(first, last + 1):
                e = table + (code - first) * step
                gw = struct.unpack_from("<H", fnt, e)[0]
                goff = struct.unpack_from("<H" if step == 4 else "<I", fnt, e + 2)[0]
                if gw != 8:
                    continue
                glyphs[code] = tuple(fnt[goff:goff + height])
            return glyphs, height


def _dos_fonts():
    """CGA's 8x8 and EGA's 8x12 code page 437 fonts, from Windows' Fonts folder (None where they aren't there)."""
    import os
    folder = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    out = {}
    for h, name in ((8, "cga80woa.fon"), (12, "ega80woa.fon")):
        try:
            g, height = _fon_glyphs(os.path.join(folder, name))
            if g and height == h:
                out[h] = g
        except (OSError, ValueError, IndexError):
            pass
    return out


def make_glyphs():
    """The code page 437 font for cell heights 8, 14 and 16 (on the GUI thread, once, before a program runs): DOS's
    own CGA and EGA fonts where Windows has them, else a monospaced font drawn into the cells."""
    if GLYPHS:
        return
    dos = _dos_fonts()
    if 8 in dos and 12 in dos:
        for h in (8, 14, 16):
            src = dos[8] if h == 8 else dos[12]
            sh = 8 if h == 8 else 12
            pad = (h - sh) // 2
            glyphs = []
            for code in range(256):
                if h != 8 and code in (176, 177, 178):
                    glyphs.append(_shade_glyph(code, h))
                elif h != 8 and 176 <= code <= 223 and code in src:
                    g = src[code]                     # (box lines and blocks: their edge rows carried on, so
                    glyphs.append((g[0],) * pad + g + (g[-1],) * (h - sh - pad))   # frames still join up)
                elif code in src:
                    rows = (0,) * pad + src[code] + (0,) * (h - sh - pad)
                    glyphs.append(rows)
                else:
                    glyphs.append((0,) * h)
            GLYPHS[h] = glyphs
        return
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont, QImage, QPainter
    chars = bytes(range(256)).decode("cp437")
    for h in (8, 14, 16):
        font = QFont("Consolas")
        font.setStyleHint(QFont.TypeWriter)
        font.setPixelSize({8: 9, 14: 14, 16: 16}[h])
        font.setBold(h == 8)
        font.setStyleStrategy(QFont.NoAntialias)
        scale = 3
        img = QImage(8 * scale, h * scale, QImage.Format_Grayscale8)
        glyphs = []
        for code in range(256):
            if 179 <= code <= 218:
                glyphs.append(_box_glyph(code, h))
                continue
            if code in (176, 177, 178, 219, 220, 221, 222, 223):
                glyphs.append(_shade_glyph(code, h))
                continue
            if code in (0, 32, 255):
                glyphs.append((0,) * h)
                continue
            ch = chars[code]
            if code < 32:
                ch = "☺☻♥♦♣♠•◘○◙♂♀♪♫☼" \
                     "►◄↕‼¶§▬↨↑↓→←∟↔▲" \
                     "▼"[code - 1] if code >= 1 else " "
            img.fill(0)
            p = QPainter(img)
            f = QFont(font)
            f.setPixelSize(font.pixelSize() * scale)
            p.setFont(f)
            p.setPen(QColor(255, 255, 255))
            p.drawText(0, 0, 8 * scale, h * scale, Qt.AlignHCenter | Qt.AlignVCenter, ch)
            p.end()
            rows = []
            for y in range(h):
                bits = 0
                for x in range(8):
                    lit = 0
                    for dy in range(scale):
                        for dx in range(scale):
                            if img.pixelColor(x * scale + dx, y * scale + dy).red() > 110:
                                lit += 1
                    if lit * 3 >= scale * scale:
                        bits |= 1 << (7 - x)
                rows.append(bits)
            glyphs.append(tuple(rows))
        GLYPHS[h] = glyphs


def _cp437_bytes(s):
    """A string's characters as the screen's bytes: CHR$(0-255) as they are, anything typed in Unicode (a box
    line or a smiley pasted into a string) as its code page 437 code."""
    try:
        return s.encode("latin-1")
    except UnicodeEncodeError:
        out = bytearray()
        for ch in s:
            o = ord(ch)
            if o < 256:
                out.append(o)
            else:
                try:
                    out += ch.encode("cp437")
                except UnicodeEncodeError:
                    out.append(63)
        return bytes(out)


def _plain_glyphs(h):
    """A fallback font (blocks) when the real one wasn't made - tests without a GUI."""
    return [(0,) * h if c in (0, 32) else tuple(0x7E if 1 <= y < h - 1 else 0 for y in range(h)) for c in range(256)]


# ---- the screen ------------------------------------------------------------------------------------------------------
class Screen:
    def __init__(self):
        self.lock = threading.RLock()
        self.version = 0
        self.cursor_on = False
        self.set_mode(0)

    # ---- modes and pages ----
    def set_mode(self, mode):
        if mode not in MODES:
            from .interp import BasicError
            raise BasicError("Illegal function call")
        with self.lock:
            self.mode = mode
            (self.w, self.h, self.cols, self.rows, self.cell_h, self.ncolors, npages) = MODES[mode]
            self.cell_w = self.w // self.cols
            self.pages = [bytearray(self.w * self.h) for _ in range(npages)]
            self.cpages = [[bytearray(b" " * self.cols) for _ in range(self.rows)] for _ in range(npages)]
            self.apage = self.vpage = 0
            self.fb = self.pages[0]
            self.chars = self.cpages[0]
            self.palette_reset()
            self.fg = 7 if mode in (0, 7, 8, 9, 12) else (15 if mode == 13 else self.ncolors - 1)
            if mode == 13:
                self.fg = 15
            self.bg = 0
            self.top, self.bottom = 1, self.rows
            self.row, self.col = 1, 1
            self.gx, self.gy = self.w // 2, self.h // 2
            self.win = None
            self.clip = None
            self.draw_angle, self.draw_scale = 0, 4
            self.glyphs = GLYPHS.get(self.cell_h) or _plain_glyphs(self.cell_h)
            self._row_cache = {}
            self.version += 1

    def set_pages(self, apage, vpage):
        with self.lock:
            if apage is not None:
                if not 0 <= apage < len(self.pages):
                    from .interp import BasicError
                    raise BasicError("Illegal function call")
                self.apage = apage
                self.fb = self.pages[apage]
                self.chars = self.cpages[apage]
            if vpage is not None:
                if not 0 <= vpage < len(self.pages):
                    from .interp import BasicError
                    raise BasicError("Illegal function call")
                self.vpage = vpage
            self.version += 1

    def pcopy(self, src, dst):
        with self.lock:
            if not (0 <= src < len(self.pages) and 0 <= dst < len(self.pages)):
                from .interp import BasicError
                raise BasicError("Illegal function call")
            self.pages[dst][:] = self.pages[src]
            self.cpages[dst] = [bytearray(r) for r in self.cpages[src]]
            if dst == self.apage:
                self.chars = self.cpages[dst]
            self.version += 1

    def width(self, cols, rows):
        with self.lock:
            if cols == 40 and self.mode == 0:
                pass                                      # (the text screen keeps 80 columns here)
            self.version += 1

    def snapshot(self):
        """(width, height, the visible page's bytes, palette, cursor (col, row, cell) or None) - for the view."""
        with self.lock:
            cur = None
            if self.cursor_on and self.vpage == self.apage:
                cur = ((self.col - 1) * self.cell_w, (self.row - 1) * self.cell_h, self.cell_w, self.cell_h,
                       self.fg)
            return self.w, self.h, bytes(self.pages[self.vpage]), list(self.pal), cur, self.mode

    # ---- colours ----
    def palette_reset(self):
        if self.mode == 13:
            self.pal = list(VGA)
        elif self.mode == 1:
            self.pal = [0x000000, 0x55FFFF, 0xFF55FF, 0xFFFFFF] + [0] * 252
        elif self.mode in (2, 11):
            self.pal = [0x000000, 0xFFFFFF] + [0] * 254
        else:
            self.pal = list(EGA) + [0] * 240
        self.version += 1

    def palette(self, attr, colour):
        with self.lock:
            if not 0 <= attr < 256:
                return
            if self.mode == 13 or colour > 63:
                r, g, b = colour & 63, (colour >> 8) & 63, (colour >> 16) & 63
                self.pal[attr] = (r * 255 // 63) << 16 | (g * 255 // 63) << 8 | (b * 255 // 63)
            else:
                self.pal[attr] = EGA64[colour & 63]
            self.version += 1

    def color(self, fg, bg):
        with self.lock:
            if fg is not None:
                if self.mode == 0:
                    fg &= 15                                  # (16 and up blink on a real screen)
                self.fg = fg % max(self.ncolors, 2) if self.mode != 13 else fg & 255
            if bg is not None:
                if self.mode == 0:
                    self.bg = bg & 7 if bg < 16 else bg & 15
                elif self.mode in (7, 8, 9, 12):
                    self.bg = 0
                    self.pal[0] = EGA[bg & 15] if bg < 16 else EGA64[bg & 63]
                    self.version += 1
                else:
                    self.bg = bg % max(self.ncolors, 2)

    # ---- text ----
    def cls(self, which=None):
        with self.lock:
            fill = self.bg if self.mode == 0 else 0
            if which == 2 or (which is None and (self.top, self.bottom) != (1, self.rows)):
                y0, y1 = (self.top - 1) * self.cell_h, self.bottom * self.cell_h
                self.fb[y0 * self.w:y1 * self.w] = bytes([fill]) * ((y1 - y0) * self.w)
                for r in range(self.top - 1, self.bottom):
                    self.chars[r][:] = b" " * self.cols
                self.row, self.col = self.top, 1
            else:
                self.fb[:] = bytes([fill]) * len(self.fb)
                for r in self.chars:
                    r[:] = b" " * self.cols
                self.row, self.col = self.top, 1
                self.gx, self.gy = self.w // 2, self.h // 2
            self.version += 1

    def locate(self, row, col):
        with self.lock:
            if row is not None:
                if not 1 <= row <= self.rows:
                    from .interp import BasicError
                    raise BasicError("Illegal function call")
                self.row = row
            if col is not None:
                if not 1 <= col <= self.cols:
                    from .interp import BasicError
                    raise BasicError("Illegal function call")
                self.col = col

    def view_print(self, top, bottom):
        with self.lock:
            if top is None:
                self.top, self.bottom = 1, self.rows
            else:
                if not (1 <= top <= bottom <= self.rows):
                    from .interp import BasicError
                    raise BasicError("Illegal function call")
                self.top, self.bottom = top, bottom
            self.row, self.col = self.top, 1

    def _glyph_rows(self, code, fg, bg):
        key = (code, fg, bg)
        rows = self._row_cache.get(key)
        if rows is None:
            g = self.glyphs[code]
            rows = [bytes(fg if bits & (0x80 >> x) else bg for x in range(8)) for bits in g]
            if len(self._row_cache) > 20000:
                self._row_cache.clear()
            self._row_cache[key] = rows
        return rows

    def putc(self, code, row, col, fg=None, bg=None):
        fg = self.fg if fg is None else fg
        bg = (self.bg if self.mode == 0 else 0) if bg is None else bg
        rows = self._glyph_rows(code, fg, bg)
        self.chars[row - 1][col - 1] = code
        w = self.w
        x0 = (col - 1) * self.cell_w
        y0 = (row - 1) * self.cell_h
        fb = self.fb
        if self.cell_w == 8:
            for i, r in enumerate(rows):
                off = (y0 + i) * w + x0
                fb[off:off + 8] = r
        else:
            for i, r in enumerate(rows):
                off = (y0 + i) * w + x0
                fb[off:off + self.cell_w] = r[:self.cell_w].ljust(self.cell_w, bytes([bg]))

    def text(self, s):
        """Print text at the cursor, wrapping and scrolling the way PRINT does."""
        if not s:
            return
        with self.lock:
            data = _cp437_bytes(s)
            for code in data:
                if code == 13:
                    self._newline()
                    continue
                if code == 7:
                    continue
                if self.col > self.cols:
                    self._newline()
                self.putc(code, self.row, self.col)
                self.col += 1
            self.version += 1

    def newline(self):
        with self.lock:
            self._newline()
            self.version += 1

    def _newline(self):
        self.col = 1
        if self.row < self.bottom:
            self.row += 1
            return
        # scroll the text window up a line
        w, ch = self.w, self.cell_h
        y0 = (self.top - 1) * ch
        y1 = self.bottom * ch
        fill = self.bg if self.mode == 0 else 0
        fb = self.fb
        fb[y0 * w:(y1 - ch) * w] = fb[(y0 + ch) * w:y1 * w]
        fb[(y1 - ch) * w:y1 * w] = bytes([fill]) * (ch * w)
        rows = self.chars
        del rows[self.top - 1]
        rows.insert(self.bottom - 1, bytearray(b" " * self.cols))

    def zone(self):
        with self.lock:
            n = 14 - ((self.col - 1) % 14)
            if self.col + n > self.cols:
                self._newline()
            else:
                for _ in range(n):
                    self.putc(32, self.row, self.col)
                    self.col += 1
            self.version += 1

    def tab(self, n):
        with self.lock:
            n = max(1, min(self.cols, n))
            if n < self.col:
                self._newline()
            while self.col < n:
                self.putc(32, self.row, self.col)
                self.col += 1
            self.version += 1

    def backspace(self):
        with self.lock:
            if self.col > 1:
                self.col -= 1
            elif self.row > self.top:
                self.row -= 1
                self.col = self.cols
            self.putc(32, self.row, self.col)
            self.version += 1

    # ---- graphics coordinates ----
    def window(self, rect, screen=False):
        with self.lock:
            if rect is None:
                self.win = None
                return
            x1, y1, x2, y2 = rect
            if x1 == x2 or y1 == y2:
                from .interp import BasicError
                raise BasicError("Illegal function call")
            self.win = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), screen)

    def view(self, rect, fill=None, border=None):
        with self.lock:
            if rect is None:
                self.clip = None
                return
            x1, y1, x2, y2 = (int(v) for v in rect)
            self.clip = (max(0, min(x1, x2)), max(0, min(y1, y2)), min(self.w - 1, max(x1, x2)),
                         min(self.h - 1, max(y1, y2)))
            if fill is not None:
                cx1, cy1, cx2, cy2 = self.clip
                for y in range(cy1, cy2 + 1):
                    self.fb[y * self.w + cx1:y * self.w + cx2 + 1] = bytes([fill & 255]) * (cx2 - cx1 + 1)
            self.version += 1

    def _xy(self, x, y, rel=False):
        """Program coordinates -> pixels (STEP, WINDOW)."""
        if self.win is not None:
            wx1, wy1, wx2, wy2, scr = self.win
            vx1, vy1, vx2, vy2 = self.clip or (0, 0, self.w - 1, self.h - 1)
            if rel:
                x, y = self.lx + x, self.ly + y
            self.lx, self.ly = x, y
            px = vx1 + (x - wx1) * (vx2 - vx1) / (wx2 - wx1)
            if scr:
                py = vy1 + (y - wy1) * (vy2 - vy1) / (wy2 - wy1)
            else:
                py = vy2 - (y - wy1) * (vy2 - vy1) / (wy2 - wy1)
            return int(round(px)), int(round(py))
        if rel:
            x, y = self.gx + x, self.gy + y
        x, y = int(round(x)), int(round(y))
        if self.clip is not None and self.win is None:
            pass
        return x, y

    def _need_graphics(self):
        if self.mode == 0:
            from .interp import BasicError
            raise BasicError("Illegal function call")

    def _plot(self, x, y, c):
        if self.clip is not None:
            x1, y1, x2, y2 = self.clip
            if not (x1 <= x <= x2 and y1 <= y <= y2):
                return
        if 0 <= x < self.w and 0 <= y < self.h:
            self.fb[y * self.w + x] = c

    def _c(self, c):
        return (self.fg if c is None else c) & (255 if self.mode == 13 else max(1, self.ncolors - 1)) \
            if self.mode == 13 or self.ncolors in (2, 4, 16, 256) else c

    def pset(self, x, y, c=None, rel=False, reset=False):
        self._need_graphics()
        with self.lock:
            px, py = self._xy(x, y, rel)
            col = (0 if reset else self.fg) if c is None else c
            self._plot(px, py, self._c(col))
            self.gx, self.gy = px, py
            self.version += 1

    def point(self, x, y=None):
        with self.lock:
            if y is None:
                which = int(x)
                return {0: self.gx, 1: self.gy, 2: self.gx, 3: self.gy}.get(which, 0)
            px, py = self._xy(x, y)
            if 0 <= px < self.w and 0 <= py < self.h:
                return self.fb[py * self.w + px]
            return -1

    def line(self, x1, y1, rel1, x2, y2, rel2, c, box, style):
        self._need_graphics()
        with self.lock:
            if x1 is None:
                ax, ay = self.gx, self.gy
            else:
                ax, ay = self._xy(x1, y1, rel1)
            self.gx, self.gy = ax, ay
            bx, by = self._xy(x2, y2, rel2)
            col = self._c(c)
            if box == "BF":
                xa, xb = sorted((ax, bx))
                ya, yb = sorted((ay, by))
                xa, xb = max(0, xa), min(self.w - 1, xb)
                if self.clip is not None:
                    xa, xb = max(xa, self.clip[0]), min(xb, self.clip[2])
                    ya, yb = max(ya, self.clip[1]), min(yb, self.clip[3])
                if xa <= xb:
                    row = bytes([col]) * (xb - xa + 1)
                    for y in range(max(0, ya), min(self.h - 1, yb) + 1):
                        self.fb[y * self.w + xa:y * self.w + xb + 1] = row
            elif box == "B":
                for (p, q, r, s) in ((ax, ay, bx, ay), (bx, ay, bx, by), (bx, by, ax, by), (ax, by, ax, ay)):
                    self._line(p, q, r, s, col, style)
            else:
                self._line(ax, ay, bx, by, col, style)
            self.gx, self.gy = bx, by
            self.version += 1

    def _line(self, x0, y0, x1, y1, c, style=None):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        bit = 0
        if dx > 4000 or -dy > 4000:
            return
        while True:
            if style is None or style & (0x8000 >> (bit % 16)):
                self._plot(x0, y0, c)
            bit += 1
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, x, y, r, c, start, end, aspect, rel):
        self._need_graphics()
        with self.lock:
            cx, cy = self._xy(x, y, rel)
            col = self._c(c)
            if self.win is not None:
                wx1, _wy1, wx2, _wy2, _s = self.win
                vx1, _vy1, vx2, _vy2 = self.clip or (0, 0, self.w - 1, self.h - 1)
                r = r * (vx2 - vx1) / (wx2 - wx1)
            if aspect is None:
                aspect = (self.h / self.w) * (4 / 3)            # (round on a 4:3 monitor)
            rx, ry = (r, r * aspect) if aspect <= 1 else (r / aspect, r)
            a0 = abs(start) if start is not None else 0.0
            a1 = abs(end) if end is not None else 2 * math.pi
            if a1 < a0:
                a1 += 2 * math.pi
            steps = max(16, int(max(rx, ry) * 2 * math.pi * (a1 - a0) / (2 * math.pi)) * 2)
            prev = None
            for k in range(steps + 1):
                a = a0 + (a1 - a0) * k / steps
                px = cx + int(round(math.cos(a) * rx))
                py = cy - int(round(math.sin(a) * ry))
                if prev is None:
                    self._plot(px, py, col)
                elif (px, py) != prev:
                    self._line(prev[0], prev[1], px, py, col)
                prev = (px, py)
            for a, neg in ((start, start is not None and start < 0), (end, end is not None and end < 0)):
                if neg:
                    self._line(cx, cy, cx + int(round(math.cos(abs(a)) * rx)), cy - int(round(math.sin(abs(a)) * ry)),
                               col)
            self.gx, self.gy = cx, cy
            self.version += 1

    def paint(self, x, y, c, border, rel):
        """Flood fill from (x, y) up to the border colour (the paint colour itself if no border is given)."""
        self._need_graphics()
        with self.lock:
            sx, sy = self._xy(x, y, rel)
            col = self._c(c)
            bcol = col if border is None else border
            w, h, fb = self.w, self.h, self.fb
            x1c, y1c, x2c, y2c = self.clip or (0, 0, w - 1, h - 1)
            if not (x1c <= sx <= x2c and y1c <= sy <= y2c):
                return
            if fb[sy * w + sx] in (bcol, col):
                return
            stack = [(sx, sy)]
            budget = w * h * 2
            while stack and budget > 0:
                px, py = stack.pop()
                off = py * w
                if fb[off + px] in (bcol, col):
                    continue
                lx = px
                while lx > x1c and fb[off + lx - 1] not in (bcol, col):
                    lx -= 1
                rx = px
                while rx < x2c and fb[off + rx + 1] not in (bcol, col):
                    rx += 1
                fb[off + lx:off + rx + 1] = bytes([col]) * (rx - lx + 1)
                budget -= rx - lx + 1
                for ny in (py - 1, py + 1):
                    if y1c <= ny <= y2c:
                        noff = ny * w
                        xx = lx
                        while xx <= rx:
                            if fb[noff + xx] not in (bcol, col):
                                stack.append((xx, ny))
                                while xx <= rx and fb[noff + xx] not in (bcol, col):
                                    xx += 1
                            xx += 1
            self.gx, self.gy = sx, sy
            self.version += 1

    def draw(self, s, vm=None):
        """DRAW's little language: U D L R E F G H [n], M x,y (or +/-), B (move without drawing), N (draw and come
        back), C colour, S scale, A angle, TA turn angle, P paint,border."""
        self._need_graphics()
        import re as _re
        s = s.upper().replace(" ", "")
        i = 0
        blank = back = False
        with self.lock:
            while i < len(s):
                ch = s[i]
                i += 1
                m = _re.match(r"[+-]?\d+(\.\d+)?", s[i:])
                num = float(m.group()) if m else None
                if m:
                    i += m.end()
                if ch == "B":
                    blank = True
                    continue
                if ch == "N":
                    back = True
                    continue
                if ch == "C":
                    self.fg = int(num or 0)
                    continue
                if ch == "S":
                    self.draw_scale = int(num or 4)
                    continue
                if ch == "A":
                    self.draw_angle = int(num or 0) * 90
                    continue
                if ch == "T" and i < len(s) and s[i] == "A":
                    i += 1
                    m = _re.match(r"[+-]?\d+", s[i:])
                    self.draw_angle = int(m.group()) if m else 0
                    if m:
                        i += m.end()
                    continue
                if ch == "P":
                    rest = _re.match(r"(\d+),(\d+)", s[i - (m.end() if m else 0) - 0:])
                    if m:
                        fillc = int(num)
                        bm = _re.match(r",(\d+)", s[i:])
                        border = int(bm.group(1)) if bm else fillc
                        if bm:
                            i += bm.end()
                        self.paint(self.gx, self.gy, fillc, border, False)
                    _ = rest
                    continue
                dirs = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0), "E": (1, -1), "F": (1, 1),
                        "G": (-1, 1), "H": (-1, -1)}
                if ch in dirs:
                    n = (num if num is not None else 1) * self.draw_scale / 4
                    dx, dy = dirs[ch]
                    dx, dy = dx * n, dy * n
                    a = math.radians(self.draw_angle)
                    rx = dx * math.cos(a) + dy * math.sin(a)
                    ry = -dx * math.sin(a) + dy * math.cos(a)
                    nx, ny = int(round(self.gx + rx)), int(round(self.gy + ry))
                elif ch == "M":
                    mm = _re.match(r"([+-]?)(\d+),([+-]?\d+)", s[i - (m.end() if m else 0):])
                    if not mm:
                        continue
                    i = i - (m.end() if m else 0) + mm.end()
                    rel = bool(mm.group(1))
                    mx = float(mm.group(1) + mm.group(2))
                    my = float(mm.group(3))
                    if rel:
                        nx, ny = int(round(self.gx + mx * self.draw_scale / 4)), int(round(self.gy + my * self.draw_scale / 4))
                    else:
                        nx, ny = int(mx), int(my)
                else:
                    continue
                if not blank:
                    self._line(self.gx, self.gy, nx, ny, self._c(None))
                if not back:
                    self.gx, self.gy = nx, ny
                blank = back = False
            self.version += 1

    def get_block(self, x1, y1, x2, y2):
        with self.lock:
            ax, ay = self._xy(x1, y1)
            bx, by = self._xy(x2, y2)
            xa, xb = sorted((ax, bx))
            ya, yb = sorted((ay, by))
            if xa < 0 or ya < 0 or xb >= self.w or yb >= self.h:
                from .interp import BasicError
                raise BasicError("Illegal function call")
            w = xb - xa + 1
            data = b"".join(bytes(self.fb[y * self.w + xa:y * self.w + xb + 1]) for y in range(ya, yb + 1))
            return (w, yb - ya + 1, data)

    def put_block(self, x, y, blob, action):
        bw, bh, data = blob
        with self.lock:
            px, py = self._xy(x, y)
            if px < 0 or py < 0 or px + bw > self.w or py + bh > self.h:
                from .interp import BasicError
                raise BasicError("Illegal function call")
            fb = self.fb
            for row in range(bh):
                off = (py + row) * self.w + px
                src = data[row * bw:(row + 1) * bw]
                if action == "PSET":
                    fb[off:off + bw] = src
                elif action == "PRESET":
                    fb[off:off + bw] = bytes((~v) & 255 for v in src)
                else:
                    dst = fb[off:off + bw]
                    if action == "XOR":
                        fb[off:off + bw] = bytes(a ^ b for a, b in zip(dst, src))
                    elif action == "OR":
                        fb[off:off + bw] = bytes(a | b for a, b in zip(dst, src))
                    else:
                        fb[off:off + bw] = bytes(a & b for a, b in zip(dst, src))
            self.version += 1

    @property
    def text_pos(self):
        return self.row, self.col

    def text_lines(self, page=None):
        """The characters on a page (the visible one by default), as text lines - what a program has printed."""
        with self.lock:
            rows = self.cpages[self.vpage if page is None else page]
            return [bytes(r).decode("cp437").rstrip() for r in rows]


# ---- sound -----------------------------------------------------------------------------------------------------------
NOTES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


class Sound:
    """BEEP, SOUND and PLAY, as square waves (on Windows through winsound; quiet elsewhere or when muted)."""

    def __init__(self, muted=lambda: False):
        self.muted = muted
        self.octave, self.length, self.tempo = 4, 4, 120
        self.style = 7 / 8                 # MN: notes sound for 7/8 of their length
        self.background = False
        self._player = None

    def _tone(self, freq, secs, vm=None):
        if secs <= 0:
            return
        if self.muted() or freq < 37 or freq > 32767:
            self._wait(secs, vm)
            return
        wav = _square_wav(freq, secs)
        self._play_wav(wav, secs, vm)

    def _rest(self, secs, vm=None):
        self._wait(secs, vm)

    def _wait(self, secs, vm):
        end = time.monotonic() + secs
        while time.monotonic() < end:
            if vm is not None and vm.stopping:
                from .interp import StopProgram
                raise StopProgram()
            time.sleep(min(0.01, max(0, end - time.monotonic())))

    def _play_wav(self, wav, secs, vm):
        try:
            import winsound
        except ImportError:
            self._wait(secs, vm)
            return
        if self.background:
            threading.Thread(target=winsound.PlaySound, args=(wav, winsound.SND_MEMORY), daemon=True).start()
            return
        t = threading.Thread(target=winsound.PlaySound, args=(wav, winsound.SND_MEMORY), daemon=True)
        t.start()
        self._wait(secs, vm)

    def beep(self):
        self._tone(800, 0.25)

    def sound(self, freq, ticks, vm=None):
        secs = float(ticks) / 18.2
        if freq == 32767 or freq < 37:
            self._rest(secs, vm)
        else:
            self._tone(float(freq), secs, vm)

    def play(self, music, vm=None):
        """PLAY's music language: notes A-G (# + -), O octave, < >, L length, T tempo, P pause, N note number,
        dotted notes, ML MN MS, MF MB."""
        import re as _re
        s = music.upper().replace(" ", "")
        i = 0
        while i < len(s):
            ch = s[i]
            i += 1
            m = _re.match(r"\d+", s[i:])
            num = int(m.group()) if m else None
            if ch in NOTES or ch == "N":
                if ch == "N":
                    if m:
                        i += m.end()
                    note = num or 0
                    length = self.length
                    if note == 0:
                        self._rest(self._secs(length, 0), vm)
                        continue
                    semis = note - 1
                else:
                    semis = NOTES[ch] + self.octave * 12
                    if i < len(s) and s[i] in "#+":
                        semis += 1
                        i += 1
                    elif i < len(s) and s[i] == "-":
                        semis -= 1
                        i += 1
                    m = _re.match(r"\d+", s[i:])
                    length = self.length
                    if m:
                        length = int(m.group()) or self.length
                        i += m.end()
                dots = 0
                while i < len(s) and s[i] == ".":
                    dots += 1
                    i += 1
                secs = self._secs(length, dots)
                freq = 440.0 * 2 ** ((semis - 45) / 12)        # O2 A = 110 ... O4 A (semis 57) = 440
                freq = 440.0 * 2 ** ((semis - 57) / 12)
                on = secs * self.style
                self._tone(freq, on, vm)
                self._rest(secs - on, vm)
                continue
            if m:
                i += m.end()
            if ch == "O" and num is not None:
                self.octave = max(0, min(6, num))
            elif ch == "<":
                self.octave = max(0, self.octave - 1)
            elif ch == ">":
                self.octave = min(6, self.octave + 1)
            elif ch == "L" and num:
                self.length = max(1, min(64, num))
            elif ch == "T" and num:
                self.tempo = max(32, min(255, num))
            elif ch in ("P", "R"):
                dots = 0
                while i < len(s) and s[i] == ".":
                    dots += 1
                    i += 1
                self._rest(self._secs(num or self.length, dots), vm)
            elif ch == "M" and i < len(s):
                kind = s[i]
                i += 1
                if kind == "L":
                    self.style = 1.0
                elif kind == "N":
                    self.style = 7 / 8
                elif kind == "S":
                    self.style = 3 / 4
                elif kind == "B":
                    self.background = True
                elif kind == "F":
                    self.background = False

    def _secs(self, length, dots):
        secs = (60.0 / self.tempo) * 4 / length
        extra = secs
        for _ in range(dots):
            extra /= 2
            secs += extra
        return secs


def _square_wav(freq, secs, rate=22050, volume=0.18):
    import struct
    n = int(rate * secs)
    period = rate / freq
    amp = int(127 * volume)
    data = bytes(128 + (amp if (k % period) < period / 2 else -amp) for k in range(n))
    return b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " + \
        struct.pack("<IHHIIHH", 16, 1, 1, rate, rate, 1, 8) + b"data" + struct.pack("<I", len(data)) + data
