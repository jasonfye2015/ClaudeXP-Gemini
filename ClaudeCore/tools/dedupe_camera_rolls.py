"""Find the extra copies in Local Storage/Camera Rolls and set them aside.

Camera rolls get copied off the phone more than once, so the same photo turns up in several dated backup folders
under the same sequential name (IMG_0001.jpg...), and names can't tell copies apart. This compares contents: files
are grouped by exact size, and files sharing a size are hashed in full (BLAKE2b); identical hashes are the same file.

From each set of identical files one copy is kept - the one in the earliest-dated top-level folder ("cam 11 9 2014",
"Phone backup 6 2 2018"...; folders without a date in their name come after dated ones; then the shallower and
shorter path) - and the others are moved into "_Duplicates (delete me)" inside Camera Rolls, keeping their folder
paths, with a list of every move so they can be put back. Folders left empty are removed.

    python dedupe_camera_rolls.py            report only (Duplicate Report.txt in Camera Rolls)
    python dedupe_camera_rolls.py --apply    report, then move the extra copies aside
    python dedupe_camera_rolls.py --restore  move everything in the quarantine back where it came from
    python dedupe_camera_rolls.py --purge    delete the quarantine folder for good

Re-run it after adding new camera rolls: anything already kept stays kept.
"""
import argparse
import hashlib
import os
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
ROOT = TIMELINE / "Local Storage" / "Camera Rolls"
QUARANTINE = "_Duplicates (delete me)"
MOVES = "moves.tsv"
REPORT = "Duplicate Report.txt"
MIN_SIZE = 1024                      # tiny files (.nomedia, thumbnails caches) aren't worth it


def folder_date(name):
    """The date in a backup folder's name as (year, month, day), or None. Understands 'cam 11 9 2014',
    'Hugo 6-19-2012', 'Cell Phone photos 2 12 20', 'Camera 12 13 16' and a bare year."""
    m = re.search(r"(?<!\d)(\d{1,2})[ \-_.](\d{1,2})[ \-_.](\d{4}|\d{2})(?!\d)", name)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        if 1 <= mo <= 12 and 1 <= d <= 31 and 1990 <= y <= 2100:
            return (y, mo, d)
    m = re.search(r"(?<!\d)(19[9]\d|20\d\d)(?!\d)", name)
    if m:
        return (int(m.group(1)), 12, 31)
    return None


def keep_rank(path, root):
    rel = Path(path).relative_to(root)
    date = folder_date(rel.parts[0]) if len(rel.parts) > 1 else None
    return (date is None, date or (0, 0, 0), len(rel.parts), len(str(rel)), str(rel).lower())


def full_hash(path):
    h = hashlib.blake2b(digest_size=20)
    with open(path, "rb") as f:
        while True:
            block = f.read(4 * 2 ** 20)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def find_sets(root, log):
    by_size = defaultdict(list)
    count = 0
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != QUARANTINE]
        for name in files:
            p = os.path.join(dirpath, name)
            try:
                n = os.path.getsize(p)
            except OSError:
                continue
            if n >= MIN_SIZE:
                by_size[n].append(p)
                count += 1
    candidates = [(n, ps) for n, ps in by_size.items() if len(ps) > 1]
    todo = sum(n * len(ps) for n, ps in candidates)
    log(f"{count:,} files; {sum(len(ps) for _n, ps in candidates):,} share a size with another "
        f"({todo / 2**30:.1f} GB to compare)")
    sets, done, last = [], 0, time.time()
    for n, paths in candidates:
        by_hash = defaultdict(list)
        for p in paths:
            try:
                by_hash[full_hash(p)].append(p)
            except OSError as exc:
                log(f"  couldn't read {p}: {exc}")
            done += n
        sets += [same for same in by_hash.values() if len(same) > 1]
        if time.time() - last > 30:
            last = time.time()
            log(f"  compared {done / 2**30:.1f} of {todo / 2**30:.1f} GB...")
    return sets


def plan(sets, root):
    """[(keep, [extras])] with the keeper chosen by keep_rank."""
    out = []
    for same in sets:
        ranked = sorted(same, key=lambda p: keep_rank(p, root))
        out.append((ranked[0], ranked[1:]))
    return out


def write_report(root, decisions):
    extra = sum(len(x) for _k, x in decisions)
    size = sum(os.path.getsize(k) * len(x) for k, x in decisions)
    per_folder = defaultdict(int)
    for _k, extras in decisions:
        for p in extras:
            per_folder[Path(p).relative_to(root).parts[0]] += 1
    lines = [f"Camera Rolls duplicate report - {time.strftime('%Y-%m-%d %H:%M')}",
             f"{len(decisions):,} sets of identical files; {extra:,} extra copies ({size / 2**30:.1f} GB).",
             "", "Extra copies by folder:"]
    lines += [f"  {n:7,}  {name}" for name, n in sorted(per_folder.items(), key=lambda x: -x[1])]
    lines += ["", "Each set: + kept, - extra copy", ""]
    for keep, extras in sorted(decisions, key=lambda d: d[0].lower()):
        lines.append(f"+ {Path(keep).relative_to(root)}")
        lines += [f"- {Path(p).relative_to(root)}" for p in extras]
    (root / REPORT).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return extra, size


def apply(root, decisions, log):
    q = root / QUARANTINE
    q.mkdir(exist_ok=True)
    moved = 0
    with open(q / MOVES, "a", encoding="utf-8") as moves:
        for _keep, extras in decisions:
            for p in extras:
                rel = Path(p).relative_to(root)
                dest = q / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    dest = dest.with_name(f"{dest.stem} ({int(time.time() * 1000) % 100000}){dest.suffix}")
                try:
                    os.replace(p, dest)
                except OSError as exc:
                    log(f"  couldn't move {rel}: {exc}")
                    continue
                moves.write(f"{dest.relative_to(q)}\t{rel}\n")
                moved += 1
    removed = remove_empty(root)
    log(f"Moved {moved:,} extra copies into '{QUARANTINE}'; removed {removed} empty folders.")


def remove_empty(root):
    removed = 0
    for dirpath, dirs, files in os.walk(root, topdown=False):
        p = Path(dirpath)
        if p == root or QUARANTINE in p.relative_to(root).parts[:1]:
            continue
        try:
            if not any(p.iterdir()):
                p.rmdir()
                removed += 1
        except OSError:
            pass
    return removed


def restore(root, log):
    q = root / QUARANTINE
    try:
        rows = (q / MOVES).read_text(encoding="utf-8").splitlines()
    except OSError:
        log("Nothing to restore.")
        return
    back = 0
    for row in rows:
        here, _tab, orig = row.partition("\t")
        src, dest = q / here, root / orig
        if src.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.replace(src, dest)
            back += 1
    (q / MOVES).unlink(missing_ok=True)
    log(f"Put {back:,} files back.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=str(ROOT))
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="move the extra copies into the quarantine folder")
    group.add_argument("--restore", action="store_true", help="put everything in the quarantine back")
    group.add_argument("--purge", action="store_true", help="delete the quarantine folder for good")
    args = ap.parse_args()
    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"No such folder: {root}")

    def log(msg):
        print(msg, flush=True)
    if args.restore:
        restore(root, log)
        return
    if args.purge:
        q = root / QUARANTINE
        if q.is_dir():
            shutil.rmtree(q)
            log(f"Deleted '{QUARANTINE}'.")
        return
    started = time.time()
    decisions = plan(find_sets(root, log), root)
    extra, size = write_report(root, decisions)
    log(f"{len(decisions):,} sets; {extra:,} extra copies ({size / 2**30:.1f} GB). Report: {root / REPORT}")
    if args.apply:
        apply(root, decisions, log)
    log(f"Done in {(time.time() - started) / 60:.1f} minutes.")


if __name__ == "__main__":
    main()
