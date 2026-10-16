"""The 'Speech and voice' page of first-boot Windows Setup: show the speech licences, set the local speech engine
up if it is not already there, then prove it works (speak a sentence, listen to it, compare) before moving on."""
import json
import re
from html import escape

from PySide6.QtCore import QThread, Signal

from ..paths import DATA
import copilot_voice as cv

ACCEPT_FILE = DATA / "speech_license.json"
TEST_SENTENCE = "The quick brown fox jumps over the lazy dog."
PASS_RATIO = 0.7

SUMMARY = (
    "<b>Whisper base.en</b> (speech recognition) - MIT License.<br>"
    "<b>faster-whisper</b> (runs Whisper) - MIT License.<br>"
    "<b>Piper</b> (speech engine) - GPL-3.0.<br>"
    "<b>Piper voices</b> - each voice has its own terms, listed below. Check them before sharing a voice or "
    "using it commercially."
)


def accepted():
    try:
        return bool(json.loads(ACCEPT_FILE.read_text(encoding="utf-8")).get("accepted"))
    except (OSError, ValueError, AttributeError):
        return False


def set_accepted(value=True):
    try:
        ACCEPT_FILE.parent.mkdir(parents=True, exist_ok=True)
        ACCEPT_FILE.write_text(json.dumps({"accepted": bool(value)}), encoding="utf-8")
    except OSError:
        pass


def voice_terms():
    """[(voice name, dataset licence)] read from the model cards saved next to each installed voice."""
    out = []
    try:
        folders = sorted(p for p in cv.MODELS_ROOT.iterdir() if (p / "MODEL_CARD").is_file())
    except OSError:
        return out
    for folder in folders:
        try:
            text = (folder / "MODEL_CARD").read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        match = re.search(r"License:\s*(.+)", text)
        out.append((folder.name, match.group(1).strip() if match else "see the model card"))
    return out


def license_html():
    rows = "".join(f"<li>{escape(name)}: {escape(terms)}</li>" for name, terms in voice_terms())
    voices = f"<ul>{rows}</ul>" if rows else ("<br>The voice licences are saved with each voice once it is "
                                              "downloaded.")
    return f"{SUMMARY}{voices}"


def _words(text):
    return re.findall(r"[a-z']+", text.lower())


def sounds_right(heard, said=TEST_SENTENCE):
    want, got = _words(said), set(_words(heard))
    return bool(want) and sum(1 for w in want if w in got) / len(want) >= PASS_RATIO


class SpeechSetup(QThread):
    """Sets the engine up when needed, then runs the speak -> listen test. Ends with passed() or failed()."""
    message = Signal(str)
    passed = Signal(str)
    failed = Signal(str)

    def __init__(self, voice_id=None):
        super().__init__()
        self.voice_id = voice_id
        self._current = None

    def cancel(self):
        self.requestInterruption()
        if self._current is not None:
            self._current.cancel()

    def _step(self, operation, **options):
        """Run one VoiceTask on this thread; returns its result text, raises on failure or cancel."""
        task = VoiceStep(operation, **options)
        self._current = task
        task.message.connect(self.message.emit)
        task.run()
        self._current = None
        if self.isInterruptionRequested():
            raise InterruptedError("Cancelled.")
        if task.error:
            raise RuntimeError(task.error)
        return task.result

    def run(self):
        import os
        import tempfile
        from pathlib import Path
        wav = None
        try:
            if not (cv._engine_ready() and cv._models_ready()):
                self.message.emit("Setting up the speech engine (this needs the models in Local Storage, or a "
                                  "network connection)...")
                self._step("setup")
            voice = self.voice_id or "en_US-lessac-medium"
            fd, name = tempfile.mkstemp(prefix="setup-speech-", suffix=".wav")
            os.close(fd)
            wav = Path(name)
            self.message.emit("Testing speech: speaking a sentence...")
            self._step("speak", text=TEST_SENTENCE, output=wav, voice_id=voice)
            self.message.emit("Testing speech: listening to it...")
            heard = self._step("transcribe", audio=wav)
            if not sounds_right(heard):
                raise RuntimeError(f"The test sentence came back as: \"{heard}\"")
            self.passed.emit(heard)
        except InterruptedError:
            self.failed.emit("Cancelled.")
        except Exception as exc:
            self.failed.emit(str(exc) or exc.__class__.__name__)
        finally:
            if wav is not None:
                wav.unlink(missing_ok=True)


class VoiceStep(cv.VoiceTask):
    """A VoiceTask that is run directly by the caller's thread and reports its outcome as attributes."""

    def __init__(self, operation, **options):
        super().__init__(operation, **options)
        self.result = ""
        self.error = ""
        self.completed.connect(lambda r: setattr(self, "result", r))
        self.failed.connect(lambda e: setattr(self, "error", e))
        self.cancelled.connect(lambda: setattr(self, "error", "Cancelled."))
