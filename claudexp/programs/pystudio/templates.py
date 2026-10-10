"""Starter programs (File > New from Template). Each one runs as it is, and uses the bundled Assets when they exist."""

LOADER = '''
def tile(pack, number, size, folder="Tiles"):
    """A picture from the Assets folder, scaled to size. A coloured square if the file isn't there."""
    path = f"Assets/{pack}/{folder}/tile_{number:04d}.png"
    try:
        return pygame.transform.scale(pygame.image.load(path).convert_alpha(), (size, size))
    except (FileNotFoundError, pygame.error):
        surface = pygame.Surface((size, size))
        surface.fill((200, 80 + number % 150, 120))
        return surface
'''

GAME_LOOP = '''"""A game window with a moving square. Arrow keys move it, Esc quits."""
import pygame

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()

player = pygame.Rect(300, 220, 40, 40)
speed = 240  # pixels per second

running = True
while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    keys = pygame.key.get_pressed()
    player.x += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * speed * dt
    player.y += (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * speed * dt
    player.clamp_ip(screen.get_rect())

    screen.fill((20, 24, 40))
    pygame.draw.rect(screen, (250, 200, 60), player)
    pygame.display.flip()

pygame.quit()
'''

SPRITES = '''"""A sprite with a walking animation, built from the bundled tiny-dungeon pictures."""
import pygame

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Sprite animation")
clock = pygame.time.Clock()
''' + LOADER + '''

class Hero(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # tiles 84-87 are four different characters; swap in your own animation frames here
        self.frames = [tile("tiny-dungeon", n, 64) for n in (84, 85, 86, 87)]
        self.index = 0.0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(320, 240))
        self.facing_left = False

    def update(self, dt, keys):
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        self.rect.x += dx * 200 * dt
        self.rect.y += dy * 200 * dt
        if dx:
            self.facing_left = dx < 0
        if dx or dy:
            self.index = (self.index + dt * 8) % len(self.frames)
        frame = self.frames[int(self.index)]
        self.image = pygame.transform.flip(frame, self.facing_left, False)
        self.rect.clamp_ip(screen.get_rect())


hero = Hero()
group = pygame.sprite.Group(hero)

running = True
while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
    group.update(dt, pygame.key.get_pressed())
    screen.fill((40, 50, 70))
    group.draw(screen)
    pygame.display.flip()

pygame.quit()
'''

TILEMAP = '''"""A tile map you can walk around. '#' is a wall, '.' is floor, 'P' is where the player starts."""
import pygame

TILE = 48
LEVEL = [
    "####################",
    "#P.......#.........#",
    "#.#####..#..#####..#",
    "#.#...#.....#...#..#",
    "#.#.#.#######.#.#..#",
    "#...#.........#....#",
    "#.#########.#####..#",
    "#..........#.......#",
    "####################",
]

pygame.init()
screen = pygame.display.set_mode((len(LEVEL[0]) * TILE, len(LEVEL) * TILE))
pygame.display.set_caption("Tile map")
clock = pygame.time.Clock()
''' + LOADER + '''
floor, wall, hero = tile("tiny-dungeon", 48, TILE), tile("tiny-dungeon", 57, TILE), tile("tiny-dungeon", 84, TILE)

walls = set()
px = py = 1
for y, row in enumerate(LEVEL):
    for x, ch in enumerate(row):
        if ch == "#":
            walls.add((x, y))
        elif ch == "P":
            px, py = x, y

running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.KEYDOWN:
            dx = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1}.get(event.key, 0)
            dy = {pygame.K_UP: -1, pygame.K_DOWN: 1}.get(event.key, 0)
            if (px + dx, py + dy) not in walls:
                px, py = px + dx, py + dy

    for y, row in enumerate(LEVEL):
        for x, _ in enumerate(row):
            screen.blit(wall if (x, y) in walls else floor, (x * TILE, y * TILE))
    screen.blit(hero, (px * TILE, py * TILE))
    pygame.display.flip()

pygame.quit()
'''

PLATFORMER = '''"""A physics playground with pymunk: arrow keys run, Space jumps, click to drop a crate."""
import pygame
import pymunk

pygame.init()
screen = pygame.display.set_mode((800, 520))
pygame.display.set_caption("Physics platformer")
clock = pygame.time.Clock()
FLOOR = 480

space = pymunk.Space()
space.gravity = (0, 1400)

# static ground and a ledge (y grows downward, like the screen)
for a, b in (((0, FLOOR), (800, FLOOR)), ((420, 380), (700, 380)), ((0, 0), (0, 520)), ((800, 0), (800, 520))):
    seg = pymunk.Segment(space.static_body, a, b, 4)
    seg.friction = 1.0
    space.add(seg)


def make_box(x, y, w, h, mass=1.0):
    body = pymunk.Body(mass, pymunk.moment_for_box(mass, (w, h)))
    body.position = x, y
    shape = pymunk.Poly.create_box(body, (w, h))
    shape.friction = 0.8
    space.add(body, shape)
    return shape


player = make_box(100, 300, 30, 44, mass=2)
player.body.moment = float("inf")  # never tips over
player.friction = 0.2
player.filter = pymunk.ShapeFilter(categories=0b10)  # so the "on the ground?" check ignores the player itself
crates = [make_box(500, 200, 40, 40), make_box(540, 120, 40, 40)]


def on_ground():
    below = (player.body.position.x, player.body.position.y + 26)
    return space.point_query_nearest(below, 4, pymunk.ShapeFilter(mask=pymunk.ShapeFilter.ALL_MASKS() ^ 0b10)) is not None


def draw_poly(shape, color):
    points = [shape.body.local_to_world(v) for v in shape.get_vertices()]
    pygame.draw.polygon(screen, color, [(p.x, p.y) for p in points])


running = True
while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and on_ground():
            player.body.apply_impulse_at_local_point((0, -900))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            crates.append(make_box(*event.pos, 36, 36))

    keys = pygame.key.get_pressed()
    player.body.velocity = ((keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 220, player.body.velocity.y)
    space.step(dt)

    screen.fill((30, 34, 52))
    pygame.draw.line(screen, (90, 200, 120), (0, FLOOR), (800, FLOOR), 8)
    pygame.draw.line(screen, (90, 200, 120), (420, 380), (700, 380), 8)
    for crate in crates:
        draw_poly(crate, (190, 140, 80))
    draw_poly(player, (250, 200, 60))
    pygame.display.flip()

pygame.quit()
'''

SOUNDS = '''"""Sound effects and music with pygame.mixer. Press 1, 2, 3 for sounds, M to toggle a tune, Up/Down for volume."""
import array
import math
import pygame

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
screen = pygame.display.set_mode((560, 200))
pygame.display.set_caption("Sounds")
font = pygame.font.SysFont("Tahoma", 20)
clock = pygame.time.Clock()


def beep(freq, seconds=0.2):
    """A tone made from nothing, so this works even without any sound files."""
    count = int(22050 * seconds)
    data = array.array("h", (int(9000 * math.sin(2 * math.pi * freq * i / 22050) * (1 - i / count))
                             for i in range(count)))
    return pygame.mixer.Sound(buffer=data.tobytes())


def load(path, fallback):
    try:
        return pygame.mixer.Sound(path)
    except (FileNotFoundError, pygame.error):
        return fallback


sounds = {
    pygame.K_1: load("Assets/digital-audio/Audio/laser1.ogg", beep(880)),
    pygame.K_2: load("Assets/interface-sounds/Audio/click_001.ogg", beep(440)),
    pygame.K_3: load("Assets/impact-sounds/Audio/footstep_carpet_000.ogg", beep(220, 0.3)),
}
tune = [beep(f, 0.25) for f in (262, 330, 392, 523)]
volume, playing, step, last = 0.6, False, 0, 0

running = True
while running:
    now = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in sounds:
                sounds[event.key].play()
            elif event.key == pygame.K_m:
                playing = not playing
            elif event.key in (pygame.K_UP, pygame.K_DOWN):
                volume = max(0.0, min(1.0, volume + (0.1 if event.key == pygame.K_UP else -0.1)))
    if playing and now - last > 280:
        tune[step % 4].play()
        step, last = step + 1, now
    for s in list(sounds.values()) + tune:
        s.set_volume(volume)
    screen.fill((24, 28, 44))
    text = f"1 2 3 = effects   M = tune {'ON' if playing else 'off'}   volume {volume:.1f}"
    screen.blit(font.render(text, True, (230, 230, 230)), (20, 80))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
'''

MENU = '''"""A title screen with pygame-menu: Play, Options (a volume slider and a name box), Quit."""
import pygame
import pygame_menu

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("My Game")
settings = {"volume": 5, "name": "Player"}


def play():
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Tahoma", 28)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return  # back to the menu
        screen.fill((30, 60, 40))
        text = f"Playing as {settings['name']} (volume {settings['volume']}). Esc = menu"
        screen.blit(font.render(text, True, (240, 240, 240)), (30, 220))
        pygame.display.flip()
        clock.tick(60)


def set_volume(value):
    settings["volume"] = int(value)


def set_name(value):
    settings["name"] = value


options = pygame_menu.Menu("Options", 640, 480, theme=pygame_menu.themes.THEME_DARK)
options.add.range_slider("Volume", 5, (0, 10), 1, onchange=set_volume)
options.add.text_input("Name: ", default="Player", onchange=set_name)
options.add.button("Back", pygame_menu.events.BACK)

menu = pygame_menu.Menu("My Game", 640, 480, theme=pygame_menu.themes.THEME_BLUE)
menu.add.button("Play", play)
menu.add.button("Options", options)
menu.add.button("Quit", pygame_menu.events.EXIT)
menu.mainloop(screen)
'''

PILLOW = '''"""Sprite-sheet tools with Pillow: cut a sheet into frames, make flipped copies, add outlines, rebuild a sheet."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

OUT = Path("My Sprites")
OUT.mkdir(exist_ok=True)


def slice_sheet(path, tile_w, tile_h, spacing=0):
    """Cut a sheet into a list of tile images (left to right, top to bottom)."""
    sheet = Image.open(path).convert("RGBA")
    frames = []
    for y in range(0, sheet.height - tile_h + 1, tile_h + spacing):
        for x in range(0, sheet.width - tile_w + 1, tile_w + spacing):
            frames.append(sheet.crop((x, y, x + tile_w, y + tile_h)))
    return frames


def outline(image, color=(0, 0, 0, 255)):
    """Add a one-pixel outline around the opaque part of a sprite."""
    big = ImageOps.expand(image, 1, (0, 0, 0, 0))
    grown = big.getchannel("A").filter(ImageFilter.MaxFilter(3))
    base = Image.new("RGBA", big.size, color)
    base.putalpha(grown)
    base.alpha_composite(big)
    return base


def build_sheet(frames, columns=4):
    w, h = frames[0].size
    rows = -(-len(frames) // columns)
    sheet = Image.new("RGBA", (w * columns, h * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % columns) * w, (i // columns) * h))
    return sheet


source = Path("Assets/1-bit-pack/Tilesheet/colored-transparent.png")
if not source.exists():  # no pack? draw a small sheet instead
    demo = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(demo)
    d.ellipse((4, 4, 28, 28), fill=(250, 200, 60, 255))
    d.rectangle((36, 6, 58, 26), fill=(90, 160, 250, 255))
    source = OUT / "demo_sheet.png"
    demo.save(source)

frames = slice_sheet(source, 32, 32) if source.name == "demo_sheet.png" else slice_sheet(source, 16, 16, spacing=1)
print(f"{len(frames)} frames cut from {source}")
mirrored = [ImageOps.mirror(f) for f in frames[:8]]
outlined = [outline(f) for f in frames[:8]]
build_sheet(frames[:8] + mirrored + outlined, 8).save(OUT / "sheet_result.png")
print("Saved My Sprites/sheet_result.png")
'''

NOISE = '''"""Terrain from noise (opensimplex): water, sand, grass, forest and snow. Space makes a new world."""
import random

import pygame
from opensimplex import OpenSimplex

W, H, CELL = 160, 120, 4
pygame.init()
screen = pygame.display.set_mode((W * CELL, H * CELL))
pygame.display.set_caption("Terrain")


def height_color(h):
    if h < -0.15:
        return (40, 80, 180)
    if h < -0.05:
        return (230, 210, 140)
    if h < 0.35:
        return (70, 160, 70)
    if h < 0.6:
        return (30, 100, 50)
    return (245, 245, 250)


def make_world(seed):
    noise = OpenSimplex(seed)
    surface = pygame.Surface((W, H))
    for y in range(H):
        for x in range(W):
            # two layers of noise: big shapes plus fine detail
            h = noise.noise2(x / 40, y / 40) + 0.35 * noise.noise2(x / 12, y / 12)
            surface.set_at((x, y), height_color(h))
    return pygame.transform.scale(surface, (W * CELL, H * CELL))


world = make_world(random.randint(0, 99999))
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            world = make_world(random.randint(0, 99999))
    screen.blit(world, (0, 0))
    pygame.display.flip()
    pygame.time.wait(30)

pygame.quit()
'''

TEMPLATES = [
    ("Game window and loop", "A window, a moving square, 60 frames a second.", GAME_LOOP),
    ("Sprite with animation", "A character with walking frames, from the bundled pictures.", SPRITES),
    ("Tile map", "A level drawn from tiles, with walls the player can't cross.", TILEMAP),
    ("Physics platformer (pymunk)", "Gravity, jumping, crates you can drop with the mouse.", PLATFORMER),
    ("Sound effects and music", "Play sounds, a little tune, and change the volume.", SOUNDS),
    ("Title menu (pygame-menu)", "A start screen with Play, Options and Quit.", MENU),
    ("Sprite sheet tools (Pillow)", "Cut sheets into frames, flip, outline, rebuild.", PILLOW),
    ("Terrain from noise", "Random islands and mountains with opensimplex.", NOISE),
]
