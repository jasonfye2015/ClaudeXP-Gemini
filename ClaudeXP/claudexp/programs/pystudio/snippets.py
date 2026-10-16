"""Reusable game-code snippets for Copilot Python Studio: save/load, camera, particles, scenes, dialogue boxes and more.
Each one is self-contained and written for pygame. Inserting adds any missing import lines at the top of the file."""
import ast
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSplitter, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

# (category, name, what it is, imports, code)
SNIPPETS = []


def snippet(category, name, about, imports, code):
    SNIPPETS.append((category, name, about, list(imports), code.strip("\n") + "\n"))


snippet("Files", "Save and load game data (JSON)",
        "Keep progress, settings or a high score in a file next to your program.", ["import json", "import os"], '''
SAVE_FILE = "savegame.json"


def save_game(data, path=SAVE_FILE):
    """Write a dict (numbers, text, lists, dicts, True/False) to disk."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_game(default, path=SAVE_FILE):
    """Read the saved dict back. Returns `default` when there is no usable save yet."""
    try:
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        return {**default, **saved}                      # new settings added later still get their defaults
    except (OSError, ValueError):
        return dict(default)


# progress = load_game({"level": 1, "coins": 0})
# progress["coins"] += 5
# save_game(progress)
''')

snippet("Files", "High score table",
        "Top-10 scores with names, saved to a file; add_score() tells you the new rank.", ["import json"], '''
SCORE_FILE = "highscores.json"


def load_scores(path=SCORE_FILE):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def add_score(name, score, path=SCORE_FILE, keep=10):
    """Insert a score; returns its rank (1 = best) or None if it did not make the table."""
    scores = load_scores(path)
    scores.append({"name": name, "score": score})
    scores.sort(key=lambda s: s["score"], reverse=True)
    del scores[keep:]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scores, f)
    for rank, entry in enumerate(scores, 1):
        if entry["name"] == name and entry["score"] == score:
            return rank
    return None


# rank = add_score("Ace", 1200)
# for place, entry in enumerate(load_scores(), 1): print(place, entry["name"], entry["score"])
''')

snippet("Files", "Find files when built into an .exe",
        "resource_path() finds your pictures and sounds both while testing and inside a PyInstaller .exe.",
        ["import os", "import sys"], '''
def resource_path(relative):
    """Use for every file your game loads: image = pygame.image.load(resource_path("Assets/hero.png"))
    When built with Build Executable, add the Assets folder as data (the build dialog bundles the script only,
    so keep Assets next to the .exe or copy it into Built Programs)."""
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(sys.argv[0]))
    bundled = os.path.join(base, relative)
    if os.path.exists(bundled):
        return bundled
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), relative)
''')

snippet("Game loop", "Fixed time-step loop",
        "Game logic runs at a steady 60 steps a second however fast the PC draws.", ["import pygame"], '''
def run_fixed_step(update, draw, step=1 / 60, max_frame=0.25):
    """update(step) is called at a fixed rate; draw(blend) once per displayed frame. Close the window to leave."""
    clock = pygame.time.Clock()
    behind, running = 0.0, True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        behind += min(clock.tick(120) / 1000, max_frame)   # max_frame stops a long pause causing a huge catch-up
        while behind >= step:
            update(step)
            behind -= step
        draw(behind / step)
        pygame.display.flip()


# run_fixed_step(lambda dt: None, lambda blend: screen.fill((20, 20, 40)))
''')

snippet("Game loop", "Scene / state manager",
        "Title screen, game and game-over as separate scenes you can switch between.", ["import pygame"], '''
class Scene:
    """Make one subclass per screen. Return a new Scene from handle() or update() to switch to it."""
    def handle(self, event):
        return None

    def update(self, dt):
        return None

    def draw(self, screen):
        pass


class SceneManager:
    def __init__(self, first):
        self.scene = first

    def run(self, screen, fps=60):
        clock = pygame.time.Clock()
        while self.scene is not None:
            dt = clock.tick(fps) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                self._switch(self.scene.handle(event))
                if self.scene is None:
                    return
            self._switch(self.scene.update(dt))
            if self.scene is None:
                return
            self.scene.draw(screen)
            pygame.display.flip()

    def _switch(self, new):
        if new is not None:
            self.scene = new if new is not False else None    # return False from a scene to quit


# class Title(Scene):
#     def handle(self, event):
#         if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
#             return Playing()
#     def draw(self, screen):
#         screen.fill((10, 10, 50))
# SceneManager(Title()).run(screen)
''')

snippet("Game loop", "Timers and cooldowns",
        "Do something every N seconds, or block an action (shooting, dashing) until it is ready again.", [], '''
class Cooldown:
    """if gun.ready(): fire(); gun.start()    and call gun.update(dt) every frame."""
    def __init__(self, seconds):
        self.seconds, self.left = seconds, 0.0

    def update(self, dt):
        self.left = max(0.0, self.left - dt)

    def ready(self):
        return self.left <= 0

    def start(self):
        self.left = self.seconds

    @property
    def fraction_ready(self):
        return 1.0 - self.left / self.seconds if self.seconds else 1.0


class Every:
    """spawner = Every(2.0)   then   for _ in range(spawner.tick(dt)): spawn_enemy()"""
    def __init__(self, seconds):
        self.seconds, self.passed = seconds, 0.0

    def tick(self, dt):
        self.passed += dt
        count = int(self.passed // self.seconds)
        self.passed -= count * self.seconds
        return count
''')

snippet("Camera and effects", "Scrolling camera",
        "Follows the player smoothly and stays inside the level; draw everything with camera.apply().", ["import pygame"], '''
class Camera:
    def __init__(self, screen_size, world_size, smoothing=8.0):
        self.view = pygame.Vector2(0, 0)
        self.screen_w, self.screen_h = screen_size
        self.world_w, self.world_h = world_size
        self.smoothing = smoothing

    def follow(self, target_rect, dt):
        """Call once a frame with the player's rect."""
        goal = pygame.Vector2(target_rect.centerx - self.screen_w / 2, target_rect.centery - self.screen_h / 2)
        self.view += (goal - self.view) * min(1.0, self.smoothing * dt)
        self.view.x = max(0, min(self.view.x, self.world_w - self.screen_w))
        self.view.y = max(0, min(self.view.y, self.world_h - self.screen_h))

    def apply(self, rect):
        """The rect to draw at on screen:  screen.blit(image, camera.apply(sprite_rect))"""
        return rect.move(-round(self.view.x), -round(self.view.y))


# camera = Camera((640, 480), (2000, 1200))
# camera.follow(player_rect, dt)
''')

snippet("Camera and effects", "Screen shake",
        "A short rumble for hits and explosions.", ["import random"], '''
class Shake:
    """shake = Shake()   shake.start(8, 0.3) on a hit   screen.blit(world, shake.offset(dt))"""
    def __init__(self):
        self.strength, self.time, self.total = 0.0, 0.0, 1.0

    def start(self, strength=6, seconds=0.25):
        self.strength, self.time, self.total = strength, seconds, seconds

    def offset(self, dt):
        if self.time <= 0:
            return (0, 0)
        self.time -= dt
        power = self.strength * max(0.0, self.time) / self.total
        return (random.uniform(-power, power), random.uniform(-power, power))
''')

snippet("Camera and effects", "Particle system",
        "Sparks, smoke, explosions and pickups: emit() a burst, update() and draw() every frame.",
        ["import math", "import pygame", "import random"], '''
class Particles:
    def __init__(self):
        self.items = []

    def emit(self, x, y, count=20, color=(255, 200, 60), speed=140, life=0.6, size=3, gravity=200, spread=360, angle=0):
        for _ in range(count):
            direction = math.radians(angle + random.uniform(-spread / 2, spread / 2))
            v = random.uniform(0.3, 1.0) * speed
            self.items.append([x, y, math.cos(direction) * v, math.sin(direction) * v,
                               life * random.uniform(0.6, 1.0), life, color, size, gravity])

    def update(self, dt):
        for p in self.items:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += p[8] * dt
            p[4] -= dt
        self.items = [p for p in self.items if p[4] > 0]

    def draw(self, screen, offset=(0, 0)):
        for x, y, _vx, _vy, left, life, color, size, _g in self.items:
            fade = left / life
            r = max(1, int(size * fade))
            pygame.draw.circle(screen, tuple(int(c * fade) for c in color), (int(x + offset[0]), int(y + offset[1])), r)


# sparks = Particles()
# sparks.emit(player.centerx, player.centery)      # a burst
# sparks.update(dt); sparks.draw(screen)
''')

snippet("Camera and effects", "Fade in / fade out",
        "Smooth screen transitions between scenes.", ["import pygame"], '''
class Fade:
    """fade = Fade((640, 480))   fade.out(0.5) to darken, fade.into(0.5) to reveal. Draw it last."""
    def __init__(self, size, color=(0, 0, 0)):
        self.cover = pygame.Surface(size)
        self.cover.fill(color)
        self.alpha, self.rate = 0.0, 0.0

    def out(self, seconds=0.5):
        self.rate = 255 / seconds

    def into(self, seconds=0.5):
        self.alpha, self.rate = 255.0, -255 / seconds

    @property
    def done(self):
        return self.rate == 0 or (self.rate > 0 and self.alpha >= 255) or (self.rate < 0 and self.alpha <= 0)

    def update(self, dt):
        self.alpha = max(0.0, min(255.0, self.alpha + self.rate * dt))

    def draw(self, screen):
        if self.alpha > 0:
            self.cover.set_alpha(int(self.alpha))
            screen.blit(self.cover, (0, 0))
''')

snippet("User interface", "Typewriter dialogue box",
        "A speech box that types text out letter by letter, with word wrapping; Space shows it all / moves on.",
        ["import pygame"], '''
def wrap_text(text, font, width):
    lines, line = [], ""
    for word in text.split(" "):
        trial = f"{line} {word}".strip()
        if font.size(trial)[0] <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


class DialogueBox:
    """box = DialogueBox(pygame.Rect(20, 360, 600, 100), font)   box.say(["Hello!", "Welcome."])
    Call box.advance() when the player presses Space/Enter, box.update(dt) each frame, box.draw(screen)."""
    def __init__(self, rect, font, speed=40, color=(250, 250, 240), back=(20, 20, 60), border=(255, 255, 255)):
        self.rect, self.font, self.speed = rect, font, speed
        self.color, self.back, self.border = color, back, border
        self.pages, self.page, self.shown = [], 0, 0.0

    @property
    def active(self):
        return self.page < len(self.pages)

    def say(self, pages):
        self.pages = [pages] if isinstance(pages, str) else list(pages)
        self.page, self.shown = 0, 0.0

    def advance(self):
        if not self.active:
            return
        if self.shown < len(self.pages[self.page]):
            self.shown = len(self.pages[self.page])         # first press: finish the line
        else:
            self.page, self.shown = self.page + 1, 0.0      # second press: next page

    def update(self, dt):
        if self.active:
            self.shown = min(len(self.pages[self.page]), self.shown + self.speed * dt)

    def draw(self, screen):
        if not self.active:
            return
        pygame.draw.rect(screen, self.back, self.rect, border_radius=8)
        pygame.draw.rect(screen, self.border, self.rect, 3, border_radius=8)
        text = self.pages[self.page][:int(self.shown)]
        y = self.rect.y + 12
        for line in wrap_text(text, self.font, self.rect.width - 28):
            screen.blit(self.font.render(line, True, self.color), (self.rect.x + 14, y))
            y += self.font.get_linesize()
''')

snippet("User interface", "Clickable button",
        "A button with hover and click colours; check button.clicked(event) in your event loop.", ["import pygame"], '''
class Button:
    def __init__(self, rect, text, font, color=(60, 90, 200), hover=(90, 125, 235), text_color=(255, 255, 255)):
        self.rect, self.text, self.font = pygame.Rect(rect), text, font
        self.color, self.hover, self.text_color = color, hover, text_color

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

    def draw(self, screen):
        over = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, self.hover if over else self.color, self.rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=6)
        label = self.font.render(self.text, True, self.text_color)
        screen.blit(label, label.get_rect(center=self.rect.center))


# play = Button((220, 200, 200, 48), "Play", font)
# in the event loop:   if play.clicked(event): start_game()
# each frame:          play.draw(screen)
''')

snippet("User interface", "Health bar and text with outline",
        "A bar that changes colour as it empties, and readable text over any background.", ["import pygame"], '''
def draw_bar(screen, x, y, width, height, fraction, color=None, back=(40, 40, 40)):
    """fraction 0.0 - 1.0. Green, then yellow, then red as it drops (or give a colour)."""
    fraction = max(0.0, min(1.0, fraction))
    if color is None:
        color = (80, 200, 80) if fraction > 0.5 else (230, 200, 40) if fraction > 0.25 else (220, 50, 50)
    pygame.draw.rect(screen, back, (x, y, width, height))
    pygame.draw.rect(screen, color, (x, y, int(width * fraction), height))
    pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height), 2)


def draw_text(screen, font, text, pos, color=(255, 255, 255), outline=(0, 0, 0)):
    """Text with a 1-pixel outline so it stays readable on busy backgrounds."""
    x, y = pos
    shadow = font.render(text, True, outline)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1), (0, 2)):
        screen.blit(shadow, (x + dx, y + dy))
    screen.blit(font.render(text, True, color), pos)


# draw_bar(screen, 10, 10, 200, 20, player_health / 100)
# draw_text(screen, font, f"Score {score}", (10, 40))
''')

snippet("Input", "Keyboard and gamepad controls",
        "Ask for 'left' or 'jump' instead of specific keys; works with arrows, WASD and a joystick.",
        ["import pygame"], '''
KEYS = {
    "left": (pygame.K_LEFT, pygame.K_a), "right": (pygame.K_RIGHT, pygame.K_d),
    "up": (pygame.K_UP, pygame.K_w), "down": (pygame.K_DOWN, pygame.K_s),
    "jump": (pygame.K_SPACE, pygame.K_z), "fire": (pygame.K_x, pygame.K_LCTRL),
}
BUTTONS = {"jump": 0, "fire": 2}                     # gamepad buttons (A and X on most pads)


class Controls:
    """controls = Controls()   then   if controls.held("left"): ...   if controls.pressed("jump", event): ..."""
    def __init__(self):
        pygame.joystick.init()
        self.pads = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for pad in self.pads:
            pad.init()

    def held(self, action):
        if any(pygame.key.get_pressed()[k] for k in KEYS.get(action, ())):
            return True
        for pad in self.pads:
            if action in BUTTONS and pad.get_button(BUTTONS[action]):
                return True
            if action in ("left", "right") and pad.get_numaxes() > 0:
                axis = pad.get_axis(0)
                if (action == "left" and axis < -0.4) or (action == "right" and axis > 0.4):
                    return True
            if action in ("up", "down") and pad.get_numaxes() > 1:
                axis = pad.get_axis(1)
                if (action == "up" and axis < -0.4) or (action == "down" and axis > 0.4):
                    return True
        return False

    def pressed(self, action, event):
        """True on the single frame the key or button goes down."""
        if event.type == pygame.KEYDOWN and event.key in KEYS.get(action, ()):
            return True
        return event.type == pygame.JOYBUTTONDOWN and BUTTONS.get(action) == event.button

    def move_x(self):
        return int(self.held("right")) - int(self.held("left"))

    def move_y(self):
        return int(self.held("down")) - int(self.held("up"))
''')

snippet("Collisions and AI", "Move and collide with walls",
        "Moves a rect along x then y and stops it at solid rects; tells you which sides touched (for jumping).",
        [], '''
def move_and_collide(rect, dx, dy, walls):
    """Move `rect` by (dx, dy), pushed back by anything in `walls` (a list of Rects).
    Returns a dict like {"left": False, "right": False, "top": False, "bottom": True}.
    bottom=True means standing on something, which is the moment a jump is allowed."""
    hit = {"left": False, "right": False, "top": False, "bottom": False}
    rect.x += round(dx)
    for wall in walls:
        if rect.colliderect(wall):
            if dx > 0:
                rect.right, hit["right"] = wall.left, True
            elif dx < 0:
                rect.left, hit["left"] = wall.right, True
    rect.y += round(dy)
    for wall in walls:
        if rect.colliderect(wall):
            if dy > 0:
                rect.bottom, hit["bottom"] = wall.top, True
            elif dy < 0:
                rect.top, hit["top"] = wall.bottom, True
    return hit


# velocity_y += 900 * dt                      # gravity
# hit = move_and_collide(player, vx * dt, velocity_y * dt, walls)
# if hit["bottom"] or hit["top"]: velocity_y = 0
# if hit["bottom"] and jump_pressed: velocity_y = -420
''')

snippet("Collisions and AI", "Enemy that patrols and chases",
        "Walks between two points, then chases the player when they come close.", ["import pygame"], '''
class Enemy:
    """enemy = Enemy((100, 300), (400, 300))   enemy.update(dt, player_rect.center)   enemy.draw(screen)"""
    def __init__(self, a, b, speed=70, chase_speed=110, sight=160):
        self.pos = pygame.Vector2(a)
        self.points = [pygame.Vector2(a), pygame.Vector2(b)]
        self.target = 1
        self.speed, self.chase_speed, self.sight = speed, chase_speed, sight
        self.chasing = False

    @property
    def rect(self):
        return pygame.Rect(self.pos.x - 14, self.pos.y - 14, 28, 28)

    def update(self, dt, player_pos):
        to_player = pygame.Vector2(player_pos) - self.pos
        self.chasing = to_player.length() < self.sight
        goal = pygame.Vector2(player_pos) if self.chasing else self.points[self.target]
        step = goal - self.pos
        speed = self.chase_speed if self.chasing else self.speed
        if step.length() <= speed * dt:
            self.pos = goal
            if not self.chasing:
                self.target = 1 - self.target
        elif step.length() > 0:
            self.pos += step.normalize() * speed * dt

    def draw(self, screen):
        pygame.draw.rect(screen, (220, 60, 60) if self.chasing else (200, 140, 60), self.rect, border_radius=4)
''')

snippet("Collisions and AI", "Find a path on a grid (A*)",
        "Shortest route around walls on a tile map, using the offline 'pathfinding' package.",
        ["from pathfinding.core.diagonal_movement import DiagonalMovement", "from pathfinding.core.grid import Grid",
         "from pathfinding.finder.a_star import AStarFinder"], '''
def find_path(level, start, goal):
    """level: list of strings, '#' = wall. start/goal: (column, row). Returns [(column, row), ...] or []."""
    matrix = [[0 if cell == "#" else 1 for cell in row] for row in level]     # 0 blocks, 1 is walkable
    grid = Grid(matrix=matrix)
    path, _runs = AStarFinder(diagonal_movement=DiagonalMovement.never).find_path(
        grid.node(*start), grid.node(*goal), grid)
    return [(node.x, node.y) for node in path]


# route = find_path(LEVEL, (1, 1), (8, 5))        # then step the enemy along `route` one tile at a time
''')

snippet("Sound", "Sound manager",
        "Loads each sound once, keeps volume settings, and never crashes if a file or sound card is missing.",
        ["import os", "import pygame"], '''
class Sounds:
    """sounds = Sounds()   sounds.play("Assets/coin.ogg")   sounds.music("Assets/theme.ogg")   sounds.volume = 0.5"""
    def __init__(self, volume=0.7):
        self.cache, self.volume, self.enabled = {}, volume, True
        try:
            pygame.mixer.init()
        except pygame.error:
            self.enabled = False                       # no sound device: the game still runs, silently

    def play(self, path):
        if not self.enabled:
            return
        if path not in self.cache:
            self.cache[path] = pygame.mixer.Sound(path) if os.path.exists(path) else None
        sound = self.cache[path]
        if sound is not None:
            sound.set_volume(self.volume)
            sound.play()

    def music(self, path, loops=-1):
        if self.enabled and os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(loops)

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        if self.enabled:
            pygame.mixer.music.set_volume(self.volume)
''')

snippet("Graphics", "Parallax scrolling background",
        "Layers that scroll at different speeds for a sense of depth; each layer repeats forever.", ["import pygame"], '''
class ParallaxLayer:
    def __init__(self, image, factor):
        """factor: 0.0 = fixed sky, 0.3 = distant hills, 1.0 = moves with the world."""
        self.image, self.factor = image, factor

    def draw(self, screen, camera_x, y=0):
        width = self.image.get_width()
        x = -(camera_x * self.factor) % width
        while x - width < screen.get_width():
            screen.blit(self.image, (x - width, y))
            x += width


# layers = [ParallaxLayer(sky, 0.0), ParallaxLayer(hills, 0.3), ParallaxLayer(trees, 0.7)]
# for layer in layers: layer.draw(screen, camera.view.x)
''')

snippet("Graphics", "Flash and tint a sprite",
        "White hit-flash and colour tint for a damaged enemy, and a blinking invincible player.", ["import pygame"], '''
def tinted(image, color):
    """A copy of the picture multiplied by a colour:  tinted(hero, (255, 120, 120)) for a red look."""
    copy = image.copy()
    copy.fill(color + (255,), special_flags=pygame.BLEND_RGBA_MULT)
    return copy


def flashed(image, amount=255):
    """A copy lit up toward white (keeps transparent pixels transparent) for a hit flash."""
    copy = image.copy()
    copy.fill((amount, amount, amount, 0), special_flags=pygame.BLEND_RGB_ADD)
    return copy


def blinking(time_left, rate=10):
    """True on alternate beats while time_left > 0:  if not blinking(invincible): draw the player."""
    return time_left > 0 and int(time_left * rate) % 2 == 0
''')

snippet("Game data", "Inventory",
        "Items with counts and a stack limit: add, remove, check and list.", [], '''
class Inventory:
    """bag = Inventory(slots=8, stack=99)   bag.add("potion", 3)   bag.has("key")   bag.remove("potion")"""
    def __init__(self, slots=8, stack=99):
        self.slots, self.stack, self.items = slots, stack, {}

    def add(self, name, count=1):
        """Returns how many could NOT be added (0 means everything fit)."""
        have = self.items.get(name, 0)
        if name not in self.items and len(self.items) >= self.slots:
            return count
        room = self.stack - have
        taken = min(room, count)
        if taken:
            self.items[name] = have + taken
        return count - taken

    def has(self, name, count=1):
        return self.items.get(name, 0) >= count

    def remove(self, name, count=1):
        if not self.has(name, count):
            return False
        self.items[name] -= count
        if self.items[name] == 0:
            del self.items[name]
        return True

    def to_dict(self):
        return dict(self.items)                      # ready for save_game()
''')

CATEGORIES = []
for _c, *_rest in SNIPPETS:
    if _c not in CATEGORIES:
        CATEGORIES.append(_c)


def by_category():
    return [(c, [s for s in SNIPPETS if s[0] == c]) for c in CATEGORIES]


def search(text):
    words = text.lower().split()
    return [s for s in SNIPPETS if all(w in f"{s[0]} {s[1]} {s[2]}".lower() for w in words)]


# ---- putting a snippet into a file ---------------------------------------------------------------------------------

def import_position(text):
    """Character offset where new import lines belong: after the docstring and the imports already at the top."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    last = 0
    for index, node in enumerate(tree.body):
        is_doc = index == 0 and isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) \
            and isinstance(node.value.value, str)
        if is_doc or isinstance(node, (ast.Import, ast.ImportFrom)):
            last = node.end_lineno
        else:
            break
    if not last:
        return 0
    lines = text.split("\n")
    return min(len(text), len("\n".join(lines[:last])) + 1)


def missing_imports(text, imports):
    return [line for line in imports if not re.search(r"^\s*" + re.escape(line) + r"\s*$", text, re.M)]


def insert_into(text, imports, code, cursor=None):
    """The file text with the snippet added at `cursor` (a character offset; default: the end), put after the line the
    cursor is on, and any missing import lines added at the top. Returns (new_text, where_the_code_starts)."""
    cursor = len(text) if cursor is None else cursor
    end = text.find("\n", cursor)
    end = len(text) if end < 0 else end
    before, after = text[:end], text[end:]
    pad = "\n\n" if before.strip() else ""
    block = pad + code.rstrip("\n") + "\n"
    if after.strip():
        block += "\n"
    body = before + block + after
    started = len(before) + len(pad)
    need = missing_imports(text, imports)
    if need:
        at = import_position(text)
        add = "\n".join(need) + "\n"
        if at and not text[:at].endswith("\n"):
            add = "\n" + add
        if not at and text.strip():
            add += "\n"
        body = body[:at] + add + body[at:]
        started += len(add) if at <= started else 0
    return body, started


class SnippetLibrary(QWidget):
    """Search and preview the snippets; `insert(snippet)` puts the chosen one into the open file."""

    def __init__(self, insert):
        super().__init__()
        self.insert = insert
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search snippets (try: save, camera, enemy, sound)")
        self.search.textChanged.connect(self._fill)
        root.addWidget(self.search)
        split = QSplitter()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.currentItemChanged.connect(self._show)
        self.tree.itemDoubleClicked.connect(lambda *_: self.insert_current())
        split.addWidget(self.tree)
        right = QWidget()
        box = QVBoxLayout(right)
        box.setContentsMargins(0, 0, 0, 0)
        self.about = QLabel("")
        self.about.setWordWrap(True)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setProperty("nospell", True)
        self.preview.setFont(QFont("Consolas", 9))
        self.preview.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.button = QPushButton("Insert into my program")
        self.button.clicked.connect(self.insert_current)
        box.addWidget(self.about)
        box.addWidget(self.preview, 1)
        box.addWidget(self.button)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        split.setSizes([230, 520])
        root.addWidget(split, 1)
        self._fill()

    def _fill(self, *_):
        self.tree.clear()
        query = self.search.text().strip()
        groups = [("Results", search(query))] if query else by_category()
        first = None
        for category, items in groups:
            if not items:
                continue
            top = QTreeWidgetItem([category])
            top.setFlags(Qt.ItemIsEnabled)
            self.tree.addTopLevelItem(top)
            for item in items:
                child = QTreeWidgetItem([item[1]])
                child.setData(0, Qt.UserRole, item)
                top.addChild(child)
                first = first or child
            top.setExpanded(True)
        if first is not None:
            self.tree.setCurrentItem(first)
        else:
            self.about.setText("No snippets match.")
            self.preview.clear()

    def current(self):
        item = self.tree.currentItem()
        return item.data(0, Qt.UserRole) if item is not None else None

    def _show(self, item, _old=None):
        data = item.data(0, Qt.UserRole) if item is not None else None
        if data is None:
            return
        _cat, name, about, imports, code = data
        needs = ("\nAdds: " + ", ".join(imports)) if imports else ""
        self.about.setText(f"<b>{name}</b><br>{about}<br><i>{needs.strip()}</i>")
        self.preview.setPlainText(code)

    def insert_current(self):
        data = self.current()
        if data is not None:
            self.insert(data)

