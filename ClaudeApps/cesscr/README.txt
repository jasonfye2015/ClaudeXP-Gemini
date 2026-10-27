Claude Entertainment System.scr - the NES clock games as a real Windows screen saver
====================================================================================

  dist\Claude Entertainment System.scr   the screen saver (one file, about 38 MB, the sprite sheets inside it)

To use it: right-click it and choose Install (Windows makes it your screen saver and opens Screen Saver Settings),
or copy it into C:\Windows\System32 so it's in the list there. Settings... picks which games play, how long each
runs and the order, plus Super Claude Bros' character and world; they're kept in
%APPDATA%\Claude Entertainment System\settings.json. It runs on every monitor (the games on the main one) and a
key, a click or moving the mouse ends it.

The games are ClaudeXP's own - supercb, smb3cb, zeldacb, zelda2cb, metroidcb and ces in ClaudeXP\claudexp -
copied in when it's built, so a change to a game there reaches the .scr the next time it's built:

  build_scr.bat     builds it (the first time it makes .venv-build: Python 3.13 with PySide6-Essentials and
                    PyInstaller, apart from ClaudeXP's own Python; that needs the internet once)
  build_scr.py      gathers the games, the shim stand-ins and only the sprite sheets they read (from Local Storage),
                    then runs PyInstaller
  scr_main.py       the program: /s full screen, /p <hwnd> the little preview monitor, /c the Settings
  shim\             what stands in for ClaudeXP around the games: drive E: (the bundled sprites), the settings
                    file, sound (a screen saver keeps quiet) and the dialog window

The sprite sheets are the Spriters Resource's NES rips, for your own use; the .scr carries them inside it.
