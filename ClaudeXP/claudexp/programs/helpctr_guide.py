"""ClaudeXP's own pages in Help and Support: what this computer is, a catalog of every program on it (built from the
program list, so it's always current), and how the people who live here - the characters the language model plays -
work: AIM buddies, the FurNet and PawPrints regulars, their memories, e-mail, LiveJournal and the AI helpers.
"""
import html

from . import installed

# Where each program sits in the catalog, and what it is. Programs not listed here go under 'Other programs' with
# their Start menu blurb.
SECTIONS = [
    ("talk", "Talking with your buddies",
     "Instant messengers and chat. All of them reach the same people, who remember you from one to the next."),
    ("web", "The Internet",
     "Dial up, browse the 2001 Web, read your mail and your friends' journals."),
    ("furry", "Furry Stuff",
     "The furry media of the time, from your archive on E:, and the residents' own directory."),
    ("office", "Office and creativity", "Documents, pictures, movies and code."),
    ("media", "Music and video", ""),
    ("games", "Games", "All in Start > Games and the desktop's Games folder."),
    ("emu", "Game emulation", "Old consoles; you bring the game files (E:\\Emulation). They're in Start > Games > "
                              "Game Emulation, and Games > Emulation on the desktop."),
    ("ai", "Your AI helpers", "Assistants you talk to directly - not characters with lives of their own."),
    ("system", "System tools and utilities", ""),
    ("other", "Other programs", ""),
]
CATALOG = {
    # talk
    "aim": ("talk", "The heart of ClaudeXP: your buddy list. Every buddy is a character with a personality, a "
                    "daily schedule, a time zone, a buddy icon and a life that moves on while you're away."),
    "msn": ("talk", "MSN Messenger 4.6 - the same buddies on Microsoft's network, with their Hotmail addresses."),
    "yim": ("talk", "Yahoo! Messenger 5.0 - the same buddies, Yahoo! style."),
    "icq": ("talk", "ICQ 2001b - everyone has a UIN, and the 'uh-oh!' is back."),
    "trillian": ("talk", "Trillian 0.71 - one window for every network; each buddy shows which one they're on."),
    "skype": ("talk", "Skype, styled as its first beta. The Call button rings and nobody picks up."),
    "kik": ("talk", "Kik, in a phone-sized window with chat bubbles."),
    "winmsgr": ("talk", "Windows Messenger 4.6, the one built into XP. It starts with Windows and keeps asking you "
                        "to sign in."),
    "irc": ("talk", "ClaudeIRC on FurNet: #furnet and friends, full of regulars who chat among themselves and "
                    "with you, and private messages."),
    "muck": ("talk", "PawPrints MUCK, a text world: walk between rooms, meet the regulars where they hang out, "
                     "page and whisper."),
    # web
    "connect": ("web", "America Online dial-up: the modem handshake, then you're online. Everything that needs "
                       "the Internet asks to connect."),
    "iexplore": ("web", "Internet Explorer 6, the default browser. The 2001 Web is written by the model as you "
                        "browse; the Furry Web's real sites come from your archive. Home page: MSN.com."),
    "navigator": ("web", "Netscape Navigator 4.79 - the same Web, with Netcenter as home."),
    "hotmail": ("web", "MSN Hotmail: you and everyone you know are @hotmail.com. Write to anyone and they answer."),
    "livejournal": ("web", "The Furry LiveJournal: everyone's journals, and your own. Buddies comment on your "
                           "posts."),
    "outlook": ("web", "Outlook Express 6 - the same mailbox as Hotmail, with Bulk Mail, Sent Items and Drafts."),
    "wab": ("web", "The Windows Address Book: everyone you know."),
    "torrent": ("web", "ClaudeTorrent - download with BitTorrent."),
    "kiwix": ("web", "Kiwix: Wikipedia offline. Read the real Wikipedia from E:\\Kiwix - search titles, random "
                     "articles, tabs. Get Content downloads up to 15 GB of it."),
    # furry
    "furdir": ("furry", "The Fur Directory: a profile for every resident - main, support and background furs, and "
                        "the user fursonas - with pictures."),
    "furlog": ("furry", "The Furry Log: a diary of everything the language model is doing, as it happens."),
    "furlocator": ("furry", "A world map with a pin where each resident lives."),
    "comix": ("furry", "Reads comics (CBR, CBZ and folders) from your archive."),
    "folio": ("furry", "Browses artists' portfolios."),
    "stories": ("furry", "Reads stories from the archive."),
    "cdviewer": ("furry", "Opens the furry art CDs and DVDs of the time."),
    "furcon": ("furry", "Convention recap discs."),
    "furvideo": ("furry", "Browses the video archive."),
    "photos": ("furry", "A gallery of your own pictures and videos in Misc Personal Image Folders on E:."),
    "miscfurry": ("furry", "The numbered albums of assorted furry pictures (Furry Media Archive\\Misc Furry Images), "
                           "as Thumbnails or Extra Large Thumbnails."),
    "mediaarchive": ("furry", "The Furry Media Archive folder on E:."),
    "miscimages": ("furry", "Your Misc Personal Image Folders folder on E:."),
    "documents": ("furry", "A gallery of your own texts and documents in Personal Texts and Docs on E:, with a "
                           "reading pane for text, web pages, Word, WordPad and PDF files."),
    "personaldocs": ("furry", "Your Personal Texts and Docs folder on E:."),
    "chatlogs": ("furry", "Years of chat logs - AIM, Yahoo!, MSN, ICQ, IRC, Second Life and more, from Gaim, Pidgin, "
                          "Trillian, Digsby and the rest - collated by service, account and buddy, with a search."),
    "camroll": ("furry", "Every photo and video in Camera Rolls on E:, by year and month in the order they were "
                         "taken, whichever backup folder they're in."),
    "tvmovies": ("furry", "Your TV and Movies folder on E:."),
    "tv": ("media", "ClaudeTV: channels made from your TV and movie files - WAGG 4 cartoons, KFUR 7 animals and "
                    "anime, KPAW 9 movies, KANI 11 anime with the Orangina commercials, KHAH 13 comedy - with a TV "
                    "Guide."),
    # office
    "gemini_word": ("office", "Word processing, Office XP style."),
    "gemini_excel": ("office", "Spreadsheets with formulas."),
    "gemini_powerpoint": ("office", "Slide shows."),
    "gemini_outlook": ("office", "Mail, calendar, tasks and contacts."),
    "gemini_access": ("office", "Databases."),
    "gemini_publisher": ("office", "Flyers and page layout."),
    "gemini_photo": ("office", "Photo editing."),
    "gemini_draw": ("office", "Vector illustration."),
    "gemini_acrobat": ("office", "Reads and prints PDF files."),
    "gemini_distiller": ("office", "Makes PDF files."),
    "paint": ("office", "Paint."),
    "wordpad": ("office", "WordPad."),
    "notepad": ("office", "Notepad."),
    "moviemaker": ("office", "Windows Movie Maker 1.1: storyboard your clips and pictures, add music, and save a "
                             "real .wmv movie."),
    "pystudio": ("office", "Copilot Python Studio: write and run Python offline, with an AI Helper."),
    # media
    "wmp": ("media", "Windows Media Player 8 with visualizations, a Media Library and skins."),
    "claudeamp": ("media", "ClaudeAmp - it really whips the llama's ass. Plays music and video."),
    "realplayer": ("media", "RealPlayer 8 Basic. Plays your files; the Radio Tuner's streams buffer forever."),
    "quicktime": ("media", "QuickTime Player 5. Plays your files, and asks you to upgrade to Pro every time."),
    "flash": ("media", "Macromedia Flash Player: plays .swf movies and games."),
    "sndvol": ("media", "Volume Control: ClaudeXP's volume and balance (they really set its level in Windows' "
                              "mixer), plus Wave for the system sounds. Click the tray speaker for a quick slider."),
    "sndrec": ("media", "Sound Recorder."),
    # games
    "rpg": ("games", "ClaudeRPG: a cozy, endless dungeon adventure."),
    "claudecraft": ("games", "ClaudeCraft: a block-building world in 3D. Walk, fly, break and place blocks; your world "
                             "is saved."),
    "furcadia": ("talk", "Claudecadia: a Furcadia-style furry graphical chat world. Your AIM buddies log in as furres; hop around "
                          "Willowmere Commons and 13 dreams to discover, sit, chat, emote, whisper (/name message) and open treasure "
                          "chests."),
    "claudeggle": ("games", "Claudeggle: a Peggle-style ball-and-peg game - twelve levels, clear the orange pegs in ten "
                            "balls, with green-peg powers, a free-ball bucket and Extreme Fever."),
    "claudemagic": ("games", "Claude and Magic: a grid-based dungeon crawler for a party of four - twenty floors, "
                             "an automap, loot and gear, merchant camps every five floors, and the Lich King at the "
                             "bottom. When the whole party falls, the run starts over."),
    "claudeanoid": ("games", "Claudeanoid: an Arkanoid-style block breaker - 40 rounds, silver and gold blocks, "
                             "Expand/Laser/Catch/Slow/Disruption/Player/Break capsules, and a top-ten high score table."),
    "fractals": ("games", "Claude Fractal Generator: Mandelbrot, Julia, Burning Ship, Tricorn, Multibrot and Newton "
                          "fractals with palettes and click-to-zoom; Save Image puts them in E:\\Created Files."),
    "terrain": ("games", "Claude Terrain Generator: fractal landscapes like VistaPro - roughness, mountains, water, "
                         "snow line, forests, sky and camera; Save Image puts them in E:\\Created Files."),
    "claudejeweled": ("games", "Claudejeweled: a Bejeweled-style gem matcher - Classic, Action and Zen modes, "
                               "Flame and Star Gems and Hypercubes. H shows a hint, P pauses."),
    "scorched": ("games", "Scorched Claude: a Scorched Earth-style artillery game for 2-10 tanks, people or "
                          "computer players. Arrows aim, Space fires, Tab picks a weapon; shop between rounds."),
    "claudecity": ("games", "ClaudeCity: build a city in the spirit of SimCity Classic - zones, power, traffic, "
                            "budgets, disasters and six scenarios."),
    "claudeablo": ("games", "Claudeablo: a Diablo-style dungeon crawler - fifty random levels down to Diablo, with "
                            "loot, spells, town portals and shops. F1 in the game explains the controls."),
    "claudequest": ("games", "ClaudeQuest: lead a wolf pack through the seasons - hunt, raise pups, mark your territory, "
                             "and survive rivals, bears, cougars and winter. F1 in the game explains the keys."),
    "doom": ("games", "Doom (bring your own WAD)."),
    "doom2": ("games", "Doom II."),
    "wolf3d": ("games", "Wolfenstein 3D."),
    "heretic": ("games", "Heretic."),
    "hexen": ("games", "Hexen."),
    "ibackgammon": ("games", "Internet Backgammon on the Zone - matched with a buddy who's awake, who remembers the "
                             "game afterwards."),
    "icheckers": ("games", "Internet Checkers on the Zone."),
    "ihearts": ("games", "Internet Hearts on the Zone."),
    "ireversi": ("games", "Internet Reversi on the Zone."),
    "ispades": ("games", "Internet Spades on the Zone."),
    # ai
    "claudeai": ("ai", "ClaudeAI: chat with your local AI - it can see pictures and think before it answers."),
    "copilotai": ("ai", "CopilotAI: chat with the local models by text or voice."),
    "copilotvoice": ("ai", "Talk out loud and hear the answer."),
    "imagecreator": ("ai", "Makes pictures with Stable Diffusion on your graphics card."),
    "clippy": ("ai", "Clippy, back from the dead - and with a language model behind him, more helpful (and more "
                     "annoying) than ever. He has a real off switch."),
    "neko": ("ai", "Neko, the classic desktop cat: chases your mouse pointer and naps when it catches it."),
    "copilotwidgets": ("ai", "Desktop widgets: clock, calendar, weather, TV guide, your Hotmail inbox and more."),
    # system
    "antivirus": ("system", "ClaudeShield AntiVirus: Auto-Protect, scans and LiveUpdate."),
    "adaware": ("system", "Ad-aware 5.62: finds the spyware that crept in, and the tracking cookies from your "
                          "browsing."),
    "winupdate": ("system", "Windows Update."),
    "defrag": ("system", "Disk Defragmenter."),
    "cleanmgr": ("system", "Disk Cleanup."),
    "sysrestore": ("system", "System Restore: put Windows' settings back the way they were."),
    "msconfig": ("system", "System Configuration Utility (type msconfig in Run): choose what starts with Windows on "
                           "the Startup tab, and boot options like /NOGUIBOOT and /SOS."),
    "activate": ("system", "Activate Windows - makes the key in the notification area go away."),
    "stylexp": ("system", "StyleXP: visual styles for Windows XP (and a trial that nags)."),
    "nero": ("system", "Nero Burning ROM."),
    "alcohol120": ("system", "Alcohol 120%."),
    "winrar": ("system", "WinRAR."),
    "winzip": ("system", "WinZip."),
}
for _key in ("nes", "snes", "gb", "gbc", "gba", "gen", "sms", "gg", "n64", "apple2"):
    CATALOG.setdefault(_key, ("emu", ""))
for _key in ("freecell", "hearts", "minesweeper", "pinball", "solitaire", "spider", "blockfall", "golf", "rodent",
             "taipei", "tripeaks", "jezzball", "skifree"):
    CATALOG.setdefault(_key, ("games", ""))
for _key in ("mycomputer", "calc", "cmd", "charmap", "msinfo", "tour"):
    CATALOG.setdefault(_key, ("system", ""))


def catalog_page():
    from . import PROGRAMS
    gone = installed.removed()
    by_section = {k: [] for k, _t, _d in SECTIONS}
    for p in PROGRAMS:
        if not p.listed:
            continue
        section, text = CATALOG.get(p.key, ("other", ""))
        by_section[section].append((p, text or p.blurb))
    total = sum(len(v) for v in by_section.values())
    out = [f"<h1>Programs on this computer</h1><p>{total} programs. Click a name to start it. Most are also in "
           "<b>Start &gt; All Programs</b>; the Start menu folder is shown in grey.</p><p>"
           + " &middot; ".join(f'<a href="#{k}">{t}</a>' for k, t, _d in SECTIONS if by_section[k]) + "</p>"]
    for key, title, desc in SECTIONS:
        items = by_section[key]
        if not items:
            continue
        out.append(f'<a name="{key}"></a><h2>{title}</h2>' + (f"<p>{desc}</p>" if desc else ""))
        rows = []
        for p, text in sorted(items, key=lambda it: it[0].name.lower()):
            where = f' <font color="#808080">({html.escape(p.group)})</font>' if p.group else ""
            name = (f'<b>{html.escape(p.name)}</b> <font color="#A00000">(removed - see Add or Remove Programs)'
                    f'</font>' if p.key in gone else f'<a href="launch:{p.key}"><b>{html.escape(p.name)}</b></a>')
            rows.append(f'<tr><td valign="top" width="28"><img src="icon:{p.key}" width="24" height="24"></td>'
                        f'<td valign="top">{name}{where}<br>{html.escape(text)}</td></tr>')
        out.append(f'<table cellpadding="3">{"".join(rows)}</table>')
    return "".join(out)


def _counts():
    """Live numbers for the people pages."""
    from ..paths import ROOT
    from .people import load_json
    from .. import life
    sim = life.get()
    aim = len(sim.buddies) if sim is not None else 0
    irc = len(load_json(ROOT / "Program Files" / "ClaudeIRC" / "regulars.json", {}).get("regulars", []))
    muck = len(load_json(ROOT / "Program Files" / "ClaudeMUCK" / "world" / "regulars.json", {}).get("regulars", []))
    everyone = len(sim.people) if sim is not None else 0
    folder = ROOT / "Program Files" / "The Fur Directory" / "residents"
    profiles = sum(1 for _ in folder.glob("*.json")) if folder.is_dir() else 0
    from ..paths import DATA
    journals = sum(1 for _ in (DATA / "journals").glob("*.json")) if (DATA / "journals").is_dir() else 0
    return aim, irc, muck, everyone, profiles, journals


def _models_table():
    try:
        from .. import ai_models
        rows = []
        for role, label, what in ai_models.ROLES:
            model = ai_models.model_for(role) or "(none installed)"
            rows.append(f"<tr><td><b>{html.escape(label)}</b></td><td>{html.escape(str(model))}</td>"
                        f"<td>{html.escape(what)}</td></tr>")
        names = ", ".join(m.id for m in ai_models.installed()) or "none yet"
        return (f'<table cellpadding="3"><tr><th align="left">Job</th><th align="left">Model</th>'
                f'<th align="left">Used for</th></tr>{"".join(rows)}</table><p>Installed models: {names}.</p>')
    except Exception:
        return "<p>Open <a href='launch:aimodels'>Control Panel &gt; AI Models</a> to see which model does what.</p>"


def people_page():
    aim, irc, muck, everyone, profiles, journals = _counts()
    return f"""<h1>The people who live here</h1>
<p>ClaudeXP's residents are characters played by a language model running on this computer. Each one has a
personality (written as a 'persona'), a schedule - they sleep, work and go out - and a life that keeps moving
whether or not you're around. Right now:</p>
<table cellpadding="3">
<tr><td><b>{aim}</b></td><td>AIM buddies - the main furs, with their own instant-messenger accounts</td></tr>
<tr><td><b>{irc}</b></td><td>FurNet IRC regulars</td></tr>
<tr><td><b>{muck}</b></td><td>PawPrints MUCK regulars (many are the same furs as on IRC)</td></tr>
<tr><td><b>{everyone}</b></td><td>people you can e-mail (everyone above, each @hotmail.com)</td></tr>
<tr><td><b>{profiles}</b></td><td>profiles in <a href="launch:furdir">The Fur Directory</a></td></tr>
<tr><td><b>{journals}</b></td><td>diaries being kept (one per resident who has done or talked about anything)</td></tr>
</table>
<h2>The kinds of accounts</h2>
<p><b>Main furs (AIM buddies)</b> have instant-messenger accounts and talk to you directly, on
<a href="launch:aim">ClaudeAIM</a> and every other messenger. <a href="help:people-aim">More...</a></p>
<p><b>Support furs</b> are the regulars you meet on <a href="launch:irc">FurNet IRC</a> and the
<a href="launch:muck">PawPrints MUCK</a>: they chat among themselves, answer you, and can be e-mailed.
<a href="help:people-regulars">More...</a></p>
<p><b>Background furs</b> are the admins, bots, idlers and lurkers - the crowd. They rarely talk to you.</p>
<p><b>User fursonas</b> are the characters offered when Windows is set up; yours is marked in the Fur Directory,
and the residents who know your fursona treat you that way. <a href="help:people-you">More...</a></p>
<h2>What makes them feel alive</h2>
<p><a href="help:people-memory">How they remember</a> &middot; <a href="help:people-mail">E-mail and Hotmail</a>
&middot; <a href="help:people-lj">LiveJournal and FurAffinity</a> &middot;
<a href="help:people-assistants">The AI helpers (not residents)</a> &middot;
<a href="help:claudexp-ai">How the language models work</a></p>"""


GUIDE = {
    "claudexp-about": ("About ClaudeXP", "claudexp", """
<p>ClaudeXP is a Windows XP computer from the autumn of 2001 - the desktop, the sounds, the dial-up modem, the
nags - with one difference: it's lived in. Your buddies on AIM, the regulars on FurNet IRC and the PawPrints MUCK,
the people writing LiveJournals and posting on FurAffinity are characters played by a language model that runs on
this computer. Nothing goes to the real Internet.</p>
<h2>Start here</h2>
<p>&#9656; <a href="help:claudexp-new">Recently added</a> - the newest games and features.<br>
&#9656; <a href="help:claudexp-catalog">Programs on this computer</a> - everything there is, by kind.<br>
&#9656; <a href="help:claudexp-games">ClaudeXP's own games</a> - what each one is and how to play.<br>
&#9656; <a href="help:people">The people who live here</a> - who they are and how they work.<br>
&#9656; <a href="help:claudexp-ai">How the language models work</a> - and what to do if nobody answers.<br>
&#9656; <a href="help:claudexp-nags">The 2001 nags</a> - activation, cleanup, upgrade offers, and how to quiet them.<br>
&#9656; <a href="help:claudexp-files">Where things are kept</a><br>
&#9656; <a href="help:claudexp-storage">What's on drive E:</a> - check what's installed, and get the language models.<br>
&#9656; <a href="launch:thanks">Thanks</a> - who made ClaudeXP, and the software and models it's built on.</p>
<h2>Drives</h2>
<p><b>C:</b> is Windows and your documents. <b>E:</b> is the external drive (Local Storage on the real computer):
the language models, the Furry Media Archive, TV and Movies, emulation games and WADs. Printing goes to
<b>E:\\Printed</b> as PDF files.</p>"""),
    "claudexp-new": ("Recently added", "claudexp", """
<h2>New games</h2>
<p>All in <b>Start &gt; Games</b> and the desktop's <b>Games</b> folder (see
<a href="help:claudexp-games">ClaudeXP's own games</a>):
<a href="launch:claudeggle">Claudeggle</a> (aim, shoot, clear the orange pegs),
<a href="launch:claudejeweled">Claudejeweled</a> (swap gems, line up three),
<a href="launch:scorched">Scorched Claude</a> (tanks and very angry physics),
<a href="launch:claudecity">ClaudeCity</a> (build a city),
<a href="launch:claudeablo">Claudeablo</a> (fifty levels down to Diablo),
<a href="launch:claudequest">ClaudeQuest</a> (lead a wolf pack).</p>
<p>And <a href="launch:furcadia">Claudecadia</a>, a furry graphical chat world, in <b>Social Networking</b>.</p>
<h2>On the desktop and Start menu</h2>
<ul><li><b>Start &gt; All Programs &gt; Social Networking</b> holds every messenger, ClaudeIRC, ClaudeMUCK and
LiveJournal - and Claudecadia.</li>
<li><b>Games</b> now holds a <b>Windows Games</b> folder (Solitaire, FreeCell, Minesweeper, Pinball,
JezzBall, Rodent's Revenge, the Internet games and the rest) and the emulators - <b>Game Emulation</b> on the Start menu, <b>Emulation</b> on the
desktop.</li>
<li>The notification area hides icons you haven't used - see <a href="help:taskbar">The notification area and
taskbar</a> - and the speaker has a volume slider and the <a href="launch:sndvol">Volume Control</a> mixer.</li>
<li><b>Alt+Tab</b> switches windows while ClaudeXP is full screen.</li>
<li><b>Log Off</b> offers <b>Switch User</b>, which keeps your programs open.</li>
<li><a href="launch:msconfig">msconfig</a> chooses what starts with Windows.</li>
<li>A <b>Loading AI Model</b> box shows progress the first time a model loads.</li>
<li><a href="launch:tv">ClaudeTV</a> has <b>KANI 11</b>, an anime channel with the Orangina commercials.</li></ul>"""),
    "claudexp-games": ("ClaudeXP's own games", "claudexp", """
<p>Games made for ClaudeXP, in the spirit of the classics. They're in <b>Start &gt; Games</b> and the desktop's
<b>Games</b> folder; most remember your progress or best scores.</p>
<table cellpadding="4">
<tr><td valign="top"><a href="launch:claudeggle"><b>Claudeggle</b></a></td><td>Peggle-style. Aim the launcher with
the mouse and click to shoot; clear every orange peg in ten balls. Green pegs set off the level's power (Super
Guide, Multiball, Fireball, Spooky Ball, Zap), the purple peg is worth 500, the moving bucket gives the ball back,
and the last orange peg sets off Extreme Fever. Twelve levels.</td></tr>
<tr><td valign="top"><a href="launch:claudejeweled"><b>Claudejeweled</b></a></td><td>Bejeweled-style. Swap two
neighbouring gems to line up three or more. Four makes a Flame Gem, an L or T a Star Gem, five a Hypercube.
Classic, Action (a draining bar) and Zen modes. H for a hint, P to pause.</td></tr>
<tr><td valign="top"><a href="launch:scorched"><b>Scorched Claude</b></a></td><td>Scorched Earth-style artillery for
2-10 tanks, people or computer players. Left/Right aim, Up/Down power, Tab picks a weapon, Space fires, A/D drive
with fuel; shop for nukes, MIRVs, napalm and shields between rounds.</td></tr>
<tr><td valign="top"><a href="launch:claudecity"><b>ClaudeCity</b></a></td><td>SimCity Classic-style city building:
zone, power, roads and rails, budgets, disasters and six scenarios.</td></tr>
<tr><td valign="top"><a href="launch:claudeablo"><b>Claudeablo</b></a></td><td>A Diablo-style dungeon crawler - fifty
random levels down to Diablo, loot, spells, town portals and shops. F1 for the controls.</td></tr>
<tr><td valign="top"><a href="launch:claudequest"><b>ClaudeQuest</b></a></td><td>Lead a wolf pack through the
seasons: hunt, raise pups, mark territory, survive rivals and winter. F1 for the keys.</td></tr>
<tr><td valign="top"><a href="launch:claudecraft"><b>ClaudeCraft</b></a></td><td>Block building in 3D: walk, fly,
break and place blocks. Your world is saved.</td></tr>
<tr><td valign="top"><a href="launch:rpg"><b>ClaudeRPG</b></a></td><td>A cozy, endless dungeon adventure.</td></tr>
</table>"""),
    "claudexp-ai": ("How the language models work", "claudexp", """
<p>Everyone's words come from language models that ClaudeXP runs itself with <b>llama.cpp</b> on the real
computer's graphics card - no Ollama, nothing online. The models live in <b>E:\\LLM Models</b>.</p>
<h2>Who does what</h2>
<p>Each job can have its own model (change them in <a href="launch:aimodels">Control Panel &gt; AI Models</a>, which
also shows live activity):</p>
{models}
<h2>One thing at a time</h2>
<p>There's one graphics card, so requests wait in a queue, most urgent first: something you're waiting on (an IM
reply, a web page), then people answering you in a room, then ambient chatter, then background upkeep (diaries,
e-mail, catching up after the PC was off). The Task Manager's CPU graph climbs while the model is 'thinking',
and the hard-disk light by the clock flickers.</p>
<h2>Buying time</h2>
<p>When a big batch of background work piles up - say, everyone's lives catching up after the PC was off for a
day - Windows plays along: <a href="launch:winupdate">Windows Update</a>, a
<a href="launch:antivirus">virus scan</a>, an <a href="launch:adaware">Ad-aware</a> spyware scan or
<a href="launch:defrag">Disk Defragmenter</a> starts, and doesn't finish until the work is done.</p>
<h2>Watching it work</h2>
<p><a href="launch:furlog">The Furry Log</a> lists every request the model handles: who asked, what for, how long it
took.</p>
<h2>Without models</h2>
<p>ClaudeXP works without models too. A warning sign by the clock says they're missing - click it to download them.
Meanwhile your buddies show as <b>Away</b> and send an away message, IRC regulars are 'away from keyboard', MUCK
players are idle, and model work (e-mail replies, LiveJournal comments, diaries) waits instead of failing; it picks
up again by itself once models are in place - no need to log off. See
<a href="help:claudexp-storage">What's on drive E:</a> and <a href="help:slow-buddies">My buddies don't answer</a>.</p>"""),
    "claudexp-nags": ("The 2001 nags (and how to quiet them)", "claudexp", """
<p>Windows XP in 2001 came with a lot of software that wanted your attention. ClaudeXP keeps the nostalgia - and
lets you turn each one off:</p>
<table cellpadding="4">
<tr><td valign="top"><b>Activate Windows</b></td><td>A key by the clock and a balloon at logon until you activate.
Click the key and go through the <a href="launch:activate">Activation Wizard</a> once (over the Internet or 'by
phone'), and it's gone for good. It never locks you out.</td></tr>
<tr><td valign="top"><b>Desktop Cleanup Wizard</b></td><td>Every 60 days, 'There are unused icons on your desktop'.
Turn it off in Display Properties &gt; Desktop &gt; Customize Desktop.</td></tr>
<tr><td valign="top"><b>Windows Messenger</b></td><td>Starts with Windows and asks you to sign in. Right-click its
icon and untick 'Run this program when Windows starts', or remove it in
<a href="launch:arp">Add or Remove Programs</a> &gt; Add/Remove Windows Components.</td></tr>
<tr><td valign="top"><b>RealPlayer</b></td><td>Wants to be your default player, offers RealPlayer Plus, and keeps
RealTray running. Exit RealTray from its menu, or remove RealPlayer.</td></tr>
<tr><td valign="top"><b>QuickTime</b></td><td>'Upgrade to QuickTime Pro' every time, and qttask asking for its file
associations back. Remove QuickTime to make it stop.</td></tr>
<tr><td valign="top"><b>StyleXP</b></td><td>A trial that reminds you it's a trial.</td></tr>
<tr><td valign="top"><b>Checking file system on C:</b></td><td>After ClaudeXP crashes or is stopped, the next boot
checks the disk. Press any key during the 10-second countdown to skip it, or Esc during the check.</td></tr>
<tr><td valign="top"><b>Clippy</b></td><td>It looks like you're reading Help! Right-click him to hide him, or turn
him off in Control Panel &gt; Office Assistant.</td></tr>
</table>"""),
    "claudexp-files": ("Where things are kept", "claudexp", """
<p>On the real computer, everything ClaudeXP remembers is in its <b>data</b> folder: your account, the residents'
diaries, your mail, your LiveJournal, game statistics, program settings. Your documents are on drive C:
(<b>data\\Drive C</b>).</p>
<p>Reinstalling Windows (System Recovery) never deletes anything outright: what it erases is moved to
<b>Recovery Backups</b>. The external drive E: (<b>Local Storage</b>) is never touched by Setup.</p>
<p><a href="launch:sysrestore">System Restore</a> can put Windows' settings back; it doesn't change your documents,
mail or what anyone remembers.</p>"""),
    "claudexp-web": ("The 2001 Web, Hotmail and LiveJournal", "web", """
<p><b>The made-up Web.</b> Type any address and the language model writes the page as it would have looked in
October 2001 - links included. Pages are kept, so they look the same next time (Internet Options &gt; Delete Files
has them written fresh). The residents have homepages on FurryCities that reflect their lives.</p>
<p><b>The Furry Web.</b> Real furry websites from your archive (FurAffinity, Housepets!, Hardblush, YiffStar and
more) open in their original form. The residents are active on FurAffinity, with your own userpage there too.</p>
<p><b>MSN Hotmail</b> (<a href="launch:hotmail">www.hotmail.com</a>) is your mailbox; Outlook Express shows the same
mail. <b>LiveJournal</b> (<a href="launch:livejournal">www.livejournal.com</a>) has everyone's journals and yours.</p>"""),
    "people-aim": ("AIM buddies (main furs)", "people", """
<p>Your AIM buddies are the residents you know best. Each has a screen name, a buddy icon, a persona, a time zone
and a sleep schedule - they sign on when they wake up, go away for work or dinner, and sign off at bedtime.</p>
<ul><li><b>Same people, every messenger.</b> MSN, Yahoo!, ICQ, Trillian, Skype, Kik and Windows Messenger reach the
same buddies with each network's style of handle; they're online on all of them at once, and remember what you
said on any of them.</li>
<li><b>They reach out.</b> When something happens in their life, a buddy may IM you about it - or, if you're not
around, send an e-mail.</li>
<li><b>They play.</b> The Zone's Internet games match you with a buddy who's awake; they chat with the Zone's
phrases and remember how it went.</li>
<li><b>They read pictures.</b> Send a picture and a model that can see describes it to them.</li></ul>"""),
    "people-regulars": ("FurNet and PawPrints regulars (support and background furs)", "people", """
<p>The regulars live on <a href="launch:irc">FurNet IRC</a> and the <a href="launch:muck">PawPrints MUCK</a>. Each
keeps their own hours (shown in their Fur Directory profile) and their favourite channels or rooms.</p>
<ul><li>They talk among themselves - ambient chatter keeps the channels moving - and answer when you talk to them
or private-message them.</li>
<li>Ops and wizards keep order; bots and idlers mostly sit there, as they did.</li>
<li>Everyone has a Hotmail address, so you can e-mail any regular, and they'll write back in their own voice once
they're awake.</li>
<li>Their profiles - species, colours, where they live - are in <a href="launch:furdir">The Fur Directory</a>, and
the <a href="launch:furlocator">Proximity Locator</a> puts them on a map.</li></ul>"""),
    "people-memory": ("How they remember", "people", """
<p>Every resident keeps a <b>diary</b> - short dated notes about their own life and about talking with you. Whatever
program you use, the recent notes are given to the model with their persona, so what you said on IRC is remembered
on AIM, and an e-mail can come up in the MUCK.</p>
<ul><li><b>Life goes on.</b> About once an hour while the PC is on, someone's life moves forward: a new diary note
about work, a con, a purchase, a small drama.</li>
<li><b>Catching up.</b> If the PC was off for a while, a few notes are written when you log on - that's when
Windows Update or a scan appears, to cover for the work.</li>
<li><b>Quiet talks.</b> A conversation that goes quiet is summarised into the diary.</li>
<li><b>No invented history.</b> They're told not to make up things you did together that aren't in their notes.</li>
<li>Even at 'It's now safe to turn off your computer', their lives keep moving.</li></ul>"""),
    "people-mail": ("E-mail with the residents", "people", """
<p>Everyone is on MSN Hotmail - you're <b>yourname@hotmail.com</b>, and so is every buddy and regular (the Address
Book in Hotmail or Outlook Express lists them all). Write to anyone and they answer a few minutes later, in
character, once they're awake.</p>
<p>The inbox fills the way it did in 2001: buddies forward jokes and chain letters to everyone they know, group
e-mails between friends land with you on CC (Reply All, and everyone answers), Hotmail Staff and the weekly
newsletter drop in, and spam - mostly caught in Bulk Mail - tries its luck. The envelope by the clock turns yellow
when mail is waiting.</p>"""),
    "people-lj": ("LiveJournal and FurAffinity", "people", """
<p><b>LiveJournal.</b> A resident's journal is their diary - the same notes that come up on AIM - with a mood and
the music they were playing. Visit a journal that's nearly empty and its owner writes a few older entries. Post in
your own journal (Update Journal) and a few buddies come by to comment; comment on theirs and they answer. Each
reply is e-mailed to you, as LiveJournal did.</p>
<p><b>FurAffinity.</b> The residents use the Furry Web's FurAffinity while you're logged on: now and then one of
them favourites some art, shouts on a friend's page, comments on a picture, writes a journal or shares a link. Main
furs are the most active; background furs mostly just favourite art.</p>"""),
    "people-you": ("You and your fursona", "people", """
<p>When Windows was set up you chose a name and, if you liked, a fursona from the presets. Your fursona's profile is
in <a href="launch:furdir">The Fur Directory</a> (marked as yours), and the residents who know it treat you
accordingly - close friends know more about you than people who've only seen you around.</p>
<p>Your account name and picture are in <a href="launch:accounts">User Accounts</a>; your online handle is the one
the residents use on every network.</p>"""),
    "people-assistants": ("The AI helpers", "people", """
<p>Some programs give you the language model directly, without a character's life around it:</p>
<ul><li><a href="launch:claudeai">ClaudeAI</a> - a chat assistant that can see pictures and think before answering.</li>
<li><a href="launch:copilotai">CopilotAI</a> and <a href="launch:copilotvoice">Copilot Voice</a> - chat by text or
speech.</li>
<li><a href="launch:imagecreator">Copilot Image Creator</a> - pictures from a description, made on your graphics
card.</li>
<li><a href="launch:pystudio">Copilot Python Studio</a> - its AI Helper writes and explains code.</li>
<li><a href="launch:clippy">Clippy</a> - the Office Assistant, now with a language model. Still Clippy.</li></ul>
<p>And one who isn't AI at all: <a href="launch:neko">Neko</a>, the desktop cat, who just wants your mouse pointer.</p>"""),
}


def _storage_parts():
    """(name, present?, what uses it, where it goes) for each part of drive E: (Local Storage)."""
    from ..explorer.vfs import local_storage
    from .. import llm_server, llm_setup
    e = local_storage()

    def any_dir(*names):
        return any((e / n).is_dir() and any((e / n).iterdir()) for n in names)
    models = [it for it in llm_setup.MANIFEST if it["kind"] == "model"]
    have = [it for it in models if llm_setup.installed(it)]
    engine = llm_server.find_engine() is not None
    lm = e / "LLM Models"
    return [
        ("Language model engine (llama.cpp)", engine, "Everything that talks: buddies, IRC, the MUCK, the made-up Web, "
         "ClaudeAI, Clippy's chat", "E:\\LLM Models\\llama.cpp\\vulkan"),
        (f"Language models ({len(have)} of {len(models)} known)", bool(have), "The residents' voices, their diaries, "
         "e-mail replies, LiveJournal, the AI helpers", "E:\\LLM Models\\models"),
        ("Furry Media Archive", any_dir("Furry Media Archive"), "FurComix, FurFolio, the story reader, the CD viewers, "
         "the Furry Video Browser, and the Furry Web's real sites (Website Rips)", "E:\\Furry Media Archive"),
        ("TV and Movies", any_dir("TV and Movies"), "ClaudeTV and the TV Guide", "E:\\TV and Movies"),
        ("Misc Personal Image Folders", any_dir("Misc Personal Image Folders"), "The Personal Image Gallery",
         "E:\\Misc Personal Image Folders"),
        ("Personal Texts and Docs", any_dir("Personal Texts and Docs"), "The Personal Document Gallery",
         "E:\\Personal Texts and Docs"),
        ("Emulation games", any_dir("Emulation"), "The NES, SNES, Game Boy, Genesis, N64 and Apple ][ emulators",
         "E:\\Emulation\\<system> (Roms)"),
        ("WADs", any_dir("WADs"), "Doom, Doom II, Wolfenstein 3D, Heretic and Hexen", "E:\\WADs"),
        ("Offline Wikipedia (Kiwix)", any((e / "Kiwix").glob("*.zim")) if (e / "Kiwix").is_dir() else False,
         "Kiwix (its Get Content page downloads it)", "E:\\Kiwix"),
        ("Python runtime", (e / "Python Studio" / "python312" / "python.exe").is_file(),
         "Running programs in Copilot Python Studio", "E:\\Python Studio\\python312"),
        ("FFmpeg", (e / "Python Studio" / "ffmpeg" / "ffmpeg.exe").is_file(),
         "Saving movies in Windows Movie Maker; converting media in Python Studio", "E:\\Python Studio\\ffmpeg"),
        ("Picture generator", (lm / "image-gen" / "models").is_dir() and any((lm / "image-gen" / "models").iterdir())
         if (lm / "image-gen" / "models").is_dir() else False, "Copilot Image Creator",
         "E:\\LLM Models\\image-gen"),
        ("Voices", (lm / "voice" / "models").is_dir() and any((lm / "voice" / "models").iterdir())
         if (lm / "voice" / "models").is_dir() else False, "Copilot Voice (speech in and out)",
         "E:\\LLM Models\\voice"),
    ]


def storage_page():
    rows = []
    missing = 0
    for name, ok, uses, where in _storage_parts():
        missing += not ok
        mark = "<font color='#207020'><b>Installed</b></font>" if ok else "<font color='#C02010'><b>Missing</b></font>"
        rows.append(f"<tr><td valign='top'><b>{html.escape(name)}</b><br><font color='#666'>{html.escape(where)}"
                    f"</font></td><td valign='top'>{mark}</td><td valign='top'>{html.escape(uses)}</td></tr>")
    summary = ("Everything is in place." if not missing else
               f"{missing} part{'s are' if missing != 1 else ' is'} missing. ClaudeXP still runs; only the programs "
               "listed beside each missing part are affected.")
    return f"""<h1>What's on drive E:</h1>
<p>Drive E: is the external drive - the <b>Local Storage</b> folder beside ClaudeXP on the real computer. It holds the
big things: the language models, your media archive and game files. {summary}</p>
<table cellpadding="4" width="100%"><tr><th align="left">Part</th><th align="left">Status</th>
<th align="left">Used by</th></tr>{"".join(rows)}</table>
<h2>Getting the language models</h2>
<p><a href="launch:aimodels-setup">Open the AI Model Setup Assistant</a> (Control Panel &gt; AI Models &gt; Setup). It
downloads the engine and models and installs them, resuming if interrupted and checking every file. If a download
doesn't work, point it at copies you already have, or give it another web address.</p>
<h2>Everything else</h2>
<p>The archive, TV and movies, games and WADs are your own files: copy them into the folders shown above on the
real computer (Local Storage\\README.txt describes each one). Programs notice them the next time they open.</p>"""


def guide_article(aid):
    """(title, html) for a guide article, filling in anything live."""
    if aid == "claudexp-storage":
        return "What's on drive E:", storage_page()
    if aid == "claudexp-catalog":
        return "Programs on this computer", catalog_page()
    if aid == "people":
        return "The people who live here", people_page()
    title, _topic, body = GUIDE[aid]
    if "{models}" in body:
        body = body.replace("{models}", _models_table())
    return title, body
