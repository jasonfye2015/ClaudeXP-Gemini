"""Set aside everything in Local Storage/Text Logs that isn't a chat log, for the user to look through.

Text Logs holds backups of chat clients' log folders, and many of them took the whole program folder along: DLLs,
skins, sounds, Second Life's texture cache, settings. This moves all of that into "_Not Logs (review)" inside Text
Logs, keeping the folder paths, with a list of every move (--restore puts them all back).

Kept in place:
  - chat logs: .html/.htm/.txt/.log/.rtf (outside program internals like caches, skins and browser profiles), .xml
    in log folders (Trillian's Query/Channel logs, MSN Messenger's History), Yahoo's Archive/Messages .dat files
    and Skype's chatsync .dat files, Skype's .db databases
  - .zip/.rar/.7z archives (some histories were packed up)

    python sort_text_logs.py            report only (Not Logs Report.txt in Text Logs)
    python sort_text_logs.py --apply    move the non-log files aside
    python sort_text_logs.py --restore  put them back
"""
import argparse
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
ROOT = TIMELINE / "Local Storage" / "Text Logs"
HOLD = "_Not Logs (review)"
MOVES = "moves.tsv"
REPORT = "Not Logs Report.txt"

LOG_EXTS = {".html", ".htm", ".txt", ".log", ".rtf"}
ARCHIVE_EXTS = {".zip", ".rar", ".7z"}
# folders inside a backed-up program that never hold logs
PROGRAM_DIRS = {"cache", "browser_profile", "skins", "skin", "themes", "theme", "emoticons", "smileys", "sounds",
                "plugins", "plugin", "help", "docs", "doc", "user_settings", "textures", "texturecache", "content",
                "pictures", "my skype received files", "dictionaries", "fonts", "lang", "languages", "images",
                "icons", "avatars", "buddyicons", "buddy icons", "updates", "temp", "tmp", "crashes", "dumps",
                "objectcache", "inv", "media_plugins", "llplugin", "app_settings", "character", "fs_cache"}
JUNK_NAMES = re.compile(r"^(readme|read me|license|licence|copying|changes|changelog|install|history\.txt$|news"
                        r"|credits|authors|whatsnew|avatar_icons_cache|stats|settings|toolbars|search_history"
                        r"|teleport_history|typed_locations|url_history|mute|crash|debug|secondlife\.log|"
                        r"browser_|plugin_)", re.I)


def is_log(rel):
    """Should this file (path relative to Text Logs) stay?"""
    parts = [p.lower() for p in rel.parts]
    name, ext = parts[-1], os.path.splitext(parts[-1])[1]
    dirs = parts[:-1]
    if ext in ARCHIVE_EXTS:
        return True
    if any(d in PROGRAM_DIRS for d in dirs):           # (not dot-folders: Gaim keeps its logs in .gaim/logs)
        return False
    if ext == ".db":
        return True                                     # Skype's and AIM 6's history databases
    if ext == ".dat":
        return ("archive" in dirs and "messages" in dirs) or "chatsync" in dirs
    if ext == ".xml":
        return bool({"query", "channel", "console", "history", "logs"} & set(dirs)) or "msn" in " ".join(dirs)
    if ext in LOG_EXTS:
        return not JUNK_NAMES.match(name)
    return False


def plan(root):
    keep, move = [], []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != HOLD]
        for name in files:
            rel = Path(dirpath, name).relative_to(root)
            if rel.name in (REPORT,):
                continue
            (keep if is_log(rel) else move).append(rel)
    return keep, move


def report(root, keep, move):
    def size(rels):
        total = 0
        for r in rels:
            try:
                total += (root / r).stat().st_size
            except OSError:
                pass
        return total
    by_ext = Counter(r.suffix.lower() or "(none)" for r in move)
    by_dir = Counter("/".join(r.parts[:3]) for r in move)
    kept_ext = Counter(r.suffix.lower() or "(none)" for r in keep)
    lines = [f"Text Logs sort - {time.strftime('%Y-%m-%d %H:%M')}",
             f"Kept as logs: {len(keep):,} files ({size(keep) / 2**30:.2f} GB)",
             f"To set aside: {len(move):,} files ({size(move) / 2**30:.2f} GB)", "",
             "Kept, by type:"] + [f"  {n:7,}  {e}" for e, n in kept_ext.most_common()]
    lines += ["", "Set aside, by type:"] + [f"  {n:7,}  {e}" for e, n in by_ext.most_common()]
    lines += ["", "Set aside, by folder:"] + [f"  {n:7,}  {d}" for d, n in by_dir.most_common()]
    lines += ["", "Every file set aside:"] + [f"  {r}" for r in sorted(move)]
    (root / REPORT).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines[:6]


def apply(root, move, log):
    hold = root / HOLD
    hold.mkdir(exist_ok=True)
    moved = 0
    with open(hold / MOVES, "a", encoding="utf-8") as moves:
        for rel in move:
            dest = hold / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.replace(root / rel, dest)
            except OSError as exc:
                log(f"  couldn't move {rel}: {exc}")
                continue
            moves.write(f"{rel}\n")
            moved += 1
    removed = 0
    for dirpath, _dirs, _files in os.walk(root, topdown=False):
        p = Path(dirpath)
        if p == root or p.relative_to(root).parts[0] == HOLD:
            continue
        try:
            if not any(p.iterdir()):
                p.rmdir()
                removed += 1
        except OSError:
            pass
    log(f"Moved {moved:,} files into '{HOLD}'; removed {removed:,} empty folders.")


def restore(root, log):
    hold = root / HOLD
    try:
        rows = (hold / MOVES).read_text(encoding="utf-8").splitlines()
    except OSError:
        log("Nothing to restore.")
        return
    back = 0
    for rel in rows:
        src, dest = hold / rel, root / rel
        if src.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.replace(src, dest)
            back += 1
    (hold / MOVES).unlink(missing_ok=True)
    log(f"Put {back:,} files back.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=str(ROOT))
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true")
    group.add_argument("--restore", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"No such folder: {root}")
    if args.restore:
        restore(root, print)
        return
    keep, move = plan(root)
    for line in report(root, keep, move):
        print(line)
    if args.apply:
        apply(root, move, print)


if __name__ == "__main__":
    main()
