"""Pictures a buddy can send: a folder of images, described by filename or captions.txt."""
import difflib
import re
from pathlib import Path

from .paths import ICON_EXTS, natural_key

PIC_TAG = re.compile(r"\[\s*(?:pic|picture|photo|img|image)\s*:\s*([^\]]+?)\s*\]", re.IGNORECASE)
SHARING_MODES = ("eager", "when_asked", "never")


class PictureSet:
    def __init__(self, folder: Path):
        self.folder = folder
        self.captions = {}  # filename -> description
        files = [p for p in folder.iterdir() if p.suffix.lower() in ICON_EXTS] if folder.is_dir() else []
        for p in sorted(files, key=lambda p: natural_key(p.name)):
            self.captions[p.name] = re.sub(r"[_-]+", " ", p.stem).strip()
        self._read_captions(folder / "captions.txt")

    def _read_captions(self, path):
        """Lines like 'park.jpg: me in my suit at the park'. The extension is optional."""
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            name, sep, caption = line.partition(":")
            if not sep or not caption.strip():
                continue
            match = self.match(name.strip())
            if match:
                self.captions[match] = caption.strip()

    def __bool__(self):
        return bool(self.captions)

    @staticmethod
    def set_of(name: str) -> str:
        """The set a picture belongs to: its name without the number at the end.
        red_truck1.jpg and red_truck6.jpg are both in set "red_truck"."""
        return re.sub(r"[\s_-]*\d+$", "", Path(name).stem) or Path(name).stem

    @property
    def sets(self) -> dict:
        """Set name -> its pictures, in order."""
        out = {}
        for name in self.captions:
            out.setdefault(self.set_of(name), []).append(name)
        return out

    def path(self, name) -> Path:
        return self.folder / name

    def match(self, ref: str):
        """Find the picture a reference means, forgiving small mistakes by the model."""
        ref = ref.strip().strip("'\"").lower()
        by_name = {n.lower(): n for n in self.captions}
        by_stem = {Path(n).stem.lower(): n for n in self.captions}
        by_caption = {c.lower(): n for n, c in self.captions.items()}
        by_set = {key.lower(): names[0] for key, names in self.sets.items()}
        for table in (by_name, by_stem, by_set, by_caption):
            if ref in table:
                return table[ref]
        close = difflib.get_close_matches(ref, list(by_name) + list(by_stem) + list(by_set),
                                          n=1, cutoff=0.75)
        if close:
            return by_name.get(close[0]) or by_stem.get(close[0]) or by_set.get(close[0])
        return None

    def extract(self, text: str):
        """Split a message into its text and the pictures it sends. Unknown pictures are dropped."""
        names = []
        for ref in PIC_TAG.findall(text):
            name = self.match(ref)
            if name and name not in names:
                names.append(name)
        clean = PIC_TAG.sub("", text)
        clean = "\n".join(line.rstrip() for line in clean.splitlines() if line.strip()).strip()
        return clean, names


def strip_tags(text: str) -> str:
    """For buddies with no pictures: never show a raw [pic: ...] tag."""
    return PIC_TAG.sub("", text).strip()
