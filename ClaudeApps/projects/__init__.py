"""The Projects: the user's own programs in Local Storage/Projects, launched from any era's Start menu.

Each one runs in its own window, the way it was built (a packaged .exe, or a Python script on this computer's own
Python). The ones that talk to a language model expect Ollama; they're given OLLAMA_HOST pointing at the Timeline's
Ollama bridge (claudecore.ai.ollama_bridge), so they use the same models as everything else."""
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF

from claudecore import host

# key -> (name, description, path inside Projects, how it runs, uses the language model)
PROJECTS = {
    "virtualpet": ("Virtual Pet 27.0", "A desktop pet that talks with you", "VirtualPet27.0/ollama_pet.py", "python", True),
    "flymind": ("Fly Mind", "A companion with a real fruit fly's limbic system",
                "fly_mind/dist/FlyMind/FlyMind.exe", "exe", True),
    "flymind1": ("FlyMind v1.0", "The FlyMind companion, with everything it remembers",
                 "FlyMind LLM Project/FlyMind v1.0.exe", "exe", True),
    "flybrainviewer": ("Fly Brain Viewer", "A live 3D map of a fruit fly's brain, talking through a language model",
                       "fly_brain_viewer/dist/FlyBrainViewer.exe", "exe", True),
    "flybraindungeon": ("Fly Brain Dungeon", "A dungeon crawler whose monster has a real mushroom-body brain",
                        "fly_brain_parts/dungeon/dist/FlyBrainDungeon.exe", "exe", False),
}
_running = {}


def projects_root():
    return host.local_storage() / "Projects"


def project_path(key):
    return projects_root() / PROJECTS[key][2]


def _python():
    """This computer's own Python, windowless (pythonw.exe beside python.exe)."""
    exe = Path(sys.executable)
    windowed = exe.with_name("pythonw.exe")
    return windowed if windowed.exists() else exe


def launch(desktop, key):
    name, _desc, _rel, how, llm = PROJECTS[key]
    path = project_path(key)
    if not path.exists():
        host.message(desktop, name, f"{name} isn't where it should be:\n{path}\n\nPut the project back in "
                     "E:\\Projects (Local Storage) and try again.", "error")
        return None
    proc = _running.get(key)
    if proc is not None and proc.poll() is None:
        host.message(desktop, name, f"{name} is already running.", "info")
        return proc
    env = dict(os.environ)
    if llm:
        try:
            from claudecore.ai import ollama_bridge
            env["OLLAMA_HOST"] = ollama_bridge.url()
        except Exception:
            pass
    cmd = [str(_python()), str(path)] if how == "python" else [str(path)]
    try:
        proc = subprocess.Popen(cmd, cwd=str(path.parent), env=env)
    except OSError as exc:
        host.message(desktop, name, f"{name} couldn't start:\n{exc}", "error")
        return None
    _running[key] = proc
    host.sound("default")
    return proc


def launcher(key):
    return lambda desktop: launch(desktop, key)


def shutdown_all():
    """Leave them running: they're separate programs (and Fly Mind would lose an unsaved thought if killed)."""


# ---- icons -----------------------------------------------------------------------------------------------------
def _canvas():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    return pm, p


def _fly(p, cx, cy, scale=1.0, body="#3A2A1A"):
    """A little fruit fly: red eyes, striped body, glassy wings."""
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(200, 220, 255, 150))
    p.drawEllipse(QRectF(cx - 9 * scale, cy - 6 * scale, 8 * scale, 5 * scale))
    p.drawEllipse(QRectF(cx + 1 * scale, cy - 6 * scale, 8 * scale, 5 * scale))
    p.setBrush(QColor(body))
    p.drawEllipse(QRectF(cx - 3 * scale, cy - 4 * scale, 6 * scale, 10 * scale))
    p.setBrush(QColor("#D02018"))
    p.drawEllipse(QRectF(cx - 3.6 * scale, cy - 6 * scale, 3 * scale, 3 * scale))
    p.drawEllipse(QRectF(cx + 0.6 * scale, cy - 6 * scale, 3 * scale, 3 * scale))
    p.setPen(QPen(QColor("#C89040"), 1))
    p.drawLine(int(cx - 2.6 * scale), int(cy + 2 * scale), int(cx + 2.6 * scale), int(cy + 2 * scale))


def icon(key):
    pm, p = _canvas()
    if key == "virtualpet":
        p.setPen(QPen(QColor("#8A5A20"), 1))
        p.setBrush(QColor("#F0B860"))
        p.drawEllipse(QRectF(5, 9, 22, 20))
        p.drawPolygon(QPolygonF([QPointF(5, 13), QPointF(6, 3), QPointF(13, 11)]))           # ears
        p.drawPolygon(QPolygonF([QPointF(27, 13), QPointF(26, 3), QPointF(19, 11)]))
        p.setBrush(QColor("#202020"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(10.5, 15, 3.5, 4))
        p.drawEllipse(QRectF(18, 15, 3.5, 4))
        p.setBrush(QColor("#D85060"))
        p.drawEllipse(QRectF(14.5, 21, 3, 2.4))
    elif key in ("flymind", "flymind1"):
        g = QLinearGradient(0, 2, 0, 30)
        g.setColorAt(0, QColor("#7A4AC8"))
        g.setColorAt(1, QColor("#2A1A5A"))
        p.setPen(QPen(QColor("#1A0E3A"), 1))
        p.setBrush(g)
        p.drawRoundedRect(QRectF(2.5, 2.5, 27, 27), 8, 8)
        _fly(p, 16, 16, 1.25, "#F0E0FF")
        if key == "flymind1":
            p.setPen(QColor("white"))
            p.setFont(QFont("Arial", 6, QFont.Bold))
            p.drawText(QRectF(14, 22, 16, 8), Qt.AlignRight, "1.0")
    elif key == "flybrainviewer":
        p.setPen(QPen(QColor("#0A2A3A"), 1))
        p.setBrush(QColor("#0E1A28"))
        p.drawRoundedRect(QRectF(2.5, 4.5, 27, 22), 3, 3)
        for x, y, c in ((10, 12, "#40E0FF"), (16, 10, "#FF60C0"), (21, 14, "#80FF80"), (13, 18, "#FFD040"),
                        (19, 20, "#40E0FF"), (8, 17, "#FF8040")):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(c))
            p.drawEllipse(QRectF(x - 1.6, y - 1.6, 3.2, 3.2))
        p.setPen(QPen(QColor(120, 200, 255, 120), 1))
        p.drawLine(10, 12, 16, 10)
        p.drawLine(16, 10, 21, 14)
        p.drawLine(13, 18, 19, 20)
    else:                                                 # the dungeon: a stone archway with a fly in it
        p.setPen(QPen(QColor("#303030"), 1))
        p.setBrush(QColor("#6A6A72"))
        p.drawRect(QRectF(2.5, 4.5, 27, 25))
        p.setBrush(QColor("#101014"))
        p.drawRoundedRect(QRectF(9, 10, 14, 19), 7, 7)
        _fly(p, 16, 20, 0.9, "#40C040")
    p.end()
    return QIcon(pm)
