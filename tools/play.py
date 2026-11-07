"""Play the development copy on its own, the way the launcher's Apps window would (the Timeline's standalone host):

    python tools/play.py            (with the Timeline's own Python, Python/python.exe at the Timeline's top)

The repo's folder ("The Hollow Oak") isn't a name Python can import, so it's loaded here as the package hollowoak."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMELINE = ROOT.parents[1]


def load_package():
    if "hollowoak" in sys.modules:
        return sys.modules["hollowoak"]
    spec = importlib.util.spec_from_file_location("hollowoak", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hollowoak"] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    sys.path.insert(0, str(TIMELINE / "ClaudeCore"))
    from claudecore import standalone as S
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtWidgets import QApplication
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv[:1])
    S.install()
    mod = load_package()
    desktop = S.Desktop()
    mod.launch(desktop)
    app.aboutToQuit.connect(mod.shutdown)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
