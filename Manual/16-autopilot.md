# 16. Kithylin Autopilot

Let Kithylin take over the computer. He sits down at EPOCH-2001 and uses it the way you would: answers whoever IMs
him on AIM, says hello to friends who come online, reads and answers his e-mail, wanders the 2001 Web, watches
ClaudeTV, logs on to the MUCK, lets his hero play ClaudeRPG, puts music on, reads comics and stories, pages through
the art in Local Storage, rereads old chat logs, writes in his LiveJournal and takes the odd break - two to four
things going at once, for as long as you let him. Think of it as a screen saver with someone home.

![Kithylin at the computer](images/autopilot.png)

## Starting him

The **Kithylin Autopilot** icon on the Windows XP desktop (or Start > All Programs). The window has two tabs:

- **What he does** - tick what he may do (hover over one for what it is), choose how long he stays, his pace and
  his voice, and click **Let Kithylin take over**. The window minimises itself out of his way.
- **Legs** - everything he knows how to do, with where it happens (in front, in the background, or all session),
  how long a stretch usually lasts and what it is. Pick one and click **Do this now** (or double-click it): he
  takes over if he isn't already and starts it straight away; whatever was in front makes way. What he's doing
  right now shows in bold.

Activities you add later come in ticked; anything you untick stays unticked.

| Activity | What he does |
|---|---|
| **AIM** | Signs on (dialling up first if the modem's idle), answers IMs, now and then IMs someone who's online. A conversation runs its course: after a handful of exchanges he lets it rest for a while. Nearly always on |
| **Roleplay sessions** | A proper scene with one buddy, 20-30 messages each way, in *asterisks* |
| **E-mail** | Opens Outlook Express, reads what's new, answers some of it, occasionally writes to someone out of the blue |
| **The Web** | Internet Explorer: a link, a read, another link, a search now and then. The adult sites on the Furry Web only if you tick them |
| **ClaudeTV** | Picks a channel with something on and watches to the end; whole movies if allowed |
| **ClaudeRPG** | Through the splash and the title to his saved hero (or a new one), with the game's own autopilot switched on |
| **The MUCK** | Logged on to PawPrints in the background: listens, says something when there's something to answer, wanders |
| **Breaks** | Coffee, the window, a few minutes away from the desk |
| **Reading comics** | FurComix Reader: picks up a comic he was reading, or browses the shelves for one, and reads it a page at a time (15-45 seconds a page), scrolling down a tall page before turning it |
| **Art portfolios** | FurFolio Reader: an artist, a folio, then the pieces in the framed viewer, 5-20 seconds each |
| **Your pictures** | Personal Image Gallery: down to a folder of your own pictures and through them |
| **Misc furry art** | Misc Furry Image Viewer: an album and its pictures |
| **Art CDs** | Fur CD Viewer: a disc off the rack, a folder on it, the pictures |
| **Old phone photos** | Camera Roll Archive: a year, a month, the photos |
| **Reading a story** | FurStory Reader: carries on where he left off, or takes a book off the shelf, and reads it - scrolling about as fast as a page can be read (around 250 words a minute) and on into the next chapter |
| **Old chat logs** | Furry Chat Logs: a service, an account, an old friend, a busy stretch of the conversation - reread at reading speed, on into the next year |
| **Exploring drive E:** | My Computer, drive E: (it spins up), down a few folders, a picture opened in the Picture and Fax Viewer and the ones beside it |
| **Reading Wikipedia** | Kiwix: a random article, scrolled through at reading speed, then a link that caught his eye |
| **Music in ClaudeAmp** | A shuffled playlist of the music found on drive E:, behind everything else (the list is found once and kept) |
| **Writing in LiveJournal** | Writes an entry about his day (what he's been doing comes into it) and posts it; his friends comment on it later |

**For how long:** until you stop him, or half an hour to eight hours. **His pace:** Relaxed, Normal or Quick.
**His voice:** which Kithylin model speaks for him (see below).

## While he's at it

- A **sky-blue glow** breathes around the edge of the screen, and a **banner** at the top says how long he's been
  there, what's open and what he's doing right now, with **Pause** and **Stop**.
- He has **his own cursor**, a sky-blue pointer that travels to what he's about to use and types at human speed.
  Your mouse stays yours.
- **Touch the mouse or keyboard and he pauses** at once (the banner says "you took the mouse"). **Resume** carries
  on where he left off; **Stop** winds everything down. Untick "Pause him when I touch the mouse" to watch without
  interrupting, and use the banner's buttons instead.
- **Stop** closes what he was in the middle of; shutting the computer down stops him too.
- Whatever he's doing in front comes to the front when he acts in it - a game or an IM won't
  cover the comic he's reading. Between actions his hands are free, so an IM gets answered in
  the middle of a story and he goes back to it.
- He keeps at most three IM windows open, closing a conversation when he lets it rest.
- The screen saver stays away while he's using the computer.

## His voice

Kithylin's words come from a Kithylin model, chosen in the panel:

- **An add-on** (`kithylin-nemomix-recent`, `kithylin-nemomix-adult`): the model trained on your own chats, riding
  on the residents' NemoMix base. The engine loads the add-ons on the base at scale 0 and switches one on just for
  his requests, so one 7.5 GB model on the card serves both sides of every conversation. The newest add-on is the
  default.
- **A whole Kithylin model** installed in the Timeline's models folder (`kithylin-v1` with `--install-timeline`).
- **The buddies' own model, asked to be Kithylin**: no training, just his character prompt. Last resort.

Who he is comes from Kithylin AI's Settings (the character and codes prompts), so changing them there changes him
here too. His replies go into the same chat logs as yours would; if you'd rather keep a run of his out of future
training, back up and format first, or read chapter 9.

## What to know

- **One graphics card.** The residents' model and his add-on share it; nothing else should be loaded on it while
  he runs - no Kithylin AI, no training.
- He uses the **real programs**, so everything he does is real: the e-mails are sent and answered, the IMs are in
  the buddies' histories, the MUCK logs it, his hero's progress is saved. The residents treat him exactly as they
  treat you, because to them he is you.
- Several buddies tend to IM him the moment he signs on. He answers them one at a time, a few seconds apart.
- **Windows 7 and 11** don't have him yet: their messengers, mail and browsers need their own legs. XP has the
  most to do and was built first.
- The Furry Log (chapter 4) records everything he does, line by line, under `AUTOPILOT`, and the panel shows the
  last of it.

## Under the hood

`ClaudeCore\claudecore\autopilot` is the engine: `engine.py` runs the legs (generators that yield seconds to wait
or a condition to wait for) and keeps two to four going - the messengers always, up to two background legs, one
foreground leg; `hud.py` is the glow, the banner and the cursor; `voice.py` asks the broker for his words with the
add-on switched on. `ClaudeXP\claudexp\autopilot\legs.py` (the messengers, mail, the Web, TV, games, the MUCK)
and `content.py` (Local Storage: comics, galleries, stories, chat logs, Explorer, Kiwix, music, LiveJournal) are
what he knows how to do on XP: one class per activity, each with a title, a line for the Legs tab and how long a
stretch lasts.
Adding an activity is one new class there; giving another computer the autopilot is an adapter with its own legs.
