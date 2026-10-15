"""Getting ClaudeXP's language models in place: what's needed, downloading it, and installing it.

MANIFEST lists the engine (llama.cpp) and every model ClaudeXP knows, with each file's address, size and SHA-256, the
folder it belongs in under E:\\LLM Models, and the info.json that goes with it. Groups: 'essential' (the engine and
the two small Gemma models - enough for everyone to talk and to see pictures), 'recommended' (the bigger models
the residents and ClaudeAI are best with) and 'optional'.

Installer (a QObject, work done in a thread) downloads with resume (.part files), retries, checks size and SHA-256,
unpacks the engine and copies the Visual C++ runtime next to it; or installs from files you already have (linked
when on the same drive, copied otherwise); or from a web address you give it. The AI Model Setup Assistant
(aimodels_cpl.py) drives it.
"""
import hashlib
import json
import os
import shutil
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

from PySide6.QtCore import QObject, Signal

HF = "https://huggingface.co/{repo}/resolve/main/{file}"
ENGINE_URL = "https://github.com/ggml-org/llama.cpp/releases/download/b11533/llama-b11533-bin-win-vulkan-x64.zip"
VC_RUNTIME = ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll",
              "concrt140.dll"]
VC_REDIST_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
CHUNK = 1 << 20
RETRIES = 3


def _f(repo, name, size, sha):
    return {"name": name, "url": HF.format(repo=repo, file=name), "size": size, "sha256": sha}


MANIFEST = [
    {"key": "engine", "title": "llama.cpp engine (Vulkan)", "group": "essential", "kind": "engine",
     "folder": "llama.cpp", "what": "Runs the models on your graphics card (NVIDIA, AMD or Intel) or the CPU.",
     "files": [{"name": "llama-b11533-bin-win-vulkan-x64.zip", "url": ENGINE_URL, "size": 33458880,
                "sha256": "807b9143dfb372c2ed9a189c3fded5cd799106585c99cbbf0bb7bd45dad03598"}]},
    {"key": "gemma3-1b", "title": "Gemma 3 1B (Google)", "group": "essential", "kind": "model",
     "what": "Tiny and fast: the residents' diaries, e-mail and background chatter.",
     "files": [_f("ggml-org/gemma-3-1b-it-GGUF", "gemma-3-1b-it-Q4_K_M.gguf", 806058240,
                  "8ccc5cd1f1b3602548715ae25a66ed73fd5dc68a210412eea643eb20eb75a135")],
     "info": {"title": "Gemma 3 1B", "source": "https://huggingface.co/ggml-org/gemma-3-1b-it-GGUF",
              "licence": "Gemma Terms of Use (https://ai.google.dev/gemma/terms)",
              "notes": "Tiny and very fast: good for background work (journals, e-mail, ambient chatter). Text only. "
                       "Q4_K_M.", "suggested": ["background"]}},
    {"key": "gemma3-4b", "title": "Gemma 3 4B (Google)", "group": "essential", "kind": "model",
     "what": "A quick all-rounder that can see pictures - buddies can talk with this alone.",
     "files": [_f("ggml-org/gemma-3-4b-it-GGUF", "gemma-3-4b-it-Q4_K_M.gguf", 2489757856,
                  "882e8d2db44dc554fb0ea5077cb7e4bc49e7342a1f0da57901c0802ea21a0863"),
               _f("ggml-org/gemma-3-4b-it-GGUF", "mmproj-model-f16.gguf", 851251104,
                  "8c0fb064b019a6972856aaae2c7e4792858af3ca4561be2dbf649123ba6c40cb")],
     "info": {"title": "Gemma 3 4B", "source": "https://huggingface.co/ggml-org/gemma-3-4b-it-GGUF",
              "licence": "Gemma Terms of Use (https://ai.google.dev/gemma/terms)",
              "notes": "Google's small all-rounder: quick, sees pictures, 128K context. Q4_K_M.",
              "suggested": ["pictures"]}},
    {"key": "nemomix-unleashed-12b", "title": "NemoMix Unleashed 12B", "group": "recommended", "kind": "model",
     "what": "The residents' voice: strong at conversation and roleplay. Wants a GPU with about 8 GB.",
     "files": [_f("bartowski/NemoMix-Unleashed-12B-GGUF", "NemoMix-Unleashed-12B-Q4_K_M.gguf", 7477203776,
                  "327afee83a36cd76814e3dd36fc62cb306ffcff164b4f55f1dbe7317d690fb82")],
     "info": {"title": "NemoMix Unleashed 12B",
              "source": "https://huggingface.co/bartowski/NemoMix-Unleashed-12B-GGUF (model by MarinaraSpaghetti, a "
                        "merge of Mistral Nemo 12B fine-tunes)", "licence": "Apache 2.0",
              "notes": "Strong at roleplay and stories. Text only. Q4_K_M. ChatML is set here, with <|im_end|> as a "
                       "stop word.", "suggested": ["conversation"], "chat_template": "chatml",
              "stop": ["<|im_end|>", "<|im_start|>"]}},
    {"key": "gemma4-12b", "title": "Gemma 4 12B (Google)", "group": "recommended", "kind": "model",
     "what": "ClaudeAI's model: sees pictures and thinks before it answers.",
     "files": [_f("ggml-org/gemma-4-12B-it-GGUF", "gemma-4-12B-it-Q4_0.gguf", 7219673216,
                  "3712b9bd32cae83a22f67ee7a4466d8d7a4f21646ac8a07d19bf9418e8767a70"),
               _f("ggml-org/gemma-4-12B-it-GGUF", "mmproj-gemma-4-12B-it-Q8_0.gguf", 158987616,
                  "59e62255435dda870e2d1de97cc031330b31a898bac12b38a182cecff9cd3738")],
     "info": {"title": "Gemma 4 12B", "source": "https://huggingface.co/ggml-org/gemma-4-12B-it-GGUF",
              "licence": "Apache 2.0", "notes": "Google's newer, stronger model: sees pictures and thinks before "
                                                "answering. Q4_0 (with a Q8_0 picture projector).",
              "suggested": ["assistant"], "thinking": True}},
    {"key": "qwen25-coder-7b", "title": "Qwen2.5 Coder 7B (Alibaba)", "group": "optional", "kind": "model",
     "what": "Python Studio's AI Helper.",
     "files": [_f("bartowski/Qwen2.5-Coder-7B-Instruct-GGUF", "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf", 4683074336,
                  "1664fccab734674a50763490a8c6931b70e3f2f8ec10031b54806d30e5f956b6")],
     "info": {"title": "Qwen2.5 Coder 7B (Alibaba)",
              "source": "https://huggingface.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF", "licence": "Apache 2.0",
              "notes": "A strong code model; wants a GPU or a fast CPU. Q4_K_M, text only.", "suggested": []}},
    {"key": "qwen25-coder-14b", "title": "Qwen2.5 Coder 14B (Alibaba)", "group": "optional", "kind": "model",
     "what": "The best code model here; needs about 10 GB of graphics memory.",
     "files": [_f("bartowski/Qwen2.5-Coder-14B-Instruct-GGUF", "Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf", 8988111072,
                  "2946d28c9e1bb2bcae6d42e8678863a31775df6f740315c7d7e6d6b6411f5937")],
     "info": {"title": "Qwen2.5 Coder 14B (Alibaba)",
              "source": "https://huggingface.co/bartowski/Qwen2.5-Coder-14B-Instruct-GGUF", "licence": "Apache 2.0",
              "notes": "The best code model here; needs a GPU with about 10 GB of memory. Q4_K_M, text only.",
              "suggested": ["coding"]}},
    {"key": "qwen25-coder-1.5b", "title": "Qwen2.5 Coder 1.5B (Alibaba)", "group": "optional", "kind": "model",
     "what": "A tiny code model - fast even on the CPU.",
     "files": [_f("bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF", "Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf", 986048800,
                  "f530705d447660a4336c329981af164b471b60b974b1d808d57e8ec9fe23b239")],
     "info": {"title": "Qwen2.5 Coder 1.5B (Alibaba)",
              "source": "https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF", "licence": "Apache 2.0",
              "notes": "Tiny code model: fast even on the CPU. Q4_K_M, text only.", "suggested": []}},
    {"key": "qwen3-4b-instruct", "title": "Qwen3 4B Instruct (Alibaba)", "group": "optional", "kind": "model",
     "what": "A small all-rounder, good at code and plain talk.",
     "files": [_f("unsloth/Qwen3-4B-Instruct-2507-GGUF", "Qwen3-4B-Instruct-2507-Q4_K_M.gguf", 2497281120,
                  "3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597")],
     "info": {"title": "Qwen3 4B Instruct 2507 (Alibaba)",
              "source": "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF", "licence": "Apache 2.0",
              "notes": "Best small all-rounder for code plus plain talk. Q4_K_M, text only.", "suggested": []}},
    {"key": "mag-mell-12b", "title": "Mag-Mell R1 12B", "group": "optional", "kind": "model",
     "what": "Another roleplay voice. No licence stated by its author: personal use only.",
     "files": [_f("bartowski/MN-12B-Mag-Mell-R1-GGUF", "MN-12B-Mag-Mell-R1-Q4_K_M.gguf", 7477205984,
                  "4e1588065eff8c310c8f2d7292da9ceef1d7fc58ecb6c455f994cf2e1b160e9d")],
     "info": {"title": "Mag-Mell R1 12B",
              "source": "https://huggingface.co/bartowski/MN-12B-Mag-Mell-R1-GGUF (model by inflatebot)",
              "licence": "None stated by the author - fine for personal use; unclear for redistribution",
              "notes": "A popular roleplay/storytelling voice; less filtered. Text only. Q4_K_M.", "suggested": []}},
]
GROUPS = [("essential", "Essential", "Needed for anyone to talk."),
          ("recommended", "Recommended", "What the residents and ClaudeAI are best with."),
          ("optional", "Optional", "Extras.")]


def root():
    from .llm_server import models_dir
    return models_dir()


def item(key):
    return next(i for i in MANIFEST if i["key"] == key)


def target_dir(it):
    return root() / ("llama.cpp" if it["kind"] == "engine" else Path("models") / it["key"])


def target(it, f):
    return target_dir(it) / f["name"]


def installed(it):
    """Is this item in place? (the engine: llama-server.exe unpacked; a model: every file at its full size)"""
    if it["kind"] == "engine":
        from . import llm_server
        return llm_server.find_engine() is not None
    return all(target(it, f).is_file() and target(it, f).stat().st_size == f["size"] for f in it["files"])


def partial(it):
    """Bytes already downloaded (finished files and .part files)."""
    n = 0
    for f in it["files"]:
        t = target(it, f)
        if t.is_file():
            n += t.stat().st_size
        elif t.with_name(t.name + ".part").is_file():
            n += t.with_name(t.name + ".part").stat().st_size
    return n


def size(it):
    return sum(f["size"] for f in it["files"])


def essentials_missing():
    return [it for it in MANIFEST if it["group"] == "essential" and not installed(it)]


def free_space():
    path = root()
    path.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(path).free


def fmt(n):
    return f"{n / 1e9:.1f} GB" if n >= 1e9 else f"{n / 1e6:.0f} MB"


def sha256_of(path, progress=None, cancel=None):
    h = hashlib.sha256()
    done = 0
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK * 4), b""):
            if cancel is not None and cancel.is_set():
                return None
            h.update(block)
            done += len(block)
            if progress:
                progress(done)
    return h.hexdigest()


class Installer(QObject):
    """Does the work in a thread. status(key, text), progress(key, done, total), item_done(key, ok, error),
    all_done(). One job at a time."""
    status = Signal(str, str)
    progress = Signal(str, object, object)
    item_done = Signal(str, bool, str)
    all_done = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cancel = threading.Event()
        self.thread = None

    def busy(self):
        return self.thread is not None and self.thread.is_alive()

    def stop(self):
        self.cancel.set()

    def _run(self, fn):
        if self.busy():
            return False
        self.cancel.clear()

        def body():
            try:
                fn()
            finally:
                self.all_done.emit()
        self.thread = threading.Thread(target=body, daemon=True, name="llm-setup")
        self.thread.start()
        return True

    # ---- downloading -------------------------------------------------------------------------------------------
    def download(self, keys, urls=None):
        """Download and install these items. urls: {file name: address} to use instead of the usual ones."""
        urls = urls or {}

        def work():
            for key in keys:
                if self.cancel.is_set():
                    break
                it = item(key)
                if installed(it):
                    self.item_done.emit(key, True, "")
                    continue
                try:
                    self._download_item(it, urls)
                    self._finish(it)
                    self.item_done.emit(key, True, "")
                except Exception as e:                      # noqa: BLE001 - reported to the user, who can retry
                    self.item_done.emit(key, False, str(e) or e.__class__.__name__)
        return self._run(work)

    def _download_item(self, it, urls):
        target_dir(it).mkdir(parents=True, exist_ok=True)
        total = size(it)
        base = 0
        for f in it["files"]:
            dest = target(it, f)
            if dest.is_file() and dest.stat().st_size == f["size"]:
                base += f["size"]
                continue
            url = urls.get(f["name"]) or f["url"]
            last = None
            for attempt in range(1, RETRIES + 1):
                if self.cancel.is_set():
                    raise RuntimeError("Cancelled.")
                try:
                    self._fetch(it["key"], url, dest, f, base, total, attempt)
                    last = None
                    break
                except Exception as e:                      # noqa: BLE001
                    last = e
                    if self.cancel.is_set():
                        raise RuntimeError("Cancelled.") from e
                    self.status.emit(it["key"], f"Problem: {e}. Trying again ({attempt}/{RETRIES})...")
                    time.sleep(2 * attempt)
            if last is not None:
                raise last
            base += f["size"]

    def _fetch(self, key, url, dest, f, base, total, attempt):
        part = dest.with_name(dest.name + ".part")
        have = part.stat().st_size if part.is_file() else 0
        if f.get("size") and have > f["size"]:
            part.unlink()
            have = 0
        headers = {"User-Agent": "ClaudeXP-LLM-Setup/1.0"}
        if have:
            headers["Range"] = f"bytes={have}-"
        req = urllib.request.Request(url, headers=headers)
        self.status.emit(key, f"Connecting to {url.split('/')[2]}...")
        with urllib.request.urlopen(req, timeout=30) as resp:
            if have and resp.status != 206:                  # the server won't resume: start over
                have = 0
            length = int(resp.headers.get("Content-Length") or 0)
            expected = f.get("size") or (have + length)
            mode = "ab" if have else "wb"
            started, got = time.monotonic(), 0
            with open(part, mode) as out:
                while True:
                    if self.cancel.is_set():
                        raise RuntimeError("Cancelled.")
                    block = resp.read(CHUNK)
                    if not block:
                        break
                    out.write(block)
                    got += len(block)
                    secs = max(0.5, time.monotonic() - started)
                    self.progress.emit(key, base + have + got, total)
                    self.status.emit(key, f"Downloading {f['name']}: {fmt(have + got)} of {fmt(expected)} "
                                          f"({got / secs / 1e6:.1f} MB/s)")
        size_now = part.stat().st_size
        if f.get("size") and size_now != f["size"]:
            raise RuntimeError(f"the download stopped early ({fmt(size_now)} of {fmt(f['size'])})")
        self._verify(key, part, f)
        os.replace(part, dest)

    def _verify(self, key, path, f):
        if not f.get("sha256"):
            return
        total = path.stat().st_size
        self.status.emit(key, f"Checking {f['name']}...")
        digest = sha256_of(path, lambda n: self.progress.emit(key, n, total), self.cancel)
        if digest is None:
            raise RuntimeError("Cancelled.")
        if digest != f["sha256"]:
            path.unlink(missing_ok=True)
            raise RuntimeError(f"{f['name']} is damaged (its checksum doesn't match) - it was deleted; try again")

    # ---- finishing an item --------------------------------------------------------------------------------------
    def _finish(self, it):
        if it["kind"] == "engine":
            self._unpack_engine(it)
        else:
            info = target_dir(it) / "info.json"
            if not info.exists() and it.get("info"):
                info.write_text(json.dumps(it["info"], indent=2), encoding="utf-8")

    def _unpack_engine(self, it):
        z = target(it, it["files"][0])
        dest = root() / "llama.cpp" / "vulkan"
        dest.mkdir(parents=True, exist_ok=True)
        self.status.emit(it["key"], "Unpacking the engine...")
        with zipfile.ZipFile(z) as zf:
            for member in zf.infolist():
                name = Path(member.filename).name
                if not name or member.is_dir():
                    continue
                with zf.open(member) as src, open(dest / name, "wb") as out:
                    shutil.copyfileobj(src, out)
        missing = []
        system32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
        for dll in VC_RUNTIME:                               # app-local copies of the Visual C++ runtime
            if (dest / dll).exists():
                continue
            if (system32 / dll).exists():
                shutil.copy2(system32 / dll, dest / dll)
            elif dll in ("vcruntime140.dll", "msvcp140.dll"):
                missing.append(dll)
        if missing:
            self.status.emit(it["key"], "The engine needs the Microsoft Visual C++ Redistributable (x64): install it "
                                        f"from {VC_REDIST_URL}")
        if not (dest / "llama-server.exe").exists():
            raise RuntimeError("the engine package didn't contain llama-server.exe")

    # ---- files you already have ---------------------------------------------------------------------------------
    def use_files(self, key, chosen):
        """chosen: {file name in the manifest: path on this computer}. Each is checked, then linked or copied in."""
        def work():
            it = item(key)
            try:
                target_dir(it).mkdir(parents=True, exist_ok=True)
                for f in it["files"]:
                    src = chosen.get(f["name"])
                    if src is None:
                        continue
                    src = Path(src)
                    if src.stat().st_size != f["size"]:
                        raise RuntimeError(f"{src.name} isn't the right file ({fmt(src.stat().st_size)}, expected "
                                           f"{fmt(f['size'])})")
                    self._verify_existing(key, src, f)
                    self._bring_in(key, src, target(it, f))
                self._finish(it)
                self.item_done.emit(key, installed(it), "" if installed(it) else "Some of its files are still "
                                                                                 "missing.")
            except Exception as e:                           # noqa: BLE001
                self.item_done.emit(key, False, str(e) or e.__class__.__name__)
        return self._run(work)

    def _verify_existing(self, key, src, f):
        if not f.get("sha256"):
            return
        total = src.stat().st_size
        self.status.emit(key, f"Checking {src.name}...")
        digest = sha256_of(src, lambda n: self.progress.emit(key, n, total), self.cancel)
        if digest is None:
            raise RuntimeError("Cancelled.")
        if digest != f["sha256"]:
            raise RuntimeError(f"{src.name} doesn't match the file ClaudeXP expects (checksum differs)")

    def _bring_in(self, key, src, dest):
        if src.resolve() == dest.resolve():
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            if dest.exists():
                dest.unlink()
            os.link(src, dest)                                # same drive: instant, no extra space
            self.status.emit(key, f"Linked {src.name}.")
            return
        except OSError:
            pass
        total = src.stat().st_size
        tmp = dest.with_name(dest.name + ".part")
        done = 0
        with open(src, "rb") as a, open(tmp, "wb") as b:
            for block in iter(lambda: a.read(CHUNK * 4), b""):
                if self.cancel.is_set():
                    raise RuntimeError("Cancelled.")
                b.write(block)
                done += len(block)
                self.progress.emit(key, done, total)
                self.status.emit(key, f"Copying {src.name}: {fmt(done)} of {fmt(total)}")
        os.replace(tmp, dest)

    def find_in_folder(self, folder):
        """{key: {file name: path}} for every manifest file found (by name and size) anywhere under folder."""
        found = {}
        wanted = {(f["name"].lower(), f["size"]): (it["key"], f["name"]) for it in MANIFEST for f in it["files"]}
        for dirpath, _dirs, files in os.walk(folder):
            for name in files:
                p = Path(dirpath) / name
                try:
                    k = (name.lower(), p.stat().st_size)
                except OSError:
                    continue
                if k in wanted:
                    key, fname = wanted[k]
                    found.setdefault(key, {})[fname] = str(p)
        return found

    # ---- any model from a web address -----------------------------------------------------------------------------
    def custom(self, url, folder_name=None):
        """Download a .gguf from any address into a new model folder."""
        name = url.split("?")[0].rstrip("/").split("/")[-1] or "model.gguf"
        if not name.lower().endswith(".gguf"):
            name += ".gguf"
        folder = folder_name or Path(name).stem.lower().replace(" ", "-")
        it = {"key": f"custom:{folder}", "title": folder, "group": "optional", "kind": "model",
              "files": [{"name": name, "url": url, "size": 0, "sha256": ""}],
              "info": {"title": Path(name).stem, "source": url, "licence": "(see the model's page)",
                       "notes": "Added from a web address in the AI Model Setup Assistant.", "suggested": []}}

        def work():
            dest_dir = root() / "models" / folder
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                self._fetch(it["key"], url, dest_dir / name, it["files"][0], 0, 0, 1)
                (dest_dir / "info.json").write_text(json.dumps(it["info"], indent=2), encoding="utf-8")
                self.item_done.emit(it["key"], True, "")
            except Exception as e:                           # noqa: BLE001
                self.item_done.emit(it["key"], False, str(e) or e.__class__.__name__)
        return self._run(work)
