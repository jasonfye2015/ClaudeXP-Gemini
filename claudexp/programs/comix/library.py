"""The comic shelves on E: (Local Storage/Furry Media Archive.../Comic Scans...), looked at one folder at a time.

Nothing is indexed up front: opening a shelf lists that one folder (names only), and a comic's cover is read the
first time its tile scrolls into view, then kept as a small thumbnail in data/comix_thumbs (never in the archive).

A comic is a folder with page images in it, or a .cbz/.zip/.cbr/.rar/.cb7/.7z/.pdf file. A folder holding only
folders is a shelf. Folders that just wrap a single folder are looked through, and an archive is hidden when a
folder of the same name sits next to it (it has already been extracted). .zip/.cbz open with Python; RAR and 7z
need 7-Zip, which most users won't have, so the user's own archive ships with those already extracted."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt
from PySide6.QtGui import QImage, QImageReader, QPainter

from ...paths import DATA

IMAGE_EXTS = {".jpg", ".jpeg", ".jfif", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
ZIP_EXTS = {".cbz", ".zip"}
SEVEN_EXTS = {".cbr", ".rar", ".cb7", ".7z"}
PDF_EXTS = {".pdf"}
ARCHIVE_EXTS = ZIP_EXTS | SEVEN_EXTS | PDF_EXTS
THUMBS = DATA / "comix_thumbs"
STATE_FILE = DATA / "comix.json"
THUMB = QSize(120, 170)


def comics_root():
    """The Comic Scans folder, or None if the user hasn't put the archive on E:."""
    from .. import archive_folder
    archive = archive_folder("mediaarchive")
    if archive is None:
        return None
    return next((d for d in sorted(archive.iterdir()) if d.is_dir() and d.name.lower().startswith("comic scans")),
                None)


def natural_key(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def nice_name(name):
    """'- Spoo #001 - #017' -> 'Spoo #001 - #017'; '[fxc]_Furnation_6' -> 'Furnation 6'."""
    n = re.sub(r"^\s*-\s+", "", name)
    n = re.sub(r"\[(fxc|fxa|kitsu|furry)\]\s*", "", n, flags=re.I)
    if "_" in n and " " not in n.strip("_"):
        n = n.replace("_", " ")
    n = re.sub(r"\s{2,}", " ", n).strip(" _-")
    return n or name


def seven_zip():
    """7z.exe if the PC has 7-Zip (or 7z on the PATH); None otherwise."""
    for p in (r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe"):
        if os.path.exists(p):
            return p
    return shutil.which("7z")


def _no_window():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


# ---- entries -------------------------------------------------------------------------------------------------

class Entry:
    """kind: 'shelf' (a folder of comics) or 'comic'. source: 'folder' | 'zip' | '7z' | 'pdf'."""
    __slots__ = ("path", "kind", "source", "name")

    def __init__(self, path, kind, source="folder", name=None):
        self.path, self.kind, self.source = Path(path), kind, source
        self.name = name or nice_name(self.path.stem if source != "folder" else self.path.name)

    @property
    def key(self):
        return str(self.path)


def _scan(folder):
    """(subfolders, images, archives) directly inside folder, by name only."""
    dirs, images, archives = [], [], []
    try:
        with os.scandir(folder) as it:
            for e in it:
                if e.name.startswith(".") or e.name.lower() in ("thumbs.db", "desktop.ini"):
                    continue
                ext = os.path.splitext(e.name)[1].lower()
                if e.is_dir():
                    dirs.append(e.name)
                elif ext in IMAGE_EXTS:
                    images.append(e.name)
                elif ext in ARCHIVE_EXTS:
                    archives.append(e.name)
    except OSError:
        pass
    key = natural_key
    return sorted(dirs, key=key), sorted(images, key=key), sorted(archives, key=key)


def resolve(folder):
    """Look through folders that only wrap one other folder. Returns (folder, (dirs, images, archives))."""
    folder = Path(folder)
    for _ in range(6):
        dirs, images, archives = _scan(folder)
        if len(dirs) == 1 and not images and not archives:
            folder = folder / dirs[0]
            continue
        return folder, (dirs, images, archives)
    return folder, _scan(folder)


def classify(path):
    """An Entry for a folder or archive file, or None if it holds nothing readable."""
    path = Path(path)
    if path.is_file():
        ext = path.suffix.lower()
        source = "zip" if ext in ZIP_EXTS else "7z" if ext in SEVEN_EXTS else "pdf" if ext in PDF_EXTS else None
        return Entry(path, "comic", source) if source else None
    inner, (dirs, images, archives) = resolve(path)
    name = nice_name(path.name)
    if images and not dirs and not _visible_archives(inner, dirs, archives):
        return Entry(inner, "comic", name=name)
    if dirs or images or archives:
        return Entry(inner, "shelf", name=name)
    return None


def _visible_archives(folder, dirs, archives):
    """Archives that haven't already been extracted next to themselves (a same-named folder)."""
    have = {d.lower() for d in dirs}
    return [a for a in archives if os.path.splitext(a)[0].lower() not in have]


def list_shelf(folder):
    """The entries on a shelf: its own loose pages (as one comic), then sub-folders and archives."""
    folder, (dirs, images, archives) = resolve(folder)
    out = []
    if images:
        out.append(Entry(folder, "comic", name=nice_name(folder.name) + (" (pages)" if dirs else "")))
    for d in dirs:
        e = classify(folder / d)
        if e is not None:
            out.append(e)
    for a in _visible_archives(folder, dirs, archives):
        e = classify(folder / a)
        if e is not None:
            out.append(e)
    return folder, out


def first_comic(entry, depth=4):
    """The comic whose cover stands for a shelf (its first readable comic)."""
    while entry is not None and entry.kind == "shelf" and depth > 0:
        _f, items = list_shelf(entry.path)
        entry = next((e for e in items if e.kind == "comic"), items[0] if items else None)
        depth -= 1
    return entry if entry is not None and entry.kind == "comic" else None


# ---- pages ------------------------------------------------------------------------------------------------

class Book:
    """An open comic: page names, and each page's image on request."""

    def __init__(self, entry):
        self.entry = entry
        self.error = ""
        self.pages = []
        self._zip = None
        self._pdf = None
        src = entry.source
        try:
            if src == "folder":
                _d, images, _a = _scan(entry.path)
                self.pages = images
            elif src == "zip":
                self._zip = zipfile.ZipFile(entry.path)
                self.pages = sorted((n for n in self._zip.namelist()
                                     if os.path.splitext(n)[1].lower() in IMAGE_EXTS and not n.startswith("__MACOSX")),
                                    key=natural_key)
            elif src == "7z":
                exe = seven_zip()
                if exe is None:
                    self.error = ("This comic is a RAR/7z archive.\n\nFurComix Reader needs 7-Zip to open it. "
                                  "Install 7-Zip, or extract the comic into a folder of the same name.")
                    return
                out = subprocess.run([exe, "l", "-slt", "-ba", str(entry.path)], capture_output=True, text=True,
                                     encoding="utf-8", errors="replace", **_no_window()).stdout
                names = [ln[7:] for ln in out.splitlines() if ln.startswith("Path = ")]
                self.pages = sorted((n for n in names if os.path.splitext(n)[1].lower() in IMAGE_EXTS),
                                    key=natural_key)
            elif src == "pdf":
                from PySide6.QtPdf import QPdfDocument
                self._pdf = QPdfDocument()
                self._pdf.load(str(entry.path))
                self.pages = [f"Page {i + 1}" for i in range(self._pdf.pageCount())]
        except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
            self.error = f"This comic couldn't be opened.\n\n{exc}"
        if not self.pages and not self.error:
            self.error = "There are no pages in this comic."

    def page_bytes(self, i):
        name = self.pages[i]
        if self.entry.source == "folder":
            return (self.entry.path / name).read_bytes()
        if self.entry.source == "zip":
            return self._zip.read(name)
        if self.entry.source == "7z":
            return subprocess.run([seven_zip(), "e", "-so", str(self.entry.path), name], capture_output=True,
                                  **_no_window()).stdout
        return b""

    def image(self, i, size=None):
        """Page i as a QImage (scaled down while decoding when size is given). Safe from worker threads."""
        if not 0 <= i < len(self.pages):
            return QImage()
        if self.entry.source == "pdf":
            pt = self._pdf.pagePointSize(i)
            scale = 2.0 if size is None else max(0.2, min(size.width() / max(1, pt.width()),
                                                          size.height() / max(1, pt.height())))
            page = self._pdf.render(i, QSize(int(pt.width() * scale), int(pt.height() * scale)))
            paper = QImage(page.size(), QImage.Format_RGB32)      # PDF pages render on a transparent background
            paper.fill(Qt.white)
            p = QPainter(paper)
            p.drawImage(0, 0, page)
            p.end()
            return paper
        try:
            data = self.page_bytes(i)
        except (OSError, KeyError, zipfile.BadZipFile):
            return QImage()
        return decode(data, size)

    def close(self):
        if self._zip is not None:
            self._zip.close()


def decode(data, size=None):
    buf = QBuffer()
    buf.setData(QByteArray(data))
    buf.open(QIODevice.ReadOnly)
    reader = QImageReader(buf)
    reader.setAutoTransform(True)
    if size is not None:
        full = reader.size()
        if full.isValid() and (full.width() > size.width() or full.height() > size.height()):
            reader.setScaledSize(full.scaled(size, Qt.KeepAspectRatio))
    img = reader.read()
    return img


# ---- covers -----------------------------------------------------------------------------------------------

def _thumb_file(entry):
    try:
        mtime = int(entry.path.stat().st_mtime)
    except OSError:
        mtime = 0
    return THUMBS / (hashlib.sha1(f"{entry.path}|{mtime}".encode("utf-8")).hexdigest()[:20] + ".jpg")


def cover(entry):
    """A cover thumbnail for an entry (cached). Runs in a worker thread."""
    comic = first_comic(entry) if entry.kind == "shelf" else entry
    if comic is None:
        return QImage()
    f = _thumb_file(comic)
    if f.exists():
        img = QImage(str(f))
        if not img.isNull():
            return img
    book = Book(comic)
    img = QImage() if book.error else book.image(0, THUMB * 2)
    book.close()
    if not img.isNull():
        img = img.scaled(THUMB, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        try:
            THUMBS.mkdir(parents=True, exist_ok=True)
            img.save(str(f), "JPG", 85)
        except OSError:
            pass
    return img


# ---- reading progress ---------------------------------------------------------------------------------------

def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    except OSError:
        pass


def remember(state, entry, page, pages):
    books = state.setdefault("books", {})
    books[entry.key] = {"page": page, "pages": pages, "name": entry.name, "source": entry.source,
                        "last": time.time()}
    save_state(state)


def recent(state, n=8):
    """Recently read comics that still exist, newest first."""
    books = sorted(state.get("books", {}).items(), key=lambda kv: -kv[1].get("last", 0))
    out = []
    for path, info in books:
        if os.path.exists(path):
            out.append(Entry(path, "comic", info.get("source", "folder"), name=info.get("name")))
        if len(out) >= n:
            break
    return out
