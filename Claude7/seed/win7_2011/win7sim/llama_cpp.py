from __future__ import annotations

from .local_ai import FailureCategory, LocalAIClient, normalize_local_url
from .messenger_context import recent_candidates, valid_context_window, valid_token_count


def normalize_llama_url(value: str) -> str:
    # Accept both server-root and OpenAI-style /v1 base addresses.
    url = normalize_local_url(value)
    return url[:-3] if url.endswith("/v1") else url


class LlamaCppClient(LocalAIClient):
    """llama-server's OpenAI-compatible API, using the shared Qt transport.

    Discovery reports only models advertised by this endpoint. It does not scan
    GGUF files or control server processes. Closing the HTTP request cancels it.
    """

    def list_models(self, base_url: str) -> None:
        if self.is_busy:
            raise RuntimeError("Wait for the current model request to finish.")
        self._base_url = normalize_llama_url(base_url)
        self.context_windows = {}
        self._request("models", "GET", f"{self._base_url}/v1/models")

    def connect_to_server(self, base_url: str, model: str) -> None:
        if self.is_busy:
            raise RuntimeError("Wait for the current model request to finish.")
        self.is_connected = False
        self._base_url = normalize_llama_url(base_url)
        self._model = model.strip()
        if not self._model:
            raise ValueError("Enter the exact model ID advertised by llama-server.")
        self._request("connect", "GET", f"{self._base_url}/v1/models")

    def send_chat(self, messages: list[dict[str, str]]) -> None:
        if not self.is_connected:
            raise RuntimeError("Connect to the configured llama-server model first.")
        payload = {"model": self._model, "messages": messages, "stream": False}
        if self.reply_limit:
            payload["max_tokens"] = self.reply_limit
        self.chatRequestStarting.emit(payload["messages"])
        self._request(
            "chat", "POST", f"{self._base_url}/v1/chat/completions",
            payload,
        )

    def send_bounded_chat(self, messages, budget):
        # Native formatting/tokenization endpoints describe one loaded model.
        # Do not use router-global tools for an arbitrary selected model.
        if not self.context_window or not getattr(self, "_single_model", False):
            return super().send_bounded_chat(messages, budget)
        self._sizing_messages = [dict(message) for message in messages]
        self._sizing_budget = min(budget, self.context_window - self.reply_limit)
        self._sizing_candidates = iter(recent_candidates(messages))
        self._next_sizing_candidate()

    def _next_sizing_candidate(self):
        candidate = next(self._sizing_candidates, None)
        if candidate is None:
            self.last_failure = FailureCategory.CONTEXT_LIMIT
            self.responseFinished.emit(
                False, "The newest message and contact/profile instructions exceed the "
                "AI input token budget. Shorten the draft, remove extra context, or "
                "choose a larger window. No generation was sent."
            )
            return
        self._sizing_selected, self._sizing_omitted = candidate
        self._request("template", "POST", f"{self._base_url}/apply-template", {
            "model": self._model, "messages": self._sizing_selected,
            "stream": False, "max_tokens": self.reply_limit,
        })

    def _sizing_finished(self, reply, kind):
        # Optional capability failures fall back only before generation. Never
        # retry a rejected chat. Cancellation/auth/transport failures stop work.
        raw = bytes(reply.readAll()) if reply.isOpen() else b""
        data = self._decode_response(raw)
        error_text = self._safe_text(reply.errorString())
        failure = self._response_failure(reply, data, error_text)
        self._request_key = ""
        reply.deleteLater()
        if self._reply is not reply:
            return
        self._reply = None
        self._request_kind = None
        self.is_busy = False
        self.busyChanged.emit(False)
        if failure and self.last_failure in (
            FailureCategory.CANCELLED, FailureCategory.AUTHENTICATION,
            FailureCategory.TRANSPORT, FailureCategory.MODEL_UNAVAILABLE,
        ):
            self.responseFinished.emit(False, failure)
            return
        prompt = data.get("prompt") if isinstance(data, dict) else None
        count = valid_token_count(data) if kind == "tokenize" else None
        try:
            if failure or (kind == "template" and (
                not isinstance(prompt, str) or not prompt
            )) or (kind == "tokenize" and count is None):
                self.last_failure = None
                return super().send_bounded_chat(self._sizing_messages, self._sizing_budget)
            if kind == "template":
                # Match chat/completion tokenization: both special-token
                # insertion and parsing are enabled (not plain-text counting).
                self._request("tokenize", "POST", f"{self._base_url}/tokenize", {
                    "content": prompt, "add_special": True,
                    "parse_special": True, "with_pieces": False,
                })
            elif count <= self._sizing_budget:
                self.inputPrepared.emit({
                    "omitted": self._sizing_omitted, "count": count, "exact": True,
                })
                self.send_chat(self._sizing_selected)
            else:
                self._next_sizing_candidate()
        except (ValueError, RuntimeError) as exc:
            self.responseFinished.emit(False, str(exc))

    def _discover_contexts(self, models, message):
        # /props describes the loaded model's per-slot runtime window, not an
        # arbitrary model behind an OpenAI-compatible router.
        if len(models) == 1:
            super()._discover_contexts(models, message)
        else:
            self.context_windows = {}
            self.modelsListed.emit(True, models, message)

    def _context_request(self):
        self._request("context", "GET", f"{self._base_url}/props")

    def _parse_context(self, data):
        settings = data.get("default_generation_settings")
        return valid_context_window(settings.get("n_ctx")) if isinstance(settings, dict) else None

    def _emit_result(self, kind, success, message, models=None):
        if kind == "models":
            self.modelsListed.emit(success, models or [], message)
        elif kind == "connect":
            self.is_connected = success
            self.connectionFinished.emit(success, message)
        else:
            self.responseFinished.emit(success, message)

    def _finished(self, reply, kind):
        if kind in ("template", "tokenize"):
            self._sizing_finished(reply, kind)
            return
        if kind == "context":
            self._context_finished(reply)
            return
        raw = bytes(reply.readAll()) if reply.isOpen() else b""
        error_text = self._safe_text(reply.errorString())
        data = self._decode_response(raw)
        failure = self._response_failure(reply, data, error_text)
        self._request_key = ""
        reply.deleteLater()
        if self._reply is not reply:
            return
        self._reply = None
        self._request_kind = None
        self.is_busy = False
        self.busyChanged.emit(False)
        if failure:
            message = failure if self.last_failure in (
                FailureCategory.CANCELLED, FailureCategory.AUTHENTICATION,
            ) else f"llama-server: {failure}"
            self._emit_result(kind, False, message)
            return
        if not isinstance(data, dict):
            self.last_failure = FailureCategory.PROTOCOL
            self._emit_result(kind, False, "llama-server returned an invalid JSON response.")
            return
        if kind in ("models", "connect"):
            items = data.get("data")
            if not isinstance(items, list) or any(
                not isinstance(item, dict) or not isinstance(item.get("id"), str)
                or not item["id"].strip() for item in items
            ):
                self.last_failure = FailureCategory.PROTOCOL
                self._emit_result(kind, False, "llama-server returned an invalid model list.")
                return
            models = sorted({item["id"] for item in items})
            self._single_model = models == [self._model]
            if kind == "models":
                self._discover_contexts(models, "llama-server is available.")
            elif self._model not in models:
                self.last_failure = FailureCategory.MODEL_UNAVAILABLE
                self._emit_result(kind, False, self._model_unavailable_message())
            else:
                self._emit_result(kind, True, f"Connected to llama-server model {self._model}.")
            return
        choices = data.get("choices")
        first = choices[0] if isinstance(choices, list) and choices else None
        message = first.get("message") if isinstance(first, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            self.last_failure = FailureCategory.EMPTY_REPLY
            self._emit_result(kind, False, "llama-server returned no chat text. No scripted reply was substituted.")
            return
        self._emit_result(kind, True, content.strip())
