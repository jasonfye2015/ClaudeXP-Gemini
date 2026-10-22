"""The residents in 2025: ClaudeXP's sync (Residents/<Name>/eras/2025.json -> the Fur Directory card, the AIM
contact with its photos, the IRC and MUCK regulars), writing into Claude11's own Program Files. The buddy icons go
to the shared gallery in ClaudeXP's ClaudeAIM, which every era's AIM reads."""
from .paths import PROGRAM_FILES

ERA = 2025


def sync():
    from . import xpcompat
    xpcompat.program_files_ready()
    from claudexp import residents_sync as rs
    rs.ERA = ERA
    rs.AIM = PROGRAM_FILES / "ClaudeAIM" / "contacts"
    rs.RECORDS = PROGRAM_FILES / "The Fur Directory" / "residents"
    rs.IRC = PROGRAM_FILES / "ClaudeIRC" / "regulars.json"
    rs.MUCK = PROGRAM_FILES / "ClaudeMUCK" / "world" / "regulars.json"
    return rs.sync()
