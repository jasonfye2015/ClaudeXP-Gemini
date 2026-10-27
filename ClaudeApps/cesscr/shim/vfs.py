"""Stands in for ClaudeXP's drive E: in the .scr - the games' sprite sheets, bundled inside it."""
import sys
from pathlib import Path


def local_storage():
    if getattr(sys, "_MEIPASS", None):                     # the built .scr: unpacked next to the program
        return Path(sys._MEIPASS) / "sprites"
    return Path(__file__).resolve().parents[3] / "sprites"  # run from the build folder (build/pkg/claudexp/explorer)
