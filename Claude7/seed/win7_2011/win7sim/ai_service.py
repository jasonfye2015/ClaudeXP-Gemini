from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

from PySide6.QtCore import QObject, QTimer, Signal

from .ai_settings import AISettings, ROLE_LABELS, load_ai_settings, save_ai_settings, normalize_endpoint
from .local_ai import FailureCategory
from .llama_cpp import LlamaCppClient
from .llama_server import LlamaServerProcess
from .ai_credentials import WindowsCredentialStore
from .messenger_context import reply_reserve

BACKENDS = {"llama_cpp": LlamaCppClient}


@dataclass
class AIJob:
    request_id: int
    role: str
    messages: list[dict[str, str]]
    cancelled: bool = False
    input_budget: int | None = None
    output_limit: int | None = None
    prepared: bool = False
    dispatched: bool = False


class AIService(QObject):
    """One local engine and one generation at a time, shared by all desktop apps."""

    changed = Signal()
    statusChanged = Signal(str, bool)
    modelsChanged = Signal(object)
    jobFinished = Signal(int, bool, str)
    jobInputPrepared = Signal(int, object)
    llmPhaseChanged = Signal(int, str, str)
    llmRequestSent = Signal(int, str, str, object)
    llmResponseCaptured = Signal(int, str, bool, str)

    def __init__(self, parent=None, backend_factory=None, settings=None, credential_store=None):
        super().__init__(parent)
        self.load_error = ""
        try:
            self.settings = (settings or load_ai_settings()).validated()
        except (OSError, ValueError) as exc:
            self.settings = AISettings()
            self.load_error = str(exc)
        self._backend_factory = backend_factory
        self.credentials = credential_store if credential_store is not None else WindowsCredentialStore()
        self.llama_server = LlamaServerProcess(self)
        self.llama_server.started.connect(self._managed_server_started)
        self.llama_server.stopped.connect(self._managed_server_stopped)
        self.llama_server.failed.connect(self._managed_server_failed)
        self._managed_url = ""
        self._managed_server_attempted = False
        self._managed_server_stopping = False
        self._startup_deadline = 0.0
        self._startup_timer = QTimer(self)
        self._startup_timer.setSingleShot(True)
        self._startup_timer.timeout.connect(self._retry_managed_server)
        self._create_backend()
        self.available_models: list[str] = []
        self.models_by_url: dict[str, list[str]] = {}
        self.context_windows_by_url: dict[str, dict[str, int]] = {}
        self._endpoint_errors: dict[str, str] = {}
        self._model_errors: dict[tuple[str, str], str] = {}
        self._discovery_urls: list[str] = []
        self._discovery_url = ""
        self._discovery_errors: list[str] = []
        self._discovery_cancelled = False
        self._connected_endpoint = ""
        self.connected = False
        self.status = self.load_error or "Not connected. Open Options → AI / Local Models."
        self.error = bool(self.load_error)
        self._queue: list[AIJob] = []
        self._active: AIJob | None = None
        self._next_id = 0
        self._testing = False
        self._stopped = False
        self.chat_available = True
        self.background_paused = False
        self.maintenance_priority_mode = False

    @property
    def is_busy(self):
        return self._testing or self._active is not None or bool(self._queue)

    @property
    def queue_count(self):
        return len(self._queue)

    @property
    def can_reconnect(self):
        return not self._stopped and not self.is_busy and not self.backend.is_busy

    def is_available(self, role):
        return (
            not self._stopped and not self._testing and self.connected
            and self.settings.models[role] in self.models_for_role(role)
        )

    def models_for_role(self, role):
        return self.models_by_url.get(self.settings.endpoint_for(role), [])

    def context_for_role(self, role="direct"):
        endpoint, model = self.settings.endpoint_for(role), self.settings.models[role]
        manual = self.settings.context_limits.get(endpoint, {}).get(model)
        discovered = self.context_windows_by_url.get(endpoint, {}).get(model)
        if manual:
            return min(manual, discovered) if discovered else manual, "manual limit" + (
                " (capped by provider)" if discovered and manual > discovered else ""
            )
        return discovered, "provider-reported window" if discovered else "unknown window"

    def set_context_limit(self, limit, role="direct"):
        if self.is_busy or self.backend.is_busy:
            raise RuntimeError("Wait for model work to finish before changing context limits.")
        endpoint, model = self.settings.endpoint_for(role), self.settings.models[role]
        if not model:
            raise ValueError("Choose a model before saving a context limit.")
        limits = {url: dict(models) for url, models in self.settings.context_limits.items()}
        limits.setdefault(endpoint, {})
        if limit:
            limits[endpoint][model] = limit
        else:
            limits[endpoint].pop(model, None)
        from dataclasses import replace
        settings = replace(self.settings, context_limits=limits).validated()
        save_ai_settings(settings)
        self.settings = settings
        self.changed.emit()

    def _create_backend(self):
        self.backend = (self._backend_factory or LlamaCppClient)(self)
        self.backend.credential_resolver = lambda endpoint: self.credentials.get(
            self.settings.backend, endpoint
        )
        self.backend.modelsListed.connect(self._models_listed)
        self.backend.connectionFinished.connect(self._connected_for_job)
        self.backend.responseFinished.connect(self._response_finished)
        if hasattr(self.backend, "inputPrepared"):
            self.backend.inputPrepared.connect(self._input_prepared)
        request_starting = getattr(self.backend, "chatRequestStarting", None)
        self._backend_reports_chat_start = request_starting is not None
        if request_starting is not None:
            request_starting.connect(self._backend_chat_request_starting)

    def _status(self, text, error=False):
        notices = [*self._endpoint_errors.values(), *self._model_errors.values()]
        if notices:
            extra = [notice for notice in notices if notice not in text]
            if extra:
                text += "\n" + "\n".join(extra)
            error = True
        self.status, self.error = text, error
        self.statusChanged.emit(text, error)
        self.changed.emit()

    def update_api_key(self, backend, endpoint, value=None):
        """A credential edit takes effect immediately, independently of Apply.

        None removes a key. Invalidate the edited endpoint's discovery rather
        than allowing cached availability to imply the new key was tested.
        """
        if self.is_busy or self.backend.is_busy or self._stopped:
            raise RuntimeError("Wait for model work to finish before editing an API key.")
        endpoint = normalize_endpoint(backend, endpoint)
        if value is not None:
            from .ai_credentials import validate_api_key
            validate_api_key(value)
        try:
            if value is None:
                self.credentials.delete(backend, endpoint)
            else:
                self.credentials.set(backend, endpoint, value)
        except Exception:
            raise RuntimeError("Could not update the API key in Windows Credential Manager. No settings were changed.") from None
        if backend == "llama_cpp":
            self._model_errors = {
                key: message for key, message in self._model_errors.items() if key[0] != endpoint
            }
            self.models_by_url.pop(endpoint, None)
            self.context_windows_by_url.pop(endpoint, None)
            self.available_models = sorted({
                model for models in self.models_by_url.values() for model in models
            })
            self.connected = bool(self.models_by_url)
            if self.backend.base_url == endpoint:
                self.backend.is_connected = False
                self._connected_endpoint = ""
            self.modelsChanged.emit(self.available_models)
        self._status("API key removed." if value is None else "API key saved.")

    def apply(self, settings):
        if self.is_busy or self.backend.is_busy:
            raise RuntimeError("Wait for model work to finish, or cancel it before applying settings.")
        settings = settings.validated()
        if not settings.context_limits:
            settings.context_limits = self.settings.context_limits
        keep_managed_server = (
            self.llama_server.matches(
                settings.llama_server_executable,
                settings.llama_model_path,
                settings.models["direct"] or Path(settings.llama_model_path).stem,
                settings.url,
                settings.llama_gpu_layers,
            )
        )
        save_ai_settings(settings)
        if self.llama_server.is_running and not keep_managed_server:
            self._startup_timer.stop()
            self._managed_server_stopping = True
            self.llama_server.stop()
            self._managed_server_stopping = False
            self._managed_url = ""
        if not keep_managed_server:
            self._managed_server_attempted = False
        self.backend.deleteLater()
        self.settings = settings
        self._create_backend()
        self._connected_endpoint = ""
        self.load_error = ""
        self.connected = False
        self.available_models = []
        self.models_by_url = {}
        self.context_windows_by_url = {}
        self._endpoint_errors = {}
        self._model_errors = {}
        self.modelsChanged.emit([])
        self.test_connection()

    def reconnect(self):
        """Refresh saved endpoint availability only; never replay conversation jobs.

        This is an explicit, idle-only action, not a retry timer. Use the same
        discovery path as the saved-connection test so role endpoints, credentials,
        cancellation, and session shutdown keep their existing protections.
        """
        self.test_connection()

    def test_connection(self):
        if self.is_busy or self.backend.is_busy or self._stopped:
            raise RuntimeError("The engine is busy or this desktop session has ended.")
        if not self.llama_server.is_running:
            self._managed_server_attempted = False
            self._managed_url = ""
        self._testing = True
        self.connected = False
        self.backend.is_connected = False
        self._connected_endpoint = ""
        self.models_by_url = {}
        self.context_windows_by_url = {}
        self.available_models = []
        self._discovery_errors = []
        self._endpoint_errors = {}
        self._model_errors = {}
        self._discovery_cancelled = False
        self._discovery_urls = list(dict.fromkeys([
            self.settings.url, *(self.settings.endpoint_for(role) for role in ROLE_LABELS),
        ]))
        self._status("Checking local engine endpoints and advertised models…")
        try:
            self._discover_next()
        except (ValueError, RuntimeError) as exc:
            self._testing = False
            self._status(str(exc), True)
            raise

    def _discover_next(self):
        self._discovery_url = self._discovery_urls.pop(0)
        try:
            self.backend.list_models(self._discovery_url)
        except (ValueError, RuntimeError):
            # Never surface arbitrary credential-store exceptions or key values.
            self._models_listed(False, [], "Could not access the API key. Check Windows Credential Manager.")

    def _models_listed(self, success, models, message):
        if success and not self._stopped and not self._discovery_cancelled:
            self.models_by_url[self._discovery_url] = list(models)
            self.context_windows_by_url[self._discovery_url] = dict(
                getattr(self.backend, "context_windows", {})
            )
        else:
            self._discovery_errors.append(f"{self._discovery_url}: {message}")
        if self._discovery_urls and not self._stopped and not self._discovery_cancelled:
            self._discover_next()
            return
        self._testing = False
        self.connected = bool(self.models_by_url) and not self._stopped and not self._discovery_cancelled
        if not self.connected:
            self.models_by_url = {}
            self.context_windows_by_url = {}
        self.available_models = sorted({model for models in self.models_by_url.values() for model in models})
        self.modelsChanged.emit(self.available_models)
        missing = [
            ROLE_LABELS[role] for role, model in self.settings.models.items()
            if model and model not in self.models_for_role(role)
        ]
        if self._discovery_cancelled:
            message = "Connection test cancelled."
        elif self._discovery_errors:
            message = " ".join(self._discovery_errors)
        else:
            message = "Local engine endpoints are available."
        if self.connected and missing:
            message += (
                " Unavailable assignments: " + ", ".join(missing) + ". Load or reinstall "
                "the assigned models, then use Options → Activity → Reconnect saved servers, "
                "or choose another model in AI / Local Models and Apply. Messages are not resent."
            )
        elif self.connected and not self.settings.models["direct"]:
            message += " Choose a direct-conversation model, then Apply."
        if self._managed_url and self._managed_url in self.models_by_url:
            self.llama_server.mark_ready()
            self._startup_timer.stop()
            self._managed_server_attempted = True
        if self.llama_server.is_starting and self._managed_url not in self.models_by_url:
            self._status(
                "llama-server is running and loading the GGUF model. "
                "The app will check again while startup is in progress.",
                False,
            )
            self._startup_timer.start(2500)
            return
        if (
            self.settings.llama_model_path
            and self.settings.url not in self.models_by_url
            and not self._managed_server_attempted
        ):
            self._start_managed_server()
            return
        self._status(message, not self.connected or bool(self._discovery_errors) or bool(missing))

    def _start_managed_server(self):
        settings = self.settings
        alias = settings.models["direct"] or Path(settings.llama_model_path).stem
        self._managed_url = settings.url
        self._managed_server_attempted = True
        try:
            self.llama_server.start(
                settings.llama_server_executable,
                settings.llama_model_path,
                alias,
                settings.url,
                settings.llama_gpu_layers,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            self._managed_url = ""
            self._status(f"Could not start the app-managed llama-server: {exc}", True)
            return
        self._startup_deadline = time.monotonic() + 600
        self._status(
            "Starting llama-server and loading the local GGUF model. "
            "This can take a few minutes on the first start.",
            False,
        )

    def _managed_server_started(self):
        if self._stopped or not self.llama_server.is_starting:
            return
        self._startup_timer.start(1800)

    def _retry_managed_server(self):
        if self._stopped or not self.llama_server.is_starting or self.is_busy:
            return
        if time.monotonic() >= self._startup_deadline:
            self._managed_server_stopping = True
            self.llama_server.stop()
            self._managed_server_stopping = False
            self._status(
                "llama-server did not finish loading within 10 minutes. "
                "Check the executable, model file, GPU layer setting, and available memory.",
                True,
            )
            return
        try:
            self.test_connection()
        except (ValueError, RuntimeError) as exc:
            self._status(f"Could not check llama-server startup: {exc}", True)

    def _managed_server_stopped(self, message):
        if self._managed_server_stopping:
            return
        self._startup_timer.stop()
        if not self._stopped:
            self._status(message, True)

    def _managed_server_failed(self, message):
        self._startup_timer.stop()
        if not self._stopped:
            self._status(message, True)

    def submit(self, role, messages, input_budget=None, output_limit=None):
        if role not in ROLE_LABELS:
            raise ValueError("Unknown AI job role.")
        if output_limit is not None and (
            type(output_limit) is not int or not 1 <= output_limit <= 2048
        ):
            raise ValueError("The generation limit must be a whole number from 1 to 2048.")
        if self._stopped or not self.is_available(role):
            raise RuntimeError(
                "This role's local model is unavailable. Load the model or restart the local server, then use "
                "Options → Activity → Reconnect saved servers, or test the saved connection "
                "in AI / Local Models."
            )
        if role == "direct" and not self.chat_available:
            raise RuntimeError("Simulated internet service is unavailable.")
        self._next_id += 1
        job = AIJob(
            self._next_id, role, [dict(message) for message in messages],
            input_budget=input_budget, output_limit=output_limit,
        )
        self._queue.append(job)
        self.changed.emit()
        QTimer.singleShot(0, self._pump)
        return job.request_id

    def _pump(self):
        if self._stopped or self._active or self._testing or self.backend.is_busy:
            return
        eligible = [
            job for job in self._queue
            if job.role == "direct" or not self.background_paused
            or self.settings.endpoint_for(job.role) in self._endpoint_errors
            or (self.settings.endpoint_for(job.role), self.settings.models[job.role]) in self._model_errors
        ]
        if not eligible:
            return
        priority = (
            {"background": 0, "summary": 1, "direct": 2}
            if self.maintenance_priority_mode
            else {"direct": 0, "summary": 1, "background": 2}
        )
        job = min(eligible, key=lambda item: (priority[item.role], item.request_id))
        self._queue.remove(job)
        self._active = job
        model = self.settings.models[job.role]
        endpoint = self.settings.endpoint_for(job.role)
        self.backend.last_failure = None
        if not self.is_available(job.role):
            self._response_finished(False, self._model_errors.get(
                (endpoint, model), "This role's local model is unavailable. "
                "Use Options → Activity → Reconnect saved servers."
            ))
            return
        self._status(f"Working: {ROLE_LABELS[job.role]} · {model}")
        try:
            window, _ = self.context_for_role(job.role)
            self.backend.context_window = window if job.role in ("direct", "summary") else None
            self.backend.reply_limit = (
                reply_reserve(window)
                if job.role in ("direct", "summary")
                else job.output_limit
            )
            if (
                self.backend.is_connected and self.backend.model_name == model
                and self._connected_endpoint == endpoint
            ):
                self._send_active()
            else:
                self._connected_endpoint = endpoint
                self.backend.connect_to_server(endpoint, model)
        except (ValueError, RuntimeError) as exc:
            self._response_finished(False, str(exc))

    def _connected_for_job(self, success, message):
        job = self._active
        if job is None:
            return
        if job.cancelled or not success:
            self._response_finished(False, "Request cancelled." if job.cancelled else message)
        else:
            try:
                self._send_active()
            except (ValueError, RuntimeError) as exc:
                self._response_finished(False, str(exc))

    def _send_active(self):
        job = self._active
        if job is None:
            return
        self.llmPhaseChanged.emit(job.request_id, job.role, "sending")
        if job.input_budget is not None and hasattr(self.backend, "send_bounded_chat"):
            self.backend.send_bounded_chat(job.messages, job.input_budget)
        elif job.input_budget is not None:
            from .messenger_context import bounded_messages, input_size
            selected, omitted = bounded_messages(
                job.messages[0]["content"], job.messages[1:], job.input_budget,
            )
            self._input_prepared({
                "omitted": omitted, "count": input_size(selected), "exact": False,
            })
            self._send_chat(selected)
        else:
            self._send_chat(job.messages)

    def _send_chat(self, messages):
        if not self._backend_reports_chat_start:
            self._record_chat_start(messages)
        self.backend.send_chat(messages)

    def _backend_chat_request_starting(self, messages):
        self._record_chat_start(messages)

    def _record_chat_start(self, messages):
        job = self._active
        if job is None or job.cancelled or job.dispatched:
            return
        job.dispatched = True
        self.llmRequestSent.emit(
            job.request_id,
            job.role,
            self.settings.models[job.role],
            [dict(message) for message in messages],
        )
        if self._backend_reports_chat_start:
            QTimer.singleShot(
                120,
                lambda request_id=job.request_id, role=job.role:
                    self._mark_generating(request_id, role),
            )
        else:
            self.llmPhaseChanged.emit(job.request_id, job.role, "generating")

    def _mark_generating(self, request_id, role):
        if self._active and self._active.request_id == request_id and self._active.dispatched:
            self.llmPhaseChanged.emit(request_id, role, "generating")

    def _input_prepared(self, measurement):
        if self._active and not self._active.cancelled:
            self._active.prepared = True
            self.jobInputPrepared.emit(self._active.request_id, measurement)

    def _response_finished(self, success, message):
        job = self._active
        if job is None:
            return
        self._active = None
        if job.cancelled:
            success, message = False, "Request cancelled."
        elif not success:
            category = getattr(self.backend, "last_failure", None)
            endpoint = self.settings.endpoint_for(job.role)
            if category == FailureCategory.MODEL_UNAVAILABLE:
                model = self.settings.models[job.role]
                self.models_by_url[endpoint] = [
                    name for name in self.models_by_url.get(endpoint, []) if name != model
                ]
                # Keep the healthy endpoint, even if it has no remaining models.
                self.available_models = sorted({
                    name for models in self.models_by_url.values() for name in models
                })
                self._model_errors[(endpoint, model)] = message
                self.backend.is_connected = False
                self._connected_endpoint = ""
                self.modelsChanged.emit(self.available_models)
            elif category is not None and category.invalidates_endpoint:
                endpoint = self.settings.endpoint_for(job.role)
                self.models_by_url.pop(endpoint, None)
                self.context_windows_by_url.pop(endpoint, None)
                self.available_models = sorted({
                    model for models in self.models_by_url.values() for model in models
                })
                self.connected = bool(self.models_by_url)
                self.backend.is_connected = False
                self._connected_endpoint = ""
                self._endpoint_errors[endpoint] = (
                    f"{endpoint}: {message} Use Options → Activity → Reconnect saved servers."
                )
                self.modelsChanged.emit(self.available_models)
        if not success and job.input_budget is not None and not job.prepared:
            message = "Message not sent: " + message
        phase = "output" if job.dispatched else "idle"
        self.llmPhaseChanged.emit(job.request_id, job.role, phase)
        self.llmResponseCaptured.emit(
            job.request_id, job.role, success, message,
        )
        self.jobFinished.emit(job.request_id, success, message)
        self.llmPhaseChanged.emit(job.request_id, job.role, "idle")
        self._status("Ready." if success else message, not success)
        QTimer.singleShot(0, self._pump)

    def cancel(self, request_id):
        for job in tuple(self._queue):
            if job.request_id == request_id:
                self._queue.remove(job)
                self.jobFinished.emit(request_id, False, "Request cancelled.")
                self.changed.emit()
                return
        if self._active and self._active.request_id == request_id:
            self._active.cancelled = True
            self.backend.cancel()

    def cancel_all(self):
        for job in tuple(self._queue):
            self.cancel(job.request_id)
        if self._active:
            self.cancel(self._active.request_id)
        elif self._testing:
            self._discovery_cancelled = True
            self._discovery_urls = []
            self.backend.cancel()

    def set_simulated_availability(self, chat_available, background_paused):
        self.chat_available = chat_available
        self.background_paused = background_paused
        if not chat_available:
            for job in [*self._queue, *([self._active] if self._active else [])]:
                if job.role == "direct":
                    self.cancel(job.request_id)
        self.changed.emit()
        QTimer.singleShot(0, self._pump)

    def set_maintenance_priority_mode(self, active):
        """Temporarily let queued world updates run before new direct chats."""
        active = bool(active)
        if self.maintenance_priority_mode == active:
            return
        self.maintenance_priority_mode = active
        self.changed.emit()
        QTimer.singleShot(0, self._pump)

    def stop(self):
        self._stopped = True
        self._startup_timer.stop()
        self.cancel_all()
        if self.llama_server.is_running:
            self._managed_server_stopping = True
            self.llama_server.stop()
            self._managed_server_stopping = False
        self.changed.emit()


class AIChannel(QObject):
    """An app's cancellable conversation channel, independent of engine details."""

    connectionFinished = Signal(bool, str)
    responseFinished = Signal(bool, str)
    busyChanged = Signal(bool)
    inputPrepared = Signal(object)

    def __init__(self, service, role="direct", parent=None):
        super().__init__(parent)
        self.service, self.role = service, role
        self.request_id = None
        service.changed.connect(self._changed)
        service.jobFinished.connect(self._finished)
        service.jobInputPrepared.connect(self._input_prepared)

    @property
    def is_connected(self):
        return self.service.is_available(self.role)

    @property
    def is_busy(self):
        return self.request_id is not None

    @property
    def model_name(self):
        return self.service.settings.models[self.role]

    def _changed(self):
        self.connectionFinished.emit(self.is_connected, self.service.status)

    def send_chat(self, messages, input_budget=None, output_limit=None):
        if self.is_busy:
            raise RuntimeError("This conversation already has a pending reply.")
        self.request_id = self.service.submit(
            self.role, messages, input_budget, output_limit
        )
        self.busyChanged.emit(True)

    def _input_prepared(self, request_id, measurement):
        if request_id == self.request_id:
            self.inputPrepared.emit(measurement)

    def _finished(self, request_id, success, message):
        if request_id != self.request_id:
            return
        self.request_id = None
        self.responseFinished.emit(success, message)
        self.busyChanged.emit(False)

    def cancel_chat(self):
        if self.request_id is not None:
            self.service.cancel(self.request_id)

    def cancel(self):
        self.cancel_chat()
