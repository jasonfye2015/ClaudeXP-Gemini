"""Copilot Voice: local speech recognition and speech synthesis for local AI chat."""
import os
import queue
import subprocess
import sys
import tempfile
import threading
import wave
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioOutput, QAudioSource, QMediaDevices, QMediaPlayer
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton,
                               QProgressBar, QVBoxLayout, QWidget)

from claudecore.ai import ai_models, broker, llm_server
from claudecore import host

VOICE_ROOT = llm_server.models_dir() / "voice"
MODELS_ROOT = VOICE_ROOT / "models"
PYTHON_HOME = VOICE_ROOT / "python312"
BASE_PYTHON = PYTHON_HOME / "python.exe"
SHARED_PYTHON = llm_server.models_dir() / "image-gen" / "python312" / "python.exe"
PYTHON_INSTALLER = VOICE_ROOT / "python-3.12.10-amd64.exe"
PYTHON_INSTALLER_URL = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
RUNTIME = VOICE_ROOT / "runtime312"
RUNTIME_READY = RUNTIME / ".claudexp-ready"
WORKER = Path(__file__).with_name("copilot_voice_worker.py")
REQUIREMENTS = Path(__file__).with_name("requirements-voice.txt")
WHISPER_DIR = MODELS_ROOT / "whisper-base.en"
PIPER_DIR = MODELS_ROOT / "en_US-lessac-medium"
_window = None

RATE = 16000
MAX_RECORD_SECONDS = 90
READY_STATUS = "Ready. Hold the button while speaking; release when finished."
SETUP_STATUS = "Set up the local speech engines and models to begin."


def _temporary_audio_path():
    fd, path = tempfile.mkstemp(prefix="copilot-voice-", suffix=".wav")
    os.close(fd)
    return Path(path)


def _runtime_python():
    return RUNTIME / "Scripts" / "python.exe"


def _engine_ready():
    return _runtime_python().is_file() and RUNTIME_READY.is_file()


def _models_ready():
    return ((WHISPER_DIR / "model.bin").is_file()
            and (PIPER_DIR / "en_US-lessac-medium.onnx").is_file()
            and (PIPER_DIR / "en_US-lessac-medium.onnx.json").is_file())


class VoiceTask(QThread):
    message = Signal(str)
    completed = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, operation, **options):
        super().__init__()
        self.operation = operation
        self.options = options
        self.process = None

    def cancel(self):
        self.requestInterruption()

    def _command(self, command):
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding="utf-8", errors="replace", bufsize=1,
                                        creationflags=flags)
        lines = queue.Queue()

        def read_output():
            for line in self.process.stdout:
                lines.put(line.rstrip())
            lines.put(None)

        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        output_done = False
        last_lines = []
        result = ""
        while self.process.poll() is None or not output_done:
            if self.isInterruptionRequested() and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                reader.join(2)
                self.cancelled.emit()
                return None
            try:
                line = lines.get(timeout=0.1)
            except queue.Empty:
                continue
            if line is None:
                output_done = True
                continue
            if not line:
                continue
            last_lines.append(line)
            del last_lines[:-8]
            if line.startswith("TRANSCRIPT:"):
                result = line.partition(":")[2]
            elif line.startswith("AUDIO_READY:"):
                result = line.partition(":")[2]
            elif line.startswith("ERROR:"):
                last_lines[-1] = line.partition(":")[2]
            else:
                self.message.emit(line)
        code = self.process.wait()
        if code:
            raise RuntimeError("\n".join(last_lines) or f"Voice worker exited with status {code}.")
        return result

    def run(self):
        try:
            if self.operation == "setup":
                self._setup_runtime()
                if self.isInterruptionRequested():
                    self.cancelled.emit()
                    return
                self.message.emit("Downloading the local English speech models...")
                result = self._command([str(_runtime_python()), str(WORKER), "install",
                                        "--models-root", str(MODELS_ROOT)])
                if result is None:
                    return
                if not _models_ready():
                    raise RuntimeError("Speech setup finished but its local models are incomplete.")
                RUNTIME_READY.parent.mkdir(parents=True, exist_ok=True)
                RUNTIME_READY.touch()
                self.completed.emit("")
            else:
                command = [str(_runtime_python()), str(WORKER), self.operation,
                           "--models-root", str(MODELS_ROOT)]
                if self.operation == "transcribe":
                    command.extend(["--audio", str(self.options["audio"])])
                elif self.operation == "install-voice":
                    command.extend(["--voice-id", self.options["voice_id"]])
                elif self.operation == "speak":
                    command.extend(["--text", self.options["text"], "--output", str(self.options["output"])])
                    if "voice_id" in self.options:
                        command.extend(["--voice-id", self.options["voice_id"]])
                    if "length_scale" in self.options:
                        command.extend(["--length-scale", str(self.options["length_scale"])])
                result = self._command(command)
                if result is not None:
                    from claudecore.ai import llmlog as furlog
                    if self.operation == "transcribe":
                        furlog.event("SPEECH HEARD (Whisper)", str(result))
                    elif self.operation == "speak":
                        furlog.event("SPEECH SPOKEN (Piper)", self.options["text"],
                                     voice=self.options.get("voice_id"))
                    self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))

    def _setup_runtime(self):
        if not REQUIREMENTS.is_file():
            raise FileNotFoundError(f"Missing voice runtime requirements file: {REQUIREMENTS}")
        VOICE_ROOT.mkdir(parents=True, exist_ok=True)
        base_python = SHARED_PYTHON if SHARED_PYTHON.is_file() else BASE_PYTHON
        if not base_python.is_file():
            self._install_python()
            base_python = BASE_PYTHON
        if not _runtime_python().is_file():
            self.message.emit("Creating a private Python environment for local speech...")
            if self._command([str(base_python), "-m", "venv", str(RUNTIME)]) is None:
                return
        self.message.emit("Installing offline speech recognition and synthesis engines...")
        if self._command([str(_runtime_python()), "-m", "pip", "install", "-r", str(REQUIREMENTS),
                          "--only-binary=:all:"]) is None:
            return

    def _install_python(self):
        import urllib.request

        self.message.emit("Downloading private Python 3.12 for the local speech engines...")
        try:
            with urllib.request.urlopen(PYTHON_INSTALLER_URL, timeout=30) as response:
                with PYTHON_INSTALLER.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        if self.isInterruptionRequested():
                            raise InterruptedError("Python runtime download cancelled.")
                        output.write(chunk)
        except Exception:
            PYTHON_INSTALLER.unlink(missing_ok=True)
            raise
        env = dict(os.environ, CLAUDEXP_PYTHON_INSTALLER=str(PYTHON_INSTALLER))
        verify = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "$s=Get-AuthenticodeSignature -LiteralPath $env:CLAUDEXP_PYTHON_INSTALLER; "
             "if ($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notlike "
             "'*Python Software Foundation*') { exit 1 }"],
            env=env, capture_output=True, text=True, check=False)
        if verify.returncode:
            PYTHON_INSTALLER.unlink(missing_ok=True)
            raise RuntimeError("The Python installer did not pass its Python Software Foundation signature check.")
        try:
            PYTHON_HOME.mkdir(parents=True, exist_ok=True)
            self.message.emit("Installing Python privately under Local Storage\\LLM Models\\voice...")
            self._command([str(PYTHON_INSTALLER), "/quiet", "InstallAllUsers=0", f"TargetDir={PYTHON_HOME}",
                           "Include_pip=1", "Include_launcher=0", "Include_test=0", "PrependPath=0",
                           "Shortcuts=0", "AssociateFiles=0"])
        finally:
            PYTHON_INSTALLER.unlink(missing_ok=True)
        if not BASE_PYTHON.is_file():
            raise RuntimeError("The private Python installer completed but python.exe was not created.")


class CopilotVoice(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.task = None
        self.job = None
        self.recording = False
        self.audio_source = None
        self.audio_io = None
        self.record_format = None
        self.audio_chunks = []
        self.history = []
        self.turn_id = 0
        self.closing = False
        self.audio_path = None
        self.speech_path = None

        self.setStyleSheet("""
            QWidget#copilotvoice { background: #ECE9D8; }
            QLabel, QCheckBox { font-family: Tahoma; font-size: 11px; }
            QPushButton { font-family: Tahoma; font-size: 11px; padding: 4px 10px; }
            QPlainTextEdit { font-family: Tahoma; font-size: 11px; }
        """)
        self.setObjectName("copilotvoice")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(QLabel("Talk naturally. Voice processing stays local; temporary audio is deleted after use."))

        self.conversation = QPlainTextEdit()
        self.conversation.setReadOnly(True)
        self.conversation.setPlaceholderText("Your conversation will appear here.")
        layout.addWidget(self.conversation, 1)

        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        controls = QHBoxLayout()
        self.record_button = QPushButton("Hold to Talk")
        self.record_button.setToolTip("Press and hold to speak; release to transcribe.")
        self.record_button.pressed.connect(self.start_recording)
        self.record_button.released.connect(self.stop_recording)
        controls.addWidget(self.record_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)
        self.cancel_button.setEnabled(False)
        controls.addWidget(self.cancel_button)
        self.clear_button = QPushButton("Clear Conversation")
        self.clear_button.clicked.connect(self.clear_conversation)
        controls.addWidget(self.clear_button)
        layout.addLayout(controls)

        self.license_link = QLabel(
            '<a href="https://huggingface.co/Systran/faster-whisper-base.en">Whisper model (MIT)</a>'
            ' &nbsp;|&nbsp; '
            '<a href="https://github.com/OHF-Voice/piper1-gpl">Piper engine (GPL-3.0)</a>'
            ' &nbsp;|&nbsp; '
            '<a href="https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/lessac/medium">'
            'Piper voice and license</a>')
        self.license_link.setOpenExternalLinks(True)
        layout.addWidget(self.license_link)
        self.license_ack = QCheckBox("I reviewed the model and voice licenses and agree to follow their terms.")
        layout.addWidget(self.license_ack)
        self.license_ack.setChecked(host.voice_license_accepted())
        self.setup_button = QPushButton("Set Up Local Voice (downloads models)")
        self.setup_button.clicked.connect(self.setup_voice)
        layout.addWidget(self.setup_button)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.errorOccurred.connect(self._playback_error)
        self.player.mediaStatusChanged.connect(self._playback_status)
        self.record_limit = QTimer(self)
        self.record_limit.setSingleShot(True)
        self.record_limit.timeout.connect(self.stop_recording)
        self._refresh()

    def _refresh(self):
        ready = _engine_ready() and _models_ready()
        busy = self._busy()
        self.setup_button.setEnabled(not busy and not ready)
        self.record_button.setEnabled(not busy and ready and not QMediaDevices.defaultAudioInput().isNull())
        self.clear_button.setEnabled(not busy and bool(self.history))
        self.cancel_button.setEnabled(busy or self.recording)
        if self.status.text() in ("", READY_STATUS, SETUP_STATUS):
            self.status.setText(READY_STATUS if ready else SETUP_STATUS)

    def _busy(self):
        return ((self.task is not None and self.task.isRunning()) or self.job is not None)

    def _start_task(self, operation, **options):
        task = VoiceTask(operation, **options)
        self.task = task
        task.message.connect(self.status.setText)
        task.completed.connect(self._task_done)
        task.failed.connect(self._task_failed)
        task.cancelled.connect(self._task_cancelled)
        task.finished.connect(self._task_finished)
        self.progress.show()
        self.record_button.setEnabled(False)
        self.setup_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        task.start()

    def setup_voice(self):
        if not self.license_ack.isChecked():
            QMessageBox.warning(self, "Copilot Voice", "Review both model and voice licenses before downloading.")
            return
        if QMessageBox.question(
                self, "Set Up Local Voice",
                "This downloads the local speech engine, an English speech-recognition model, and one English "
                "speech voice into Local Storage\\LLM Models\\voice. Setup needs an Internet connection; "
                "afterward, transcription and speech run locally. Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self._start_task("setup")

    def start_recording(self):
        if self.recording or self._busy():
            return
        if not (_engine_ready() and _models_ready()):
            self.status.setText("Set up the local speech engines before recording.")
            return
        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            self.status.setText("No microphone is available. Connect a microphone and try again.")
            return
        preferred = device.preferredFormat()
        rates = {RATE, 22050, 44100, 48000, preferred.sampleRate()}
        channels = {1, 2, preferred.channelCount()}
        audio_format = None
        for sample_rate in sorted((rate for rate in rates if rate > 0), key=lambda rate: abs(rate - RATE)):
            for channel_count in sorted(ch for ch in channels if ch > 0):
                candidate = QAudioFormat()
                candidate.setSampleRate(sample_rate)
                candidate.setChannelCount(channel_count)
                candidate.setSampleFormat(QAudioFormat.Int16)
                if device.isFormatSupported(candidate):
                    audio_format = candidate
                    break
            if audio_format is not None:
                break
        if audio_format is None:
            self.status.setText("The selected microphone does not support PCM audio recording.")
            return
        self.record_format = audio_format
        self.audio_source = QAudioSource(device, audio_format, self)
        self.audio_io = self.audio_source.start()
        if self.audio_io is None or self.audio_source.error() != QAudio.Error.NoError:
            self.status.setText("The microphone could not be opened. Check device access and privacy settings.")
            self.audio_source = None
            return
        self.audio_chunks = []
        self.audio_io.readyRead.connect(self._read_audio)
        self.recording = True
        self.status.setText("Listening locally... release the button when you are done.")
        self.record_button.setText("Listening... release to finish")
        self.cancel_button.setEnabled(True)
        self.record_limit.start(MAX_RECORD_SECONDS * 1000)

    def _read_audio(self):
        if self.audio_io is not None:
            data = bytes(self.audio_io.readAll().data())
            if data:
                self.audio_chunks.append(data)

    def stop_recording(self):
        if not self.recording:
            return
        self.recording = False
        self.record_limit.stop()
        self._read_audio()
        if self.audio_source is not None:
            self.audio_source.stop()
            self.audio_source.deleteLater()
        self.audio_source = None
        self.audio_io = None
        raw = b"".join(self.audio_chunks)
        self.audio_chunks = []
        minimum_bytes = self.record_format.sampleRate() * self.record_format.channelCount() * 2 * 2 // 3
        if len(raw) < minimum_bytes:
            self.status.setText("That recording was too short. Hold the button and speak a little longer.")
            self._refresh()
            return
        self.audio_path = _temporary_audio_path()
        with wave.open(str(self.audio_path), "wb") as wav_file:
            wav_file.setnchannels(self.record_format.channelCount())
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.record_format.sampleRate())
            wav_file.writeframes(raw[:len(raw) // 2 * 2])
        self.status.setText("Transcribing with the local Whisper model...")
        self._start_task("transcribe", audio=self.audio_path)

    def _task_done(self, result):
        operation = self.task.operation
        if operation == "setup":
            self.license_ack.setChecked(False)
            self.status.setText("Local speech engines and models are ready. No audio leaves this computer.")
        elif operation == "transcribe":
            self._remove_audio("audio_path")
            if not result.strip():
                self.status.setText("No speech was recognized. Try speaking closer to the microphone.")
                return
            self._send_to_local_ai(result.strip())
        elif operation == "speak":
            self.speech_path = Path(result)
            self.player.setSource(QUrl.fromLocalFile(result))
            self.player.play()
            self.status.setText("Speaking the local AI reply...")

    def _send_to_local_ai(self, text):
        self.conversation.appendPlainText(f"You: {text}")
        if not llm_server.available():
            self.status.setText("The local AI is not ready. Check Control Panel > AI Models.")
            QMessageBox.warning(self, "Copilot Voice", llm_server.status())
            return
        model = ai_models.model_for("conversation")
        if not model:
            self.status.setText("Install a local language model in Control Panel > AI Models first.")
            return
        self.history.append({"role": "user", "content": text})
        self.conversation.appendPlainText("Copilot: ")
        self.clear_button.setEnabled(False)
        self.status.setText("Thinking with your local AI...")

        turn = self.turn_id

        def on_chunk(response):
            if turn == self.turn_id:
                self._replace_current_reply(response)

        def on_done(response, error):
            if turn != self.turn_id:
                if self.closing:
                    self.frame.desktop.close_window(self.frame)
                return
            self.job = None
            if error:
                stopped = error == "stopped"
                self._replace_current_reply("Cancelled." if stopped else f"Local AI error: {error}")
                self.status.setText("Cancelled." if stopped else "The local AI request failed.")
                self.clear_button.setEnabled(bool(self.history))
                if self.closing:
                    self.frame.desktop.close_window(self.frame)
                return
            answer = response.strip()
            self._replace_current_reply(answer)
            self.history.append({"role": "assistant", "content": answer})
            self.history = self.history[-20:]
            self.clear_button.setEnabled(True)
            self.status.setText("Preparing local speech...")
            if answer:
                self.speech_path = _temporary_audio_path()
                self.audio_output.setVolume(0.0 if host.muted() else 1.0)
                self._start_task("speak", text=answer, output=self.speech_path)
            else:
                self.status.setText("The local AI returned an empty reply.")

        context = self.history[-12:]
        self.job = broker.get().stream(
            model, context, {"num_ctx": ai_models.config()["context"], "temperature": 0.7},
            on_chunk, on_done, broker.FOREGROUND, think=False)

    def _replace_current_reply(self, text):
        content = self.conversation.toPlainText()
        prefix = "Copilot: "
        marker = content.rfind(prefix)
        if marker >= 0:
            self.conversation.setPlainText(content[:marker] + prefix + text)
            cursor = self.conversation.textCursor()
            cursor.movePosition(cursor.End)
            self.conversation.setTextCursor(cursor)

    def _task_failed(self, message):
        if self.task is not None:
            if self.task.operation == "transcribe":
                self._remove_audio("audio_path")
            elif self.task.operation == "speak":
                self._remove_audio("speech_path")
        self.status.setText("The local voice operation failed.")
        QMessageBox.critical(self, "Copilot Voice", message)

    def _task_cancelled(self):
        if self.task is not None:
            if self.task.operation == "transcribe":
                self._remove_audio("audio_path")
            elif self.task.operation == "speak":
                self._remove_audio("speech_path")
        self.status.setText("Cancelled.")

    def _task_finished(self):
        self.progress.hide()
        self.task = None
        if self.closing:
            self.frame.desktop.close_window(self.frame)
            return
        self._refresh()

    def cancel(self):
        if self.recording:
            self.recording = False
            self.record_limit.stop()
            if self.audio_source is not None:
                self.audio_source.stop()
                self.audio_source.deleteLater()
            self.audio_source = None
            self.audio_io = None
            self.audio_chunks = []
            self.status.setText("Recording cancelled.")
            self._refresh()
        elif self.task is not None and self.task.isRunning():
            self.task.cancel()
            self.status.setText("Cancelling...")
            self.cancel_button.setEnabled(False)
        elif self.job is not None:
            self.job.stop()
            self.status.setText("Cancelling local AI request...")

    def clear_conversation(self):
        self.turn_id += 1
        if self.job is not None:
            self.job.stop()
            self.job = None
        self.history.clear()
        self.conversation.clear()
        self.status.setText("Conversation cleared.")
        self._refresh()

    def _playback_error(self, _error, message):
        self.player.setSource(QUrl())
        self._remove_audio("speech_path")
        self.status.setText(f"Local speech playback failed: {message}")

    def _playback_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setSource(QUrl())
            self._remove_audio("speech_path")
            self.status.setText(READY_STATUS)

    def _remove_audio(self, attr):
        path = getattr(self, attr)
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                self.status.setText(f"Could not remove temporary voice audio: {exc}")
            setattr(self, attr, None)

    def closeEvent(self, event):
        if self.recording or self._busy() or self.job is not None:
            self.closing = True
            event.ignore()
            self.cancel()
            return
        self.player.stop()
        self.player.setSource(QUrl())
        self._remove_audio("audio_path")
        self._remove_audio("speech_path")
        event.accept()


def voice_icon():
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#333333"), 1.5))
    painter.setBrush(QColor("#E8E8E8"))
    painter.drawRoundedRect(10, 3, 12, 19, 6, 6)
    painter.setBrush(Qt.NoBrush)
    painter.drawArc(6, 10, 20, 17, 180 * 16, 180 * 16)
    painter.drawLine(16, 27, 16, 30)
    painter.drawLine(11, 30, 21, 30)
    painter.end()
    return QIcon(pixmap)


def open_copilot_voice(desktop):
    global _window
    if _window is not None and _window.isVisible():
        desktop.activate(_window)
        return _window
    body = CopilotVoice(desktop)
    _window = host.window(desktop, "Copilot Voice", body, voice_icon(), (620, 480))
    body.frame = _window
    desktop.open_window(_window)
    return _window


def shutdown():
    global _window
    if _window is not None:
        window, _window = _window, None
        window.request_close()
