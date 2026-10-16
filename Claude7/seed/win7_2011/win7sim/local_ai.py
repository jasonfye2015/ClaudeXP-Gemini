from __future__ import annotations

import ipaddress
import json
from enum import Enum
from urllib.parse import urlsplit, urlunsplit

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class FailureCategory(Enum):
    TRANSPORT = "transport"
    AUTHENTICATION = "authentication"
    MODEL_UNAVAILABLE = "model_unavailable"
    CANCELLED = "cancelled"
    CONTEXT_LIMIT = "context_limit"
    EMPTY_REPLY = "empty_reply"
    REQUEST = "request"
    PROTOCOL = "protocol"

    @property
    def invalidates_endpoint(self):
        return self in (self.TRANSPORT, self.AUTHENTICATION)


def normalize_local_url(value: str) -> str:
    """Accept loopback/private-network AI endpoints, never public hosts."""
    parsed = urlsplit(value.strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Enter a valid local server URL, such as http://127.0.0.1:9931.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in the server URL are not supported.")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("The server URL contains an invalid port.") from exc
    hostname = parsed.hostname.lower()
    is_local_name = hostname in ("localhost",) or hostname.endswith(".local")
    try:
        address = ipaddress.ip_address(hostname)
        is_local_name = is_local_name or address.is_loopback or address.is_private or address.is_link_local
    except ValueError:
        pass
    if not is_local_name:
        raise ValueError("The AI server must use localhost or a private/local-network address.")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))


class LocalAIClient(QObject):
    """Shared asynchronous transport and failure handling for local AI servers."""

    request_timeout_ms = 120_000
    connectionFinished = Signal(bool, str)
    responseFinished = Signal(bool, str)
    busyChanged = Signal(bool)
    modelsListed = Signal(bool, object, str)
    inputPrepared = Signal(object)
    chatRequestStarting = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self._request_kind: str | None = None
        self._base_url = ""
        self._model = ""
        self.is_connected = False
        self.is_busy = False
        # Resolver is supplied by the desktop service; never serialize a key.
        self.credential_resolver = None
        self._request_key = ""
        self.last_failure: FailureCategory | None = None
        self._cancel_requested = False
        self.context_windows: dict[str, int] = {}
        self.context_window = None
        self.reply_limit = None
        self._context_pending = []
        self._context_models = []
        self._context_model = ""
        self._models_message = ""

    def _safe_text(self, text: str) -> str:
        return text.replace(self._request_key, "[redacted]") if self._request_key else text

    def _decode_response(self, raw: bytes):
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            return None

        def redact(value):
            if isinstance(value, str):
                return self._safe_text(value)
            if isinstance(value, list):
                return [redact(item) for item in value]
            if isinstance(value, dict):
                return {self._safe_text(key): redact(item) for key, item in value.items()}
            return value

        return redact(data)

    def _http_failure(self, reply) -> str | None:
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status in (401, 403):
            return (
                f"Authentication failed (HTTP {status}). Invalid API key or insufficient "
                "permission. Save or replace this server's API key in Options → AI / Local Models."
            )
        if isinstance(status, int) and 300 <= status < 400:
            return "Server redirects are not followed. Enter the final local server address in Options."
        return None

    def _response_failure(self, reply, data, error_text):
        """Classify at the transport boundary, not by UI-facing error text."""
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error = reply.error()
        server_error = data.get("error") if isinstance(data, dict) else None
        detail = server_error.get("message") if isinstance(server_error, dict) else server_error
        http_failure = self._http_failure(reply)
        message = http_failure or (detail if isinstance(detail, str) else None) or error_text
        if self._cancel_requested:
            category, message = FailureCategory.CANCELLED, "Request cancelled."
        elif status in (401, 403):
            category = FailureCategory.AUTHENTICATION
        elif server_error and self._is_context_limit(server_error):
            category = FailureCategory.CONTEXT_LIMIT
        elif self._request_kind == "chat" and server_error and self._is_model_unavailable(server_error):
            category = FailureCategory.MODEL_UNAVAILABLE
            message = self._model_unavailable_message()
        elif isinstance(status, int) and (status >= 500 or status == 408):
            category = FailureCategory.TRANSPORT
        elif isinstance(status, int) and status >= 300:
            category = FailureCategory.REQUEST
        elif error != QNetworkReply.NetworkError.NoError:
            category = FailureCategory.TRANSPORT
        elif server_error:
            category = FailureCategory.REQUEST
        else:
            return None
        self.last_failure = category
        if category.invalidates_endpoint or category == FailureCategory.MODEL_UNAVAILABLE:
            self.is_connected = False
        return message or "The local server request failed."

    def _model_unavailable_message(self):
        return (
            f"Model “{self._model}” is missing or unloaded at {self._base_url}. "
            "Load or reinstall this model on the local server, then use "
            "Options → Activity → Reconnect saved servers, or choose another model "
            "in Options → AI / Local Models and Apply. Messages are not resent."
        )

    @staticmethod
    def _is_model_unavailable(server_error):
        if isinstance(server_error, dict):
            fields = (server_error.get("code"), server_error.get("type"), server_error.get("message"))
        else:
            fields = (server_error,)
        text = " ".join(value.lower() for value in fields if isinstance(value, str))
        if any(marker in text for marker in (
            "model_not_found", "model_not_loaded", "model_unavailable",
            "unknown model", "no model loaded",
        )):
            return True
        return "model" in text and any(marker in text for marker in (
            "not found", "does not exist", "not loaded", "unloaded",
            "not available", "not installed",
        ))

    @staticmethod
    def _is_context_limit(server_error):
        if isinstance(server_error, dict):
            fields = (server_error.get("code"), server_error.get("type"), server_error.get("message"))
        else:
            fields = (server_error,)
        text = " ".join(value.lower() for value in fields if isinstance(value, str))
        return any(marker in text for marker in (
            "context_length_exceeded", "exceed_context_size_error", "context too large",
            "context length", "context window", "context size", "input is too long",
            "too many tokens", "prompt too long",
        ))

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    def list_models(self, base_url: str) -> None:
        raise NotImplementedError

    def connect_to_server(self, base_url: str, model: str) -> None:
        raise NotImplementedError

    def send_chat(self, messages: list[dict[str, str]]) -> None:
        raise NotImplementedError

    def send_bounded_chat(self, messages, budget):
        """Conservatively bound input when the server has no exact tokenizer path."""
        from .messenger_context import bounded_messages, input_size
        selected, omitted = bounded_messages(
            messages[0]["content"], messages[1:], budget,
        )
        self.inputPrepared.emit({
            "omitted": omitted, "count": input_size(selected), "exact": False,
        })
        self.send_chat(selected)

    def _discover_contexts(self, models, message):
        self.context_windows = {}
        self._context_models = models
        self._models_message = message
        self._context_pending = list(models)
        self._next_context()

    def _context_request(self):
        raise NotImplementedError

    def _parse_context(self, data):
        raise NotImplementedError

    def _next_context(self):
        while self._context_pending:
            self._context_model = self._context_pending.pop(0)
            try:
                self._context_request()
                return
            except (RuntimeError, ValueError):
                continue
        self.modelsListed.emit(True, self._context_models, self._models_message)

    def _context_finished(self, reply):
        raw = bytes(reply.readAll()) if reply.isOpen() else b""
        data = self._decode_response(raw)
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        success = reply.error() == QNetworkReply.NetworkError.NoError and status == 200
        cancelled = self._cancel_requested
        self._request_key = ""
        reply.deleteLater()
        if self._reply is not reply:
            return
        self._reply = None
        self._request_kind = None
        self.is_busy = False
        self.busyChanged.emit(False)
        if cancelled:
            self.last_failure = FailureCategory.CANCELLED
            self.modelsListed.emit(False, [], "Context discovery cancelled.")
            return
        if success and isinstance(data, dict):
            window = self._parse_context(data)
            if window:
                self.context_windows[self._context_model] = window
        # Metadata is optional; its absence must not block advertised models.
        self._next_context()

    def cancel_chat(self) -> None:
        if self._request_kind == "chat" and self._reply is not None:
            self._cancel_requested = True
            self._reply.abort()

    def cancel(self) -> None:
        if self._reply is not None:
            self._cancel_requested = True
            self._reply.abort()

    def _request(self, kind: str, method: str, url: str, payload=None) -> None:
        if self._reply is not None:
            raise RuntimeError("A local AI request is already in progress.")
        self.last_failure = None
        self._cancel_requested = False
        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(
            min(self.request_timeout_ms, 5000)
            if kind in ("context", "template", "tokenize") else self.request_timeout_ms
        )
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
        )
        self._request_key = ""
        if self.credential_resolver is not None:
            try:
                key = self.credential_resolver(self._base_url)
            except Exception:
                self.last_failure = FailureCategory.AUTHENTICATION
                raise RuntimeError("Could not access the API key. Check Windows Credential Manager.") from None
            if key:
                from .ai_credentials import validate_api_key
                self._request_key = validate_api_key(key)
                request.setRawHeader(b"Authorization", b"Bearer " + key.encode("ascii"))
        if method == "POST":
            request.setHeader(
                QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
            )
            reply = self._manager.post(
                request, json.dumps(payload, ensure_ascii=False).encode("utf-8")
            )
        else:
            reply = self._manager.get(request)
        self._reply = reply
        self._request_kind = kind
        self.is_busy = True
        self.busyChanged.emit(True)
        reply.finished.connect(lambda current=reply, request_kind=kind: self._finished(current, request_kind))

    def _finished(self, reply: QNetworkReply, kind: str) -> None:
        raise NotImplementedError
