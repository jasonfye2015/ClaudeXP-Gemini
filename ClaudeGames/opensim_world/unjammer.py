"""Unpacking an InstallJammer installer (what the Cool VL Viewer ships as) without running it, so the viewer lands in
Local Storage and nothing is installed on Windows.

The installer is a Tcl "installkit" with its files appended: a table of 256-byte entry headers (type, compression,
name, size, packed size, mtime, offset) and each file's data at its offset, either LZMA (5 property bytes, then a
raw LZMA1 stream) or raw deflate. main.tcl, one of those files, maps the payload's entries (file0001...) to their real
names and folders through lines like:

    File ::<id> -name CoolVLViewer.exe -parent <id> -srcfile file0042 -directory <%InstallDir%>/. -size ...

    python -m opensim_world.unjammer Setup.exe target_folder
"""
import lzma
import re
import sys
import zlib
from pathlib import Path

_TYPES = (b"FILE", b"DIRE", b"LINK")


def _entries(data):
    """{name: (method, size, packed, offset)} from the header table at the end of the installer."""
    tail = data.rfind(b"CRAP")
    if tail < 0:
        raise ValueError("not an InstallJammer installer")
    pos = tail
    while pos >= 256 and data[pos - 256:pos - 252] in _TYPES:
        pos -= 256
    out = {}
    while data[pos:pos + 4] in _TYPES:
        field = lambda a, b: data[pos + a:pos + b].split(b"\0")[0].decode("utf-8", "replace")
        if field(0, 4) == "FILE":
            out[field(6, 134)] = (field(4, 6), int(field(134, 146) or 0), int(field(146, 158) or 0),
                                  int(field(172, 184) or 0))
        pos += 256
    return out


def _read(data, entry):
    method, size, packed, offset = entry
    raw = data[offset:offset + packed]
    if method == "LZ":
        props = raw[0]
        lc, rest = props % 9, props // 9
        lp, pb = rest % 5, rest // 5
        dict_size = int.from_bytes(raw[1:5], "little") or (1 << 16)
        dec = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[
            {"id": lzma.FILTER_LZMA1, "lc": lc, "lp": lp, "pb": pb, "dict_size": dict_size}])
        return dec.decompress(raw[5:], max_length=size)
    if method == "ZL":
        return zlib.decompressobj(-15).decompress(raw, size)
    return raw[:size]


_FILE = re.compile(r"^File ::\S+ (.*)$", re.M)
_OPT = re.compile(r"-(name|srcfile|directory|size) (\{[^}]*\}|\S+)")


def extract(installer, target, progress=None):
    """Unpack every installed file into `target`; returns how many were written."""
    data = Path(installer).read_bytes()
    entries = _entries(data)
    script = _read(data, entries["main.tcl"]).decode("utf-8", "replace")
    target = Path(target)
    count = 0
    for m in _FILE.finditer(script):
        opts = {k: v.strip("{}") for k, v in _OPT.findall(m.group(1))}
        src = opts.get("srcfile")
        if not src or src not in entries:
            continue
        folder = opts.get("directory", "<%InstallDir%>").replace("<%InstallDir%>", "").strip("/")
        if "<%" in folder:                   # somewhere outside the install folder (shortcuts etc.): not wanted
            continue
        out = (target / folder / opts["name"]).resolve()
        if target.resolve() not in out.parents:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(_read(data, entries[src]))
        count += 1
        if progress is not None and count % 200 == 0:
            progress(count)
    return count


if __name__ == "__main__":
    print(extract(sys.argv[1], sys.argv[2], progress=lambda n: print(n, "files...")), "files")
