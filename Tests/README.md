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
| `test_soulsong.py` | Soul and Song on a stand-in model: the memory banks sized to the context and classic 7:7:7 over weeks of made-up days, Interlink's three modes, and the window (talking, the raw log, the memory bars, Settings) |
| `test_qbasic.py` | QBasic Studio's interpreter: 34 programs and exactly what they print, the errors it should catch, its speed, and every built-in example |
| `test_screensavers.py` | Every screen saver runs and paints; the Claude Entertainment System plays each NES game in turn, and is the default everywhere |
| `test_persona_styles.py` | The frozen Contact Persona Styles still fit today's code (the AIM replies that failed on 26 October 2026) |
| `test_backup.py` | Backup settings, a backup and restore on a make-believe Timeline, and every part pointing at a real folder |
| `test_manual.py` | The Manual's links and pictures, its contents page, and its program list matching the computers |
| `test_standalone.py` | The launcher's APPS: each app opens and closes on its own through the stand-in host, runs its own engine there, and the APPS window starts each the right way |
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
