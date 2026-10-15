Local Storage - ClaudeXP's drive E: (the External Drive)
========================================================

ClaudeXP runs fine with this folder empty. Two separate downloads go here:

  * LLM Models (about 3.3 GB or more) - the language model that plays your buddies and everyone else. Without it,
    everything except the talking still works. Copilot Image Creator can also install an image engine and
    Stable Diffusion 1.5 / SDXL models under LLM Models\image-gen\; both models plus the engine require several
    additional gigabytes. Copilot Voice can install local speech-recognition and speech-synthesis engines and
    models under LLM Models\voice\; setup requires an Internet connection, but voice processing then runs locally.
    CopilotAI uses this same optional voice installation for push-to-talk, automatic listening, and spoken replies.
  * The media archive - it gives the media programs something to show.

  Copilot Python Studio runs your programs with its own Python 3.12 under Python Studio\ (python312\ is the
  interpreter, wheels\ holds ~60 offline wheels: numpy, Pillow, pygame, matplotlib, flask, sympy, rich, PyInstaller
  and more; Run > Build Executable makes standalone .exe files). Python Studio\ffmpeg\ffmpeg.exe (about 100 MB)
  powers Tools > Audio and Video Converter, and Python Studio\docs\ holds the offline manuals. The code
  formatter (ruff) and pytest are installed in python312\ and also kept in wheels\. Nothing there needs a network;
  to add a package later, put its .whl files in wheels\ and use Tools > Install Package from Offline Wheels.

Unpack them so the folders sit directly in this one:

  Local Storage\
    LLM Models\               the language model and its engine (see the README inside)
    Furry Media Archive ...   FurComix Reader, FurFolio, FurStory, Fur CD Viewer, Furry Con CD Viewer,
                              Furry Video Browser, The Fur Directory's pictures
      Art CDs and DVDs ...      (Fur CD Viewer)
      Authors and Stories ...   (FurStory Reader)
      Comic Scans ...           (FurComix Reader)
      FurCon CDs ...            (Furry Con CD Viewer)
      Portfolios ...            (FurFolio Reader)
      Video ...                 (Furry Video Browser)
      Website Rips\             (Netscape's Furry Web: FurAffinity, HousePets, Hardblush, Jay Naylor, SexyFur,
                                YiffStar and clubstripes, each a folder named exactly that, served at their own
                                addresses; a missing one shows a 404 page)
    TV and Movies ...         ClaudeTV
    Emulation\                the Game Emulation programs (NES, SNES, Game Boy, Genesis, Apple ][ ...)
    WADs\                     Doom, Doom II, Wolfenstein 3D, Heretic and Hexen

Folders are found by how their names begin, so "Furry Media Archive (2001)" works as well as
"Furry Media Archive" (and "Emulation Archive" as well as "Emulation"). The one exception is WADs, which must be
called exactly that. Everything here stays on your PC: git ignores this folder (except this file).
