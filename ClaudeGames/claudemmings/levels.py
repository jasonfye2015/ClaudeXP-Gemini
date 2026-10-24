"""The twelve Fun levels: which map, its trapdoor and exit (found on the maps by matching the trapdoor frame of the
sprite sheet and the blue of each exit's doorway), and the rules - lemmings, how many to save, release rate, time,
and the skills on offer. The rules follow the spirit of the originals; the skills are the ones each level is named for.

trapdoor: (left, top) of the open trapdoor graphic on the map (45 x 25)
door:     (left, top, right, bottom) of the exit's doorway; the game finds the floor under it itself
"""

ALL = ("climber", "floater", "bomber", "blocker", "builder", "basher", "miner", "digger")


def skills(**counts):
    """The level's own skills (15 each), plus 3 of every other skill as a safety net: these maps are pictures of the
    originals, and a picture can't say which bits were meant to be solid, so no level is left unwinnable."""
    return {s: (15 if s in counts else 3) for s in ALL}


def every(n):
    return {s: n for s in ALL}


LEVELS = [
    {"name": "Just Dig!", "map": 1, "trapdoor": (192, 36), "door": (348, 112, 377, 131),
     "lemmings": 10, "save": 10, "rate": 50, "minutes": 5, "skills": skills(digger=10)},
    {"name": "Only Floaters Can Survive This", "map": 2, "trapdoor": (80, 8), "door": (331, 129, 360, 148),
     "lemmings": 10, "save": 10, "rate": 50, "minutes": 5, "skills": skills(floater=10)},
    {"name": "Tailor-Made For Blockers", "map": 3, "trapdoor": (134, 4), "door": (129, 133, 158, 152),
     "lemmings": 50, "save": 10, "rate": 50, "minutes": 5, "skills": skills(blocker=10)},
    {"name": "Now Use Miners and Climbers", "map": 4, "trapdoor": (199, 12), "door": (381, 30, 390, 40),
     "lemmings": 10, "save": 10, "rate": 50, "minutes": 5, "skills": skills(climber=10, miner=10)},
    {"name": "You Need Bashers This Time", "map": 5, "trapdoor": (130, 25), "door": (615, 113, 630, 127),
     "lemmings": 50, "save": 10, "rate": 50, "minutes": 5, "skills": skills(basher=10)},
    {"name": "A Task For Blockers and Bombers", "map": 6, "trapdoor": (231, 20), "door": (486, 86, 501, 96),
     "lemmings": 50, "save": 10, "rate": 50, "minutes": 5, "skills": skills(blocker=10, bomber=10)},
    {"name": "Builders Will Help You Here", "map": 7, "trapdoor": (211, 80), "door": (777, 80, 786, 89),
     "lemmings": 50, "save": 10, "rate": 50, "minutes": 5, "skills": skills(builder=10)},
    {"name": "Not As Complicated As it Looks", "map": 8, "trapdoor": (547, 36), "door": (526, 81, 555, 100),
     "lemmings": 50, "save": 50, "rate": 50, "minutes": 5, "skills": every(10)},
    {"name": "As Long As You Try Your Best", "map": 9, "trapdoor": (63, 80), "door": (229, 108, 238, 117),
     "lemmings": 10, "save": 50, "rate": 50, "minutes": 5, "skills": every(10)},
    {"name": "Smile if You Love Lemmings", "map": 10, "trapdoor": (760, 4), "door": (707, 125, 736, 144),
     "lemmings": 50, "save": 60, "rate": 50, "minutes": 6, "skills": every(10)},
    {"name": "Keep Your Hair on Mr. Lemming", "map": 11, "trapdoor": (15, 72), "door": (277, 120, 286, 129),
     "lemmings": 50, "save": 70, "rate": 50, "minutes": 5, "skills": every(10)},
    {"name": "Patience", "map": 12, "trapdoor": (0, 76), "door": (283, 101, 312, 119),
     "lemmings": 50, "save": 80, "rate": 1, "minutes": 8, "skills": every(10)},
]

# the music: every level has the track named after it (05 to 16 in Local Storage\Lemmings\background Music)
TITLE_MUSIC = "01 Title Screen"
INTRO_MUSIC = "02 Stage Intro"
CLEAR_MUSIC = "03 Stage Clear"
FAIL_MUSIC = "04 Failure"


def level_music(index):
    return f"{index + 5:02d} {LEVELS[index]['name']}"
