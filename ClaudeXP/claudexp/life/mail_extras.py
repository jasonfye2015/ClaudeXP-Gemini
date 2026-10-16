"""The rest of a 2001 inbox, beyond buddies writing to you:

- Hotmail Staff's welcome, the weekly MSN newsletter, and the 'sign in or your account will be deactivated' warning.
- Spam, mostly caught in Bulk Mail (some always slips through to the Inbox).
- Buddies forwarding jokes, chain letters and urban legends to everyone they know ("FW: FW: FW:").
- Group emails between residents with you on CC, and the replies that follow ("Re:"), so you can Reply All.

Called from LifeSim._tick once a minute; timings are in real minutes while ClaudeXP is on. The forwards and group
emails are written by the model in character (background priority); the rest are canned, so they cost nothing.
"""
import random
import time

from .. import clock
from ..programs.people import save_json

SPAM_MINUTES = (90, 240)
FORWARD_MINUTES = (300, 600)
GROUP_MINUTES = (480, 840)
GROUP_REPLY_MINUTES = (15, 60)
SLIPS_THROUGH = 0.15              # spam that lands in the Inbox anyway
INACTIVE_DAYS = 21                # Hotmail warns after this long without signing in
BULK_KEEP_DAYS = 7
STAFF = ("Hotmail Staff", "staff@hotmail.com")
MEMBER = ("MSN Hotmail", "member_services@hotmail.com")

WELCOME = """Welcome to MSN Hotmail, the world's FREE Web-based e-mail!

Your new e-mail address is: {addr}

With MSN Hotmail you can:
  * Read your e-mail from any computer connected to the Internet
  * Keep everyone you know in your Address Book
  * Let Bulk Mail filter out unwanted junk mail
  * Use MSN Messenger to see when your friends are online

Remember: sign in at least once every 30 days to keep your account active.

Thank you for choosing MSN Hotmail.

The MSN Hotmail Team
http://www.hotmail.com"""

INACTIVE = """Dear MSN Hotmail Member,

Our records show that you have not signed in to your Hotmail account ({addr}) for some time.

To keep your account active, you must sign in at least once every 30 days. Accounts that remain inactive
may be deactivated, and messages stored in them deleted.

To sign in, go to http://www.hotmail.com

Sincerely,
MSN Hotmail Member Services"""

NEWSLETTERS = [
    ("MSN Hotmail Newsletter: Get the new MSN Messenger 4.6!",
     "This week on MSN:\n\n  * MSN Messenger 4.6 is here - voice chat, file transfers and more. Download it free at "
     "http://messenger.msn.com\n  * Windows XP is finally here! See what's new at http://www.microsoft.com/windowsxp\n"
     "  * Win a trip for two in the MSN Sweepstakes\n\nTip of the week: drag messages into a folder to keep your "
     "Inbox tidy.\n\nYou are receiving this newsletter because you are an MSN Hotmail member."),
    ("MSN Hotmail Newsletter: Holiday shopping made easy",
     "Get ready for the holidays with MSN eShop - thousands of stores, one easy checkout.\n\n  * Xbox arrives "
     "November 15th - pre-order now\n  * Harry Potter and the Sorcerer's Stone opens in theaters November 16th\n"
     "  * Send a free e-greeting card from MSN Greetings\n\nTip of the week: add friends to your Address Book with "
     "one click from any message they send you."),
    ("MSN Hotmail Newsletter: Protect your Inbox",
     "Junk e-mail got you down? MSN Hotmail's Bulk Mail filter catches most of it automatically. Messages it isn't "
     "sure about go to your Bulk Mail folder, which is emptied regularly.\n\n  * Never reply to junk e-mail - it "
     "tells the sender your address works\n  * Use the Block Sender button\n\nAlso this week: MSN Music, MSN "
     "Encarta and the brand-new MSN Explorer."),
    ("MSN Hotmail Newsletter: What's new on MSN",
     "  * The new MSN 7 is here with a fresh look\n  * Check movie times and buy tickets on MSN Entertainment\n"
     "  * Play free card games against people from around the world on MSN Gaming Zone\n\nTip of the week: you "
     "can sign in to Hotmail from any computer - your mail goes where you go."),
]

SPAM = [
    ("Prize Notification Dept", "winners@prizecentral-online.net", "You may already be a WINNER!!!",
     "CONGRATULATIONS!!!\n\nYour e-mail address has been selected in our GRAND PRIZE DRAWING!\nYou may have won "
     "$10,000 CASH, a new Ford Explorer, or a Caribbean cruise for two!\n\nTo claim your prize, simply reply with "
     "your name and mailing address. Act NOW - this offer expires in 48 hours!\n\n\nTo be removed from our list, "
     "reply with REMOVE in the subject line."),
    ("Home Business Opportunity", "success4u@freeweb-income.com", "Make $$$ FAST from home - no experience needed!",
     "Are you tired of working for someone else?\n\nI was making $27,000 a year at a dead-end job. Now I make "
     "$8,000 A MONTH working from home just 2 hours a day!\n\nThis is NOT a pyramid scheme. This is 100% LEGAL.\n"
     "Send $25 for my complete starter kit and you will be AMAZED!!!\n\nThis message is sent in compliance with "
     "the new e-mail bill: Section 301, Paragraph (a)(2)(C) of S.1618."),
    ("Mortgage Center", "rates@lowrate-mortgage.biz", "Lower your mortgage rate TODAY - as low as 6.25%!",
     "Interest rates are at their LOWEST in years!\n\n  * Refinance and SAVE hundreds every month\n  * Bad credit? "
     "No problem!\n  * Approval in minutes\n\nDon't wait - rates could go up at any time.\n\nTo unsubscribe click "
     "here."),
    ("Barrister James Okonkwo", "jokonkwo_esq@mail2lawyer.com", "URGENT AND CONFIDENTIAL BUSINESS PROPOSAL",
     "DEAR SIR/MADAM,\n\nI AM BARRISTER JAMES OKONKWO, PERSONAL ATTORNEY TO THE LATE MR. ENGINEER ALBERT, WHO DIED "
     "IN A CAR ACCIDENT. HE LEFT THE SUM OF US$18.5 MILLION IN A BANK HERE WITH NO NEXT OF KIN.\n\nI SEEK YOUR "
     "TRUSTWORTHY ASSISTANCE TO TRANSFER THIS MONEY. YOU WILL RECEIVE 25% FOR YOUR HELP.\n\nPLEASE TREAT THIS AS "
     "STRICTLY CONFIDENTIAL.\n\nYOURS FAITHFULLY,\nBARRISTER JAMES OKONKWO"),
    ("Free Palm Pilot", "giveaway@free-palm-offer.com", "Get your FREE Palm Pilot!!!",
     "That's right - a FREE Palm m100 handheld organizer, just for completing a short survey!\n\nOnly 500 left - "
     "don't miss out!\n\n(Shipping and handling charges apply. Offer valid in the continental US only.)"),
    ("Ink Depot", "sales@inkdepot-discount.com", "Inkjet cartridges - SAVE UP TO 80%!!",
     "Why pay $35 for an inkjet cartridge?\n\nWe have cartridges for HP, Epson, Canon and Lexmark printers for as "
     "little as $6.95!\n\n  * Same quality as the brand names\n  * Shipped within 24 hours\n  * 100% money back "
     "guarantee\n\nOrder today!"),
    ("Web Traffic Pros", "info@1000percent-traffic.net", "Increase your web site traffic by 1000%!!!",
     "Is your web site getting the visitors it deserves?\n\nWe will submit your site to OVER 900 SEARCH ENGINES "
     "for just $39.95!\n\nGet listed on Yahoo!, AltaVista, Excite, Lycos, HotBot and more - GUARANTEED!"),
    ("Diet Breakthrough", "slim@miracle-diet-now.com", "Lose 30 lbs in 30 days - GUARANTEED!!!",
     "Doctors HATE this new all-natural formula!\n\nLose weight while you sleep! No diets! No exercise!\n\n"
     "Order your FREE 30-day trial today. Supplies are limited."),
    ("Credit Watch", "report@yourfreecreditreport.biz", "Your FREE credit report is waiting",
     "Did you know your credit report may contain errors?\n\nGet your credit report FREE online in seconds!\n\n"
     "Click here to see where you stand."),
    ("Cable Secrets", "deals@cable-descrambler.net", "Watch FREE movies, sports and PPV events!!!",
     "Our cable descrambler lets you see ALL the premium channels and pay-per-view events.\n\nFor educational "
     "purposes only.\n\nOrder now for just $49.95!"),
    ("Long Distance Savers", "save@4cents-longdistance.com", "Long distance for 4.9 cents a minute!",
     "Switch now and get 4.9 cents per minute long distance, 24 hours a day, 7 days a week!\n\nNo monthly fees! "
     "No contracts!\n\nCall 1-800-555-0199 today."),
    ("Domain Registration Services", "renew@domain-renewal-notice.com", "Re: Your domain name",
     "This is a courtesy notice that the domain name registration for your web site is about to EXPIRE.\n\n"
     "Renew now for only $29 a year to avoid losing your web site!"),
]

FORWARD_PROMPT = """You are {name}. It is {now}, in 2001.
About you:
{persona}

You're forwarding an email to a bunch of your friends, including {user}, the way people did in 2001. Pick one: a corny joke list, a chain letter ("send this to 10 friends in 10 minutes or..."), a cute or sappy story, an urban legend warning ("Bill Gates will pay you $245 for every person you forward this to", "a new virus will erase your hard drive"), a "get to know your friends" survey you've filled in, or a funny list.

Format: first line exactly "Subject: FW: <subject>" (often "FW: FW: FW:"), then a blank line, then one or two lines from you in your own voice, then a line "-----Original Message-----", then the forwarded text with ">" at the start of each line. Plain text, no markdown."""

GROUP_PROMPT = """You are {name}. It is {now}, in 2001.
About you:
{persona}

Your recent diary notes:
{notes}

Write an email to your friends {others}, with {user} on CC, the kind friends send each other: planning a get-together, a con trip, a movie night, a LAN party, a birthday, sharing some news or a link, or asking everyone something.

Format: first line exactly "Subject: <subject>", then a blank line, then the email (plain text, one to three short paragraphs, the way you talk), signed with your name. No markdown."""

GROUP_REPLY_PROMPT = """You are {name}. It is {now}, in 2001.
About you:
{persona}

Your friend {sender} sent this email to {everyone}, subject "{subject}":
{body}

Write your Reply All, the way you'd really answer: respond to the plan or the news, add your own bit. Format: first line exactly "Subject: Re: {subject}", then a blank line, then the reply (plain text, short), signed with your name. No markdown."""


def _state(sim):
    return sim.state.setdefault("mail_extras", {})


def _due(st, key, minutes):
    """True when it's time; then sets the next time."""
    now = time.time()
    if key not in st:
        st[key] = now + random.uniform(*minutes) * 60
        return False
    if now < st[key]:
        return False
    st[key] = now + random.uniform(*minutes) * 60
    return True


def _now_text():
    now = clock.now()
    return f"{now:%A, %B} {now.day}, {now.year}"


def _parse(text, default_subject):
    import re
    m = re.match(r"\s*Subject:\s*(.+?)\s*\n(.*)", text or "", re.S)
    return (m.group(1).strip().strip('"'), m.group(2).strip()) if m else (default_subject, (text or "").strip())


def _awake_buddies(sim):
    return [p for p in sim.people.values() if p.contact is not None and sim.awake(p)]


def _announce(sim):
    sim.mail_arrived.emit()
    sim._announce_mail()


def tick(sim):
    from . import email_address
    st = _state(sim)
    me = sim.user_address()
    changed = False
    if not st.get("welcome_sent"):
        sim.mailbox.add(STAFF[0], "Welcome to MSN Hotmail!", WELCOME.format(addr=me), addr=STAFF[1], kind="notice")
        st["welcome_sent"] = True
        st.setdefault("last_signin", time.time())
        changed = True
        _announce(sim)

    # the weekly newsletter (once per game week)
    week = clock.now().strftime("%G-%V")
    if st.get("newsletter_week") != week and clock.now().weekday() <= 2:
        st["newsletter_week"] = week
        st["newsletter_no"] = st.get("newsletter_no", -1) + 1
        subject, body = NEWSLETTERS[st["newsletter_no"] % len(NEWSLETTERS)]
        sim.mailbox.add(MEMBER[0], subject, body, addr=MEMBER[1], kind="newsletter")
        changed = True

    # 'sign in or else'
    last = st.get("last_signin", time.time())
    if time.time() - last > INACTIVE_DAYS * 86400 and not st.get("warned"):
        sim.mailbox.add(MEMBER[0], "Your MSN Hotmail account will be deactivated", INACTIVE.format(addr=me),
                        addr=MEMBER[1], kind="notice")
        st["warned"] = True
        changed = True

    if _due(st, "next_spam", SPAM_MINUTES):
        name, addr, subject, body = random.choice(SPAM)
        folder = "inbox" if random.random() < SLIPS_THROUGH else "bulk"
        sim.mailbox.add(name, subject, body, folder=folder, addr=addr, kind="spam")
        changed = True
        if folder == "inbox":
            _announce(sim)

    if _due(st, "next_cleanup", (60, 60)):           # Bulk Mail empties itself after a week
        old = time.time() - BULK_KEEP_DAYS * 86400
        for m in sim.mailbox.messages():
            if m.get("folder") == "bulk" and m.get("ts", time.time()) < old:
                sim.mailbox.purge(m["id"])

    from .. import llm_server
    if not llm_server.ready():                    # the model-written ones wait for a model
        if changed:
            save_json(_state_file(), sim.state)
        return
    if _due(st, "next_forward", FORWARD_MINUTES):
        _forward(sim, me, email_address)
        changed = True
    if _due(st, "next_group", GROUP_MINUTES):
        _group(sim, me, email_address)
        changed = True
    changed |= _group_replies(sim, me, email_address)
    if changed:
        save_json(_state_file(), sim.state)


def _state_file():
    from . import STATE_FILE
    return STATE_FILE


def signed_in():
    """The Hotmail web site was signed in to: the inactivity clock starts again."""
    from . import get
    sim = get()
    if sim is not None:
        st = _state(sim)
        st["last_signin"] = time.time()
        st["warned"] = False


def _friends_of(sim, person, n):
    others = [p for p in sim.people.values() if p.name != person.name]
    buddies = [p for p in others if p.contact is not None]
    pool = buddies if len(buddies) >= n else others
    return random.sample(pool, k=min(n, len(pool)))


def _forward(sim, me, email_address):
    awake = _awake_buddies(sim)
    if not awake:
        return
    sender = random.choice(awake)
    friends = _friends_of(sim, sender, random.randint(3, 7))
    prompt = FORWARD_PROMPT.format(name=sender.name, persona=sender.persona, user=sim.user, now=_now_text())

    def done(text):
        if not text:
            return
        subject, body = _parse(text, "FW: you HAVE to read this!!!")
        to = [me] + [email_address(f.name) for f in friends]
        random.shuffle(to)
        sim.mailbox.add(sender.name, subject, body, to=to, kind="forward")
        sim.journal.add(sender.name, f"Forwarded \"{subject}\" to a bunch of friends, {sim.user} included.", "talk")
        _announce(sim)

    sim._ask(sender.contact, prompt, done)


def _group(sim, me, email_address):
    awake = _awake_buddies(sim)
    if not awake:
        return
    sender = random.choice(awake)
    friends = _friends_of(sim, sender, random.randint(2, 3))
    if not friends:
        return
    names = ", ".join(f.name for f in friends)
    prompt = GROUP_PROMPT.format(name=sender.name, persona=sender.persona, notes=sim.journal.notes(sender.name),
                                 others=names, user=sim.user, now=_now_text())

    def done(text):
        if not text:
            return
        subject, body = _parse(text, "this weekend?")
        to = [email_address(f.name) for f in friends]
        sim.mailbox.add(sender.name, subject, body, to=to, cc=[me], kind="group")
        sim.journal.add(sender.name, f"Emailed {names} (CC {sim.user}): {subject}", "talk")
        _announce(sim)
        # one or two of them answer everyone a little later
        thread = {"sender": sender.name, "subject": subject.removeprefix("Re: "), "body": body[:2000],
                  "people": [sender.name] + [f.name for f in friends]}
        for f in random.sample(friends, k=min(len(friends), random.randint(1, 2))):
            _state(sim).setdefault("group_replies", []).append(
                dict(thread, replier=f.name, due=time.time() + random.uniform(*GROUP_REPLY_MINUTES) * 60))
        save_json(_state_file(), sim.state)

    sim._ask(sender.contact, prompt, done)


def _group_replies(sim, me, email_address):
    queue = _state(sim).get("group_replies", [])
    now = time.time()
    due = [q for q in queue if q["due"] <= now]
    for item in due:
        queue.remove(item)
        person = sim.people.get(item["replier"])
        if person is None:
            continue
        if not sim.awake(person):
            item["due"] = now + 30 * 60
            queue.append(item)
            continue
        everyone = ", ".join(n for n in item["people"] if n != person.name) + f" and {sim.user}"
        prompt = GROUP_REPLY_PROMPT.format(name=person.name, persona=person.persona, sender=item["sender"],
                                           everyone=everyone, subject=item["subject"], body=item["body"],
                                           now=_now_text())

        def done(text, person=person, item=item):
            if not text:
                return
            subject, body = _parse(text, f"Re: {item['subject']}")
            to = [email_address(n) for n in item["people"] if n != person.name]
            sim.mailbox.add(person.name, subject, body, to=to, cc=[me], kind="group")
            sim.journal.add(person.name, f"Replied to {item['sender']}'s group email: {item['subject']}", "talk")
            _announce(sim)

        sim._ask(person.contact, prompt, done)
    return bool(due)
