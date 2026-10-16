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

Moved here so far: claudeggle, claudecraft, clauderpg (with its game files in clauderpg/game), claudequest,
claudeablo, claudecity, scorched and claudejeweled. Their art lives in each game's own assets/ folder.
