"""Where assets/wand.npz and assets/wand.png came from: KayKit's wand (Kay Lousberg, the Adventurers pack, CC0), as the
Timeline's Claude and Magic figures carry it, read once out of the Claudenites 3-D development repo's figure pack and
kept here - so The Hollow Oak itself needs nothing of any other game.

    python tools/export_wand.py        (only needed to make them again)"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NITES = ROOT.parent / "Claudenites 3-D"


def main():
    spec = importlib.util.spec_from_file_location("claudenites", NITES / "__init__.py", submodule_search_locations=[str(NITES)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["claudenites"] = mod
    try:
        spec.loader.exec_module(mod)
    except ImportError:
        pass
    from claudenites.engine.figures import Pack
    m = Pack.load().model("gear:wand")
    v = m.skinned(m.skin_matrices(None, 0))
    np.savez_compressed(ROOT / "assets" / "wand.npz", positions=v[:, :3].astype(np.float32), uv=m.uv, colours=m.colours,
                        indices=m.indices)
    (ROOT / "assets" / "wand.png").write_bytes(m.texture)
    print("the wand:", len(v), "vertices")


if __name__ == "__main__":
    main()
