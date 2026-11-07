"""The tests: python tests/run.py [name-filter]. Plain functions named test_* in tests/test_*.py, run in order; no
packages needed beyond numpy (the game's logic has no Qt in it). Saves go to a scratch folder, never the real ones."""
import importlib.util
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_package():
    if "claudenites" not in sys.modules:
        spec = importlib.util.spec_from_file_location("claudenites", ROOT / "__init__.py",
                                                      submodule_search_locations=[str(ROOT)])
        mod = importlib.util.module_from_spec(spec)
        sys.modules["claudenites"] = mod
        try:
            spec.loader.exec_module(mod)
        except ImportError:                   # (no Qt or no Timeline here - CI: the subpackages still load)
            pass
    return sys.modules["claudenites"]


def share_floors():
    """Each floor (depth, seed) is made once in a run of the tests and handed out as a copy: the slow tests walk the
    same hundred floors (seeds 99 and "0:0"), and no test can spoil another's."""
    import copy
    from claudenites.game import levels
    if getattr(levels.dungeon, "shared", False):
        return
    made, real = {}, levels.dungeon

    def dungeon(depth, seed):
        key = (depth, str(seed))
        if key not in made:
            made[key] = real(depth, seed)
        return copy.deepcopy(made[key])
    dungeon.shared = True
    levels.dungeon = dungeon


def main(argv):
    load_package()
    share_floors()
    pick = argv[0] if argv else ""
    passed = failed = 0
    t0 = time.time()
    for f in sorted((ROOT / "tests").glob("test_*.py")):
        spec = importlib.util.spec_from_file_location(f"tests_{f.stem}", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in [n for n in dir(mod) if n.startswith("test_")]:
            if pick and pick not in f"{f.stem}.{name}":
                continue
            t = time.time()
            try:
                getattr(mod, name)()
                passed += 1
                print(f"  ok    {f.stem}.{name} ({time.time() - t:.1f} s)", flush=True)
            except Exception:
                failed += 1
                print(f"  FAIL  {f.stem}.{name}", flush=True)
                traceback.print_exc()
    print(f"{'all ' + str(passed) + ' passed' if not failed else f'{failed} failed, {passed} passed'} "
          f"in {time.time() - t0:.0f} s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
