"""Copilot Image Creator: install local Stable Diffusion models and generate images."""
import html
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox,
                               QPlainTextEdit, QProgressBar, QPushButton, QSpinBox, QDoubleSpinBox,
                               QVBoxLayout, QWidget)

from ..explorer import vfs
from ..llm_server import models_dir
from ..paths import ROOT
from ..wm import XPWindow

MODEL_INFO = {
    "sd15": ("Stable Diffusion 1.5", "stable-diffusion-v1-5/stable-diffusion-v1-5",
             "About 2-4 GB", "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5"),
    "sdxl": ("Stable Diffusion XL", "stabilityai/stable-diffusion-xl-base-1.0",
             "About 5-7 GB", "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0"),
}
IMAGEGEN_ROOT = models_dir() / "image-gen"
MODEL_ROOT = IMAGEGEN_ROOT / "models"
PYTHON_HOME = IMAGEGEN_ROOT / "python312"
BASE_PYTHON = PYTHON_HOME / "python.exe"
PYTHON_INSTALLER = IMAGEGEN_ROOT / "python-3.12.10-amd64.exe"
PYTHON_INSTALLER_URL = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
RUNTIME = IMAGEGEN_ROOT / "runtime312"
RUNTIME_READY = RUNTIME / ".claudexp-ready"
WORKER = Path(__file__).with_name("imagegen_worker.py")
REQUIREMENTS = ROOT / "requirements-imagegen.txt"
CUDA_INDEX = "https://download.pytorch.org/whl/cu128"
_window = None


def _model_path(key):
    return MODEL_ROOT / key


def _installed(key):
    path = _model_path(key)
    components = ["unet", "vae", "text_encoder"]
    if key == "sdxl":
        components.append("text_encoder_2")
    return ((path / "model_index.json").is_file()
            and all((path / part / "config.json").is_file()
                    and any((path / part).glob("*.safetensors")) for part in components))


def _runtime_python():
    return RUNTIME / "Scripts" / "python.exe"


def _engine_ready():
    return _runtime_python().is_file() and RUNTIME_READY.is_file()


_active = set()


def generating():
    """True while any image is being generated (used by the desktop System Monitor)."""
    return bool(_active)


class ImageTask(QThread):
    message = Signal(str)
    progress = Signal(int, int)
    completed = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, operation, model, **options):
        super().__init__()
        self.operation = operation
        self.model = model
        self.options = options
        self.process = None

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
        image_path = ""
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
            if line.startswith("PROGRESS:"):
                try:
                    _, current, total = line.split(":")
                    self.progress.emit(int(current), int(total))
                except ValueError:
                    self.message.emit(line)
            else:
                self.message.emit(line)
            if line.startswith("IMAGE_READY:"):
                image_path = line.partition(":")[2]
        code = self.process.wait()
        if code:
            raise RuntimeError("\n".join(last_lines) or f"Worker exited with status {code}.")
        return image_path

    def run(self):
        counted = self.operation != "setup"
        if counted:
            _active.add(self)
        try:
            self._run()
        finally:
            _active.discard(self)

    def _run(self):
        try:
            if self.operation == "setup":
                self._ensure_python()
                if self.isInterruptionRequested():
                    self.cancelled.emit()
                    return
                if not _runtime_python().is_file():
                    self.message.emit("Creating the GTX 1080 Ti-compatible image environment...")
                    result = self._command([str(BASE_PYTHON), "-m", "venv", str(RUNTIME)])
                    if result is None:
                        return
                self.message.emit("Installing the Pascal-compatible CUDA image engine...")
                result = self._command([str(_runtime_python()), "-m", "pip", "install", "-r", str(REQUIREMENTS),
                                        "--only-binary=:all:", "--extra-index-url", CUDA_INDEX])
                if result is None:
                    return
                self.message.emit("Checking the CUDA engine against your graphics card...")
                result = self._command([
                    str(_runtime_python()), "-c",
                    "import torch; cap=torch.cuda.get_device_capability(); "
                    "arch=f'sm_{cap[0]}{cap[1]}'; "
                    "print('GPU:',torch.cuda.get_device_name()); "
                    "print('CUDA kernels:',','.join(torch.cuda.get_arch_list())); "
                    "assert torch.cuda.is_available() and arch in torch.cuda.get_arch_list(), "
                    "f'PyTorch has no {arch} kernels for this GPU'; "
                    "torch.ones(1, device='cuda'); print('CUDA GPU test passed')"])
                if result is None:
                    return
            else:
                command = [str(_runtime_python()), str(WORKER), self.operation, "--model", self.model]
                if self.operation == "install":
                    command.extend(["--models-root", str(MODEL_ROOT)])
                else:
                    command.extend(["--model-path", str(_model_path(self.model))])
                    for name, value in self.options.items():
                        command.extend(["--" + name.replace("_", "-"), str(value)])
                result = self._command(command)
            if result is None:
                return
            if self.operation == "setup":
                RUNTIME_READY.parent.mkdir(parents=True, exist_ok=True)
                RUNTIME_READY.touch()
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))

    def cancel(self):
        self.requestInterruption()

    def _ensure_python(self):
        if BASE_PYTHON.is_file():
            return
        IMAGEGEN_ROOT.mkdir(parents=True, exist_ok=True)
        self.message.emit("Downloading an isolated Python runtime for GTX 1080 Ti support...")
        try:
            import urllib.request
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
            self.message.emit("Installing Python privately under Local Storage\\LLM Models...")
            result = self._command([
                str(PYTHON_INSTALLER), "/quiet", "InstallAllUsers=0", f"TargetDir={PYTHON_HOME}",
                "Include_pip=1", "Include_launcher=0", "Include_test=0", "PrependPath=0",
                "Shortcuts=0", "AssociateFiles=0"])
            if result is None:
                return
        finally:
            PYTHON_INSTALLER.unlink(missing_ok=True)
        if not BASE_PYTHON.is_file():
            raise RuntimeError("The private Python installer completed but python.exe was not created.")


class ImageCreator(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.task = None
        self.image_path = None
        self._install_remaining = []
        self.closing = False
        self.setStyleSheet("""
            QWidget#imagecreator { background: #ECE9D8; }
            QLabel { font-family: Tahoma; font-size: 11px; }
            QGroupBox { font-family: Tahoma; font-size: 11px; }
            QPlainTextEdit { font-family: Tahoma; font-size: 11px; }
            QPushButton, QComboBox, QSpinBox, QDoubleSpinBox { font-family: Tahoma; font-size: 11px; }
        """)
        self.setObjectName("imagecreator")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)

        info = QLabel("Generate images locally with Stable Diffusion. Install the engine and at least one model first.")
        info.setWordWrap(True)
        outer.addWidget(info)

        model_box = QGroupBox("Model")
        model_grid = QGridLayout(model_box)
        self.model = QComboBox()
        for key, (name, _repo, size, _url) in MODEL_INFO.items():
            self.model.addItem(name, key)
        self.model.currentIndexChanged.connect(self._refresh)
        self.model_status = QLabel()
        self.install_button = QPushButton("Install Selected Model")
        self.install_button.clicked.connect(self.install_selected)
        self.install_both_button = QPushButton("Install Both Models")
        self.install_both_button.clicked.connect(self.install_both)
        self.setup_button = QPushButton("Set Up Image Engine")
        self.setup_button.clicked.connect(self.setup_engine)
        self.license_link = QLabel()
        self.license_link.setOpenExternalLinks(True)
        self.license_ack = QCheckBox("I have reviewed the model license(s) and agree to follow their terms.")
        self.license_ack.setToolTip("For Install Both, review both model cards linked above.")
        self.model.currentIndexChanged.connect(lambda *_: self.license_ack.setChecked(False))
        self.all_license_links = QLabel(
            '<a href="https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5">SD 1.5 license</a>'
            ' &nbsp;|&nbsp; '
            '<a href="https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0">SDXL license</a>')
        self.all_license_links.setOpenExternalLinks(True)
        model_grid.addWidget(QLabel("Choose a model:"), 0, 0)
        model_grid.addWidget(self.model, 0, 1)
        model_grid.addWidget(self.model_status, 1, 0, 1, 2)
        model_grid.addWidget(self.license_link, 2, 0, 1, 2)
        model_grid.addWidget(self.all_license_links, 3, 0, 1, 2)
        model_grid.addWidget(self.license_ack, 4, 0, 1, 2)
        install_row = QHBoxLayout()
        install_row.addWidget(self.install_button)
        install_row.addWidget(self.install_both_button)
        install_row.addWidget(self.setup_button)
        model_grid.addLayout(install_row, 5, 0, 1, 2)
        outer.addWidget(model_box)

        options_box = QGroupBox("Prompt and options")
        grid = QGridLayout(options_box)
        grid.addWidget(QLabel("Prompt:"), 0, 0, 1, 2)
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText("Describe the image you want to create...")
        self.prompt.setFixedHeight(72)
        grid.addWidget(self.prompt, 1, 0, 1, 2)
        grid.addWidget(QLabel("Negative prompt:"), 2, 0, 1, 2)
        self.negative = QPlainTextEdit()
        self.negative.setPlaceholderText("Optional: things to avoid in the image")
        self.negative.setFixedHeight(46)
        grid.addWidget(self.negative, 3, 0, 1, 2)
        self.width = self._spin(512, 512, 1024, 64)
        self.height = self._spin(512, 512, 1024, 64)
        self.steps = self._spin(25, 10, 60, 1)
        self.seed = self._spin(0, 0, 2147483647, 1)
        self.guidance = QDoubleSpinBox()
        self.guidance.setRange(1, 20)
        self.guidance.setSingleStep(0.5)
        self.guidance.setValue(7)
        for col, label, widget in ((0, "Width:", self.width), (2, "Height:", self.height),
                                   (4, "Steps:", self.steps), (6, "Guidance:", self.guidance),
                                   (8, "Seed:", self.seed)):
            grid.addWidget(QLabel(label), 4, col)
            grid.addWidget(widget, 4, col + 1)
        outer.addWidget(options_box)

        self.preview = QLabel("Your generated image will appear here.")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(450, 220)
        self.preview.setStyleSheet("background: #404040; color: white; border: 1px solid #808080;")
        outer.addWidget(self.preview, 1)

        bottom = QHBoxLayout()
        self.status = QLabel("Ready.")
        bottom.addWidget(self.status, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFixedWidth(150)
        bottom.addWidget(self.progress)
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        bottom.addWidget(self.generate_button)
        bottom.addWidget(self.cancel_button)
        outer.addLayout(bottom)
        self._refresh()

    @staticmethod
    def _spin(value, minimum, maximum, step):
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setValue(value)
        return spin

    def _selected_model(self):
        return self.model.currentData()

    def _refresh(self):
        key = self._selected_model()
        name, _repo, size, url = MODEL_INFO[key]
        installed = _installed(key)
        ready = _engine_ready()
        self.model_status.setText(f"{name}: {'Installed' if installed else 'Not installed'} "
                                  f"({size} download). Image engine: {'Ready' if ready else 'Not installed'}.")
        self.license_link.setText(f'<a href="{html.escape(url, quote=True)}">Model card and license</a>')
        self.install_button.setEnabled(not self._busy() and ready and not installed)
        self.install_both_button.setEnabled(not self._busy() and ready)
        self.setup_button.setEnabled(not self._busy() and not ready)
        self.generate_button.setEnabled(not self._busy() and ready and installed)

    def _busy(self):
        return self.task is not None and self.task.isRunning()

    def _start_task(self, operation, model, **options):
        task = ImageTask(operation, model, **options)
        self.task = task
        task.message.connect(self.status.setText)
        task.progress.connect(self._step_progress)
        task.completed.connect(self._task_done)
        task.failed.connect(self._task_failed)
        task.cancelled.connect(self._task_cancelled)
        task.finished.connect(self._task_finished)
        self.progress.setRange(0, 0)
        self.generate_button.setEnabled(False)
        self.install_button.setEnabled(False)
        self.install_both_button.setEnabled(False)
        self.setup_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        task.start()

    def _step_progress(self, current, total):
        self.progress.setRange(0, total)
        self.progress.setValue(current)
        self.status.setText(f"Generating image: step {current} of {total}...")

    def setup_engine(self):
        if not REQUIREMENTS.is_file():
            QMessageBox.critical(self, "Image Creator", f"Missing runtime requirements file:\n{REQUIREMENTS}")
            return
        self._start_task("setup", self._selected_model())

    def install_selected(self):
        if not _engine_ready():
            QMessageBox.warning(self, "Image Creator", "Set up the local image engine before installing models.")
            return
        if not self.license_ack.isChecked():
            QMessageBox.warning(self, "Image Creator", "Review the selected model's license before installing it.")
            return
        key = self._selected_model()
        if _installed(key):
            self.status.setText("This model is already installed.")
            return
        self._start_task("install", key)

    def install_both(self):
        if not _engine_ready():
            QMessageBox.warning(self, "Image Creator", "Set up the local image engine before installing models.")
            return
        if not self.license_ack.isChecked():
            QMessageBox.warning(self, "Image Creator", "Review both model licenses before installing them.")
            return
        missing = [key for key in MODEL_INFO if not _installed(key)]
        if not missing:
            self.status.setText("Both models are already installed.")
            return
        answer = QMessageBox.question(
            self, "Install both models",
            "This will download several gigabytes of model files into "
            "Local Storage\\LLM Models\\image-gen. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        self._install_remaining = list(missing)
        self._install_next()

    def _install_next(self):
        if self._install_remaining:
            self._start_task("install", self._install_remaining.pop(0))

    def generate(self):
        key = self._selected_model()
        prompt = self.prompt.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Image Creator", "Enter a prompt before generating an image.")
            self.prompt.setFocus()
            return
        if not _engine_ready():
            QMessageBox.warning(self, "Image Creator", "Set up the local image engine first.")
            return
        if not _installed(key):
            QMessageBox.warning(self, "Image Creator", "Install the selected model first.")
            return
        vfs.my_pictures().mkdir(parents=True, exist_ok=True)
        output = vfs.my_pictures() / f"Image Creator {time.strftime('%Y%m%d-%H%M%S')}.png"
        from .. import furlog
        furlog.event("IMAGE REQUEST", prompt, model=key, size=f"{self.width.value()}x{self.height.value()}",
                     steps=self.steps.value(), guidance=self.guidance.value(), seed=self.seed.value(),
                     negative=self.negative.toPlainText().strip(), output=output.name)
        self._start_task("generate", key, prompt=prompt, negative_prompt=self.negative.toPlainText().strip(),
                         width=self.width.value(), height=self.height.value(), steps=self.steps.value(),
                         guidance=self.guidance.value(), seed=self.seed.value(), output=output)

    def cancel(self):
        if self.task is not None and self.task.isRunning():
            self.status.setText("Cancelling...")
            self.cancel_button.setEnabled(False)
            self.task.cancel()

    def _task_done(self, result):
        if result:
            self.image_path = Path(result)
            pixmap = QPixmap(str(self.image_path))
            self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.status.setText(f"Saved to My Pictures\\{self.image_path.name}")
        elif self._install_remaining:
            self.status.setText("Model installed.")
        else:
            self.status.setText("Image engine is ready." if self.task.operation == "setup" else "Model installed.")

    def _task_failed(self, message):
        self.status.setText("The operation failed.")
        self._install_remaining = []
        QMessageBox.critical(self, "Image Creator", message)

    def _task_cancelled(self):
        self.status.setText("Cancelled.")
        self._install_remaining = []

    def _task_finished(self):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.cancel_button.setEnabled(False)
        self.task = None
        self._refresh()
        if getattr(self, "_install_remaining", None):
            QTimer.singleShot(0, self._install_next)
        elif self.closing:
            self.frame.desktop.close_window(self.frame)

    def resizeEvent(self, event):
        if self.image_path is not None:
            pixmap = QPixmap(str(self.image_path))
            self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        if self._busy():
            self.closing = True
            event.ignore()
            self.cancel()
            return
        event.accept()


def imagegen_icon():
    icon = QIcon()
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    from PySide6.QtGui import QColor, QPainter, QPen
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#4A4A4A"), 1))
    painter.setBrush(QColor("#D8E8F8"))
    painter.drawRoundedRect(2, 3, 28, 26, 3, 3)
    painter.setBrush(QColor("#4B8F53"))
    painter.drawEllipse(6, 18, 8, 7)
    painter.setBrush(QColor("#70BFEA"))
    painter.drawEllipse(17, 7, 7, 7)
    painter.setPen(QPen(QColor("#805070"), 2))
    painter.drawLine(6, 26, 20, 12)
    painter.end()
    icon.addPixmap(pixmap)
    return icon


def open_imagegen(desktop):
    global _window
    if _window is not None and _window.isVisible():
        desktop.activate(_window)
        return _window
    body = ImageCreator(desktop)
    _window = XPWindow(desktop, "Copilot Image Creator", body, imagegen_icon(), (760, 620))
    body.frame = _window
    desktop.open_window(_window)
    return _window


def shutdown():
    global _window
    if _window is not None:
        window, _window = _window, None
        window.request_close()
