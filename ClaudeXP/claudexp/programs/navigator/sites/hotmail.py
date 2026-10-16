"""MSN Hotmail, autumn 2001: the world's free web-based e-mail, at http://www.hotmail.com/ in Internet Explorer or
Netscape. It is the same mailbox Outlook Express shows (data/mail.json for what comes in, Outlook Express's store
for Sent and Drafts); everyone you know has an address @hotmail.com, and whatever you send is answered in character
(life.receive_email). Pages are real HTML with real forms, served by the furry web's local server.

Folders: Inbox, Bulk Mail (spam), Sent Messages, Drafts and Trash Can.
"""
import html
import re
from urllib.parse import parse_qs, quote, urlencode

from PySide6.QtCore import QObject, Signal

from . import Response, Site, redirect

HOST = "www.hotmail.com"
QUOTA = 2 * 1024 * 1024                     # 2 MB, as free Hotmail gave you in 2001
PAGE_SIZE = 25
FOLDERS = [("inbox", "Inbox"), ("bulk", "Bulk Mail"), ("sent", "Sent Messages"), ("drafts", "Drafts"),
           ("trash", "Trash Can")]
_session = {"signed_in": False}


# ---- talking to the rest of ClaudeXP (this runs on the web server's thread) -------------------------------------

class _Bridge(QObject):
    """Hands sent mail to the living world on the main thread."""
    send = Signal(dict)
    signed_in = Signal()

    def __init__(self):
        super().__init__()
        self.send.connect(self._send)
        self.signed_in.connect(self._signed_in)

    def _send(self, msg):
        from ...outlook import deliver
        deliver(None, msg)

    def _signed_in(self):
        from ....life import mail_extras
        mail_extras.signed_in()


def _sim():
    from ....life import get
    return get()


def _mailbox():
    from ....life import Mailbox
    return Mailbox()


def _store():
    from ...outlook import _store as store
    return store()


def _save_store(data):
    from ....life import mail_lock
    from ...outlook import STORE
    from ...people import save_json
    with mail_lock:
        save_json(STORE, data)


def _me():
    from .... import user
    return user.email_address(), user.online_handle()


def _addr(name):
    from ....life import email_address
    return email_address(name)


def _people():
    sim = _sim()
    return sorted(sim.people, key=str.lower) if sim is not None else []


def _now_text():
    from .... import clock
    now = clock.now()
    return f"{now:%a, %b} {now.day} {now.year} {clock.time_text(now)}"


# ---- page parts ---------------------------------------------------------------------------------------------------

ENVELOPE = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='12'>"
            "<rect x='0.5' y='0.5' width='15' height='11' fill='%23FFF6C8' stroke='%23806A20'/>"
            "<path d='M0.5 0.5 L8 7 L15.5 0.5' fill='none' stroke='%23806A20'/></svg>")
OPENED = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='12'>"
          "<rect x='0.5' y='3.5' width='15' height='8' fill='%23FFFFFF' stroke='%23909090'/>"
          "<path d='M0.5 3.5 L8 0.5 L15.5 3.5 L8 8 Z' fill='%23F0F0F0' stroke='%23909090'/></svg>")
CSS = """
body { margin: 0; background: #FFFFFF; font-family: Verdana, Arial, sans-serif; font-size: 11px; color: #000000; }
td, th, div, li, p, form, select, input { font-family: Verdana, Arial, sans-serif; font-size: 11px; }
a { color: #0033CC; } a:visited { color: #0033CC; }
.top { background: #003399; color: #FFFFFF; }
.logo { font-family: Verdana; font-size: 26px; font-weight: bold; color: #FFFFFF; letter-spacing: -1px; }
.logo span { color: #FF9900; }
.tabs td { padding: 4px 12px; font-weight: bold; font-size: 11px; }
.tab { background: #7A9CD3; } .tab a { color: #FFFFFF; text-decoration: none; }
.tab-on { background: #FFFFFF; } .tab-on a { color: #003399; text-decoration: none; }
.bar { background: #DDE6F5; border-top: 1px solid #99AACC; border-bottom: 1px solid #99AACC; }
.btn { font-family: Verdana; font-size: 11px; background: #EEF2FA; border: 1px solid #6688BB; padding: 1px 6px; }
.folders { background: #EEF2FA; border-right: 1px solid #99AACC; }
.folders a { text-decoration: none; }
.list th { background: #6688BB; color: #FFFFFF; text-align: left; font-size: 11px; padding: 3px; }
.list td { padding: 3px; border-bottom: 1px solid #E0E6F0; font-size: 11px; }
.unread td { font-weight: bold; background: #FFFFFF; }
.read td { background: #F7F9FD; }
.ad { background: #FFF3D6; border: 1px solid #E8B860; font-size: 11px; padding: 6px; }
.meter { width: 120px; height: 8px; border: 1px solid #6688BB; background: #FFFFFF; }
.meter div { height: 8px; background: #FF9900; }
.foot { color: #666666; font-size: 10px; }
.msghead td { font-size: 11px; padding: 2px 4px; }
pre.body { font-family: Arial, sans-serif; font-size: 13px; white-space: pre-wrap; margin: 8px; }
input.text, textarea { font-family: Arial; font-size: 12px; border: 1px solid #7F9DB9; }
"""


def _page(title, inner, tab=None, ads=True):
    tabs = "".join(
        f'<td class="{"tab-on" if key == tab else "tab"}"><a href="{url}">{label}</a></td>'
        for key, label, url in (("home", "Home", "/cgi-bin/hmhome?f=inbox&summary=1"),
                                ("inbox", "Inbox", "/cgi-bin/hmhome?f=inbox"),
                                ("compose", "Compose", "/cgi-bin/compose"),
                                ("addresses", "Address Book", "/cgi-bin/addresses")))
    me, handle = _me()
    ad = ('<td align="right" valign="middle"><div class="ad"><b>Get MSN Messenger</b> - see when your friends are '
          'online and send instant messages! <a href="http://messenger.msn.com/">Download it free</a></div></td>'
          if ads else "<td></td>")
    return f"""<html><head><title>MSN Hotmail - {html.escape(title)}</title><style>{CSS}</style></head><body>
<table width="100%" cellspacing="0" cellpadding="6" class="top"><tr>
<td><span class="logo">msn<span>.</span> Hotmail</span></td>
<td align="right" style="color:#FFFFFF">{html.escape(me)} &nbsp;|&nbsp; <a href="/cgi-bin/logout" style="color:#FFFFFF">Sign Out</a>
&nbsp;|&nbsp; <a href="http://www.msn.com/" style="color:#FFFFFF">MSN Home</a> &nbsp;|&nbsp;
<a href="/cgi-bin/help" style="color:#FFFFFF">Help</a></td></tr></table>
<table width="100%" cellspacing="0" cellpadding="0" style="background:#003399"><tr><td>
<table cellspacing="2" cellpadding="0" class="tabs"><tr>{tabs}</tr></table></td>{ad}</tr></table>
{inner}
<br><center class="foot">&copy; 2001 Microsoft Corporation. All rights reserved. &nbsp;
<a href="/cgi-bin/help">TERMS OF USE</a> &nbsp; <a href="/cgi-bin/help">TRUSTe Approved Privacy Statement</a></center>
<br></body></html>"""


def _size(m):
    n = len(m.get("body", "")) + len(m.get("subject", "")) + 400
    return f"{max(1, round(n / 1024))}k"


def _all_messages():
    """folder -> list of messages (newest first); sent and drafts come from Outlook Express's store."""
    box = _mailbox().messages()
    store = _store()
    out = {"inbox": [], "bulk": [], "trash": []}
    for m in box:
        f = {"deleted": "trash"}.get(m.get("folder", "inbox"), m.get("folder", "inbox"))
        out.setdefault(f, []).append(m)
    out["sent"] = list(store["sent"])
    out["drafts"] = list(store["drafts"])
    return {k: v[::-1] for k, v in out.items()}


def _used(folders):
    return sum(len(m.get("body", "")) + 400 for msgs in folders.values() for m in msgs)


def _folder_pane(folders, current):
    rows = []
    for key, label in FOLDERS:
        unread = sum(1 for m in folders.get(key, []) if key in ("inbox", "bulk") and not m.get("read", True))
        count = f" ({unread})" if unread else ""
        name = f"<b>{label}{count}</b>" if key == current else f"{label}{count}"
        rows.append(f'<tr><td style="padding:3px 6px"><a href="/cgi-bin/hmhome?f={key}">{name}</a></td></tr>')
    used = _used(folders)
    pct = min(100, round(used * 100 / QUOTA))
    return (f'<td width="130" valign="top" class="folders"><table width="100%">'
            f'<tr><td style="padding:6px 6px 2px 6px"><b>Folders</b></td></tr>{"".join(rows)}</table>'
            f'<div style="padding:10px 6px"><div class="meter"><div style="width:{max(1, pct)}%"></div></div>'
            f'You are using {pct}% of your {QUOTA // (1024 * 1024)} MB</div></td>')


def _who(m):
    if "from" in m:
        return m["from"]
    return m.get("to", "")[:40] or "(no recipient)"


# ---- the site ----------------------------------------------------------------------------------------------------

class Hotmail(Site):
    host = HOST
    aliases = ("hotmail.com", "lw1fd.law1.hotmail.msn.com", "hotmail.msn.com", "login.passport.com")
    title = "MSN Hotmail"
    blurb = "Free web-based e-mail"

    def __init__(self):
        from PySide6.QtWidgets import QApplication
        self.bridge = _Bridge()
        app = QApplication.instance()
        if app is not None:
            self.bridge.moveToThread(app.thread())

    def installed(self):
        return True

    # ---- GET ----
    def handle(self, path, query):
        q = {k: v[0] for k, v in parse_qs(query, keep_blank_values=True).items()}
        if path in ("/", "/index.html", "/cgi-bin/login"):
            return redirect("/cgi-bin/hmhome?f=inbox") if _session["signed_in"] else self._login(after=q.get("next", ""))
        if path == "/cgi-bin/logout":
            _session["signed_in"] = False
            return self._signed_out()
        if path == "/cgi-bin/help":
            return self._help()
        if not _session["signed_in"]:
            # sign in first, then on to the page that was asked for (a message clicked in the desktop widget)
            wanted = path + (f"?{query}" if query else "")
            return redirect("/cgi-bin/login?" + urlencode({"next": wanted}))
        if path == "/cgi-bin/hmhome":
            return self._folder(q.get("f", "inbox"), int(q.get("page", "0") or 0), q.get("note", ""))
        if path == "/cgi-bin/getmsg":
            return self._message(q.get("f", "inbox"), q.get("id", ""))
        if path == "/cgi-bin/compose":
            return self._compose(q)
        if path == "/cgi-bin/addresses":
            return self._addresses(q.get("letter", ""), q.get("q", ""))
        return None

    # ---- POST ----
    def handle_post(self, path, query, form):
        f = {k: v[-1] for k, v in form.items()}
        if path == "/cgi-bin/dologin":
            return self._do_login(f)
        if not _session["signed_in"]:
            return redirect("/cgi-bin/login")
        if path == "/cgi-bin/premail":
            return self._send(f)
        if path == "/cgi-bin/domove":
            return self._move(f.get("f", "inbox"), form.get("id", []), f.get("action", ""), f.get("dest", ""))
        return None

    # ---- signing in ----
    def _login(self, error="", after=""):
        _me_addr, handle = _me()
        err = f'<p style="color:#CC0000"><b>{html.escape(error)}</b></p>' if error else ""
        return f"""<html><head><title>Welcome to MSN Hotmail</title><style>{CSS}</style></head><body>
<table width="100%" cellspacing="0" cellpadding="8" class="top"><tr><td><span class="logo">msn<span>.</span> Hotmail</span></td>
<td align="right" style="color:#FFFFFF">The World's FREE Web-based E-mail</td></tr></table>
<table width="100%" cellpadding="16"><tr valign="top">
<td width="55%"><font size="4" color="#003399"><b>Welcome to MSN Hotmail</b></font><br><br>
Get your FREE e-mail account that you can use from any computer connected to the Internet.<br><br>
<b>With MSN Hotmail you can:</b><ul><li>Read your e-mail anywhere, any time</li>
<li>Keep everyone you know in your Address Book</li><li>Stop junk mail with the Bulk Mail filter</li>
<li>See when friends are online with MSN Messenger</li></ul>
<div class="ad"><b>New to Hotmail?</b> <a href="/cgi-bin/help">Sign up now</a> - it's free!</div></td>
<td><table cellpadding="10" style="border:1px solid #6688BB; background:#EEF2FA" width="100%"><tr><td>
<font size="3" color="#003399"><b>Sign In</b></font>{err}
<form method="post" action="/cgi-bin/dologin"><input type="hidden" name="next" value="{html.escape(after)}">
Sign-In Name<br><input class="text" name="login" value="{html.escape(handle.lower())}" size="18"> @hotmail.com<br><br>
Password<br><input class="text" type="password" name="passwd" value="********" size="18"><br><br>
<input type="checkbox" name="remember" checked> Keep me signed in<br><br>
<input type="submit" class="btn" value="Sign In"></form>
<span class="foot"><a href="/cgi-bin/help">Forgot your password?</a></span></td></tr></table></td></tr></table>
<center class="foot">&copy; 2001 Microsoft Corporation. All rights reserved.</center></body></html>"""

    def _do_login(self, f):
        _session["signed_in"] = True                   # (the password box is for show: anything signs in)
        self.bridge.signed_in.emit()
        after = f.get("next", "")
        if after.startswith("/cgi-bin/") and not any(c in after for c in "\r\n"):
            return redirect(after)
        return redirect("/cgi-bin/hmhome?f=inbox&summary=1")

    def _signed_out(self):
        return f"""<html><head><title>MSN Hotmail - Signed Out</title><style>{CSS}</style></head><body>
<table width="100%" cellspacing="0" cellpadding="8" class="top"><tr><td><span class="logo">msn<span>.</span> Hotmail</span></td></tr></table>
<blockquote><br><font size="3" color="#003399"><b>You have signed out of MSN Hotmail.</b></font><br><br>
Thank you for using MSN Hotmail.<br><br><a href="/cgi-bin/login">Sign in again</a> &nbsp;|&nbsp;
<a href="http://www.msn.com/">Go to MSN.com</a></blockquote></body></html>"""

    def _help(self):
        inner = ("<blockquote><br><font size='3' color='#003399'><b>MSN Hotmail Help</b></font><br><br>"
                 "<b>Everyone has Hotmail.</b> Every friend you know has an address @hotmail.com - look them up in the "
                 "<a href='/cgi-bin/addresses'>Address Book</a>. Write to them and they'll write back.<br><br>"
                 "<b>Bulk Mail</b> catches junk mail. If a real message lands there, open it and click <b>Not Junk"
                 "</b>.<br><br><b>Outlook Express</b> shows this same mailbox: read and send from either one.<br><br>"
                 "<b>Stay active:</b> sign in at least once every 30 days.</blockquote>")
        return _page("Help", inner) if _session["signed_in"] else (
            f"<html><head><title>MSN Hotmail - Help</title><style>{CSS}</style></head><body>{inner}"
            "<blockquote><a href='/cgi-bin/login'>Back to Sign In</a></blockquote></body></html>")

    # ---- folders ----
    def _folder(self, key, page, note):
        folders = _all_messages()
        if key not in dict(FOLDERS):
            key = "inbox"
        msgs = folders.get(key, [])
        shown = msgs[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
        rows = []
        for m in shown:
            unread = key in ("inbox", "bulk", "trash") and not m.get("read", True)
            icon = ENVELOPE if unread else OPENED
            link = (f"/cgi-bin/compose?draft={m['id']}" if key == "drafts"
                    else f"/cgi-bin/getmsg?f={key}&id={m['id']}")
            who = html.escape(_who(m) if key not in ("sent", "drafts") else (m.get("to") or "(no recipient)")[:40])
            rows.append(f'<tr class="{"unread" if unread else "read"}"><td width="20"><input type="checkbox" '
                        f'name="id" value="{m["id"]}"></td><td width="20"><img src="{icon}"></td>'
                        f'<td width="25%">{who}</td><td><a href="{link}">{html.escape(m.get("subject") or "(no subject)")}'
                        f'</a></td><td width="18%" nowrap>{html.escape(m.get("date", ""))}</td>'
                        f'<td width="40" align="right">{_size(m)}</td></tr>')
        if not rows:
            rows.append('<tr><td colspan="6" align="center" style="padding:20px">There are no messages in this '
                        'folder.</td></tr>')
        label = dict(FOLDERS)[key]
        unread = sum(1 for m in msgs if not m.get("read", True))
        pages = (len(msgs) + PAGE_SIZE - 1) // PAGE_SIZE
        nav = ""
        if pages > 1:
            nav = " ".join(f'<a href="/cgi-bin/hmhome?f={key}&page={i}">{i + 1}</a>' if i != page else f"<b>{i + 1}</b>"
                           for i in range(pages))
            nav = f"Page: {nav}"
        moves = "".join(f'<option value="{k}">{v}</option>' for k, v in FOLDERS if k not in (key, "sent", "drafts"))
        actions = ['<input type="submit" class="btn" name="action" value="Delete">']
        if key in ("inbox", "bulk", "trash"):
            actions.append(f'<input type="submit" class="btn" name="action" value="Move To"> '
                           f'<select name="dest" style="font-size:11px">{moves}</select>')
        if key == "bulk":
            actions.append('<input type="submit" class="btn" name="action" value="Not Junk">')
        elif key == "inbox":
            actions.append('<input type="submit" class="btn" name="action" value="Junk">')
            actions.append('<input type="submit" class="btn" name="action" value="Mark As Unread">')
        if key in ("trash", "bulk"):
            actions.append('<input type="submit" class="btn" name="action" value="Empty Folder">')
        notes = {"sent": "Your message has been sent.", "moved": "The messages were moved.",
                 "deleted": "The messages were deleted.", "emptied": "The folder was emptied.",
                 "draft": "Your message was saved in Drafts."}
        note_html = f'<div class="ad" style="margin:6px 0"><b>{notes[note]}</b></div>' if note in notes else ""
        bulk_note = ("<div class='foot' style='padding:4px'>Messages in Bulk Mail are deleted automatically after "
                     "a few days. Open a message and click <b>Not Junk</b> if it was a real one.</div>"
                     if key == "bulk" else "")
        me, handle = _me()
        greeting = ""
        if key == "inbox":
            from .... import clock
            now = clock.now()
            greeting = (f'<div style="padding:6px 0"><font size="3" color="#003399"><b>{html.escape(handle)}\'s '
                        f'Inbox</b></font> &nbsp; {now:%A, %B} {now.day}, {now.year} &nbsp; - &nbsp; '
                        f'{unread} unread message{"s" if unread != 1 else ""}</div>')
        inner = f"""<table width="100%" cellspacing="0" cellpadding="0"><tr valign="top">{_folder_pane(folders, key)}
<td style="padding:8px">{greeting}{note_html}
<form method="post" action="/cgi-bin/domove"><input type="hidden" name="f" value="{key}">
<table width="100%" cellpadding="4" class="bar"><tr><td>{" ".join(actions)}</td>
<td align="right">{len(msgs)} message{"s" if len(msgs) != 1 else ""} in {label} &nbsp; {nav}</td></tr></table>
<table width="100%" cellspacing="0" class="list"><tr><th></th><th></th><th>{"To" if key in ("sent", "drafts") else "From"}</th>
<th>Subject</th><th>Date</th><th>Size</th></tr>{"".join(rows)}</table></form>{bulk_note}</td></tr></table>"""
        return _page(label, inner, "inbox" if key == "inbox" else None)

    def _move(self, key, ids, action, dest):
        box = _mailbox()
        ids = [int(i) for i in ids if str(i).isdigit()]
        note = "moved"
        if action == "Empty Folder":
            if key in ("trash", "bulk"):
                folder = "deleted" if key == "trash" else "bulk"
                for m in box.messages():
                    if m.get("folder", "inbox") == folder:
                        box.purge(m["id"])
            return redirect(f"/cgi-bin/hmhome?f={key}&note=emptied")
        if key in ("sent", "drafts"):
            if action == "Delete" and ids:
                store = _store()
                store[key] = [m for m in store[key] if m["id"] not in ids]
                _save_store(store)
            return redirect(f"/cgi-bin/hmhome?f={key}&note=deleted")
        for i in ids:
            if action == "Delete":
                if key == "trash":
                    box.purge(i)
                else:
                    box.move(i, "deleted")
                note = "deleted"
            elif action == "Move To" and dest in ("inbox", "bulk", "trash"):
                box.move(i, {"trash": "deleted"}.get(dest, dest))
            elif action == "Junk":
                box.move(i, "bulk")
            elif action == "Not Junk":
                box.move(i, "inbox")
            elif action == "Mark As Unread":
                box.mark_read(i, False)
        return redirect(f"/cgi-bin/hmhome?f={key}&note={note}")

    # ---- reading ----
    def _message(self, key, msg_id):
        folders = _all_messages()
        msgs = folders.get(key, [])
        m = next((x for x in msgs if str(x.get("id")) == str(msg_id)), None)
        if m is None:
            return redirect(f"/cgi-bin/hmhome?f={key}")
        if key in ("inbox", "bulk", "trash") and not m.get("read", True):
            _mailbox().mark_read(m["id"])
        i = msgs.index(m)
        prev_link = (f'<a href="/cgi-bin/getmsg?f={key}&id={msgs[i - 1]["id"]}">&laquo; Previous</a>' if i > 0 else "")
        next_link = (f'<a href="/cgi-bin/getmsg?f={key}&id={msgs[i + 1]["id"]}">Next &raquo;</a>'
                     if i + 1 < len(msgs) else "")
        me, _handle = _me()
        if key == "sent":
            sender = f"{_handle} &lt;{html.escape(me)}&gt;"
            to = html.escape(m.get("to", ""))
            cc = ""
        else:
            sender = f"{html.escape(m.get('from', ''))} &lt;{html.escape(m.get('addr', ''))}&gt;"
            to = html.escape(", ".join(m.get("to") or [me]))
            cc = html.escape(", ".join(m.get("cc") or []))
        mid = m["id"]
        buttons = [f'<a class="btn" href="/cgi-bin/compose?mode=reply&f={key}&id={mid}">Reply</a>',
                   f'<a class="btn" href="/cgi-bin/compose?mode=all&f={key}&id={mid}">Reply All</a>',
                   f'<a class="btn" href="/cgi-bin/compose?mode=forward&f={key}&id={mid}">Forward</a>']
        form_buttons = '<input type="submit" class="btn" name="action" value="Delete">'
        if key == "bulk":
            form_buttons += ' <input type="submit" class="btn" name="action" value="Not Junk">'
        elif key == "inbox":
            form_buttons += ' <input type="submit" class="btn" name="action" value="Junk">'
        cc_row = f"<tr><td><b>Cc:</b></td><td>{cc}</td></tr>" if cc else ""
        body = html.escape(m.get("body", ""))
        body = re.sub(r"(https?://[^\s<>&]+)", r'<a href="\1">\1</a>', body)
        inner = f"""<table width="100%" cellspacing="0" cellpadding="0"><tr valign="top">{_folder_pane(folders, key)}
<td style="padding:8px"><form method="post" action="/cgi-bin/domove"><input type="hidden" name="f" value="{key}">
<input type="hidden" name="id" value="{mid}">
<table width="100%" cellpadding="4" class="bar"><tr><td>{" ".join(buttons)} &nbsp; {form_buttons}</td>
<td align="right">{prev_link} &nbsp; {next_link} &nbsp; <a href="/cgi-bin/hmhome?f={key}">{dict(FOLDERS)[key]}</a></td></tr></table></form>
<table class="msghead" width="100%" style="background:#F2F5FB; border-bottom:1px solid #99AACC">
<tr><td width="60"><b>From:</b></td><td>{sender}</td></tr><tr><td><b>To:</b></td><td>{to}</td></tr>{cc_row}
<tr><td><b>Subject:</b></td><td><b>{html.escape(m.get("subject", ""))}</b></td></tr>
<tr><td><b>Date:</b></td><td>{html.escape(m.get("date", ""))}</td></tr></table>
<pre class="body">{body}</pre></td></tr></table>"""
        return _page(m.get("subject", "Message"), inner)

    # ---- writing ----
    def _compose(self, q):
        me, handle = _me()
        to = q.get("to", "")
        cc = subject = body = ""
        draft_id = ""
        if q.get("draft"):
            d = next((x for x in _store()["drafts"] if str(x["id"]) == q["draft"]), None)
            if d is not None:
                to, subject, body, draft_id = d.get("to", ""), d.get("subject", ""), d.get("body", ""), str(d["id"])
        elif q.get("mode") and q.get("id"):
            m = next((x for x in _all_messages().get(q.get("f", "inbox"), []) if str(x.get("id")) == q["id"]), None)
            if m is not None:
                orig = m.get("subject", "")
                quoted = "\n".join("> " + line for line in m.get("body", "").splitlines())
                who = m.get("from") or handle
                header = (f"\n\n\n----- Original Message -----\nFrom: {who}"
                          f"{' <' + m['addr'] + '>' if m.get('addr') else ''}\nSent: {m.get('date', '')}\n"
                          f"Subject: {orig}\n\n")
                if q["mode"] == "forward":
                    subject = orig if orig.lower().startswith("fw") else f"Fw: {orig}"
                    body = header + quoted
                else:
                    subject = orig if orig.lower().startswith("re:") else f"Re: {orig}"
                    body = header + quoted
                    to = m.get("addr", "") if "from" in m else m.get("to", "")
                    if q["mode"] == "all" and "from" in m:
                        others = [a for a in (m.get("to") or []) + (m.get("cc") or [])
                                  if a.lower() != me.lower() and a.lower() != to.lower()]
                        cc = ", ".join(others)
        quick = "".join(f'<option value="{html.escape(_addr(n))}">{html.escape(n)}</option>' for n in _people())
        inner = f"""<table width="100%" cellpadding="8"><tr><td>
<form method="post" action="/cgi-bin/premail" name="composeform">
<input type="hidden" name="draft" value="{draft_id}">
<table cellpadding="4" class="bar" width="100%"><tr><td><input type="submit" class="btn" name="action" value="Send">
<input type="submit" class="btn" name="action" value="Save Draft">
<input type="submit" class="btn" name="action" value="Cancel"></td>
<td align="right">From: <b>{html.escape(me)}</b></td></tr></table>
<table cellpadding="3" width="100%"><tr><td width="60" align="right"><b>To:</b></td>
<td><input class="text" name="to" id="to" value="{html.escape(to)}" style="width:100%"></td>
<td width="200" rowspan="3" valign="top"><b>Quick Address List</b><br>
<select size="6" style="width:200px; font-size:11px" onchange="var t=document.getElementById('to');
t.value=(t.value?t.value+', ':'')+this.value;">{quick}</select></td></tr>
<tr><td align="right"><b>Cc:</b></td><td><input class="text" name="cc" value="{html.escape(cc)}" style="width:100%"></td></tr>
<tr><td align="right"><b>Subject:</b></td><td><input class="text" name="subject" value="{html.escape(subject)}" style="width:100%"></td></tr>
<tr><td></td><td colspan="2"><textarea name="body" rows="18" style="width:100%">{html.escape(body)}</textarea></td></tr>
</table></form></td></tr></table>"""
        return _page("Compose", inner, "compose")

    def _send(self, f):
        action = f.get("action", "Send")
        if action == "Cancel":
            return redirect("/cgi-bin/hmhome?f=inbox")
        to = ", ".join(x.strip() for x in (f.get("to", ""), f.get("cc", "")) if x.strip())
        msg = {"to": to, "subject": f.get("subject", "").strip() or "(no subject)", "body": f.get("body", ""),
               "date": _now_text()}
        store = _store()
        draft = f.get("draft", "")
        if draft.isdigit():
            store["drafts"] = [d for d in store["drafts"] if d["id"] != int(draft)]
        msg["id"] = store["next_id"]
        store["next_id"] += 1
        if action == "Save Draft":
            store["drafts"].append(msg)
            _save_store(store)
            return redirect("/cgi-bin/hmhome?f=drafts&note=draft")
        if not to:
            return Response(_page("Compose", "<blockquote><br><b style='color:#CC0000'>Please enter at least one "
                                             "address in the To box.</b><br><br><a href='javascript:history.back()'>"
                                             "Back</a></blockquote>", "compose"))
        store["sent"].append(msg)
        _save_store(store)
        self.bridge.send.emit(dict(msg))
        return redirect("/cgi-bin/hmhome?f=sent&note=sent")

    # ---- the Address Book ----
    def _addresses(self, letter, query):
        names = _people()
        if query:
            names = [n for n in names if query.lower() in n.lower()]
        elif letter:
            names = [n for n in names if n[:1].upper() == letter.upper()
                     or (letter == "#" and not n[:1].isalpha())]
        letters = " ".join(f'<a href="/cgi-bin/addresses?letter={quote(c)}">{c}</a>'
                           for c in "#ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        sim = _sim()
        rows = []
        for n in names:
            person = sim.people.get(n) if sim is not None else None
            kind = "AIM buddy" if person is not None and person.contact is not None else "FurNet / PawPrints"
            addr = _addr(n)
            rows.append(f'<tr class="read"><td><b>{html.escape(n)}</b></td><td>{html.escape(addr)}</td>'
                        f'<td>{kind}</td><td><a href="/cgi-bin/compose?{urlencode({"to": addr})}">Send Mail</a></td></tr>')
        inner = f"""<table width="100%" cellpadding="8"><tr><td>
<font size="3" color="#003399"><b>Address Book</b></font> &nbsp; {len(names)} contact{"s" if len(names) != 1 else ""}<br><br>
<form method="get" action="/cgi-bin/addresses">Find: <input class="text" name="q" value="{html.escape(query)}">
<input type="submit" class="btn" value="Go"> &nbsp; {letters} &nbsp; <a href="/cgi-bin/addresses">All</a></form>
<table width="100%" cellspacing="0" class="list"><tr><th>Name</th><th>E-mail</th><th>Knows you from</th><th></th></tr>
{"".join(rows) or '<tr><td colspan="4">No contacts found.</td></tr>'}</table></td></tr></table>"""
        return _page("Address Book", inner, "addresses")
