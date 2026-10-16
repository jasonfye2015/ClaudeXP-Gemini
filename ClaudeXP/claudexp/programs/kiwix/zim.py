"""A reader for ZIM files (openZIM - the format Kiwix uses for offline Wikipedia), in plain Python.

Clusters are zstd- or xz-compressed; Python's standard library handles both (compression.zstd, lzma). Supports the
old namespaces (A articles, I images, - styles and scripts, M metadata) and the new ones (C content, M metadata,
W well-known, X indexes). Lookups are binary searches over the URL and title pointer lists, so even a 13 GB
Wikipedia opens instantly. Thread-safe: one file handle, guarded by a lock; decompressed clusters are cached.
"""
import lzma
import random
import struct
import threading
from collections import OrderedDict
from pathlib import Path

MAGIC = 72173914
REDIRECT, LINKTARGET, DELETED = 0xFFFF, 0xFFFE, 0xFFFD
CACHE_CLUSTERS = 24


class Entry:
    __slots__ = ("index", "mime", "namespace", "url", "title", "cluster", "blob", "redirect")

    def __init__(self, index, mime, namespace, url, title, cluster=None, blob=None, redirect=None):
        self.index, self.mime, self.namespace = index, mime, namespace
        self.url, self.title = url, title
        self.cluster, self.blob, self.redirect = cluster, blob, redirect

    @property
    def is_redirect(self):
        return self.redirect is not None

    @property
    def path(self):
        return f"{self.namespace}/{self.url}"


class ZimFile:
    def __init__(self, path):
        self.path = Path(path)
        self.f = open(self.path, "rb")
        self.lock = threading.RLock()
        self.cache = OrderedDict()
        h = self._read(0, 80)
        (magic, self.major, self.minor) = struct.unpack_from("<IHH", h, 0)
        if magic != MAGIC:
            raise ValueError(f"{self.path.name} isn't a ZIM file")
        self.uuid = h[8:24]
        (self.entry_count, self.cluster_count, self.url_ptr_pos, self.title_ptr_pos, self.cluster_ptr_pos,
         self.mime_list_pos, self.main_page, self.layout_page, self.checksum_pos) = struct.unpack_from(
            "<IIQQQQIIQ", h, 24)
        self.mimes = self._read_mimes()
        self.size = self.path.stat().st_size
        self.new_namespaces = self._has_namespace("C")
        self._meta = {}

    # ---- raw reading ----------------------------------------------------------------------------------------
    def _read(self, pos, n):
        with self.lock:
            self.f.seek(pos)
            return self.f.read(n)

    def _read_mimes(self):
        data = self._read(self.mime_list_pos, 4096)
        out, i = [], 0
        while True:
            j = data.index(b"\0", i)
            if j == i:
                break
            out.append(data[i:j].decode("utf-8", "replace"))
            i = j + 1
        return out

    def close(self):
        with self.lock:
            self.f.close()

    # ---- directory entries ----------------------------------------------------------------------------------
    def _url_ptr(self, i):
        return struct.unpack("<Q", self._read(self.url_ptr_pos + 8 * i, 8))[0]

    def _titles(self):
        """(count, index_of(i)) for the title-ordered list. Older ZIMs keep it in the header; newer ones (6.3+) store
        X/listing/titleOrdered/v1 instead - articles only, as an array of entry numbers."""
        if not hasattr(self, "_title_list"):
            self._title_list = None
            if self.title_ptr_pos >= self.size:
                e = self.find("X", "listing/titleOrdered/v1") or self.find("X", "listing/titleOrdered/v0")
                data = self.content(e) if e is not None else None
                if data:
                    import array
                    arr = array.array("I")
                    arr.frombytes(data[: len(data) // 4 * 4])
                    self._title_list = arr
        if self._title_list is not None:
            return len(self._title_list), self._title_list.__getitem__
        return self.entry_count, self._title_idx

    def _title_idx(self, i):
        return struct.unpack("<I", self._read(self.title_ptr_pos + 4 * i, 4))[0]

    def entry(self, i):
        pos = self._url_ptr(i)
        head = self._read(pos, 1024)
        mime, param_len, ns = struct.unpack_from("<HBc", head, 0)
        ns = ns.decode("latin-1")
        if mime == REDIRECT:
            (target,) = struct.unpack_from("<I", head, 8)
            off = 12
            cluster = blob = None
        elif mime in (LINKTARGET, DELETED):
            target, cluster, blob, off = None, None, None, 8
        else:
            cluster, blob = struct.unpack_from("<II", head, 8)
            target, off = None, 16
        if head.count(b"\0", off) < 2:                      # very long url/title: read more
            head = self._read(pos, 8192)
        j = head.index(b"\0", off)
        url = head[off:j].decode("utf-8", "replace")
        k = head.index(b"\0", j + 1)
        title = head[j + 1:k].decode("utf-8", "replace") or url
        return Entry(i, None if mime >= DELETED else (self.mimes[mime] if mime < len(self.mimes) else ""),
                     ns, url, title, cluster, blob, target)

    def _key(self, i):
        e = self.entry(i)
        return e.namespace, e.url

    def find(self, namespace, url, exact=True):
        """Binary search the URL list. exact=False returns the first index >= (namespace, url)."""
        lo, hi = 0, self.entry_count
        target = (namespace, url)
        while lo < hi:
            mid = (lo + hi) // 2
            key = self._key(mid)
            if (key[0].encode("latin-1"), key[1].encode("utf-8")) < (target[0].encode("latin-1"),
                                                                     target[1].encode("utf-8")):
                lo = mid + 1
            else:
                hi = mid
        if lo >= self.entry_count:
            return None
        if exact:
            e = self.entry(lo)
            return e if (e.namespace, e.url) == target else None
        return lo

    def _has_namespace(self, ns):
        i = self.find(ns, "", exact=False)
        return i is not None and self.entry(i).namespace == ns

    def resolve(self, entry, depth=0):
        """Follow redirects to the entry that has content."""
        while entry is not None and entry.is_redirect and depth < 20:
            entry = self.entry(entry.redirect)
            depth += 1
        return entry

    # ---- content ----------------------------------------------------------------------------------------------
    def _cluster_offsets(self, c):
        start = struct.unpack("<Q", self._read(self.cluster_ptr_pos + 8 * c, 8))[0]
        if c + 1 < self.cluster_count:
            end = struct.unpack("<Q", self._read(self.cluster_ptr_pos + 8 * (c + 1), 8))[0]
        else:
            end = self.checksum_pos if self.checksum_pos else self.size
        return start, end

    def _cluster(self, c):
        with self.lock:
            if c in self.cache:
                self.cache.move_to_end(c)
                return self.cache[c]
        start, end = self._cluster_offsets(c)
        raw = self._read(start, end - start)
        info = raw[0]
        comp, extended = info & 0x0F, bool(info & 0x10)
        body = raw[1:]
        if comp == 5:
            from compression import zstd
            body = zstd.decompress(body)
        elif comp == 4:
            body = lzma.decompress(body)
        elif comp not in (0, 1):
            raise ValueError(f"unsupported cluster compression {comp}")
        size = 8 if extended else 4
        fmt = "<Q" if extended else "<I"
        first = struct.unpack_from(fmt, body, 0)[0]
        count = first // size
        offsets = [struct.unpack_from(fmt, body, size * i)[0] for i in range(count)]
        value = (body, offsets)
        with self.lock:
            self.cache[c] = value
            while len(self.cache) > CACHE_CLUSTERS:
                self.cache.popitem(last=False)
        return value

    def content(self, entry):
        entry = self.resolve(entry)
        if entry is None or entry.cluster is None:
            return None
        body, offsets = self._cluster(entry.cluster)
        if entry.blob + 1 >= len(offsets):
            return b""
        return body[offsets[entry.blob]:offsets[entry.blob + 1]]

    # ---- what Kiwix needs ---------------------------------------------------------------------------------------
    @property
    def article_ns(self):
        return "C" if self.new_namespaces else "A"

    def get(self, path):
        """'C/Foo', 'A/Foo', 'I/x.png', or (new ZIMs) a bare content path 'Foo' -> Entry or None."""
        if len(path) > 2 and path[1] == "/" and path[0] in "ACIMWX-JUV":
            e = self.find(path[0], path[2:])
            if e is not None:
                return e
        return self.find(self.article_ns, path)

    def metadata(self, name):
        if name not in self._meta:
            e = self.find("M", name)
            data = self.content(e) if e is not None else None
            self._meta[name] = data.decode("utf-8", "replace") if isinstance(data, bytes) and \
                not name.startswith("Illustration") else data
        return self._meta[name]

    def main_entry(self):
        if self.main_page != 0xFFFFFFFF:
            return self.entry(self.main_page)
        e = self.find("W", "mainPage")
        return e

    def illustration(self):
        for name in ("Illustration_48x48@1", "Illustration_96x96@1"):
            data = self.metadata(name)
            if data:
                return data
        e = self.find("-", "favicon") or self.find("I", "favicon.png")
        return self.content(e) if e is not None else None

    def title(self):
        return self.metadata("Title") or self.path.stem

    def soft_target(self, entry):
        """Wikipedia ZIMs have tiny pages that just jump elsewhere (meta refresh): -> the url they jump to, or None."""
        import re
        if entry is None or entry.is_redirect or not (entry.mime or "").startswith("text/html"):
            return None
        data = self.content(entry)
        if not data or len(data) > 800 or b"refresh" not in data:
            return None
        m = re.search(rb"url=['\"]?([^\"'>]+)", data, re.I)
        if not m:
            return None
        from urllib.parse import unquote
        return unquote(m.group(1).decode("utf-8", "replace")).lstrip("./").split("#")[0] or None

    def suggest(self, text, limit=20):
        """Titles starting with text (tried as typed, Capitalized and Title Case) -> [(title, path)], one per article
        (redirects and soft redirects lead to the article they point at)."""
        ns = self.article_ns
        targets, out = set(), []
        for variant in dict.fromkeys((text, text[:1].upper() + text[1:], text.title())):
            for e in self._title_prefix(ns, variant, limit * 4):
                target = self.resolve(e)
                if target is None or not (target.mime or "").startswith("text/html"):
                    continue
                path = target.path if not self.new_namespaces else target.url
                title = target.title
                soft = self.soft_target(target)
                if soft:                                       # a jump page: suggest the article it jumps to
                    real = self.resolve(self.get(soft))
                    if real is not None:
                        path, title = (real.url if self.new_namespaces else real.path), real.title
                if path in targets:                            # one suggestion per article
                    continue
                targets.add(path)
                out.append((title, path))
                if len(out) >= limit:
                    return out
        return out

    def _title_prefix(self, ns, prefix, limit):
        count, at = self._titles()
        lo, hi = 0, count
        want = (ns.encode("latin-1"), prefix.encode("utf-8"))
        while lo < hi:
            mid = (lo + hi) // 2
            e = self.entry(at(mid))
            if (e.namespace.encode("latin-1"), e.title.encode("utf-8")) < want:
                lo = mid + 1
            else:
                hi = mid
        found = []
        i = lo
        while i < count and len(found) < limit:
            e = self.entry(at(i))
            if e.namespace != ns or not e.title.startswith(prefix):
                break
            found.append(e)
            i += 1
        return found

    def random_article(self, tries=80):
        """A random real article (not a redirect, a soft redirect or an asset)."""
        count, at = self._titles()
        ns = self.article_ns
        for _ in range(tries):
            e = self.entry(at(random.randrange(count)))
            if e.is_redirect or e.namespace != ns or not (e.mime or "").startswith("text/html"):
                continue
            if e.url.startswith(("_", "-")) or self.soft_target(e):
                continue
            main = self.resolve(self.main_entry())
            if main is not None and main.index == e.index:
                continue
            return e.url if self.new_namespaces else e.path
        return None


def info(path):
    """{title, description, language, date, count, size} for the library, without keeping the file open."""
    z = ZimFile(path)
    try:
        return {"title": z.title(), "description": z.metadata("Description") or "",
                "language": z.metadata("Language") or "", "date": z.metadata("Date") or "",
                "creator": z.metadata("Creator") or "", "count": z.entry_count, "size": z.size,
                "illustration": z.illustration()}
    finally:
        z.close()
