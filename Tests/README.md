# Tests

One command checks that the Timeline still works: double-click **Run All Tests.bat**, or

```
python Tests\run.py
```

It takes about two minutes and says, line by line, what passed. The whole report is also saved as
`Tests\last run.txt`, so it can be read afterwards or handed to whoever's fixing something.

| Command | What it runs |
|---|---|
| `python Tests\run.py` | everything but the slow tests |
| `python Tests\run.py --slow` | also boots each computer in a sandbox and opens its programs |
| `python Tests\run.py --slow --all-programs` | boots each computer and opens *every* program on it |
| `python Tests\run.py qbasic soul` | only the files whose names have these words |
| `python Tests\run.py --keep` | keeps the scratch folders the tests wrote to (the path is printed) |
| `python Tests\test_qbasic.py` | one file on its own |

## What's checked

| File | What |
|---|---|
| `test_code.py` | Every Python file compiles without warnings; pyflakes finds no undefined names; the launcher's self-check finds nothing that would stop a computer |
| `test_model_threads.py` | The crash of 27-28 October 2026 can't come back: the model threads behind Soul and Song, Kithylin AI and the code studios are never let go of while running |
| `test_claudemagic.py` | Claude and Magic, the one-file game, driven in Qt WebEngine offscreen on a scratch profile: the built file matches its source, every floor is solvable and stocked (and the same from the same seed), the old game's rules hold (fights, levelling, chests, the camp, the Hall of Fame), a run saves and comes back after a reload and travels as text, the first-person view draws with WebGL, and the Timeline's window opens, takes the old Python game's saves once, and closes |
| `test_loops.py` | A model going round in circles can't spread (Kithylin's night of 28-29 October 2026): what counts as a loop and what doesn't (a chorus, a refrain, "hehe"), the engine asking for llama.cpp's DRY sampler and stopping a loop as it's written, Kithylin AI and Soul and Song keeping a reply only up to where its repeats began, and retraining never taught one |
| `test_soulsong.py` | Soul and Song on a stand-in model: the memory banks sized to the context and classic 7:7:7 over weeks of made-up days, Interlink's three modes, and the window (talking, the raw log, the memory bars, Settings) |
| `test_inner_life.py` | Soul and Song's inner life: free time (and the encyclopedia finding the right article), the beliefs record, fading memories, and their own rules changing only with your leave |
| `test_pictures.py` | Soul and Song's pictures, with no model started: the engine loading a model's vision add-on only when asked, the graphics memory counting it, a picture seen once and remembered in the Companion's own words (or a model that can't see told so), and the window - pasted, dropped, kept small, shown, and the Pictures setting |
| `test_kithylin_bots.py` | Kithylin AI on Telegram and Discord, with stand-ins and no model started: its own bots in its own words (an AI model of Kithylin, not Kithylin), each person a chat of their own answered in turn, guests named in the prompt, notes for pictures and voice messages, its windows and How to connect, and waiting in the notification area |
| `test_discord.py` | Soul and Song on Discord, with stand-ins for Discord's API and gateway: linking (the app described as an AI), who may talk (never a server's channel or a bot), the gateway (identify, heartbeats, a dead connection noticed, resuming after a drop, a refused token), reading back what came while it was away, and the window - its Discord window and How to connect, pictures, writing first where you last wrote from |
| `test_telegram.py` | Soul and Song on Telegram, with a stand-in for Telegram: linking (and the bot labelled an AI), who may talk (the user and invited guests by code, anyone else told once), listening and sending, writing first only when it should, guests left out of retraining, pictures fetched in order (and a note for voice messages), and the window answering on Telegram and listening on when closed |
| `test_web_reading.py` | Soul and Song reading the real web in free time - with the network blocked and canned answers: the sources' parsers, a book read to its end, nothing online when it's off, the fallbacks when the web is down |
| `test_qbasic.py` | QBasic Studio's interpreter: 34 programs and exactly what they print, the errors it should catch, its speed, and every built-in example |
| `test_screensavers.py` | Every screen saver runs and paints; the Claude Entertainment System plays each NES game in turn, and is the default everywhere |
| `test_persona_styles.py` | The frozen Contact Persona Styles still fit today's code (the AIM replies that failed on 26 October 2026) |
| `test_backup.py` | Backup settings, a backup and restore on a make-believe Timeline, and every part pointing at a real folder |
| `test_manual.py` | The Manual's links and pictures, its contents page, and its program list matching the computers |
| `test_standalone.py` | The launcher's APPS (Soul and Song, ClaudeRPG, Claude and Magic, the code studios): each app opens and closes on its own through the stand-in host, runs its own engine there, runs once (started again, the one open comes forward), and the APPS window starts each the right way - or brings forward the one already open |
| `test_computer_xp.py`, `_7`, `_11` | (slow) each computer booted for real in a sandbox: power on to the desktop, the Start menu, programs opening and closing, logging off, shutting down |
| `ClaudeCore\tests\` | the resident loader and the relocation check |

## The rule: tests never touch your real things

Everything a test writes goes into a scratch folder that's deleted afterwards. The computers boot with a scratch
data folder, scratch Program Files, an **empty** E: drive, no language model server, and the Bluesky watcher off.
Soul and Song's tests make their own Companions from the Companion Project's mind files. Nothing reads your chats or
opens your Companions, and nothing uses the graphics card.

Some tests need `Local Storage` (the sprite sheets, the mind files, the Persona Styles). Without it they're
**skipped**, not failed.

## Writing a test

A test is a function named `test_...` in a file named `test_*.py` here; the first line of its docstring is what the
report calls it. It fails by raising (`assert`), and skips with `support.skip("why")`. `support.py` has the rest:
`support.scratch()` for a folder to write in, `support.qapp()` and `support.pump()` for Qt, `support.catch_errors()`
for the errors Qt only prints. A file with `SLOW = True` runs only with `--slow`; `TIMEOUT = seconds` gives it longer
than the usual three minutes. Each file runs in its own process, so one that crashes outright is reported as crashed
and the rest still run.
