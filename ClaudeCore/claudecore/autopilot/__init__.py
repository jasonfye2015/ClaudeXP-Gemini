"""Kithylin Autopilot: Kithylin sits down at the computer and uses it - answers IMs, writes e-mail, browses, watches
TV, plays - for as long as you let him, with a second cursor of his own and a sky-blue glow around the screen while
he's at it.

Three layers, kept apart:
  legs    (engine.py)   what he does: scripted, randomised stretches of 15-60+ minutes, two to four at once the way a
                        person multitasks - the messengers nearly always open, a game or the TV in the background,
                        mail or the Web in front
  voice   (voice.py)    the words: a Kithylin model (the add-ons trained on the user's own chats, switched on per
                        request on the residents' base model) given what's on the screen
  hands   (hud.py)      the second cursor that travels to what it's about to use and types at human speed, and the
                        glow, the banner and the Pause / Stop controls

The engine never touches an operating system: each computer has an adapter that provides its legs (ClaudeXP:
claudexp/autopilot). The user's own mouse or keyboard pauses him at once."""
