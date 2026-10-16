"""Safety and HTTP helpers for explicitly enabled, real-server tests.

No server discovery, downloads, subprocesses, or network access at import time.
"""
import json
import os
import re
import time
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from win7_2011.win7sim.ai_settings import normalize_endpoint

OWNED_PREFIX = "win7-recovery-test-"


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Opt-in real-server test requires {name}.")
    return value


def owned_model(name):
    if not re.fullmatch(r"win7-recovery-test-[A-Za-z0-9_-]+(?::[A-Za-z0-9_.-]+)?", name):
        raise ValueError(f"Only explicitly test-owned {OWNED_PREFIX} model IDs may be managed.")
    return name


class RealHTTP:
    def __init__(self, backend, url, timeout=180):
        self.url = normalize_endpoint(backend, url)
        self.timeout = timeout
        self.opener = build_opener(NoRedirects())

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(self.url + path, data=data, method=method,
                          headers={"Content-Type": "application/json"})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            # No response body logging: endpoints may include private details.
            raise AssertionError(
                f"Real server {method} {path} returned HTTP {exc.code}."
            ) from None
        return json.loads(raw) if raw.strip() else {}


class LlamaRouter:
    """Only unload explicitly named test presets; never delete files/models."""

    def __init__(self, http, primary, healthy=""):
        self.http = http
        self.primary = owned_model(primary)
        self.healthy = owned_model(healthy) if healthy else ""
        if self.primary == self.healthy:
            raise ValueError("The healthy preset must have a different model ID.")
        self.initial = {}

    def models(self):
        return {item["id"]: item["status"]["value"]
                for item in self.http.request("GET", "/v1/models")["data"]}

    def prepare(self):
        props = self.http.request("GET", "/props")
        if props.get("role") != "router" or props.get("models_autoload") is not False:
            raise ValueError("Use a dedicated llama-server router with --no-models-autoload.")
        maximum = props.get("max_instances")
        if self.healthy and (not isinstance(maximum, int) or maximum == 1):
            raise ValueError("The router needs --models-max 2 (or higher/0) for isolation checks.")
        models = self.models()
        targets = [self.primary] + ([self.healthy] if self.healthy else [])
        if not all(model in models for model in targets):
            raise ValueError("The test presets must already be advertised by the router.")
        self.initial = {model: models[model] for model in targets}
        if any(state not in ("loaded", "unloaded") for state in self.initial.values()):
            raise ValueError("Test presets must be idle, loaded or unloaded, before the run.")

    def load(self, model):
        self._check(model)
        current = self.models()[model]
        if current not in ("loaded", "loading"):
            self.http.request("POST", "/models/load", {"model": model})
        self.wait_state(model, "loaded")

    def unload(self, model):
        self._check(model)
        current = self.models()[model]
        if current == "loading":
            # A timed-out load can still be completing when cleanup runs.
            self.wait_state(model, "loaded")
            current = "loaded"
        if current == "loaded":
            self.http.request("POST", "/models/unload", {"model": model})
        self.wait_state(model, "unloaded")

    def wait_state(self, model, state):
        deadline = time.monotonic() + self.http.timeout
        while time.monotonic() < deadline:
            current = self.models()[model]
            if current == state:
                return
            time.sleep(.05)
        raise AssertionError(f"Test preset {model} did not become {state}.")

    def _check(self, model):
        owned_model(model)
        if model not in self.initial:
            raise ValueError("Refusing to manage a preset outside this test's initial snapshot.")

    def restore(self):
        failures = []
        for model, state in self.initial.items():
            try:
                self.load(model) if state == "loaded" else self.unload(model)
            except Exception as exc:
                failures.append(f"{model}: {type(exc).__name__}")
        if failures:
            raise AssertionError("Could not restore test preset states: " + "; ".join(failures))
