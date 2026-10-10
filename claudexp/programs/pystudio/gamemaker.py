"""Make a game from a description: the prompt for the AI, and turning its answer into a project file. No Qt."""
import re
from pathlib import Path

GENRES = {
    "Anything that fits": "Pick the game style that best fits the description.",
    "Arcade (dodge or collect)": "An arcade game: score, lives, increasing difficulty, game over screen with restart.",
    "Platformer": "A side-view platformer with gravity, jumping and platforms.",
    "Top-down shooter": "A top-down shooter: move in all directions, shoot, enemies that come at the player.",
    "Puzzle or board game": "A turn-based puzzle or board game controlled with the mouse or keyboard.",
    "Racing or driving": "A top-down or side-scrolling driving game with obstacles and a score or timer.",
}

RULES = (
    "Write ONE complete, runnable pygame program in a single python code block, and nothing long outside it. Rules:\n"
    "- Use only pygame and the Python standard library. Do not load any image, sound or font files: draw everything "
    "with pygame.draw shapes and pygame.font.Font(None, size), and make sounds optional.\n"
    "- Window 800x600, 60 FPS using pygame.time.Clock, a proper event loop, and quit cleanly with pygame.quit().\n"
    "- Keyboard: arrow keys or WASD to move, Space for the main action, Esc to quit, R to restart after game over.\n"
    "- Show the score and the controls on screen. Keep the code tidy with small functions or classes and short "
    "comments.\n"
    "- It must work the first time: double check names, indentation and pygame 2 API calls.\n"
    "After the code block, add two short lines: how to play, and one idea to extend it.")


def build_prompt(description, genre=None):
    style = GENRES.get(genre or "", GENRES["Anything that fits"])
    return (f"Make a game for me. What I want: {description.strip()}\n\nStyle: {style}\n\n{RULES}")


def pick_code(reply):
    """The biggest python code block in an AI reply (a game is the long one), or None."""
    blocks = [m.group(1) for m in re.finditer(r"```[\w+-]*[ \t]*\r?\n(.*?)```", reply, re.S)]
    blocks = [b.rstrip("\n") + "\n" for b in blocks if "pygame" in b]
    return max(blocks, key=len) if blocks else None


def slug(description):
    words = re.findall(r"[a-z0-9]+", description.lower())
    return "_".join(words[:4]) or "game"


def save_game(projects_dir, description, code):
    """Write the game to <projects>/<name>/main.py in a folder that does not exist yet; returns the path."""
    base = Path(projects_dir)
    name, n = slug(description), 1
    folder = base / name
    while folder.exists():
        n += 1
        folder = base / f"{name}_{n}"
    folder.mkdir(parents=True)
    path = folder / "main.py"
    path.write_text(code, encoding="utf-8")
    return path
