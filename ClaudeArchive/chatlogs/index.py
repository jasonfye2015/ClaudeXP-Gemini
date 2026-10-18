"""The chat log index: every line of every log in Local Storage/Text Logs, from whichever client wrote it, in one
SQLite file (Text Logs/_Index/chatlogs.sqlite) that the Furry Chat Logs program reads.

Readers, one per log format:
  - Gaim / Pidgin   logs/<protocol>/<account>/<contact>/<YYYY-MM-DD.HHMMSS>.html|.txt   (".chat" contacts are rooms)
  - Digsby          <user>/<service>/<account>/<contact>_<service>/<YYYY-MM-DD>.html     (times in UTC)
  - Trillian        <SERVICE>/Query|Channel/<contact>.xml (or .log when there's no .xml)
  - Second Life     <Contact Name>.txt and chat.txt in a viewer's per-account log folder
  - mIRC / vIRC     <#channel or nick>[.YYYYMMDD].log

The same conversation is usually in several backups (and in more than one client's logs), and clients name the user
differently ("Alpha", "lupine14221"), so a line counts as already known when the same service, account and contact
have a line in the same minute, in the same direction, with the same text. Old Second Life logs carry only the
time of day: those lines take the date of the backup they came from (marked approximate), and are matched on the
time of day instead.

    python -m chatlogs.index            (from ClaudeArchive) builds the index from scratch
"""
import html
import os
import re
import sqlite3
import struct
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote

INDEX_DIR = "_Index"
DB_NAME = "chatlogs.sqlite"
SKIP_DIRS = {INDEX_DIR.lower(), "_not logs (review)"}
SERVICES = {"aim": "AIM", "icq": "ICQ", "yahoo": "Yahoo! Messenger", "yim": "Yahoo! Messenger", "msn": "MSN Messenger",
            "jabber": "Jabber", "gtalk": "Google Talk", "google": "Google Talk", "irc": "IRC", "facebook": "Facebook Chat",
            "secondlife": "Second Life", "skype": "Skype", "zephyr": "Zephyr", "gadu-gadu": "Gadu-Gadu"}
SL_ACCOUNTS = re.compile(r"(kithylin[ _]perth|khisanth[ _]skytower|griff[ _.]beeks|redfox[ _]costello)", re.I)

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    service TEXT, account TEXT, contact TEXT, room INTEGER,
    ts INTEGER, approx INTEGER, outgoing INTEGER, speaker TEXT, text TEXT,
    dkey TEXT, source TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS same_line ON messages (service, account, contact, dkey, outgoing, text);
CREATE TABLE IF NOT EXISTS info (key TEXT PRIMARY KEY, value TEXT);
"""


def db_path(root):
    return Path(root) / INDEX_DIR / DB_NAME


def service_name(raw):
    raw = raw.lower().replace("prpl-", "")
    return SERVICES.get(raw, raw.upper() if len(raw) <= 4 else raw.title())


def clean(text):
    """Plain text from a line of HTML (or plain text): tags gone, entities decoded, whitespace tidied."""
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", "", text))
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


_MIRC = re.compile(r"\x03\d{0,2}(?:,\d{1,2})?|[\x02\x0f\x16\x1d\x1f]")
# mIRC's own notices, which look like '/me' actions ('* Joins: ...', '* Topic is ...')
_IRC_NOTICE = re.compile(r"(Joins|Parts|Quits|Topic|Set by|Now talking|Retrieving|Disconnected|Attempting|Connect"
                         r"|Logging|Unknown command|You're now known|\S+ sets mode|\S+ is now known as|\S+ was kicked"
                         r"|\S+ changes topic|\S+ has joined|\S+ has left|\S+ has quit)\b")


def norm_name(name):
    return re.sub(r"\s+", "", name).lower()


def read_text(path):
    try:
        data = Path(path).read_bytes()
    except OSError:
        return ""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", "replace")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", "replace")


def _clock(hms, ampm=None):
    """'18:09:13' / '6:08' / '12:02am' -> seconds into the day."""
    m = re.match(r"(\d{1,2}):(\d\d)(?::(\d\d))?\s*([ap]m)?", hms.strip(), re.I)
    if not m:
        return None
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    ampm = (m.group(4) or ampm or "").lower()
    if ampm == "pm" and h < 12:
        h += 12
    elif ampm == "am" and h == 12:
        h = 0
    if h > 23 or mi > 59:
        return None
    return h * 3600 + mi * 60 + s


class Day:
    """Puts times of day onto dates, moving to the next day when the clock goes backwards (past midnight)."""

    def __init__(self, start):
        self.date = datetime(start.year, start.month, start.day)
        self.last = start.hour * 3600 + start.minute * 60 + start.second

    def stamp(self, secs):
        if secs < self.last - 3600:                 # (an hour's slack for clocks that wobble)
            self.date += timedelta(days=1)
        self.last = secs
        return int((self.date + timedelta(seconds=secs)).timestamp())


# ---- the readers: each yields dicts {service, account, contact, room, ts, approx, outgoing, speaker, text} -------
def read_gaim(path, parts):
    """Gaim / Pidgin: .../logs/<protocol>/<account>/<contact>/<date>.html|txt"""
    low = [p.lower() for p in parts]
    i = len(low) - 1 - low[::-1].index("logs")
    proto, account, contact = parts[i + 1], parts[i + 2], parts[i + 3]
    if contact == ".system":
        return
    room = contact.endswith(".chat")
    contact = contact[:-5] if room else contact
    m = re.match(r"(\d{4})-(\d\d)-(\d\d)\.(\d\d)(\d\d)(\d\d)", parts[-1])
    if not m:
        return
    day = Day(datetime(*map(int, m.groups()[:3])))      # (the header's time can disagree with the lines')
    text = read_text(path)
    service = service_name(proto)
    me = {norm_name(account)}
    if path.suffix.lower() in (".html", ".htm"):
        for line in re.split(r"<br\s*/?>\s*\n", text):
            lm = re.search(r'<font color="#([0-9A-Fa-f]{6})"><font size="2">\((?:(\d{4})-(\d\d)-(\d\d) )?'
                           r'(\d{1,2}:\d\d:\d\d(?:\s*[AP]M)?)\)</font> <b>(.*?):</b></font>(.*)', line, re.S)
            if not lm:
                continue
            colour, y, mo, d, hms, who, said = lm.groups()
            if y:
                day = Day(datetime(int(y), int(mo), int(d)))
            secs = _clock(hms)
            if secs is None:
                continue
            outgoing = colour.upper() == "16569E"
            if outgoing:
                me.add(norm_name(clean(who)))
            yield dict(service=service, account=account, contact=contact, room=room, ts=day.stamp(secs), approx=0,
                       outgoing=outgoing, speaker=clean(who), text=clean(said))
    else:
        for line in text.splitlines():
            lm = re.match(r"\((?:(\d{4})-(\d\d)-(\d\d) )?(\d{1,2}:\d\d:\d\d(?:\s*[AP]M)?)\) ([^:]{1,80}): (.*)", line)
            if not lm:
                continue
            y, mo, d, hms, who, said = lm.groups()
            if y:
                day = Day(datetime(int(y), int(mo), int(d)))
            secs = _clock(hms)
            if secs is None:
                continue
            yield dict(service=service, account=account, contact=contact, room=room, ts=day.stamp(secs), approx=0,
                       outgoing=norm_name(who) in me or norm_name(who) in OWN, speaker=who.strip(), text=said.strip())


def read_digsby(path, parts):
    """Digsby: .../<user>/<service>/<account>/<contact>_<service>/<YYYY-MM-DD>.html (times in UTC)."""
    service, account, folder = parts[-4], parts[-3], parts[-2]
    contact = re.sub(r"_[a-z]+$", "", folder)
    if service.lower() not in SERVICES:              # a backup with its own folder where the service should be
        suffix = re.search(r"_([a-z]+)$", folder)
        service = suffix.group(1) if suffix else service
    text = read_text(path)
    for m in re.finditer(r'<div class="(incoming|outgoing)[^"]*"[^>]*timestamp="(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)"[^>]*>'
                         r'\s*<span class="buddy">(.*?)</span>\s*<span class="msgcontent">(.*?)</span>\s*</div>',
                         text, re.S):
        way, stamp, who, said = m.groups()
        utc = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        yield dict(service=service_name(service), account=account, contact=contact, room=False,
                   ts=int(utc.timestamp()), approx=0, outgoing=way == "outgoing", speaker=clean(who), text=clean(said))


def read_trillian_xml(path, parts):
    """Trillian: <SERVICE>/Query|Channel/<contact>.xml - one element per line, values %-encoded, epoch times."""
    service, kind = parts[-3], parts[-2].lower()
    contact = Path(parts[-1]).stem
    text = read_text(path)
    for m in re.finditer(r"<message ([^>]*)/>", text):
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        kind_attr = attrs.get("type", "")
        if "Message" not in kind_attr or "time" not in attrs:
            continue
        outgoing = kind_attr.startswith("outgoing")
        account = unquote(attrs.get("from" if outgoing else "to", ""))
        who = unquote(attrs.get("from_display") or attrs.get("from", ""))
        try:
            ts = int(attrs["time"])
        except ValueError:
            continue
        yield dict(service=service_name(attrs.get("medium") or service), account=account or "?", contact=contact,
                   room=kind == "channel",
                   ts=ts, approx=0, outgoing=outgoing, speaker=who, text=clean(unquote(attrs.get("text", ""))))


def read_trillian_log(path, parts):
    """Trillian's plain logs: 'Session Start (account:Alias): Sat Mar 31 16:43:29 2007' then '[16:43] Who: text'."""
    if path.with_suffix(".xml").exists():
        return                                        # the .xml twin has the same lines, with seconds
    service, kind = parts[-3], parts[-2].lower()
    contact = Path(parts[-1]).stem
    account, day = "?", None
    for line in read_text(path).splitlines():
        sm = re.match(r"Session Start \(([^:]*):(.*)\): \w{3} (\w{3} +\d+ \d\d:\d\d:\d\d \d{4})", line)
        if sm:
            account = sm.group(1)
            try:
                day = Day(datetime.strptime(re.sub(r" +", " ", sm.group(3)), "%b %d %H:%M:%S %Y"))
            except ValueError:
                day = None
            continue
        lm = re.match(r"\[(\d{1,2}:\d\d(?::\d\d)?\s*(?:[ap]m)?)\] ([^:]{1,80}): (.*)", line, re.I)
        if lm and day is not None:
            secs = _clock(lm.group(1))
            if secs is None:
                continue
            who = lm.group(2).strip()
            yield dict(service=service_name(service if service.lower() in SERVICES else service.split()[0]),
                       account=account, contact=contact, room=kind == "channel",
                       ts=day.stamp(secs), approx=0, outgoing=norm_name(who) == norm_name(account) or norm_name(who) in OWN,
                       speaker=who, text=lm.group(3).strip())


def sl_account(parts):
    for part in reversed(parts[:-1]):
        m = SL_ACCOUNTS.search(part)
        if m:
            return re.sub(r"[_.]", " ", m.group(1)).title()
    return None


def folder_date(parts):
    """The date in a backup folder's name ('(03-16-2007)', 'feb 23 2010', '12-04-2010'), else None."""
    for part in parts[:-1]:
        m = re.search(r"(\d{1,2})[-/ ](\d{1,2})[-/ ](\d{4}|\d{2})(?!\d)", part)
        if m:
            mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            y += 2000 if y < 100 else 0
            try:
                return datetime(y, mo, d)
            except ValueError:
                pass
        m = re.search(r"([A-Za-z]{3})[a-z]* (\d{1,2}),? (\d{4})", part)
        if m:
            try:
                return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%b %d %Y")
            except ValueError:
                pass
    return None


def read_sl(path, parts):
    """Second Life: one .txt per person or group (chat.txt is local chat). '[2008/11/18 6:08]  Who: text', or just
    '[5:35]  Who: text' in old logs (dated by the backup, approximately)."""
    account = sl_account(parts) or "Second Life"
    contact = Path(parts[-1]).stem
    text = read_text(path)
    lines = []
    for line in text.splitlines():
        lm = re.match(r"\[(?:(\d{4})/(\d\d)/(\d\d) )?(\d{1,2}:\d\d(?::\d\d)?)\]\s+(?:IM: )?([^:\[\]]{1,60}): (.*)", line)
        if lm:
            lines.append(lm.groups())
    if not lines:
        return
    speakers = {norm_name(g[4]) for g in lines}
    room = contact.lower() in ("chat", "local chat") or len(speakers) > 3
    if contact.lower() == "chat":
        contact = "Local chat"
    try:
        fallback = folder_date(parts) or datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        fallback = datetime(2007, 1, 1)
    me = norm_name(account)
    for y, mo, d, hm, who, said in lines:
        secs = _clock(hm)
        if secs is None:
            continue
        if y:
            ts = int((datetime(int(y), int(mo), int(d)) + timedelta(seconds=secs)).timestamp())
            approx = 0
        else:
            ts = int((datetime(fallback.year, fallback.month, fallback.day) + timedelta(seconds=secs)).timestamp())
            approx = 1
        yield dict(service="Second Life", account=account, contact=contact, room=room, ts=ts, approx=approx,
                   outgoing=norm_name(who) == me, speaker=who.strip(), text=said.strip(),
                   hhmm=f"{secs // 3600:02d}:{secs // 60 % 60:02d}")


def read_irc(path, parts):
    """mIRC / vIRC: 'Session Start: Mon May 03 00:02:36 2004', then '[12:02am] <nick> text' or '* nick does'."""
    name = parts[-1]
    target = re.sub(r"(\.\d{8})?\.log$", "", name, flags=re.I)
    room = target.startswith(("#", "&"))
    path_text = " ".join(parts[:-1]).lower()
    account = "vIRC" if "virc" in path_text else "mIRC" if "mirc" in path_text else "IRC"
    day = None
    for raw in read_text(path).splitlines():
        line = _MIRC.sub("", raw)
        sm = re.match(r"Session Start: \w{3} (\w{3} \d+ \d\d:\d\d:\d\d \d{4})", line)
        if sm:
            try:
                day = Day(datetime.strptime(sm.group(1), "%b %d %H:%M:%S %Y"))
            except ValueError:
                day = None
            continue
        lm = re.match(r"\[(\d{1,2}:\d\d(?::\d\d)?\s*(?:[ap]m)?)\] (?:<[~&@%+]?([^>]{1,40})> (.*)|\* (\S+) (.*))", line,
                      re.I)
        if not lm or day is None or (lm.group(4) and _IRC_NOTICE.match(f"{lm.group(4)} {lm.group(5)}")):
            continue
        secs = _clock(lm.group(1))
        if secs is None:
            continue
        who, said = (lm.group(2), lm.group(3)) if lm.group(2) else (lm.group(4), f"* {lm.group(4)} {lm.group(5)}")
        yield dict(service="IRC", account=account, contact=target, room=room, ts=day.stamp(secs), approx=0,
                   outgoing=norm_name(who) in OWN, speaker=who, text=said.strip())


def read_yim(path, parts):
    """Yahoo! Messenger's archive: Archive/Messages/<contact>/<YYYYMMDD>-<account>.dat, a run of records:
    time, kind, direction (0 = sent), length, the text XOR'd with the account name, then 4 more bytes."""
    m = re.match(r"\d{8}-(.+)\.dat$", parts[-1], re.I)
    if not m:
        return
    account, contact = m.group(1), parts[-2]
    key = account.encode("latin-1", "ignore") or b"?"
    try:
        data = path.read_bytes()
    except OSError:
        return
    pos = 0
    while pos + 16 <= len(data):
        ts, _kind, direction, length = struct.unpack_from("<IIII", data, pos)
        pos += 16
        if length > 200000 or pos + length > len(data):
            break
        raw = bytes(b ^ key[i % len(key)] for i, b in enumerate(data[pos:pos + length]))
        pos += length + 4
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("cp1252", "replace")
        text = clean(re.sub(r"\x1b\[[^m]{0,12}m", "", text))
        if not (946684800 <= ts <= 2000000000):             # (not a sensible time: not a message record)
            continue
        yield dict(service="Yahoo! Messenger", account=account, contact=contact, room=False, ts=ts, approx=0,
                   outgoing=direction == 0, speaker=account if direction == 0 else contact, text=text)


def read_msn(path, parts):
    """MSN / Windows Live Messenger history: <account><digits>/History/<contact><digits>.xml."""
    import xml.etree.ElementTree as ET
    contact = re.sub(r"\d{6,}$", "", Path(parts[-1]).stem) or Path(parts[-1]).stem
    owner = next((p for p in reversed(parts[:-1]) if re.search(r"[a-z]\d{6,}$", p, re.I)), "")
    account = re.sub(r"\d{6,}$", "", owner.split(" ")[-1]) or "?"
    try:
        log = ET.fromstring(read_text(path).lstrip("﻿"))
    except ET.ParseError:
        return
    OWN.add(norm_name(account))
    for msg in log.iter("Message"):
        stamp = msg.get("DateTime")
        sender = msg.find("From/User")
        if not stamp or sender is None:
            continue
        try:
            when = datetime.fromisoformat(stamp.replace("Z", "+00:00")[:26] if "." in stamp else
                                          stamp.replace("Z", "+00:00"))
        except ValueError:
            continue
        who = sender.get("FriendlyName", "")
        yield dict(service="MSN Messenger", account=account, contact=contact, room=False, ts=int(when.timestamp()),
                   approx=0, outgoing=norm_name(who) in OWN, speaker=who, text=clean(msg.findtext("Text") or ""))


def read_aimlogger(path, parts):
    """AIMLogger: AIMLogger/<account>/IM Logs/<contact>.html, a table of day headings, times and lines."""
    low = [p.lower() for p in parts]
    i = low.index("aimlogger", len(low) - 4) if "aimlogger" in low[-4:] else len(low) - 4
    account, contact = parts[i + 1], Path(parts[-1]).stem
    day, clock = None, 0
    text = read_text(path)
    for m in re.finditer(r'<td colspan="2" class="(time2?)">(.*?)</td>|<td class="(local|remote)">(.*?)</td>\s*'
                         r'<td class="msg"[^>]*>(.*?)</td>', text, re.S):
        if m.group(1) == "time":
            try:
                day = datetime.strptime(clean(m.group(2)), "%A, %B %d, %Y")
            except ValueError:
                day = None
        elif m.group(1) == "time2":
            secs = _clock(clean(m.group(2)))
            clock = secs if secs is not None else clock
        elif day is not None:
            who = clean(m.group(4)).rstrip(":")
            yield dict(service="AIM", account=account, contact=contact, room=False,
                       ts=int((day + timedelta(seconds=clock)).timestamp()), approx=0, outgoing=m.group(3) == "local",
                       speaker=who, text=clean(m.group(5)))


def read_skype(path, parts):
    """Skype's own database: <account>/main.db (Messages joined to Conversations; type 2 conversations are groups)."""
    account = parts[-2]
    try:
        db = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro&immutable=1", uri=True)
        convs = {cid: (ident, name, kind) for cid, ident, name, kind in
                 db.execute("SELECT id, identity, displayname, type FROM Conversations")}
        rows = db.execute("SELECT convo_id, author, from_dispname, timestamp, type, body_xml FROM Messages"
                          " WHERE body_xml IS NOT NULL AND type IN (60, 61, 68) ORDER BY timestamp").fetchall()
        db.close()
    except sqlite3.Error:
        return
    for convo, author, who, ts, kind, body in rows:
        ident, name, ckind = convs.get(convo, (str(convo), str(convo), 1))
        room = ckind == 2
        text = clean(body)
        if kind == 60:
            text = f"* {who or author} {text}"
        yield dict(service="Skype", account=account, contact=(name or ident) if room else ident, room=room, ts=ts,
                   approx=0, outgoing=author == account, speaker=who or author, text=text)


OWN = set()          # the user's own names, learned as the logs are read (Gaim's outgoing colour, Digsby, SL)


def reader_for(rel):
    parts = list(rel.parts)
    low = [p.lower() for p in parts]
    ext = os.path.splitext(low[-1])[1]
    if "logs" in low[:-1] and len(low) - low[::-1].index("logs") - 1 == len(low) - 5:   # logs/proto/account/contact/file
        if ext in (".html", ".htm", ".txt") and re.match(r"\d{4}-\d\d-\d\d\.\d{6}", low[-1]):
            return read_gaim
    if low[-1] == "main.db" and "skype" in " ".join(low[:-1]):
        return read_skype
    if ext == ".dat" and "messages" in low[:-1] and re.match(r"\d{8}-.+\.dat$", low[-1]):
        return read_yim
    if ext == ".xml" and "history" in low[:-1] and re.search(r"\d{6,}$", Path(low[-1]).stem):
        return read_msn
    if ext == ".html" and "aimlogger" in low[:-1]:
        return read_aimlogger
    if ext == ".html" and re.match(r"\d{4}-\d\d-\d\d\.html", low[-1]) and len(parts) >= 5 and "_" in parts[-2]:
        return read_digsby
    if len(parts) >= 3 and low[-2] in ("query", "channel"):
        if ext == ".xml":
            return read_trillian_xml
        if ext == ".log":
            return read_trillian_log
    if ext == ".log" and ("irc" in " ".join(low) or low[-1].startswith("#")):
        return read_irc
    if ext == ".txt" and ("second life" in " ".join(low) or "secondlife" in " ".join(low) or sl_account(parts)):
        return read_sl
    return None


# ---- packed-up backups -------------------------------------------------------------------------------------------
SEVEN_ZIP = Path(__file__).resolve().parents[1] / "tools" / "7-Zip" / "7z.exe"
NOT_CHATS = re.compile(r"foxmail|torchlight|mushclient|phoca|worlds|^mc\.zip|main\.zip|dconv|received files", re.I)


def unpack(root, log):
    """Zipped and RAR'd log backups are unpacked (once) into _Index/unpacked/<archive> and read like the rest."""
    out = Path(root) / INDEX_DIR / "unpacked"
    if not SEVEN_ZIP.exists():
        log("  (7-Zip isn't there: packed-up backups are left out)")
        return
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        for name in names:
            if os.path.splitext(name.lower())[1] not in (".zip", ".rar", ".7z"):
                continue
            rel = Path(dirpath, name).relative_to(root)
            if NOT_CHATS.search(str(rel)):
                continue
            dest = out / re.sub(r"[\\/]", " - ", str(rel))
            if (dest / ".unpacked").exists():
                continue
            dest.mkdir(parents=True, exist_ok=True)
            done = subprocess.run([str(SEVEN_ZIP), "x", "-y", "-bd", f"-o{dest}", str(Path(root) / rel)],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            (dest / ".unpacked").write_text(str(done.returncode), encoding="utf-8")
            log(f"  unpacked {rel}")


# ---- building ------------------------------------------------------------------------------------------------------
def build(root, log=lambda msg: print(msg, flush=True)):
    root = Path(root)
    target = db_path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".building")
    tmp.unlink(missing_ok=True)
    db = sqlite3.connect(tmp)
    db.executescript(SCHEMA)
    unpack(root, log)
    files = []
    for top in (root, root / INDEX_DIR / "unpacked"):
        for dirpath, dirs, names in os.walk(top):
            dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
            for name in names:
                rel = Path(dirpath, name).relative_to(root)
                reader = reader_for(rel)
                if reader is not None:
                    files.append((rel, reader))
    # oldest backups first (so an undated line keeps its earliest date), and HTML before text (to learn own names)
    files.sort(key=lambda f: ((folder_date(list(f[0].parts)) or datetime(2100, 1, 1)), f[0].suffix.lower() != ".html",
                              str(f[0]).lower()))
    log(f"{len(files):,} log files to read")
    counts, added, seen, last = {}, 0, 0, time.time()
    insert = ("INSERT OR IGNORE INTO messages (service, account, contact, room, ts, approx, outgoing, speaker, text, "
              "dkey, source) VALUES (?,?,?,?,?,?,?,?,?,?,?)")
    for n, (rel, reader) in enumerate(files):
        rows = []
        try:
            for msg in reader(root / rel, list(rel.parts)):
                if not msg["text"]:
                    continue
                if msg["account"] and msg["account"] != "?":
                    OWN.add(norm_name(msg["account"]))
                if msg["outgoing"]:
                    OWN.add(norm_name(msg["speaker"]))
                dkey = f"~{msg['hhmm']}" if msg.get("approx") else str(msg["ts"] // 60)
                contact = msg["contact"] if msg["service"] == "Second Life" else norm_name(msg["contact"])
                rows.append((msg["service"], msg["account"].lower(), contact, int(msg["room"]), msg["ts"],
                             msg["approx"], int(msg["outgoing"]), msg["speaker"], msg["text"], dkey, str(rel)))
        except Exception as exc:                                    # one odd file never stops the build
            log(f"  skipped {rel}: {exc}")
            continue
        before = db.total_changes
        db.executemany(insert, rows)
        added += db.total_changes - before
        seen += len(rows)
        counts[reader.__name__] = counts.get(reader.__name__, 0) + 1
        if time.time() - last > 20:
            last = time.time()
            db.commit()
            log(f"  {n + 1:,} of {len(files):,} files; {added:,} lines ({seen - added:,} repeats skipped)")
    # an undated Second Life line that also turns up dated (in a later backup) is the same line
    db.execute("CREATE INDEX IF NOT EXISTS by_text ON messages (service, account, contact, text)")
    db.execute("""DELETE FROM messages WHERE approx = 1 AND EXISTS (
                      SELECT 1 FROM messages m WHERE m.approx = 0 AND m.service = messages.service
                      AND m.account = messages.account AND m.contact = messages.contact
                      AND m.outgoing = messages.outgoing AND m.text = messages.text
                      AND strftime('%H:%M', m.ts, 'unixepoch', 'localtime') = substr(messages.dkey, 2))""")
    db.executescript("""
        CREATE INDEX IF NOT EXISTS by_conversation ON messages (service, account, contact, ts);
        CREATE TABLE contacts AS
            SELECT service, account, contact, MAX(room) AS room, COUNT(*) AS lines, MIN(ts) AS first, MAX(ts) AS last
            FROM messages GROUP BY service, account, contact;
        CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(text, content='messages', content_rowid='id');
        INSERT INTO search(search) VALUES ('rebuild');
    """)
    total = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    db.execute("INSERT OR REPLACE INTO info VALUES ('built', ?)", (time.strftime("%Y-%m-%d %H:%M"),))
    db.execute("INSERT OR REPLACE INTO info VALUES ('own_names', ?)", (" ".join(sorted(OWN)),))
    db.commit()
    db.close()
    tmp.replace(target)
    log(f"Done: {total:,} lines from {len(files):,} files ({seen - total:,} repeats left out). "
        f"Files by reader: {counts}")
    return target


if __name__ == "__main__":
    here = Path(__file__).resolve().parents[2]
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else here / "Local Storage" / "Text Logs")
