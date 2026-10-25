"""What's in Local Storage: walks the whole drive and writes Manual/14-local-storage.md - every folder two levels deep
(three for the big archives), with its files, sub-folders, size and what kinds of files they are.

    python -m manual.inventory [--storage PATH] [--out PATH]

Takes a few minutes over USB; run it again whenever the archive changes, so the manual says what's really there."""
import argparse
import os
import time
from collections import Counter
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
STORAGE = TIMELINE / "Local Storage"
OUT = TIMELINE / "Manual" / "14-local-storage.md"
DEEPER = {"Furry Media Archive", "TV and Movies", "Emulation", "LLM Models"}       # three levels for these

KINDS = [
    ("pictures", {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".psd", ".svg", ".ico", ".heic", ".cr2", ".tga", ".pspimage"}),
    ("video", {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v", ".mpg", ".mpeg", ".flv", ".webm", ".ts", ".vob", ".3gp", ".ogv"}),
    ("audio", {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".wma", ".aac", ".mid", ".midi", ".opus"}),
    ("comics", {".cbr", ".cbz", ".cb7"}),
    ("archives", {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso", ".bin", ".cue", ".nrg", ".mdf", ".img"}),
    ("text and documents", {".txt", ".doc", ".docx", ".rtf", ".pdf", ".odt", ".md", ".log", ".csv", ".xls", ".xlsx",
                            ".epub", ".mobi", ".lit", ".pdb"}),
    ("web pages", {".html", ".htm", ".css", ".js", ".php", ".xml", ".json", ".shtml"}),
    ("Flash", {".swf", ".fla"}),
    ("models and Kiwix", {".gguf", ".safetensors", ".bin.index", ".pt", ".pth", ".ckpt", ".onnx", ".zim"}),
    ("ROMs and WADs", {".nes", ".smc", ".sfc", ".gb", ".gbc", ".gba", ".gen", ".sms", ".gg", ".z64", ".n64",
                       ".v64", ".dsk", ".wad", ".pk3", ".32x"}),
    ("programs", {".exe", ".dll", ".py", ".pyd", ".so", ".dylib", ".bat", ".sh", ".msi"}),
]
KIND_OF = {ext: kind for kind, exts in KINDS for ext in exts}


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024


class Node:
    __slots__ = ("name", "files", "dirs", "size", "kinds", "exts", "children")

    def __init__(self, name):
        self.name, self.files, self.dirs, self.size = name, 0, 0, 0
        self.kinds, self.exts, self.children = Counter(), Counter(), {}

    def add(self, other):
        """Count another folder's files into this one (its folders are counted where it's walked)."""
        self.files += other.files
        self.size += other.size
        self.kinds.update(other.kinds)
        self.exts.update(other.exts)

    def kinds_text(self, top=3):
        if not self.files:
            return ""
        parts = []
        for kind, n in self.kinds.most_common(top):
            label = kind
            if kind == "other":                       # say which kinds of "other": the commonest extensions
                exts = [e or "no extension" for e, _n in self.exts.most_common(3)]
                label = f"other ({', '.join(exts)})"
            parts.append(f"{label} {n:,}" if n != self.files else label)
        return ", ".join(parts)


def scan(folder, depth, keep):
    """A Node for `folder`, with children kept `keep` levels down (totals always cover everything beneath)."""
    node = Node(folder.name)
    try:
        entries = list(os.scandir(folder))
    except OSError:
        return node
    for e in entries:
        try:
            if e.is_dir(follow_symlinks=False):
                child = scan(Path(e.path), depth + 1, keep)
                node.dirs += 1 + child.dirs
                node.add(child)
                if keep > 0:
                    node.children[e.name] = child
            elif e.is_file(follow_symlinks=False):
                node.files += 1
                node.size += e.stat(follow_symlinks=False).st_size
                ext = os.path.splitext(e.name)[1].lower()
                kind = KIND_OF.get(ext, "other")
                node.kinds[kind] += 1
                if kind == "other":
                    node.exts[ext] += 1
        except OSError:
            continue
    return node


def row(name, node, indent=0):
    label = ("&nbsp;&nbsp;&nbsp;&nbsp;" * indent) + name.replace("|", "/")
    return f"| {label} | {node.files:,} | {node.dirs:,} | {human(node.size)} | {node.kinds_text()} |"


def write(root, storage, out):
    lines = ["# 14. What's in Local Storage", "",
             f"Scanned {time.strftime('%d %B %Y')} from `{storage}`. This is the inventory of the drive the Timeline is "
             "built around; the project is not meant to run without it. Sizes are the files' own, not the space they "
             "take on the exFAT drive, where small files round up to 256 KB. Regenerate with "
             "`python -m manual.inventory` from `ClaudeApps` after the archive changes.", "",
             f"**In all: {root.files:,} files in {root.dirs:,} folders, {human(root.size)}.**", "",
             "| Folder | Files | Folders | Size | Mostly |", "|---|---:|---:|---:|---|"]
    for name, node in sorted(root.children.items(), key=lambda kv: -kv[1].size):
        lines.append(row(f"**{name}**", node))
    lines += ["", "## Folder by folder", "",
              "Each top folder, with what's inside it. Counts and sizes include everything beneath a folder."]
    for name, node in sorted(root.children.items(), key=lambda kv: -kv[1].size):
        lines += ["", f"### {name}", "",
                  f"{node.files:,} files, {node.dirs:,} folders, {human(node.size)}" +
                  (f"; {node.kinds_text(5)}" if node.files else ""), ""]
        if not node.children:
            continue
        lines += ["| Folder | Files | Folders | Size | Mostly |", "|---|---:|---:|---:|---|"]
        for cname, child in sorted(node.children.items(), key=lambda kv: -kv[1].size):
            lines.append(row(cname, child))
            for gname, grand in sorted(child.children.items(), key=lambda kv: -kv[1].size):
                lines.append(row(gname, grand, 1))
    kinds = Counter()
    for node in root.children.values():
        kinds.update(node.kinds)
    lines += ["", "## By kind of file", "", "| Kind | Files |", "|---|---:|"]
    for kind, n in kinds.most_common():
        lines.append(f"| {kind} | {n:,} |")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--storage", type=Path, default=STORAGE)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    started = time.time()
    root = Node(args.storage.name)
    for e in sorted(os.scandir(args.storage), key=lambda e: e.name.lower()):
        if e.is_dir(follow_symlinks=False):
            keep = 2 if e.name in DEEPER else 1
            child = scan(Path(e.path), 1, keep)
            root.dirs += 1 + child.dirs
            root.add(child)
            root.children[e.name] = child
        elif e.is_file(follow_symlinks=False):
            root.files += 1
            root.size += e.stat().st_size
    write(root, args.storage, args.out)
    print(f"{root.files:,} files, {human(root.size)}, {time.time() - started:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
