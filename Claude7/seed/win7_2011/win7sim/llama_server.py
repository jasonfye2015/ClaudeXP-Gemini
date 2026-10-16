from __future__ import annotations

import ipaddress
from pathlib import Path
from urllib.parse import urlsplit

from PySide6.QtCore import QObject, QProcess, Signal

from .llama_cpp import normalize_llama_url


def _model_launch_options(model_file: Path) -> list[str]:
    """Known model-specific corrections; leave other GGUF metadata alone."""
    name = model_file.stem.casefold()
    if name == "nemomix-unleashed-12b" or name.startswith("nemomix-unleashed-12b-"):
        # Bartowski's NemoMix GGUF has no tokenizer.chat_template, so the
        # server otherwise falls back to ChatML. This merge expects Mistral
        # instruction tokens, with NeMo's Tekken whitespace conventions.
        # DRY is the author's recommended repeated-sequence control.
        return [
            "--chat-template", "mistral-v3-tekken",
            "--dry-multiplier", "0.8",
        ]
    return []


class LlamaServerProcess(QObject):
    """Own one llama-server child process for the current desktop session."""

    started = Signal()
    stopped = Signal(str)
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self.process.started.connect(self.started.emit)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._process_error)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self._config: tuple[str, str, str, str, int] | None = None
        self._stderr = ""
        self._starting = False

    @property
    def is_running(self) -> bool:
        return self.process.state() != QProcess.ProcessState.NotRunning

    @property
    def is_starting(self) -> bool:
        return self._starting and self.is_running

    @property
    def last_error(self) -> str:
        return self._stderr.strip()[-3000:]

    def matches(
        self, executable: str, model_path: str, alias: str, endpoint: str, gpu_layers: int,
    ) -> bool:
        return self._config == (
            executable, model_path, alias, normalize_llama_url(endpoint), gpu_layers,
        ) and self.is_running

    def start(
        self,
        executable: str,
        model_path: str,
        alias: str,
        endpoint: str,
        gpu_layers: int = 99,
    ) -> bool:
        """Launch an explicitly configured binary/model; never downloads either."""
        if self.is_running:
            raise RuntimeError("The app-managed llama-server is already running.")

        executable_path = Path(executable).expanduser()
        model_file = Path(model_path).expanduser()
        if not executable_path.is_file():
            raise ValueError(
                f"llama-server was not found at {executable_path}. "
                "Choose its executable in AI / Local Models."
            )
        if not model_file.is_file() or model_file.suffix.lower() != ".gguf":
            raise ValueError(
                "Choose an existing .gguf model file. The simulator does not download models."
            )
        alias = alias.strip()
        if not alias:
            raise ValueError(
                "Choose a model name for Direct conversations before starting llama-server."
            )
        if type(gpu_layers) is not int or not 0 <= gpu_layers <= 999:
            raise ValueError("GPU layers must be a whole number from 0 to 999.")

        base_url = normalize_llama_url(endpoint)
        parsed = urlsplit(base_url)
        host = (parsed.hostname or "").lower()
        try:
            local_host = host == "localhost" or ipaddress.ip_address(host).is_loopback
        except ValueError:
            local_host = False
        if (
            parsed.scheme != "http" or not local_host
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment
        ):
            raise ValueError(
                "The app-managed server must use a plain HTTP loopback address "
                "without an API path, such as http://127.0.0.1:9931."
            )
        port = parsed.port or 80
        if not 1 <= port <= 65535:
            raise ValueError("The llama-server port must be from 1 to 65535.")

        self._stderr = ""
        self._config = (
            str(executable_path), str(model_file), alias, base_url, gpu_layers,
        )
        self._starting = True
        self.process.setProgram(str(executable_path))
        self.process.setArguments([
            "--model", str(model_file),
            "--alias", alias,
            "--host", host,
            "--port", str(port),
            "--n-gpu-layers", str(gpu_layers),
        ] + _model_launch_options(model_file))
        self.process.start()
        return True

    def mark_ready(self) -> None:
        self._starting = False

    def stop(self) -> None:
        self._starting = False
        if not self.is_running:
            return
        self.process.terminate()
        if not self.process.waitForFinished(2000):
            self.process.kill()
            self.process.waitForFinished(2000)
        self._config = None

    def _read_stderr(self) -> None:
        chunk = bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace")
        if chunk:
            self._stderr = (self._stderr + chunk)[-6000:]

    def _process_error(self, error) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._starting = False
            detail = self.process.errorString().strip()
            self.failed.emit(
                f"Could not start llama-server: {detail or 'the process could not be started.'}"
            )

    def _finished(self, exit_code, exit_status) -> None:
        self._starting = False
        self._read_stderr()
        detail = self.last_error
        if exit_code and detail:
            message = f"llama-server stopped with exit code {exit_code}: {detail}"
        elif exit_code:
            message = f"llama-server stopped with exit code {exit_code}."
        elif exit_status == QProcess.ExitStatus.CrashExit:
            message = f"llama-server crashed.{f' {detail}' if detail else ''}"
        else:
            message = "llama-server stopped."
        self.stopped.emit(message)
