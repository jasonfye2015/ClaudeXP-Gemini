"""Picture formats Qt can't read, found on 1990s art discs: PC Paintbrush (.pcx) and Amiga IFF/ILBM (.iff, .lbm,
.ilbm, .ham8, .iff24 - including EHB, HAM6, HAM8 and 24-bit 'deep' images). Pure Python; fine for the screen-sized
pictures of the era. load(path) returns a QImage (null if the file can't be read)."""
import struct
from pathlib import Path

from PySide6.QtGui import QImage

PCX = {".pcx"}
IFF = {".iff", ".lbm", ".ilbm", ".ham", ".ham6", ".ham8", ".iff24", ".24"}
EXTS = PCX | IFF


def load(path):
    path = Path(path)
    try:
        data = path.read_bytes()
    except OSError:
        return QImage()
    try:
        if data[:4] == b"FORM" and data[8:12] in (b"ILBM", b"PBM "):
            return _ilbm(data)
        if data[:4] == b"FORM" and data[8:12] == b"ANIM":   # an Amiga animation: show its first frame
            i = data.find(b"FORM", 12)
            if i >= 0 and data[i + 8:i + 12] == b"ILBM":
                size = struct.unpack(">I", data[i + 4:i + 8])[0]
                return _ilbm(data[i:i + 8 + size])
        if data[:1] == b"\x0a":
            return _pcx(data)
    except (struct.error, IndexError, ValueError, ZeroDivisionError):
        pass
    return QImage()


def _image(width, height, rgb_rows):
    """rgb_rows: list of bytes (3 bytes per pixel) -> QImage."""
    raw = b"".join(rgb_rows)
    return QImage(raw, width, height, width * 3, QImage.Format_RGB888).copy()


# ---- PCX ------------------------------------------------------------------------------------------------------

def _pcx(d):
    _man, _ver, enc, bpp, x0, y0, x1, y1 = struct.unpack("<BBBBHHHH", d[:12])
    planes, bpl = d[65], struct.unpack("<H", d[66:68])[0]
    w, h = x1 - x0 + 1, y1 - y0 + 1
    # decode the RLE stream
    total = bpl * planes * h
    out = bytearray()
    i = 128
    while len(out) < total and i < len(d):
        b = d[i]
        i += 1
        if enc == 1 and b >= 0xC0:
            out += bytes([d[i]]) * (b & 0x3F)
            i += 1
        else:
            out.append(b)
    rows = []
    if bpp == 8 and planes == 1:
        pal = d[-768:] if len(d) > 769 and d[-769] == 0x0C else bytes(range(256)) * 3
        for y in range(h):
            line = out[y * bpl:y * bpl + w]
            rows.append(b"".join(pal[c * 3:c * 3 + 3] for c in line))
    elif bpp == 8 and planes >= 3:
        for y in range(h):
            base = y * bpl * planes
            r, g, b_ = out[base:base + w], out[base + bpl:base + bpl + w], out[base + 2 * bpl:base + 2 * bpl + w]
            rows.append(bytes(v for px in zip(r, g, b_) for v in px))
    elif bpp == 1:
        pal = d[16:64]
        for y in range(h):
            base = y * bpl * planes
            row = bytearray()
            for x in range(w):
                idx = 0
                for pl in range(planes):
                    if out[base + pl * bpl + x // 8] & (0x80 >> (x % 8)):
                        idx |= 1 << pl
                if planes == 1:
                    row += b"\xff\xff\xff" if idx else b"\x00\x00\x00"
                else:
                    row += pal[idx * 3:idx * 3 + 3]
            rows.append(bytes(row))
    else:
        return QImage()
    return _image(w, h, rows)


# ---- Amiga IFF ILBM -------------------------------------------------------------------------------------------

def _chunks(d):
    i = 12
    while i + 8 <= len(d):
        cid = d[i:i + 4]
        size = struct.unpack(">I", d[i + 4:i + 8])[0]
        yield cid, d[i + 8:i + 8 + size]
        i += 8 + size + (size & 1)


def _byterun1(src, length):
    out = bytearray()
    i = 0
    while len(out) < length and i < len(src):
        n = src[i]
        i += 1
        if n < 128:
            out += src[i:i + n + 1]
            i += n + 1
        elif n > 128:
            out += bytes([src[i]]) * (257 - n)
            i += 1
    return bytes(out)


def _ilbm(d):
    pbm = d[8:12] == b"PBM "
    bmhd = cmap = body = None
    camg = 0
    for cid, chunk in _chunks(d):
        if cid == b"BMHD":
            bmhd = struct.unpack(">HHhhBBBBHBBhh", chunk[:20])
        elif cid == b"CMAP":
            cmap = chunk
        elif cid == b"CAMG":
            camg = struct.unpack(">I", chunk[:4])[0]
        elif cid == b"BODY":
            body = chunk
    if bmhd is None or body is None:
        return QImage()
    w, h, _x, _y, nplanes, masking, compression = bmhd[:7]
    if pbm:                                            # Deluxe Paint 'PBM': one byte per pixel, no planes
        rowbytes = w + (w & 1)
        raw = _byterun1(body, rowbytes * h) if compression == 1 else body
        pal = cmap or bytes(range(256)) * 3
        return _image(w, h, [b"".join(pal[c * 3:c * 3 + 3] for c in raw[y * rowbytes:y * rowbytes + w])
                             for y in range(h)])
    rowbytes = ((w + 15) // 16) * 2
    planes_per_row = nplanes + (1 if masking == 1 else 0)
    raw = _byterun1(body, rowbytes * planes_per_row * h) if compression == 1 else body
    ham = bool(camg & 0x800) or (nplanes in (6, 8) and cmap is not None and len(cmap) // 3 < (1 << nplanes)
                                 and len(cmap) // 3 in (16, 64))
    ehb = bool(camg & 0x80) or (nplanes == 6 and cmap is not None and len(cmap) // 3 == 32 and not ham)
    pal = list(cmap or b"")
    colours = [tuple(pal[i:i + 3]) for i in range(0, len(pal) - 2, 3)]
    if ehb:
        colours = colours[:32] + [(r // 2, g // 2, b // 2) for r, g, b in colours[:32]]
    rows = []
    for y in range(h):
        base = y * rowbytes * planes_per_row
        # each plane's row as one big integer: bit (rowbytes*8-1-x) is pixel x
        plane_ints = [int.from_bytes(raw[base + p * rowbytes:base + (p + 1) * rowbytes], "big")
                      for p in range(nplanes)]
        top = rowbytes * 8 - 1
        row = bytearray()
        if nplanes == 24:                               # deep: 8 planes each of R, G, B
            for x in range(w):
                bit = top - x
                v = 0
                for p in range(24):
                    v |= ((plane_ints[p] >> bit) & 1) << p
                row += bytes((v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF))
            rows.append(bytes(row))
            continue
        r = g = b = 0
        if colours:
            r, g, b = colours[0]
        shift = nplanes - 2
        for x in range(w):
            bit = top - x
            v = 0
            for p in range(nplanes):
                v |= ((plane_ints[p] >> bit) & 1) << p
            if ham:
                ctl, val = v >> shift, v & ((1 << shift) - 1)
                val = val * 255 // ((1 << shift) - 1)
                if ctl == 0:
                    r, g, b = colours[v] if v < len(colours) else (0, 0, 0)
                elif ctl == 1:
                    b = val
                elif ctl == 2:
                    r = val
                else:
                    g = val
                row += bytes((r, g, b))
            else:
                row += bytes(colours[v] if v < len(colours) else (0, 0, 0))
        rows.append(bytes(row))
    return _image(w, h, rows)
