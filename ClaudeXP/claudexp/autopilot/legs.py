"""EPOCH-2001's legs: what Kithylin does on the Windows XP computer. Each knows one program - ClaudeAIM, Outlook
Express, Internet Explorer, ClaudeTV, ClaudeRPG, ClaudeMUCK - and drives it the way a person would: opens it, moves
the cursor to the thing, reads for a while, types. The words come from the voice (claudecore.autopilot.voice),
asked through his day (claudecore.autopilot.day.speak): the layered prompt with today's one story, then a check
that the reply keeps to it."""
import random
import time

from PySide6.QtCore import QPoint, QPointF, QUrl
from PySide6.QtWidgets import QToolButton
from shiboken6 import isValid

from claudecore.autopilot.day import speak
from claudecore.autopilot.engine import ALWAYS, BACKGROUND, FOREGROUND, Leg
from claudecore.autopilot.voice import persona

from .. import clock, programs

IM_NOTE = ("\n\nYou're on AOL Instant Messenger on your Windows XP computer in {year}. Reply with one short IM: a line "
           "or two, casual, the way you really type. No narration, no name prefix.")
RP_NOTE = ("\n\nYou're on AOL Instant Messenger in {year}, roleplaying with {name}. Actions go in *asterisks*, speech "
           "plain. Stay in the scene, two to four sentences, and leave {name} something to respond to. No name prefix.")
MAIL_NOTE = ("\n\nYou're writing an e-mail from your Hotmail account in {year}. Write only the body of the message: "
             "a few friendly paragraphs or a few sentences, as yourself, and sign off with your name.")
MUCK_NOTE = ("\n\nYou're logged on to PawPrints MUCK in {year}, standing in {room}. People here: {people}. Reply with "
             "ONE line you say out loud - no quotes, no name prefix, no actions.")


# ---- helpers ---------------------------------------------------------------------------------------------------
def frame_titled(desktop, prefix):
    for w in reversed(desktop.windows):
        if isValid(w) and str(getattr(w, "title", "")).startswith(prefix):
            return w
    return None


def focus(ctx, frame):
    """Bring a window up the way a person would: the pointer goes to its title bar, then it comes forward."""
    if frame is None or not isValid(frame):
        return
    yield from ctx.hands.move_to((frame, QPoint(min(frame.width() // 2, 220), 12)))
    ctx.desktop.activate(frame)
    yield random.uniform(0.3, 0.8) * ctx.pace


def year():
    return clock.now().year


def ensure_online(ctx):
    """2001 is dial-up: if the computer isn't online, open the connection and press Dial, then wait for the modem."""
    from .. import network
    if network.is_connected():
        return
    net = network.get(ctx.desktop)
    ctx.status("Dialing up")
    network.connect(ctx.desktop)
    yield (lambda: net.connect_win is not None or network.is_connected(), 10)
    win = net.connect_win
    if win is not None and isValid(win) and not network.is_connected():
        from PySide6.QtWidgets import QPushButton
        button = next((b for b in win.findChildren(QPushButton)
                       if b.text().replace("&", "") in ("Dial", "Connect")), None)
        yield from focus(ctx, win)
        if button is not None:
            yield from ctx.hands.click(button)
    yield (lambda: network.is_connected(), 150)


def send_button(widget, text="Send"):
    for b in widget.findChildren(QToolButton):
        if b.text().strip().lower() == text.lower():
            return b
    return None


# ---- the messengers (always) -----------------------------------------------------------------------------------
class Messengers(Leg):
    """ClaudeAIM, open the whole session: Kithylin answers whoever IMs him, and now and then says hello to someone
    who's online. A conversation runs its course - after a handful of exchanges he lets it rest. How quickly he
    answers, how long it runs and who he IMs first follow his interests (the Interests tab): a love interest gets an
    IM as soon as they come online."""
    key, title, kind = "messengers", "AIM", ALWAYS
    blurb = "answer IMs, say hello to friends who are online (nearly always on)"
    doing = "chatting on AIM"

    def run(self, ctx):
        from ..programs import aim
        yield from ctx.hands.take(self.key)
        try:
            yield from ensure_online(ctx)
        finally:
            ctx.hands.release(self.key)
        ctx.status("Signing on to AIM...")
        programs.launch(ctx.desktop, "aim")
        yield (lambda: aim._app is not None and aim._app.world is not None and aim._app.world.running, 240)
        app = aim._app
        if app is None or app.world is None:
            ctx.note("AIM didn't start.")
            return
        world = app.world
        if ctx.engine.asleep and ctx.day is not None:      # he sat down asleep: AIM wasn't on to show it
            world.set_user_away(True, ctx.day.block_info().get("away", ""))
        queue = []
        world.message_added.connect(lambda bid, entry: queue.append((bid, entry)))
        pending, budget, rested, last_used = {}, {}, {}, {}
        greeted = set()                                 # love interests he's IMed since they came online
        greet_at = {}                                   # ... and when he'll send that IM
        next_hello = time.monotonic() + random.uniform(4, 10) * 60 * ctx.pace
        ctx.engine.claims = getattr(ctx.engine, "claims", set())
        ctx.status("On AIM.")
        try:
            while True:
                now = time.monotonic()
                if ctx.engine.asleep:                       # asleep or out: the away message answers for him
                    queue.clear()
                    pending.clear()
                    greet_at.clear()
                    greeted.clear()                         # awake again: his love interests get a good morning
                    next_hello = now + random.uniform(10, 30) * 60 * ctx.pace
                    yield 2
                    continue
                slow = ctx.day.reply_pace() if ctx.day is not None else 1.0
                while queue:
                    bid, entry = queue.pop(0)
                    if entry.get("kind") != "contact" or bid in ctx.engine.claims:
                        continue
                    if now < rested.get(bid, 0):
                        continue                                  # letting that conversation rest
                    busy = any(k in ctx.engine.tasks for k in ("tv", "rpg"))
                    lo, hi = self.tier(ctx, bid)["reply"]
                    delay = random.uniform(lo, hi) * ctx.pace * slow + (random.uniform(10, 50) if busy else 0)
                    pending[bid] = max(pending.get(bid, 0), now + delay)
                for bid, when in list(pending.items()):
                    if now >= when:
                        del pending[bid]
                        if bid not in world.buddies:
                            continue
                        used = budget.setdefault(bid, [0, random.randint(*self.tier(ctx, bid)["exchanges"])])
                        if used[0] >= used[1]:
                            rested[bid] = now + random.uniform(*self.tier(ctx, bid)["rest"]) * 60
                            budget.pop(bid, None)
                            ctx.note(f"Let the conversation with {world.buddies[bid].name} rest.")
                            if ctx.day is not None:
                                ctx.day.end_conversation(world.buddies[bid].name)
                            yield from self.close_im(ctx, app, bid)
                            continue
                        used[0] += 1
                        last_used[bid] = time.monotonic()
                        yield from self.reply(ctx, app, bid)
                        for old in sorted((b for b in app.im_windows if b not in pending and b != bid),
                                          key=lambda b: last_used.get(b, 0))[:max(0, len(app.im_windows) - 3)]:
                            yield from self.close_im(ctx, app, old)     # no more than three IM windows open
                for bid in self.sweethearts(ctx, app, greeted, rested, pending, now):
                    greeted.add(bid)
                    greet_at[bid] = now + random.uniform(15, 60) * ctx.pace * slow
                    ctx.note(f"{world.buddies[bid].name} is online - IMing them in a moment.")
                for bid, when in list(greet_at.items()):
                    if now < when:
                        continue
                    del greet_at[bid]
                    if bid in world.buddies and bid not in app.im_windows and bid not in pending:
                        yield from self.reply(ctx, app, bid, instruction=f"{world.buddies[bid].name} just came "
                                              "online. IM them first: one short, warm message, glad to see them.")
                        budget[bid] = [1, random.randint(*self.tier(ctx, bid)["exchanges"])]
                        last_used[bid] = time.monotonic()
                if now >= next_hello:
                    next_hello = now + random.uniform(12, 30) * 60 * ctx.pace * slow
                    yield from self.say_hello(ctx, app, pending)
                yield 1
        finally:
            try:
                world.message_added.disconnect()
            except Exception:
                pass

    def reply(self, ctx, app, bid, instruction=None, note=IM_NOTE, max_tokens=120, thread_ok=True, extra_note="",
              check=True):
        world = app.world
        b = world.buddies[bid]
        yield from ctx.hands.take(self.key)
        try:
            app.open_im(bid)
            win = app.im_windows.get(bid)
            frame = getattr(win, "_xp_frame", None) if win is not None else None
            yield from focus(ctx, frame)
            ctx.status(f"Reading {b.name}'s IM")
            yield random.uniform(2, 6) * ctx.pace
            history = []
            for m in b.history.messages[-24:]:
                if m.get("kind") == "user" and m.get("text"):
                    history.append({"role": "assistant", "content": m["text"]})
                elif m.get("kind") in ("contact", "contact_auto") and m.get("text"):
                    history.append({"role": "user", "content": m["text"]})
            ctx.status(f"Replying to {b.name}")
        finally:
            ctx.hands.release(self.key)                 # thinking of what to say: the hands are free meanwhile
        text = yield from speak(ctx, b.name, persona(b.name), note.format(year=year(), name=b.name) + extra_note,
                                history, instruction, max_tokens=max_tokens, max_lines=3, thread_ok=thread_ok,
                                check=check)
        if not text or win is None or not isValid(win):
            return
        yield from ctx.hands.take(self.key)
        try:
            if ctx.desktop.active is not frame:
                yield from focus(ctx, frame)
            yield from ctx.hands.type_into(win.input, text)
            yield from ctx.hands.click((win.input, QPoint(win.input.width() - 20, win.input.height() - 12)),
                                       action=win._send)
            ctx.status(f"Chatting with {b.name}")
        finally:
            ctx.hands.release(self.key)

    @staticmethod
    def tier(ctx, bid):
        from claudecore.autopilot.day import TIERS
        return ctx.day.tier_info(bid) if ctx.day is not None else TIERS["close"]

    def sweethearts(self, ctx, app, greeted, rested, pending, now):
        """Love interests who are online and haven't had an IM from him since they came on (or since their last
        conversation rested): he IMs them at once."""
        from claudeaim.engine import Presence
        if ctx.day is None:
            return []
        out = []
        for bid, b in app.world.buddies.items():
            online = b.presence == Presence.ONLINE
            if not online or now < rested.get(bid, 0):
                if not online:
                    greeted.discard(bid)
                continue
            if rested.pop(bid, None) is not None:
                greeted.discard(bid)                     # the rest is over: another conversation
            if (ctx.day.tier(bid) == "love" and bid not in greeted and bid not in pending
                    and bid not in app.im_windows and bid not in ctx.engine.claims):
                out.append(bid)
            elif bid in app.im_windows:
                greeted.add(bid)                         # already talking
        return out[:1]

    def close_im(self, ctx, app, bid):
        """Close a conversation's IM window, the pointer going to its close box."""
        win = app.im_windows.get(bid)
        frame = getattr(win, "_xp_frame", None) if win is not None else None
        if frame is None or not isValid(frame):
            return
        yield from ctx.hands.take(self.key)
        try:
            yield from ctx.hands.click((frame, QPoint(frame.width() - 14, 12)), action=frame.request_close)
        finally:
            ctx.hands.release(self.key)

    def say_hello(self, ctx, app, pending):
        from claudeaim.engine import Presence
        world = app.world
        quiet = [b for b in world.buddies.values() if b.presence == Presence.ONLINE and b.id not in pending
                 and b.id not in ctx.engine.claims and b.id not in app.im_windows]
        if not quiet:
            return
        weights = [self.tier(ctx, b.id)["hello"] for b in quiet]
        b = random.choices(quiet, weights=weights)[0]
        ctx.note(f"Saying hello to {b.name}.")
        opener = ctx.day.opener() if ctx.day is not None else ""
        yield from self.reply(ctx, app, b.id, instruction=f"Start a conversation with {b.name}: one short, friendly "
                                                          "IM, as if you just noticed them online."
                                                          + (f" The way you often start: {opener}" if opener else ""))


# ---- a roleplay session (foreground) ---------------------------------------------------------------------------
class Roleplay(Leg):
    """A proper scene with one buddy on AIM, the messengers leg standing aside for them. With an RP track (the RP
    Tracks tab: scenes from his own logs) he follows it and leads, a beat at a time; without one, a scene of his
    own, or a roleplay seed from his threads. How long it runs and who it's with follow his interests."""
    key, title, kind = "roleplay", "Roleplay on AIM", FOREGROUND
    blurb = "a proper scene with one buddy, led along one of your RP tracks"
    doing = "roleplaying with a friend on AIM"
    minutes, weight, cooldown = (25, 50), 0.8, 60 * 60

    def run(self, ctx):
        from ..programs import aim
        from claudeaim.engine import Presence
        app = aim._app
        if app is None or app.world is None or not app.world.running:
            return
        world = app.world
        free = [b for b in world.buddies.values() if b.presence == Presence.ONLINE
                and b.id not in getattr(ctx.engine, "claims", set())]
        if not free:
            return
        tiers = [Messengers.tier(ctx, x.id) for x in free]
        b = random.choices(free, weights=[t["roleplay"] for t in tiers])[0]
        ctx.engine.claims = getattr(ctx.engine, "claims", set()) | {b.id}
        ctx.doing(f"roleplaying with {b.name} on AIM")
        turns = random.randint(*Messengers.tier(ctx, b.id)["turns"])
        track = ctx.day.track_for(b.id) if ctx.day is not None else None
        seed = ctx.day.roleplay_seed() if ctx.day is not None and track is None else None
        if track is not None:
            turns = max(turns, 2 * len(track.get("beats", [])))
            note, _first = ctx.day.track_step(track, b.name, 0, turns)
            opening = (f"Open the roleplay with {b.name}: set the scene ({track.get('setting') or track['title']}) "
                       f"and the situation, in *asterisks*, two or three sentences, and draw them in.")
            ctx.note(f"Roleplay with {b.name}, following the track \"{track['title']}\".")
            ctx.day.track_used(track["id"])
        else:
            note = ""
            opening = (f"Suggest a roleplay scene to {b.name} and open it - {seed['title']}: "
                       f"{seed.get('facts') or ''} Set the place and what you're doing, in *asterisks*, two or three "
                       "sentences." if seed else
                       f"Suggest a roleplay scene to {b.name} and open it: set the place and what you're doing, in "
                       "*asterisks*, two or three sentences.")
        helper = Messengers()
        helper.key = self.key
        try:
            ctx.status(f"Starting a roleplay with {b.name}" + (f": {track['title']}" if track else ""))
            yield from helper.reply(ctx, app, b.id, note=RP_NOTE, max_tokens=220, instruction=opening,
                                    thread_ok=False, extra_note=note, check=False)
            for step in range(1, turns + 1):
                if ctx.time_left() <= 0 or ctx.stopping:
                    break
                mark = len(b.history.messages)
                yield (lambda: len(b.history.messages) > mark
                       and b.history.messages[-1].get("kind") == "contact", 240)
                if not (len(b.history.messages) > mark and b.history.messages[-1].get("kind") == "contact"):
                    break
                yield random.uniform(6, 20) * ctx.pace
                if track is not None:
                    note, instruction = ctx.day.track_step(track, b.name, step, turns)
                    ctx.status(f"Roleplaying with {b.name}: {track['title']} ({step} of {turns})")
                else:
                    instruction = "Continue the roleplay in character."
                yield from helper.reply(ctx, app, b.id, note=RP_NOTE, max_tokens=220, instruction=instruction,
                                        thread_ok=False, extra_note=note, check=False)
            if not ctx.stopping:
                yield from helper.reply(ctx, app, b.id, note=IM_NOTE, max_tokens=80,
                                        instruction="Wrap the scene up warmly in one or two lines and say you need "
                                                    "to go do something for a bit.", thread_ok=False, check=False)
                ctx.event(f"roleplayed with {b.name}")
        finally:
            ctx.engine.claims.discard(b.id)


# ---- e-mail (foreground) ---------------------------------------------------------------------------------------
class Mail(Leg):
    """Outlook Express: read what's new, answer some of it, now and then write to someone unprompted."""
    key, title, kind = "mail", "E-mail", FOREGROUND
    blurb = "read what's new in Outlook Express and answer some of it"
    doing = "catching up on e-mail"
    minutes, weight, cooldown = (8, 20), 1.0, 40 * 60

    def run(self, ctx):
        from ..life import get as life
        from ..programs import outlook
        sim = life()
        if sim is None:
            return
        yield from ctx.hands.take(self.key)
        try:
            yield from ensure_online(ctx)
            ctx.status("Checking e-mail")
            win = outlook.open_outlook(ctx.desktop)
            oe = win.content
            yield from focus(ctx, win)
            yield random.uniform(2, 5) * ctx.pace
            oe.refresh()
            unread = sim.mailbox.unread()[-3:]
            for m in unread:
                if ctx.time_left() <= 0 or ctx.stopping:
                    break
                yield from self.read(ctx, oe, m)
                if random.random() < 0.7:
                    yield from self.write(ctx, oe, sim, to=f"{m['from']} <{m.get('addr', '')}>",
                                          subject=m["subject"] if m["subject"].lower().startswith("re:")
                                          else "Re: " + m["subject"],
                                          context=f"From {m['from']}, subject \"{m['subject']}\":\n\n{m['body']}",
                                          instruction=f"Write your reply to {m['from']}'s e-mail.")
            if not unread and random.random() < 0.5 and sim.people:
                name = random.choice(sorted(sim.people))
                from ..life import email_address
                yield from self.write(ctx, oe, sim, to=f"{name} <{email_address(name)}>", subject="",
                                      context=f"You feel like writing to your friend {name}.",
                                      instruction=f"Write {name} a short, friendly e-mail out of the blue: what "
                                                  "you've been up to, a question for them. Start with a one-line "
                                                  "subject on its own first line, written as 'Subject: ...'.")
            yield random.uniform(3, 8) * ctx.pace
        finally:
            ctx.hands.release(self.key)
            win = frame_titled(ctx.desktop, "Inbox - Outlook Express")
            if win is not None and random.random() < 0.6:
                win.request_close()

    def read(self, ctx, oe, m):
        item = None
        for i in range(oe.list.topLevelItemCount()):
            it = oe.list.topLevelItem(i)
            d = it.data(0, 0x0100)
            if isinstance(d, dict) and d.get("id") == m["id"]:
                item = it
                break
        if item is not None:
            rect = oe.list.visualItemRect(item)
            yield from ctx.hands.click((oe.list.viewport(), rect.center()), action=lambda: oe.list.setCurrentItem(item))
        ctx.status(f"Reading an e-mail from {m['from']}")
        ctx.hands.release(self.key)                     # reading: free for an IM meanwhile
        yield min(60, 6 + len(m.get("body", "")) / 25) * ctx.pace
        yield from ctx.hands.take(self.key)
        yield from focus(ctx, oe.frame) if ctx.desktop.active is not oe.frame else iter(())

    def write(self, ctx, oe, sim, to, subject, context, instruction):
        win = oe.compose(to=to, subject=subject)
        body_w = win.content
        yield from focus(ctx, win)
        who = to.split("<")[0].strip()
        ctx.status(f"Writing to {who}")
        ctx.hands.release(self.key)                     # working out what to write
        text = yield from speak(ctx, who, persona(who), MAIL_NOTE.format(year=year()),
                                [{"role": "user", "content": context}], instruction, max_tokens=320)
        yield from ctx.hands.take(self.key)
        if not isValid(win):
            return
        if not text:
            win.request_close()
            return
        if ctx.desktop.active is not win:
            yield from focus(ctx, win)
        if not subject:
            first, _, rest = text.partition("\n")
            if first.lower().startswith("subject:"):
                yield from ctx.hands.type_into(body_w.subject, first.split(":", 1)[1].strip())
                text = rest.strip()
            else:
                yield from ctx.hands.type_into(body_w.subject, "Hey there")
        yield from ctx.hands.type_into(body_w.body, text, speed=11)
        yield random.uniform(1, 3) * ctx.pace
        button = send_button(body_w)
        yield from ctx.hands.click(button if button is not None else body_w.body, action=body_w.send)
        ctx.note(f"Sent an e-mail to {to}: {subject or '(new)'}")
        ctx.event(f"e-mailed {who}")


# ---- the Web (foreground) --------------------------------------------------------------------------------------
class Browse(Leg):
    """Internet Explorer: a wander through the 2001 Web - a link, a read, another link, a search now and then."""
    key, title, kind = "browse", "The Web", FOREGROUND
    blurb = "wander the 2001 Web in Internet Explorer"
    doing = "browsing the Web"
    minutes, weight, cooldown = (10, 25), 1.2, 25 * 60
    SEARCHES = ["furry art", "husky plush", "furry conventions 2001", "anthro wolf art", "winamp skins", "furry comics",
                "how to make a buddy icon", "furry webrings", "coffee roasting", "fursuit making", "angel wings costume",
                "upstate new york hiking", "snow husky pictures"]

    ADULT = ("hardblush", "sexyfur", "yiffstar", "yiff.", "/adult")

    def run(self, ctx):
        from ..programs.navigator import iexplore
        yield from ctx.hands.take(self.key)
        try:
            yield from ensure_online(ctx)
            ctx.status("Opening Internet Explorer")
            iexplore.launch(ctx.desktop)
            yield (lambda: iexplore._frame is not None, 30)
            frame = iexplore._frame
            if frame is None:
                return
            browser = frame.content
            yield from focus(ctx, frame)
        finally:
            ctx.hands.release(self.key)
        adult_ok = bool(ctx.settings.get("adult_web", False))
        while ctx.time_left() > 0 and not ctx.stopping and isValid(frame):
            yield (lambda: getattr(browser, "loader", None) is None, 90)
            title = browser.url or "the page"
            ctx.status(f"Reading {title[:60]}")
            yield random.uniform(15, 50) * ctx.pace                    # reading: the hands are free for IMs
            links = [(h, t) for h, t in browser.links.items() if not h.startswith("mailto:")
                     and (adult_ok or not any(a in (h + " " + t).lower() for a in self.ADULT))]
            roll = random.random()
            yield from ctx.hands.take(self.key)
            try:
                if not isValid(frame):
                    return
                yield from focus(ctx, frame)
                if links and roll < 0.75:
                    href, text = random.choice(links)
                    yield from ctx.hands.move_to(browser.view)
                    yield random.uniform(0.2, 0.6)
                    browser.link_clicked(QUrl(href))
                    ctx.note(f"Clicked a link: {text or href}")
                elif roll < 0.9 or not links:
                    words = random.choice(self.SEARCHES)
                    browser.location.clear()
                    yield from ctx.hands.type_into(browser.location, words)
                    browser._go_typed()
                    ctx.note(f"Searched for {words}")
                    ctx.event(f"looked up {words} online", share=random.random() < 0.3)
                else:
                    yield from ctx.hands.click(frame, action=browser.home)
            finally:
                ctx.hands.release(self.key)


# ---- a break (foreground) --------------------------------------------------------------------------------------
class Idle(Leg):
    """Away from the desk for a few minutes: coffee, the window, the dog."""
    key, title, kind = "idle", "A break", FOREGROUND
    blurb = "coffee, the window, a few minutes away from the desk"
    minutes, weight, cooldown = (3, 8), 0.7, 30 * 60

    def run(self, ctx):
        why = random.choice(["Getting coffee", "Stretching", "Looking out the window", "Away from the desk a minute"])
        ctx.status(why)
        ctx.doing(why.lower().replace("away from the desk a minute", "away from the desk for a minute"))
        yield from ctx.hands.move_to(QPointF(ctx.desktop.width() - 60, ctx.desktop.height() - 90))
        while ctx.time_left() > 0 and not ctx.stopping:
            yield 2


# ---- the TV (background) ---------------------------------------------------------------------------------------
class TV(Leg):
    """ClaudeTV: pick a channel with something on and watch it to the end - a whole movie if that's allowed."""
    key, title, kind = "tv", "ClaudeTV", BACKGROUND
    blurb = "watch whatever's on ClaudeTV, in the background"
    doing = "watching TV"
    minutes, weight, cooldown = (30, 90), 1.0, 45 * 60

    def run(self, ctx):
        from claudetv import schedule, tuner
        yield from ctx.hands.take(self.key)
        try:
            ctx.status("Turning on the TV")
            win = tuner.open_tv(ctx.desktop)
            t = win.content
            yield from focus(ctx, win)
            yield (lambda: bool(t.channels), 120)
            if not t.channels:
                return
            secs = schedule.seconds(clock.now())
            options = []
            for ch in t.channels:
                slot = ch.at(secs) if not ch.dead else None
                if slot is None or slot.kind != "program":
                    continue
                remaining = slot.end - secs
                movie = slot.media.kind == "movie"
                if movie and not ctx.settings.get("whole_movies", True):
                    continue
                if remaining < 8 * 60:
                    continue
                options.append((ch, slot, remaining, movie))
            if not options:
                ctx.note("Nothing much on.")
                return
            ch, slot, remaining, movie = random.choice(options)
            yield from ctx.hands.click((win, QPoint(60, win.height() - 30)), action=lambda: t.tune(ch))
            title, _sub, _desc = tuner.describe(slot)
            until = slot.until()
            ctx.status(f"Watching {ch.label()}: {title} until {clock.time_text(until)}")
            ctx.note(f"Watching {title} on channel {ch.number}.")
            ctx.doing(f"watching {title} on TV")
        finally:
            ctx.hands.release(self.key)
        end = time.monotonic() + (remaining if movie and ctx.settings.get("whole_movies", True)
                                  else min(remaining, ctx.time_left()))
        while time.monotonic() < end and not ctx.stopping and isValid(win):
            yield 5
        ctx.event(f"watched {title} on TV", share=movie or random.random() < 0.3)
        if isValid(win) and not ctx.stopping:
            yield from ctx.hands.take(self.key)
            try:
                yield from ctx.hands.click((win, QPoint(win.width() - 16, 12)), action=win.request_close)
                ctx.note("Turned the TV off.")
            finally:
                ctx.hands.release(self.key)


# ---- ClaudeRPG on its own autopilot (background) -----------------------------------------------------------------
class RPG(Leg):
    """ClaudeRPG: through the splash, the prologue and the title to a run - continuing the saved hero, or a new one
    in an empty slot - with the game's own autopilot switched on, for a good while. If the hero dies, the next
    hero takes over."""
    key, title, kind = "rpg", "ClaudeRPG", BACKGROUND
    blurb = "let the hero play ClaudeRPG on the game's own autopilot"
    doing = "playing ClaudeRPG"
    minutes, weight, cooldown = (30, 60), 0.9, 60 * 60
    # one step towards playing, whatever screen the game is on; returns the step taken, 'playing' or 'stuck'
    ADVANCE = """(function(){
        const vis=e=>!!e&&e.getBoundingClientRect().width>0, byId=id=>document.getElementById(id);
        const byText=re=>[...document.querySelectorAll('button')].find(b=>vis(b)&&re.test(b.textContent||''));
        if (typeof P==='object'&&P&&P.cls&&vis(byId('pausebtn'))) {
            if (typeof state!=='string'||state==='play') return 'playing';
            if (state==='pause'&&vis(byId('resbtn'))) { byId('resbtn').click(); return 'resume'; }
            document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',code:'Escape',bubbles:true}));
            return 'close:'+state;
        }
        const ov=byId('overlay');
        if (vis(ov)&&/Click or press any key/.test(document.body.innerText)) { ov.click(); return 'splash'; }
        if (vis(byId('storygo'))) { byId('storygo').click(); return 'story'; }
        if (vis(byId('contbtn'))) { byId('contbtn').click(); return 'continue'; }
        if (vis(byId('linebtn'))) { byId('linebtn').click(); return 'bloodline'; }
        if (vis(byId('againbtn'))) { byId('againbtn').click(); return 'new hero'; }
        let b=byText(/Start here/); if (b) { b.click(); return 'slot'; }
        if (vis(byId('playauto'))) {
            byId('playauto').click();
            const c=[...document.querySelectorAll('.cls')].find(e=>vis(e)&&!/locked/.test(e.className));
            if (c) { c.click(); return 'hero'; }
        }
        if (vis(byId('newbtn'))) { byId('newbtn').click(); return 'new'; }
        if (vis(byId('sgo'))) { byId('sgo').click(); return 'descend'; }
        b=byText(/^(Continue|Next|Skip|OK|Play)/); if (b) { b.click(); return 'next:'+b.textContent.trim().slice(0,20); }
        return 'stuck';
    })()"""
    AUTO_ON = """(function(){ if (typeof P!=='object'||!P) return 'no run'; if (P.auto) return 'on';
        const b=document.getElementById('autobtn'); if (b) b.click(); if (P.auto) return 'on';
        document.dispatchEvent(new KeyboardEvent('keydown',{key:'y',code:'KeyY',bubbles:true})); return P.auto?'on':'off'; })()"""
    AUTO_OFF = """(function(){ if (typeof P!=='object'||!P||!P.auto) return 'off';
        const b=document.getElementById('autobtn'); if (b) b.click(); return P.auto?'on':'off'; })()"""

    def js(self, view, code):
        box = {}
        try:
            view.page().runJavaScript(code, lambda r: box.__setitem__("r", r))
        except Exception:
            box["r"] = None
        yield (lambda: "r" in box, 20)
        return box.get("r")

    def get_playing(self, ctx, view, tries=12):
        """Step through whatever screens are up until a run is on, with the pointer over the game."""
        for _ in range(tries):
            step = yield from self.js(view, self.ADVANCE)
            ctx.note(f"ClaudeRPG: {step}")
            if step == "playing":
                return True
            if step == "stuck":
                yield 4 * ctx.pace
                continue
            yield from ctx.hands.move_to(view)
            yield random.uniform(1.5, 3) * ctx.pace
        return False

    def run(self, ctx):
        import clauderpg
        yield from ctx.hands.take(self.key)
        try:
            ctx.status("Starting ClaudeRPG")
            programs.launch(ctx.desktop, "rpg")
            win = clauderpg._open.get("win")
            if win is None or not isValid(win) or win.content.view is None:
                return
            view = win.content.view
            yield from focus(ctx, win)
            yield 8 * ctx.pace
            if not (yield from self.get_playing(ctx, view)):
                ctx.note("ClaudeRPG: couldn't get a run going; leaving it open.")
            else:
                state = yield from self.js(view, self.AUTO_ON)
                ctx.note(f"ClaudeRPG autopilot: {state}")
            ctx.status("Playing ClaudeRPG (the hero's on autopilot)")
        finally:
            ctx.hands.release(self.key)
        check = time.monotonic() + 60
        while ctx.time_left() > 0 and not ctx.stopping and isValid(win):
            if time.monotonic() >= check:                   # a death screen, a prompt: carry on
                check = time.monotonic() + 60
                step = yield from self.js(view, self.ADVANCE)
                if step not in ("playing", None):
                    yield from ctx.hands.take(self.key)
                    try:
                        ctx.note(f"ClaudeRPG: {step}")
                        if (yield from self.get_playing(ctx, view, tries=8)):
                            yield from self.js(view, self.AUTO_ON)
                    finally:
                        ctx.hands.release(self.key)
            yield 5
        if isValid(win):
            yield from ctx.hands.take(self.key)
            try:
                yield from self.js(view, self.AUTO_OFF)
                ctx.event("played some ClaudeRPG")
                yield 1.5
                yield from ctx.hands.click((win, QPoint(win.width() - 16, 12)), action=win.request_close)
                ctx.note("Put ClaudeRPG away.")
            finally:
                ctx.hands.release(self.key)


# ---- the MUCK (background) -------------------------------------------------------------------------------------
class Muck(Leg):
    """PawPrints MUCK: logged on in the background, listening, saying something now and then, wandering."""
    key, title, kind = "muck", "The MUCK", BACKGROUND
    blurb = "log on to PawPrints MUCK and chat with whoever's there"
    doing = "hanging out on the MUCK"
    minutes, weight, cooldown = (20, 45), 0.8, 40 * 60

    def run(self, ctx):
        from ..programs import muck
        yield from ctx.hands.take(self.key)
        try:
            yield from ensure_online(ctx)
        finally:
            ctx.hands.release(self.key)
        ctx.status("Logging on to the MUCK")
        programs.launch(ctx.desktop, "muck")
        yield (lambda: muck._frame is not None, 30)
        frame = muck._frame
        if frame is None:
            return
        client = frame.content
        world = client.world
        yield (lambda: world.logged_in, 300)
        if not world.logged_in:
            ctx.note("Couldn't get logged on to the MUCK.")
            return
        heard = []
        world.line.connect(lambda kind, text: heard.append((kind, text)))
        next_act = time.monotonic() + random.uniform(30, 90) * ctx.pace
        ctx.status("On the MUCK")
        try:
            while ctx.time_left() > 0 and not ctx.stopping and isValid(frame):
                if time.monotonic() >= next_act:
                    next_act = time.monotonic() + random.uniform(40, 150) * ctx.pace
                    others = [t for k, t in heard[-20:] if k in ("say", "pose", "page", "whisper")
                              and not t.startswith("You ")]
                    heard.clear()
                    yield from ctx.hands.take(self.key)
                    try:
                        yield from focus(ctx, frame)
                        if others:
                            room = world.room(world.player_room)
                            people = ", ".join(p.name for p in world.people_in(world.player_room)) or "nobody else"
                            history = [{"role": "user", "content": "\n".join(others[-12:])}]
                            ctx.hands.release(self.key)
                            text = yield from speak(ctx, "the MUCK", persona("the people here"),
                                                    MUCK_NOTE.format(year=year(), room=room.name, people=people),
                                                    history, "Say your one line.", max_tokens=90, max_lines=1,
                                                    thread_ok=False)
                            yield from ctx.hands.take(self.key)
                            if isValid(frame) and ctx.desktop.active is not frame:
                                yield from focus(ctx, frame)
                            if text:
                                text = text.strip().strip('"')
                                yield from ctx.hands.type_into(client.input, '"' + text)
                                typed = client.input.text()
                                yield from ctx.hands.click((client.input, QPoint(client.input.width() - 12, 8)),
                                                           action=lambda: (client.input.clear(), client.send(typed)))
                        else:
                            room = world.room(world.player_room)
                            if room.exits and random.random() < 0.5:
                                ex = random.choice(room.exits)
                                cmd = "go " + ex.names[0]
                                ctx.note(f"MUCK: {cmd}")
                            else:
                                cmd = random.choice(["look", "who", ":looks around.", ":wags.", ":sips some coffee."])
                            yield from ctx.hands.type_into(client.input, cmd)
                            typed = client.input.text()
                            yield from ctx.hands.click((client.input, QPoint(client.input.width() - 12, 8)),
                                                       action=lambda: (client.input.clear(), client.send(typed)))
                    finally:
                        ctx.hands.release(self.key)
                yield 2
        finally:
            try:
                world.line.disconnect()
            except Exception:
                pass
            if isValid(frame) and not ctx.stopping:
                frame.request_close()


LEGS = [Messengers, Roleplay, Mail, Browse, Idle, TV, RPG, Muck]
