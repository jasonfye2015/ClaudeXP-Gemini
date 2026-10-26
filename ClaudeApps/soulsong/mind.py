"""A Companion's mind files (Mind L1-L6), read and written in the project's own plain-text format.

L1 Mind Resources: the roadmaps, the planned events and the system time stamp, in <Section> ... <End Section> blocks.
L2-L5 the memory banks: <Short Term Memory Bank> ... <End Short Term Memory Bank>, the memories inside it each
starting with a header line the program writes:
    [Memory #12 | Short-Term | 2026-10-26 21:14]
L6 System Instructions: read as it is.
A bank whose text has no header lines but isn't the "No memories yet" line (memories pasted in by hand) counts as
one memory. Files keep Windows line endings, like the originals."""
import re
import shutil
from datetime import datetime
from pathlib import Path

LEVELS = {1: "Mind Resources", 2: "Short Term Memory", 3: "Long Term Memory", 4: "Deep Recall Memory",
          5: "Historical Memory Bank", 6: "System Instructions"}
BANKS = {2: "Short Term Memory Bank", 3: "Long Term Memory Bank", 4: "Deep Recall Memory Bank",
         5: "Historical Memory Bank"}
KINDS = {2: "Short-Term", 3: "Long-Term", 4: "Deep Recall", 5: "Historical"}
EMPTY = {2: "No Memories Yet. New Day!", 3: "No Memories Yet! New Week!", 4: "No entries yet.", 5: "No entries yet."}
HEADER = re.compile(r"^\[Memory #(\d+) \| ([^|\]]+) \| ([^\]]+)\]\s*$", re.M)
STAMP = "%Y-%m-%d %H:%M"
TIME_LINE = re.compile(r"<Current System Time Stamp:[^>]*>")


def stamp(when=None):
    return (when or datetime.now()).strftime(STAMP)


def file_name(level):
    return f"Mind L{level} - {LEVELS[level]}.txt"


def section(text, name):
    """The text between <name> and <End name> ('' if there's no such section)."""
    m = re.search(rf"<{re.escape(name)}>\s*\n(.*?)\n?<End {re.escape(name)}>", text, re.S | re.I)
    return m.group(1).strip("\n") if m else ""


def set_section(text, name, body):
    pat = re.compile(rf"(<{re.escape(name)}>\s*\n)(.*?)(\n?<End {re.escape(name)}>)", re.S | re.I)
    if pat.search(text):
        return pat.sub(lambda m: m.group(1) + body.strip("\n") + "\n" + m.group(3).lstrip("\n"), text, count=1)
    return text.rstrip("\n") + f"\n\n<{name}>\n{body.strip()}\n<End {name}>\n"


class Mind:
    def __init__(self, folder):
        self.folder = Path(folder)

    # ---- files ----
    def path(self, level):
        return self.folder / file_name(level)

    def read(self, level):
        try:
            return self.path(level).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        except OSError:
            return ""

    def write(self, level, text):
        self.folder.mkdir(parents=True, exist_ok=True)
        tmp = self.path(level).with_suffix(".part")
        tmp.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
        tmp.replace(self.path(level))

    def create_from(self, templates):
        """A new Companion's mind: copies of the project's own L1-L6 (blank banks if a template is missing)."""
        self.folder.mkdir(parents=True, exist_ok=True)
        for level in LEVELS:
            src = Path(templates) / file_name(level)
            if src.exists():
                self.write(level, src.read_text(encoding="utf-8-sig"))
            elif level in BANKS:
                self.write(level, f"<{BANKS[level]}>\n{EMPTY[level]}\n<End {BANKS[level]}>\n")
            else:
                self.write(level, "")

    def all_text(self):
        """L1-L6, in order, as the Companion is shown them."""
        return [(level, LEVELS[level], self.read(level)) for level in LEVELS]

    # ---- the memory banks ----
    def entries(self, level):
        """[(number, kind, stamp, text)] in the bank, oldest first."""
        body = section(self.read(level), BANKS[level])
        heads = list(HEADER.finditer(body))
        if not heads:
            plain = body.strip()
            if not plain or plain.lower().rstrip("!.") in (e.lower().rstrip("!.") for e in EMPTY.values()) \
                    or plain.lower().startswith(("no memories yet", "no memrories yet", "no entries yet")):
                return []
            return [(0, KINDS[level], "", plain)]
        out = []
        for i, h in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
            out.append((int(h.group(1)), h.group(2).strip(), h.group(3).strip(), body[h.end():end].strip()))
        return out

    def count(self, level):
        return len(self.entries(level))

    def add(self, level, number, text, when=None):
        """A memory into a bank (the "No memories yet" line goes)."""
        entries = self.entries(level)
        blocks = [self._block(n, k, s, t) for n, k, s, t in entries if n] or \
                 ([entries[0][3]] if entries else [])
        blocks.append(self._block(number, KINDS[level], stamp(when), text))
        self._set_bank(level, "\n\n".join(blocks))

    def clear(self, level, archive_reason=""):
        """Empty a bank, keeping a copy of what was in it in Archive/."""
        if self.entries(level):
            arch = self.folder / "Archive"
            arch.mkdir(exist_ok=True)
            name = f"{datetime.now():%Y-%m-%d %H%M%S} L{level} {archive_reason}".strip() + ".txt"
            shutil.copy2(self.path(level), arch / name)
        self._set_bank(level, EMPTY[level])

    def bank_text(self, level):
        return "\n\n".join(self._block(n, k, s, t) if n else t for n, k, s, t in self.entries(level))

    @staticmethod
    def _block(number, kind, when, text):
        return f"[Memory #{number} | {kind} | {when}]\n{text.strip()}"

    def _set_bank(self, level, body):
        self.write(level, set_section(self.read(level), BANKS[level], body))

    # ---- L1: time stamp, roadmaps, planned events ----
    def set_time_stamp(self, when=None):
        text = self.read(1)
        line = f"<Current System Time Stamp: {stamp(when)}>"
        text = TIME_LINE.sub(line, text) if TIME_LINE.search(text) else text.rstrip("\n") + f"\n\n{line}\n"
        self.write(1, text)

    def set_start_date(self, when, name, gender=""):
        text = self.read(1)
        value = ", ".join(x for x in (stamp(when), name, gender) if x)
        text, n = re.subn(r"(?m)^(- Start Date:).*$", lambda m: f"{m.group(1)} {value}", text, count=1)
        if not n:
            road = section(text, "Companion's Development Roadmap")
            text = set_section(text, "Companion's Development Roadmap", f"- Start Date: {value}\n{road}")
        self.write(1, text)

    def roadmap(self, which="user"):
        name = "Users's Life Roadmap" if which == "user" else "Companion's Development Roadmap"
        return section(self.read(1), name)

    def set_roadmap(self, which, body):
        name = "Users's Life Roadmap" if which == "user" else "Companion's Development Roadmap"
        self.write(1, set_section(self.read(1), name, body))

    def user_fields(self):
        """The user's roadmap as [(field, value)], in the template's order."""
        out = []
        for line in self.roadmap("user").splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out.append((k.strip(), v.strip()))
        return out

    def set_user_fields(self, fields):
        self.set_roadmap("user", "\n".join(f"{k}: {v}" for k, v in fields))

    def events(self):
        """The planned events: [{"id", "when", "description", "done"}]."""
        out, cur = [], None
        for line in section(self.read(1), "Planned Events").splitlines():
            line = line.strip()
            if line.lower().startswith("event id:"):
                cur = {"id": line.split(":", 1)[1].strip().lstrip("#"), "when": "", "description": "", "done": False}
                out.append(cur)
            elif cur is not None and line.lower().startswith("date/time:"):
                cur["when"] = line.split(":", 1)[1].strip()
            elif cur is not None and line.lower().startswith("description:"):
                cur["description"] = line.split(":", 1)[1].strip()
            elif cur is not None and line.lower().startswith("status:"):
                cur["done"] = "done" in line.lower() or "past" in line.lower()
        return out

    def set_events(self, events):
        if not events:
            body = "None yet."
        else:
            body = "\n\n".join(f"Event ID: {e['id']}\nDate/Time: {e['when']}\nDescription: {e['description']}"
                               + ("\nStatus: Done" if e.get("done") else "") for e in events)
        self.write(1, set_section(self.read(1), "Planned Events", body))
