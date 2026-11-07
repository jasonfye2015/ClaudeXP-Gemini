ClaudeGames - games every computer in the Claude Timeline can play
===================================================================

Each game is a Python package here (e.g. claudeggle/), the same on every computer. Only the window around it
changes: each OS draws it in its own style (XP Luna, 7 Aero, 11 Mica).

  Saves/       progress and high scores, shared by every era (not in git: they're yours)

How a shared program talks to the computer it's on - never by importing the OS's own modules, always through
ClaudeCore's host (ClaudeCore/claudecore/host.py):

    from claudecore import host
    host.window(desktop, title, body, icon, size)    # a window in this OS's style
    host.sound("ding")                               # this OS's sound for an event
    host.saves("claudeggle")                         # Saves/claudeggle/
    host.local_storage()                             # the shared Local Storage

Each OS lists the games in its own Start menu and desktop folders; ClaudeXP imports them with programs._shared().

Claudenites 3-D (claudenites/) is a Python game drawn with OpenGL 3.3 through PyOpenGL and numpy (in
ClaudeXP/requirements.txt); its development repo is ClaudeGames/Claudenites 3-D (jasonfye2015/claudenites-3d), brought in
here as a subtree. Its saves are Saves/claudenites/slot1..3.json.

The Hollow Oak (hollowoak/) is a Python game on the same footing (OpenGL 3.3, PyOpenGL, numpy), standing alone from
the others; its development repo is ClaudeGames/The Hollow Oak (jasonfye2015/the-hollow-oak), brought in here as a
subtree. Its saves go in Saves/hollowoak/.
Two games are single HTML files, played in a Qt WebEngine window on a permanent browser profile in Saves/: clauderpg
(the user's own, dropped into clauderpg/game) and claudemagic (built from claudemagic/src by its build.py into
claudemagic/game; see claudemagic/README.txt). Both play in an ordinary browser as they are.
Moved here so far: claudeggle, claudecraft, clauderpg (with its game files in clauderpg/game), claudequest,
claudeablo, claudecity, scorched and claudejeweled.
Their art lives in each game's own assets/ folder.
Newer: claudemmings (Lemmings, on your media in Local Storage\Lemmings) and claudualties (Casualties: Unknown, on
your media in Local Storage\casualties unknown; the sound is synthesized).
emulators/ (the NES, SNES, Game Boy, Genesis, N64 and Apple ][ emulators, plus Doom, Doom II and Wolfenstein 3D,
with the libretro cores in emulators/cores) and doom/ (Heretic and Hexen on Chocolate Doom, in doom/engines). They
find their games in Local Storage: Emulation\<system> and WADs.
