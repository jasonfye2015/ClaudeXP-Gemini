"""Offline Python and pygame lessons for Python Studio. No Qt here; checking is done by running the learner's code."""
import ast
import os
import subprocess

MARK = "@@CHECK@@"

# Each lesson: id, title, text (HTML), starter, solution, hints, and one way to check the work:
#   harness + expected: the learner's code is run, then the harness prints results that must equal `expected`
#   needs: pygame lessons; the code must contain these names, and must run without errors (a window that is still
#          open when the time limit hits counts as running fine)
LESSONS = [
    {
        "id": "print", "title": "1. Say hello with print()",
        "text": "<h3>print() shows text on the screen</h3>"
                "<p>Text goes inside quotes. Numbers do not need quotes, and Python can do math for you.</p>"
                "<p><b>Your job:</b> print your name on the first line, then print the answer to 6 times 7 on the "
                "second line (let Python do the math).</p>",
        "starter": "# Line 1: your name\n\n# Line 2: 6 times 7, worked out by Python\n",
        "solution": 'print("Jason")\nprint(6 * 7)\n',
        "hints": ["Write print(\"your name\") on the first line.", "print(6 * 7) prints 42 without you typing 42."],
        "harness": "",
        "expected": None,
        "check_lines": lambda lines: len(lines) >= 2 and lines[0].strip() != "" and lines[1].strip() == "42",
        "fail": "I expected your name on line 1 and 42 on line 2.",
    },
    {
        "id": "variables", "title": "2. Variables",
        "text": "<h3>A variable is a name for a value</h3>"
                "<p><code>lives = 3</code> stores 3 under the name <code>lives</code>. You can then use it in math.</p>"
                "<p><b>Your job:</b> make a variable <code>speed</code> equal to 4 and a variable "
                "<code>seconds</code> equal to 5, then make <code>distance</code> by multiplying them. "
                "Keep the print line at the bottom.</p>",
        "starter": "speed = 0\nseconds = 0\ndistance = 0\nprint(distance)\n",
        "solution": "speed = 4\nseconds = 5\ndistance = speed * seconds\nprint(distance)\n",
        "hints": ["Change the 0 after speed and seconds.", "distance = speed * seconds"],
        "harness": "print(speed, seconds, distance)",
        "expected": ["4 5 20"],
        "fail": "speed should be 4, seconds 5, and distance should be speed * seconds (20).",
    },
    {
        "id": "if", "title": "3. Making decisions with if",
        "text": "<h3>if, elif and else</h3>"
                "<p>A program can choose what to do.</p>"
                "<pre>if score &gt;= 50:\n    print('pass')\nelse:\n    print('fail')</pre>"
                "<p>The indented lines (4 spaces) belong to the line above them.</p>"
                "<p><b>Your job:</b> finish <code>grade(score)</code>. It should return \"gold\" for 90 or more, "
                "\"silver\" for 50 or more, otherwise \"none\".</p>",
        "starter": 'def grade(score):\n    # return "gold", "silver" or "none"\n    pass\n',
        "solution": 'def grade(score):\n    if score >= 90:\n        return "gold"\n    elif score >= 50:\n'
                    '        return "silver"\n    else:\n        return "none"\n',
        "hints": ["Check the biggest number first (90).", "Use elif for the second test and else for the rest."],
        "harness": "print(grade(95), grade(90), grade(50), grade(49), grade(0))",
        "expected": ["gold gold silver none none"],
        "fail": "Try grade(95), grade(90), grade(50) and grade(49). They should give gold, gold, silver, none.",
    },
    {
        "id": "loops", "title": "4. Loops",
        "text": "<h3>for repeats things</h3>"
                "<pre>for number in range(3):\n    print(number)   # 0, 1, 2</pre>"
                "<p><code>range(1, 4)</code> counts 1, 2, 3 (it stops before the last number).</p>"
                "<p><b>Your job:</b> finish <code>total(n)</code> so it adds up 1 + 2 + ... + n and returns it.</p>",
        "starter": "def total(n):\n    result = 0\n    # add each number from 1 to n\n    return result\n",
        "solution": "def total(n):\n    result = 0\n    for number in range(1, n + 1):\n        result += number\n"
                    "    return result\n",
        "hints": ["range(1, n + 1) includes n.", "Inside the loop write result += number."],
        "harness": "print(total(1), total(4), total(10), total(0))",
        "expected": ["1 10 55 0"],
        "fail": "total(4) should be 10 and total(10) should be 55.",
    },
    {
        "id": "lists", "title": "5. Lists and dictionaries",
        "text": "<h3>Keeping many things together</h3>"
                "<pre>items = ['sword', 'shield']\nitems.append('potion')\nstats = {'hp': 10, 'mp': 4}\n"
                "stats['hp'] -= 3</pre>"
                "<p><b>Your job:</b> finish <code>count_items(inventory)</code>. <code>inventory</code> is a list "
                "of item names such as ['potion', 'sword', 'potion']. Return a dictionary of how many of each, "
                "like {'potion': 2, 'sword': 1}.</p>",
        "starter": "def count_items(inventory):\n    counts = {}\n    # go through the list and count\n"
                   "    return counts\n",
        "solution": "def count_items(inventory):\n    counts = {}\n    for item in inventory:\n"
                    "        counts[item] = counts.get(item, 0) + 1\n    return counts\n",
        "hints": ["Loop with: for item in inventory:", "counts.get(item, 0) gives 0 when the item is new."],
        "harness": "print(sorted(count_items(['potion', 'sword', 'potion']).items()), count_items([]))",
        "expected": ["[('potion', 2), ('sword', 1)] {}"],
        "fail": "count_items(['potion', 'sword', 'potion']) should be {'potion': 2, 'sword': 1}.",
    },
    {
        "id": "functions", "title": "6. Writing your own functions",
        "text": "<h3>def packages code so you can reuse it</h3>"
                "<pre>def add(a, b):\n    return a + b</pre>"
                "<p><code>return</code> hands the answer back. A function can also have a default value: "
                "<code>def hello(name='friend')</code>.</p>"
                "<p><b>Your job:</b> write <code>clamp(value, low, high)</code>. It returns <code>low</code> if value "
                "is below low, <code>high</code> if above high, otherwise value. Games use this constantly to keep a "
                "player on the screen.</p>",
        "starter": "def clamp(value, low, high):\n    pass\n",
        "solution": "def clamp(value, low, high):\n    if value < low:\n        return low\n    if value > high:\n"
                    "        return high\n    return value\n",
        "hints": ["Three cases: too low, too high, fine.", "Or in one line: return max(low, min(value, high))"],
        "harness": "print(clamp(5, 0, 10), clamp(-3, 0, 10), clamp(99, 0, 10), clamp(0, 0, 10))",
        "expected": ["5 0 10 0"],
        "fail": "clamp(-3, 0, 10) should be 0, clamp(99, 0, 10) should be 10 and clamp(5, 0, 10) should be 5.",
    },
    {
        "id": "classes", "title": "7. Classes (game objects)",
        "text": "<h3>A class is a blueprint for objects</h3>"
                "<pre>class Dog:\n    def __init__(self, name):\n        self.name = name\n"
                "    def speak(self):\n        return self.name + ' says woof'</pre>"
                "<p><code>self</code> is the object itself. Each object keeps its own data.</p>"
                "<p><b>Your job:</b> finish <code>Player</code>. It starts with 10 <code>hp</code>. "
                "<code>hit(damage)</code> lowers hp but never below 0. <code>alive()</code> returns True while hp "
                "is above 0.</p>",
        "starter": "class Player:\n    def __init__(self):\n        pass\n\n    def hit(self, damage):\n"
                   "        pass\n\n    def alive(self):\n        pass\n",
        "solution": "class Player:\n    def __init__(self):\n        self.hp = 10\n\n    def hit(self, damage):\n"
                    "        self.hp = max(0, self.hp - damage)\n\n    def alive(self):\n        return self.hp > 0\n",
        "hints": ["Start with self.hp = 10 in __init__.", "hit: self.hp = max(0, self.hp - damage)"],
        "harness": "p = Player()\np.hit(4)\na = (p.hp, p.alive())\np.hit(50)\nprint(a, p.hp, p.alive())",
        "expected": ["(6, True) 0 False"],
        "fail": "After hit(4) hp should be 6 and alive. After hit(50) hp should be 0 (not negative) and not alive.",
    },
    {
        "id": "window", "title": "8. Your first pygame window",
        "text": "<h3>A game is a loop that never stops</h3>"
                "<p>Every pygame program does the same four things: start pygame, make a window, loop "
                "(handling events, drawing), and quit.</p>"
                "<p><b>Your job:</b> fill in the blanks (marked TODO) so a blue window appears and closes when you "
                "click its X. Press F5 to see it, then press Check.</p>",
        "starter": "import pygame\n\npygame.init()\nscreen = pygame.display.set_mode((640, 360))\n"
                   "clock = pygame.time.Clock()\nrunning = True\n\nwhile running:\n    for event in pygame.event.get():\n"
                   "        # TODO: when event.type is pygame.QUIT, set running to False\n        pass\n"
                   "    # TODO: fill the screen with blue, e.g. screen.fill((30, 60, 160))\n"
                   "    pygame.display.flip()\n    clock.tick(60)\n\npygame.quit()\n",
        "solution": "import pygame\n\npygame.init()\nscreen = pygame.display.set_mode((640, 360))\n"
                    "clock = pygame.time.Clock()\nrunning = True\n\nwhile running:\n    for event in pygame.event.get():\n"
                    "        if event.type == pygame.QUIT:\n            running = False\n"
                    "    screen.fill((30, 60, 160))\n    pygame.display.flip()\n    clock.tick(60)\n\npygame.quit()\n",
        "hints": ["if event.type == pygame.QUIT: running = False", "screen.fill((30, 60, 160)) before the flip."],
        "needs": ["pygame.QUIT", "running = False", ".fill("],
        "fail": "",
    },
    {
        "id": "move", "title": "9. Moving with the keyboard",
        "text": "<h3>Reading the keys</h3>"
                "<pre>keys = pygame.key.get_pressed()\nif keys[pygame.K_LEFT]:\n    x -= speed</pre>"
                "<p>Doing this every frame makes things move smoothly. Multiply by the frame time "
                "(<code>dt</code>) so speed is the same on every computer.</p>"
                "<p><b>Your job:</b> complete the TODOs so a red square moves with the arrow keys and cannot leave "
                "the window. (Hint: lesson 6's <code>clamp</code> idea.)</p>",
        "starter": "import pygame\n\npygame.init()\nscreen = pygame.display.set_mode((640, 360))\n"
                   "clock = pygame.time.Clock()\nplayer = pygame.Rect(300, 160, 40, 40)\nspeed = 240\nrunning = True\n\n"
                   "while running:\n    dt = clock.tick(60) / 1000\n    for event in pygame.event.get():\n"
                   "        if event.type == pygame.QUIT:\n            running = False\n\n"
                   "    keys = pygame.key.get_pressed()\n    # TODO: left and right arrows change player.x by speed * dt\n"
                   "    # TODO: up and down arrows change player.y\n    # TODO: keep the square inside the window with "
                   "player.clamp_ip(screen.get_rect())\n\n    screen.fill((20, 20, 40))\n"
                   "    pygame.draw.rect(screen, (220, 50, 50), player)\n    pygame.display.flip()\n\npygame.quit()\n",
        "solution": "import pygame\n\npygame.init()\nscreen = pygame.display.set_mode((640, 360))\n"
                    "clock = pygame.time.Clock()\nplayer = pygame.Rect(300, 160, 40, 40)\nspeed = 240\nrunning = True\n\n"
                    "while running:\n    dt = clock.tick(60) / 1000\n    for event in pygame.event.get():\n"
                    "        if event.type == pygame.QUIT:\n            running = False\n\n"
                    "    keys = pygame.key.get_pressed()\n    if keys[pygame.K_LEFT]:\n        player.x -= speed * dt\n"
                    "    if keys[pygame.K_RIGHT]:\n        player.x += speed * dt\n    if keys[pygame.K_UP]:\n"
                    "        player.y -= speed * dt\n    if keys[pygame.K_DOWN]:\n        player.y += speed * dt\n"
                    "    player.clamp_ip(screen.get_rect())\n\n    screen.fill((20, 20, 40))\n"
                    "    pygame.draw.rect(screen, (220, 50, 50), player)\n    pygame.display.flip()\n\npygame.quit()\n",
        "hints": ["Four ifs: K_LEFT, K_RIGHT, K_UP, K_DOWN.", "player.x += speed * dt (and -= for left)."],
        "needs": ["K_LEFT", "K_RIGHT", "K_UP", "K_DOWN", "clamp_ip"],
        "fail": "",
    },
    {
        "id": "collide", "title": "10. Collisions",
        "text": "<h3>Did two things touch?</h3>"
                "<p>pygame's <code>Rect</code> knows: <code>a.colliderect(b)</code> is True when they overlap. "
                "A Rect is made from (x, y, width, height).</p>"
                "<p><b>Your job:</b> finish <code>touching(a, b)</code>. Each argument is a tuple (x, y, w, h). "
                "Return True if the two rectangles overlap. Rectangles that only share an edge do not count.</p>",
        "starter": "import pygame\n\n\ndef touching(a, b):\n    pass\n",
        "solution": "import pygame\n\n\ndef touching(a, b):\n    return pygame.Rect(a).colliderect(pygame.Rect(b))\n",
        "hints": ["Turn each tuple into pygame.Rect(a).", "return pygame.Rect(a).colliderect(pygame.Rect(b))"],
        "harness": "print(touching((0, 0, 10, 10), (5, 5, 10, 10)), touching((0, 0, 10, 10), (20, 0, 5, 5)), "
                   "touching((0, 0, 10, 10), (10, 0, 5, 5)))",
        "expected": ["True False False"],
        "fail": "Overlapping should be True; far apart or only sharing an edge should be False.",
    },
]


def by_id(lesson_id):
    return next((x for x in LESSONS if x["id"] == lesson_id), None)


def _env():
    env = dict(os.environ)
    for var in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(var, None)
    env.update({"PYTHONUTF8": "1", "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy",
                "PYGAME_HIDE_SUPPORT_PROMPT": "1"})
    return env


def _run(python, source, timeout):
    """Returns (stdout, stderr, timed_out)."""
    try:
        done = subprocess.run([python, "-u", "-c", source], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout, env=_env(), cwd=os.environ.get("TEMP") or None)
        return done.stdout, done.stderr, False
    except subprocess.TimeoutExpired as exc:
        def text(x):
            return x.decode("utf-8", "replace") if isinstance(x, bytes) else (x or "")
        return text(exc.stdout), text(exc.stderr), True


def _last_error(stderr):
    lines = [ln for ln in stderr.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def _names_missing(code, needs):
    stripped = "\n".join(ln.split("#", 1)[0] for ln in code.splitlines())
    return [n for n in needs if n not in stripped]


def check(python, lesson, code, timeout=None):
    """Run the learner's code against the lesson. Returns (passed, message)."""
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return False, f"Python can't read line {exc.lineno} yet: {exc.msg}."
    needs = lesson.get("needs")
    if needs:
        missing = _names_missing(code, needs)
        if missing:
            return False, "Not finished yet. I can't find: " + ", ".join(missing)
        _out, err, _timed = _run(python, code, timeout or 4)
        if "Traceback" in err:
            return False, "The program crashed: " + _last_error(err)
        return True, "It ran without errors. Press F5 to try it yourself too!"
    source = code + f"\nprint({MARK!r})\n" + lesson["harness"] + "\n"
    out, err, timed = _run(python, source, timeout or 8)
    if timed:
        return False, "It ran for too long. Is there a loop that never ends?"
    if MARK not in out:
        if "Traceback" in err:
            return False, "The program crashed: " + _last_error(err)
        return False, "The program stopped before the check could run."
    before, after = out.split(MARK, 1)
    result = [ln for ln in after.splitlines() if ln.strip()]
    if "Traceback" in err:
        return False, "The test crashed: " + _last_error(err)
    if "check_lines" in lesson:
        lines = [ln for ln in before.splitlines() if ln.strip()]
        ok = lesson["check_lines"](lines)
    else:
        ok = result == lesson["expected"]
    if ok:
        return True, "Correct! Nice work."
    extra = f" (I got: {' | '.join(result)})" if result and "check_lines" not in lesson else ""
    return False, lesson["fail"] + extra
