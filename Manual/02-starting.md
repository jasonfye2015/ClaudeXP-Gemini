# 2. Starting and stopping

## Starting it

**On Windows:** plug the SSD into a USB 3 port, open the drive and double-click **Claude Timeline.exe**. It opens
the SYSTEC Multi-Boot Manager with the Timeline's own portable Python (`Python\pythonw.exe`); nothing is installed on
the PC. `Claude Timeline.bat` does the same thing with a console window, which is handy when something won't start:
the error shows there.

**On a Mac** (Apple silicon): double-click **Claude Timeline.command**. The first time, macOS may say it can't be
opened because it's from an unidentified developer: right-click it, choose Open, and allow it once. It uses
`Python-mac`. See [On a Mac](12-mac.md) for what differs.

**On the development PC** the computers run on ClaudeXP's own `.venv` when it exists; everywhere else, on the
portable Python. You don't choose; the launcher does.

## The SYSTEC Multi-Boot Manager

![The system selection screen](images/launcher.png)

The launcher is the system selection screen: one card per computer with its picture, its one-line specs and its
OS. Click a card to open it; the card shows **LOAD THIS COMPUTER**, **LOAD AND FORMAT**, **CONFIG** and **BACK**, and
the panel beside it lists the machine's parts with a line about each. Double-clicking a card loads it.

Keys: **Left/Right** pick a card, **Enter** loads it, **F11** toggles full screen, **Esc** goes back (or leaves full
screen).

Along the bottom:

- **Your identity chip** (left): your name, your fursona's picture and your Furry Code. Click the chip to change who
  you are; click **CODES** to edit your Furry Code and YIFF Code.
- **HELP** - a short reminder of what the buttons do.
- **PROFILE** - the same identity dialog.
- **BACKUP** - [backup and restore](10-backup.md).
- **APPS** - the programs that also run on their own (below).
- **MANUAL** - this manual.
- **POWER OFF** - closes the launcher.
- **SELF-CHECK** (right) - `OK`, or how many warnings or problems it found. Click it for the list. See
  [the self-check](11-troubleshooting.md).
- The real date and time.

While a computer runs, the launcher minimises itself and comes back when the computer shuts down. If automatic
backups are on, it quietly makes one then.

## Apps: programs on their own

**APPS** opens a small window of programs that also run straight on your PC, with no computer around them:
**Kithylin AI**, **Soul and Song**, **ClaudeRPG**, **Copilot Python Studio** and **Claude QBasic Studio**. Click one
to start it in a window of its own. With no residents, mail, web or desktop running behind it, it starts quickly and
has the graphics card to itself. A tile outlined in green is already open.

They use the same things the computers do: your Companions, Kithylin chats, game saves and the programs in
`Local Storage\Projects`. So Soul and Song, Kithylin AI and ClaudeRPG won't start on their own while a computer is
running (it may have the same files open), and booting a computer asks first if one of them is open on its own. The
code studios can run alongside a computer.

On their own, Soul and Song and Kithylin AI run their models on an engine of their own, at the context their own
Settings choose. The code studios' AI uses the model, engine and context in **APPS > SETTINGS** (Automatic is the
model marked for coding, Qwen3 Coder 30B). Their settings are kept in `Profile\Standalone Apps`, apart from every
computer's.

## The first run: who are you in the Timeline?

The first time the launcher starts it asks who you are: your **name**, your **fursona** (one of the presets from the
Fur Directory, or none) and, from the fursona, default **codes**. This is `Profile\profile.json`. Every computer's
Setup takes your account from here, so Windows never asks for a name.

**Your codes matter.** The residents read your Furry Code and YIFF Code: attraction, roleplay, what you have in
common. A fursona comes with defaults; change them any time from the launcher or from FurCoder inside a computer
("Make these my codes"). Changes take effect the next time a computer starts.

## Config

**CONFIG** on a card shows the machine's spec sheet and where its **Local Storage (drive E:)** is. By default it's
the `Local Storage` folder beside the computers. Point it somewhere else if the full archive lives on another drive;
**DEFAULT** puts it back.

## Booting a computer

**LOAD THIS COMPUTER** first runs the quick part of the self-check. If something would stop this computer from
starting (a bad program name, a broken settings file, a missing Python), it tells you and offers **BOOT ANYWAY**,
**CHECK AGAIN** or **CANCEL**. Otherwise the computer starts in a window of its own.

What you'll see depends on the era; the details are in [the three computers](03-computers.md). On every one:

- **F11** toggles full screen (Alt+Tab then switches that computer's windows instead of the real PC's).
- **Ctrl+Alt+End** opens Task Manager (the real Ctrl+Alt+Del goes to the real Windows).
- The first boot after a format goes through Windows Setup and the welcome pages, prefilled from your profile.

The first time a computer needs the language model it loads it onto the graphics card, which takes a little while
(a 12B model is 7.5 GB). The AI loading box says so.

## Load and Format

**LOAD AND FORMAT** reinstalls that computer's Windows: it erases only that computer's own `data` (its account, mail,
chats, desktop, the residents' memories in that era). Your profile, your game saves, the shared archive and the other
two computers are untouched. For EPOCH-2001 the dialog also offers a **Contact Persona Style**: a frozen version of
how the residents are made and prompted (V1.0, V1.1, or "Development", whatever the code does right now). The style
stays until the next format.

Nothing is really deleted: everything a format "erases" is moved to that computer's `Recovery Backups\<date time>`
folder, outside the virtual PC, so a reset can be undone by hand.

## Shutting down

Shut a computer down from its own Start menu (Turn Off Computer, Shut down, or the power button), the way its
Windows did it. Logging off and restarting work too. The launcher comes back on its own.

Closing the computer's window with the real close box, or killing it, also works but skips the shutdown: open chats
and the living world don't get to save their last moments.

**Before you unplug the drive:** no computer running, no training running, no Kithylin AI open, and if a Claude Code
session is working in the Timeline folder, move it off the drive first. Then eject the drive from the tray.
