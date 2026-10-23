"""Where Kithylin AI keeps everything: one folder, so the program can be lifted out of the Timeline whole.

    kithylinai/
      assets/     the icon (your account picture) and anything else the program is built with
      Art/        Kithylin's Art - the gallery (build_art.py copies it here and makes the thumbnails)
      Models/     the Kithylin models (<name>/<name>-Q4_K_M.gguf + info.json), made by selfmodel.make_model
      Engine/     optional: a llama.cpp build of its own (llama-server.exe and DLLs) for running standalone
      Data/       settings, the chat history and saved chats, the engine log
The Timeline's own engine builds and models (Local Storage/LLM Models) are used when they're there too."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMELINE = HERE.parents[1]
ASSETS = HERE / "assets"
ART = HERE / "Art"
MODELS = HERE / "Models"
ENGINE = HERE / "Engine"
DATA = HERE / "Data"
ICON = ASSETS / "kithylin.jpg"

LLM = TIMELINE / "Local Storage" / "LLM Models"
TIMELINE_MODELS = LLM / "models"
TIMELINE_ENGINES = {"vulkan": LLM / "llama.cpp" / "vulkan", "cuda": LLM / "llama.cpp" / "cuda"}


def hosted():
    """Running inside one of the Timeline's computers (a host is registered), or standalone?"""
    try:
        from claudecore import host
        host.get()
        return True
    except Exception:
        return False
