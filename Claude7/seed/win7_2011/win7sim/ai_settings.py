from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .llama_cpp import normalize_llama_url
from .messenger_context import valid_context_window

BACKEND_LABELS = {"llama_cpp": "llama.cpp (llama-server)"}
DEFAULT_URLS = {"llama_cpp": "http://127.0.0.1:9931"}

ROLE_LABELS = {
    "direct": "Direct conversations",
    "background": "Background community activity",
    "summary": "Summaries and memory",
}


def normalize_endpoint(backend: str, url: str) -> str:
    if backend not in BACKEND_LABELS:
        raise ValueError("Unknown local AI backend.")
    return normalize_llama_url(url)


@dataclass
class AISettings:
    backend: str = "llama_cpp"
    url: str = "http://127.0.0.1:9931"
    models: dict[str, str] = field(default_factory=lambda: dict.fromkeys(ROLE_LABELS, ""))
    role_urls: dict[str, str] = field(default_factory=dict)
    context_limits: dict[str, dict[str, int]] = field(default_factory=dict)
    llama_server_executable: str = field(
        default_factory=lambda: str(config.LLAMA_SERVER_EXECUTABLE)
    )
    llama_model_path: str = ""
    llama_gpu_layers: int = 99

    def endpoint_for(self, role: str) -> str:
        return self.role_urls.get(role) or self.url

    def validated(self) -> AISettings:
        if self.backend not in BACKEND_LABELS:
            raise ValueError("Unknown local AI backend.")
        if not isinstance(self.models, dict) or set(self.models) != set(ROLE_LABELS) or any(
            not isinstance(model, str) for model in self.models.values()
        ):
            raise ValueError("AI settings must contain a model assignment for each role.")
        if not isinstance(self.role_urls, dict) or any(
            role not in ROLE_LABELS or not isinstance(url, str)
            for role, url in self.role_urls.items()
        ):
            raise ValueError("Role server addresses must use the supported AI roles.")
        normalize = normalize_llama_url
        if not isinstance(self.url, str):
            raise ValueError("The AI server address must be text.")
        if not isinstance(self.context_limits, dict):
            raise ValueError("Invalid per-model context limits.")
        if (
            not isinstance(self.llama_server_executable, str)
            or not isinstance(self.llama_model_path, str)
            or type(self.llama_gpu_layers) is not int
            or not 0 <= self.llama_gpu_layers <= 999
        ):
            raise ValueError("llama.cpp launch settings are invalid.")
        limits = {}
        for endpoint, models in self.context_limits.items():
            if not isinstance(endpoint, str) or not isinstance(models, dict) or any(
                not isinstance(model, str) or not model.strip() or valid_context_window(limit) is None
                for model, limit in models.items()
            ):
                raise ValueError("Per-model context limits must be whole token windows from 256 to 16777216.")
            limits[normalize(endpoint)] = {model.strip(): limit for model, limit in models.items()}
        return AISettings(
            "llama_cpp", normalize(self.url),
            {role: model.strip() for role, model in self.models.items()},
            {role: normalize(url) if url.strip() else "" for role, url in self.role_urls.items()},
            limits, self.llama_server_executable.strip(),
            self.llama_model_path.strip(), self.llama_gpu_layers,
        )


def settings_file() -> Path:
    return config.SYSTEM_ROOT / "ai.json"


def load_ai_settings() -> AISettings:
    path = settings_file()
    if not path.exists():
        settings = _import_legacy_ollama_settings() or AISettings().validated()
        settings = _autoconfigure_local_gguf(settings)
        if settings_file().exists() is False and (
            settings.llama_model_path or any(settings.models.values())
        ):
            save_ai_settings(settings)
        return settings
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("version") not in (1, 2, 3, 4, 5):
            raise ValueError("Unknown AI settings format.")
        settings = _autoconfigure_local_gguf(_settings_from_saved(raw).validated())
        if raw.get("version") != 5 or raw.get("backend") != "llama_cpp":
            save_ai_settings(settings)
        return settings
    except (KeyError, TypeError, AttributeError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read centralized AI settings: {exc}") from exc


def _autoconfigure_local_gguf(settings: AISettings) -> AISettings:
    """Use one unambiguous local GGUF as the managed model default."""
    model_path = settings.llama_model_path
    if not model_path:
        try:
            candidates = sorted(
                path for path in config.MODELS_ROOT.iterdir()
                if path.is_file() and path.suffix.lower() == ".gguf"
            )
        except OSError:
            candidates = []
        if len(candidates) != 1:
            return settings
        model_path = str(candidates[0])

    models = dict(settings.models)
    if not models["direct"]:
        models["direct"] = Path(model_path).stem
    return AISettings(
        "llama_cpp", settings.url, models, dict(settings.role_urls),
        {url: dict(limits) for url, limits in settings.context_limits.items()},
        settings.llama_server_executable, model_path, settings.llama_gpu_layers,
    ).validated()


def _import_legacy_ollama_settings() -> AISettings | None:
    """Convert the retired one-model config once, retaining its model assignment."""
    legacy = config.SYSTEM_ROOT / "ollama.json"
    if not legacy.exists():
        return None
    try:
        raw = json.loads(legacy.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Legacy local AI settings must be a JSON object.")
        model = raw.get("model", "")
        if not isinstance(model, str):
            raise ValueError("Legacy local AI model assignment must be text.")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read legacy local AI settings: {exc}") from exc
    return AISettings(
        url=DEFAULT_URLS["llama_cpp"],
        models=dict.fromkeys(ROLE_LABELS, model),
    ).validated()


def _settings_from_saved(raw: dict) -> AISettings:
    """Read current settings or safely migrate a saved Ollama profile."""
    backend = raw.get("backend")
    if backend not in ("ollama", "llama_cpp"):
        raise ValueError("Unknown local AI backend.")
    roles = raw["roles"]
    role_urls = raw.get("role_urls", {})
    context_limits = raw.get("context_limits", {})
    executable = raw.get("llama_server_executable", str(config.LLAMA_SERVER_EXECUTABLE))
    model_path = raw.get("llama_model_path", "")
    gpu_layers = raw.get("llama_gpu_layers", 99)
    url = raw["url"]
    if backend == "ollama":
        # A previous migration may already have saved a working llama.cpp
        # profile. Reuse its launch details, but retain active role assignments.
        profile = raw.get("profiles", {}).get("llama_cpp", {})
        if isinstance(profile, dict):
            url = profile.get("url", DEFAULT_URLS["llama_cpp"])
            role_urls = profile.get("role_urls", {})
            executable = profile.get(
                "llama_server_executable", str(config.LLAMA_SERVER_EXECUTABLE)
            )
            model_path = profile.get("llama_model_path", "")
            gpu_layers = profile.get("llama_gpu_layers", 99)
            context_limits = profile.get("context_limits", {})
        else:
            url = DEFAULT_URLS["llama_cpp"]
            role_urls = {}
            context_limits = {}
    return AISettings(
        "llama_cpp", url, roles, role_urls, context_limits,
        executable, model_path, gpu_layers,
    )


def save_ai_settings(settings: AISettings) -> None:
    settings = settings.validated()
    path = settings_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    try:
        temporary.write_text(
            json.dumps({
                "version": 5, "backend": "llama_cpp",
                "url": settings.url, "roles": settings.models,
                "role_urls": settings.role_urls,
                "context_limits": settings.context_limits,
                "llama_server_executable": settings.llama_server_executable,
                "llama_model_path": settings.llama_model_path,
                "llama_gpu_layers": settings.llama_gpu_layers,
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
