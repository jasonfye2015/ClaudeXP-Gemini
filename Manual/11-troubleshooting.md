# 11. The self-check and troubleshooting

## The self-check

The launcher runs a self-check in the background every time it starts, and again, quickly, before any computer boots.
It looks for the things that have actually stopped a computer from starting, so they show up as a plain message
instead of a computer that won't load:

- **Program names Windows can't use as file names** (a colon in "Claudualties: Unknown" once stopped the XP machine
  from loading, because every program gets a `.lnk` shortcut named after it), and duplicate program keys.
- **Python syntax errors** in every program file. Only files changed since the last check are re-read; the results
  are cached in `Profile\selfcheck.json`.
- **Settings and save files that can't be read** (a half-written JSON file after a crash).
- **Leftovers of an interrupted backup or restore.**
- **Free space** on the drive.
- **The Python runtime, each computer and the language-model engine being where they should be.**
- **How long since the last backup.**

![The self-check, all clear](images/selfcheck.png)

The chip at the bottom right says **SELF-CHECK OK**, or counts **WARNINGS** (it may misbehave) or **PROBLEMS** (it
won't start, or will lose something). Click it for the list, each with a line of advice. **CHECK AGAIN** reruns it.

When you click **LOAD THIS COMPUTER** and something would stop that computer, you see it first, with **BOOT ANYWAY**,
**CHECK AGAIN** and **CANCEL**. Each computer also runs the quick checks itself as it starts.

## When something breaks

**A computer won't boot, or closes straight back to the launcher.**
Run `Claude Timeline.bat` instead of the `.exe`: the console shows the error. Look at that computer's `logs\crash.log`
(`ClaudeXP\logs`, `Claude7\logs`, `Claude11\logs`): every start is logged, and a crash leaves the Python stack of
every thread. Then the self-check's list. The usual causes: a program name with a forbidden character (fix the name
in the registry), a settings file in `data` that didn't finish writing (delete that one file; it's rebuilt), or
something missing in `Local Storage`.

**The first boot hangs for minutes, or loading a model takes forever.**
The drive is on a USB 2 port. Move it to a USB 3 port (blue, or marked SS). A model file is 7.5 GB; at 25 MB/s that's
five minutes, at 370 MB/s twenty seconds.

**The drive disappears: "location is not available", the computer freezes, training stops.**
USB selective suspend. Power Options > Change plan settings > Change advanced power settings > USB settings > USB
selective suspend setting > **Disabled**, for the plugged-in setting. Check with `powercfg /q` that the AC index reads
0. Also check the drive for errors afterwards (`chkdsk E: /f` with nothing running).

**Nobody talks: the buddies don't answer, the Web won't load, a warning sign in the tray.**
The engine isn't running or the models aren't there. Control Panel > AI Models > Engine: Start, or View Log. Check
`Local Storage\LLM Models\models` has the folders and `llama.cpp\vulkan\llama-server.exe` exists. If the engine
starts but replies are glacial, something else is on the graphics card (training, Kithylin AI, Image Creator).

**Everything is suddenly thirty times slower.**
Video memory ran out and the driver spilled into system RAM. Close whatever else uses the card; lower "models kept
loaded" or the context size in AI Models > Engine.

**Training stopped.**
Run the matching **Resume ....bat**; it carries on from the last checkpoint (every 30 minutes). If it stops again at
the same place, read the error in the console. The log is `runs\<name>\train_log.jsonl`.

**Kithylin AI shows a model greyed out.**
An add-on model needs its base in `Local Storage\LLM Models\models` (NemoMix Unleashed 12B for the NemoMix
Kithylins). If the base was deleted to save space, download its GGUF again from the address in its `info.json`.

**The desktop is missing an icon or a folder.**
Icons are files in that computer's Desktop folder; a deleted shortcut stays deleted on purpose. Make a new one from
the Start menu (right-click > Send To > Desktop on XP, or drag), or format the computer for a fresh desktop.

**Wrong fonts, boxes, or magenta where there should be a picture (Mac).**
See [On a Mac](12-mac.md). Magenta means a picture file wasn't found: usually a path with the wrong case, since the
Mac's drive is case-sensitive about nothing but Windows wasn't checking.

**A restore says it can't while the computer is running.**
That's by design. Shut the computer down and restore from the launcher.

**Starting a computer over.**
Load and Format in the launcher. Everything it removes goes to `Recovery Backups\<date time>` in that computer's
folder, so it can be undone.

## Where the settings are

| Setting | File |
|---|---|
| Who you are, your codes | `Profile\profile.json` |
| Backup settings | `Profile\backup.json` |
| Self-check cache | `Profile\selfcheck.json` |
| Where Local Storage is, per computer | `ClaudeLauncher\settings.json` |
| A computer's model choices | `<computer>\data\ai_models.json` |
| A computer's desktop layout | in `<computer>\data` |
| Kithylin AI | `ClaudeApps\kithylinai\Data\settings.json` |
| The persona style EPOCH-2001 was set up with | `ClaudeXP\data\persona_style.json` |

All of them are JSON; a broken one can be deleted and is rebuilt with defaults (you'd lose only that file's settings).
