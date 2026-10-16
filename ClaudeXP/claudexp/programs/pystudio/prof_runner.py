"""Runs a program for Copilot Python Studio's profiler. Usage: prof_runner.py MODE REPORT.json SCRIPT.py

MODE is "overlay" (draw an FPS readout on the pygame window), "profile" (cProfile only) or "both".
The report is rewritten every few seconds, so it still exists when the user presses Stop."""
import json
import os
import runpy
import sys
import time

mode, report_path, script = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3])
script_dir = os.path.dirname(script)
want_overlay = mode in ("overlay", "both")
want_profile = mode in ("profile", "both")

frames = []                         # seconds between display updates
started = time.perf_counter()
last = [None]
last_dump = [started]
profiler = None
if want_profile:
    import cProfile
    profiler = cProfile.Profile()


def percentile_low(times, fraction):
    """FPS of the slowest `fraction` of frames (the "1% low" gamers quote)."""
    worst = sorted(times, reverse=True)[:max(1, int(len(times) * fraction))]
    return 1.0 / (sum(worst) / len(worst)) if worst and sum(worst) else 0.0


def function_rows(limit=40):
    if profiler is None:
        return []
    import pstats
    profiler.create_stats()
    rows = []
    for (filename, line, name), (_cc, calls, own, cum, _callers) in pstats.Stats(profiler).stats.items():
        rows.append({"file": filename, "line": line, "name": name, "calls": calls, "own": own, "cum": cum})
    rows.sort(key=lambda r: -r["own"])
    mine = [r for r in rows if r["file"].lower().startswith(script_dir.lower()) and "<" not in r["file"]]
    return rows[:limit] + [r for r in mine[:60] if r not in rows[:limit]]


def dump(final=False):
    times = frames[-20000:]
    summary = {"frames": len(frames), "seconds": time.perf_counter() - started, "final": final,
               "script": script, "script_dir": script_dir, "times": times[-600:], "functions": function_rows()}
    if times:
        avg = sum(times) / len(times)
        summary.update(avg_fps=1.0 / avg if avg else 0.0, avg_ms=avg * 1000, worst_ms=max(times) * 1000,
                       low1=percentile_low(times, 0.01), slow=sum(1 for t in times if t > 1 / 30))
    tmp = report_path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(summary, f)
        os.replace(tmp, report_path)
    except OSError:
        pass


def tick(surface):
    now = time.perf_counter()
    if last[0] is not None:
        frames.append(now - last[0])
    last[0] = now
    if want_overlay and surface is not None:
        draw_overlay(surface)
    if now - last_dump[0] > 3:
        last_dump[0] = now
        if profiler is not None:
            profiler.disable()
        dump()
        if profiler is not None:
            profiler.enable()


_font = []


def draw_overlay(surface):
    import pygame
    recent = frames[-60:]
    if not recent:
        return
    avg = sum(recent) / len(recent)
    if not _font:
        _font.append(pygame.font.SysFont("consolas", 14))
    text = f"{1 / avg:5.1f} FPS  {avg * 1000:5.1f} ms  worst {max(recent) * 1000:5.1f} ms"
    img = _font[0].render(text, True, (255, 255, 255), (0, 0, 0))
    surface.blit(img, (4, 4))
    graph_h = 30
    for i, t in enumerate(frames[-120:]):
        h = min(graph_h, int(t * 1000 / 33.3 * graph_h * 0.5))
        color = (80, 220, 80) if t < 1 / 50 else (230, 200, 60) if t < 1 / 30 else (230, 70, 70)
        pygame.draw.line(surface, color, (4 + i, 8 + img.get_height() + graph_h), (4 + i, 8 + img.get_height() + graph_h - h))


def patch_pygame():
    try:
        import pygame
        import pygame.display as display
    except ImportError:
        return
    real_flip, real_update = display.flip, display.update

    def flip():
        tick(display.get_surface())
        return real_flip()

    def update(*args, **kwargs):
        tick(display.get_surface())
        return real_update(*args, **kwargs)

    display.flip, display.update = flip, update


sys.path.insert(0, script_dir)
sys.argv = [script]
os.chdir(script_dir)
patch_pygame()
code = 0
if profiler is not None:
    profiler.enable()
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
except BaseException:
    import traceback
    traceback.print_exc()
    code = 1
finally:
    if profiler is not None:
        profiler.disable()
    dump(final=True)
sys.exit(code)
