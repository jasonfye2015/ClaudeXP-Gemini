"""An Ollama-compatible server for programs that expect Ollama (http://localhost:11434), answered by the Timeline's
own llama.cpp engine. The Projects (Fly Mind, the Fly Brain Viewer, the Virtual Pet...) are launched with OLLAMA_HOST
pointing here, so they talk to the same models every other program uses, with no Ollama installed.

Speaks the parts of Ollama's API they use:
  GET  /api/tags      the installed models, with Ollama-style names ('gemma4:12b', 'nomic-embed-text:latest')
  GET  /api/version   /api/ps
  POST /api/chat      chat, streamed as Ollama's lines of JSON (pictures, format 'json', options, token counts)
  POST /api/generate  the same for a single prompt
  POST /api/embed     embeddings (and the older /api/embeddings), from an embedding model such as nomic-embed-text
  POST /api/show      a model's details, including the context the engine really runs it with
  POST /api/pull      'already here' (models are added in Control Panel > AI Models)
Chat requests go straight to the engine's router (it queues them per model itself)."""
import base64
import json
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import ai_models, llm_server

_server = None
_lock = threading.Lock()


def url():
    """The bridge's address (starting it the first time): give it to a program as OLLAMA_HOST."""
    global _server
    with _lock:
        if _server is None:
            _server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
            _server.daemon_threads = True
            threading.Thread(target=_server.serve_forever, name="ollama-bridge", daemon=True).start()
        return f"http://127.0.0.1:{_server.server_address[1]}"


def stop():
    global _server
    with _lock:
        if _server is not None:
            _server.shutdown()
            _server = None


# ---- names ----------------------------------------------------------------------------------------------------
def ollama_name(model):
    """'gemma4-12b' -> 'gemma4:12b', 'qwen25-coder-7b' -> 'qwen25-coder:7b', 'nomic-embed-text' -> 'nomic-embed-text:latest'."""
    m = re.match(r"(.+)-(\d+(?:\.\d+)?b)$", model.id)
    return f"{m.group(1)}:{m.group(2)}" if m else f"{model.id}:latest"


def _norm(text):
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def resolve(name, embedding=False):
    """The installed model a program means ('gemma4:12b', 'nomic-embed-text', 'gemma3-4b'...)."""
    wanted = re.sub(r":latest$", "", str(name or ""))
    models = ai_models.installed(embeddings=True)
    for m in models:
        if m.embedding == embedding and _norm(wanted) in (_norm(m.id), _norm(ollama_name(m)), _norm(m.title)):
            return m
    if embedding:
        found = ai_models.embedders()
        return found[0] if found else None
    return ai_models.get(ai_models.resolve(wanted))


# ---- translating -------------------------------------------------------------------------------------------------
def _image_part(data):
    raw = base64.b64decode(data[:64] + "=" * (-len(data[:64]) % 4), validate=False) if isinstance(data, str) else b""
    mime = "image/png" if raw[:4] == b"\x89PNG" else "image/gif" if raw[:3] == b"GIF" else \
        "image/webp" if raw[8:12] == b"WEBP" else "image/jpeg"
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def _messages(messages):
    out, pictures = [], False
    for m in messages or []:
        content = m.get("content") or ""
        images = m.get("images") or []
        if images:
            pictures = True
            content = [{"type": "text", "text": content}] + [_image_part(i) for i in images]
        out.append({"role": m.get("role", "user"), "content": content})
    return out, pictures


def _options(body):
    o = body.get("options") or {}
    out = {}
    for ours, theirs in (("temperature", "temperature"), ("top_p", "top_p"), ("top_k", "top_k"), ("seed", "seed"),
                         ("stop", "stop"), ("repeat_penalty", "repeat_penalty"), ("min_p", "min_p"),
                         ("presence_penalty", "presence_penalty"), ("frequency_penalty", "frequency_penalty")):
        if ours in o:
            out[theirs] = o[ours]
    if o.get("num_predict", -1) and int(o.get("num_predict", -1)) > 0:
        out["max_tokens"] = int(o["num_predict"])
    fmt = body.get("format")
    if fmt == "json":
        out["response_format"] = {"type": "json_object"}
    elif isinstance(fmt, dict):
        out["response_format"] = {"type": "json_schema", "json_schema": {"name": "reply", "schema": fmt}}
    return out


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _post(path, body, timeout=900):
    base = llm_server.ensure_started()
    req = urllib.request.Request(base + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=timeout)


class _Handler(BaseHTTPRequestHandler):
    server_version = "Ollama"

    def log_message(self, *args):
        pass

    # ---- plumbing --------------------------------------------------------------------------------------------
    def _json(self, data, status=200):
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, OSError):
            return {}

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path in ("", "/"):
            raw = b"Ollama is running"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif path == "/api/version":
            self._json({"version": "0.6.0"})
        elif path == "/api/tags":
            models = []
            for m in ai_models.installed(embeddings=True):
                models.append({"name": ollama_name(m), "model": ollama_name(m), "modified_at": _now(), "size": m.size,
                               "digest": "", "details": {"format": "gguf",
                                                         "family": "nomic-bert" if m.embedding else "llama",
                                                         "parameter_size": "", "quantization_level": ""}})
            self._json({"models": models})
        elif path == "/api/ps":
            self._json({"models": []})
        else:
            self._json({"error": f"unknown path {path}"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        body = self._body()
        try:
            if path == "/api/chat":
                self._chat(body, body.get("messages"), "message")
            elif path == "/api/generate":
                messages = ([{"role": "system", "content": body["system"]}] if body.get("system") else []) + \
                           [{"role": "user", "content": body.get("prompt", ""), "images": body.get("images") or []}]
                self._chat(body, messages, "response")
            elif path in ("/api/embed", "/api/embeddings"):
                self._embed(body, legacy=path == "/api/embeddings")
            elif path == "/api/show":
                self._show(body)
            elif path == "/api/pull":
                self._json({"status": "success"})
            else:
                self._json({"error": f"unknown path {path}"}, 404)
        except RuntimeError as exc:                          # the engine isn't set up / couldn't start
            self._json({"error": str(exc)}, 500)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            try:
                self._json({"error": f"the language model engine: {exc}"}, 500)
            except OSError:
                pass

    # ---- the endpoints ---------------------------------------------------------------------------------------
    def _chat(self, body, messages, field):
        model = resolve(body.get("model"))
        if model is None:
            self._json({"error": "no language model is installed (Control Panel > AI Models)"}, 404)
            return
        converted, pictures = _messages(messages)
        if pictures and not model.vision:                       # a model that can see takes over for pictures
            seeing = ai_models.get(ai_models.vision_model())
            model = seeing or model
        name = body.get("model") or ollama_name(model)
        stream = body.get("stream", True)
        request = {"model": model.id, "messages": converted, "stream": bool(stream), **_options(body)}
        if stream:
            request["stream_options"] = {"include_usage": True}
        started = time.time()
        with _post("/v1/chat/completions", request) as r:
            if not stream:
                data = json.load(r)
                text = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
                usage = data.get("usage") or {}
                self._json(self._final(name, field, text, usage, started))
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.end_headers()
            usage, reason = {}, "stop"
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                except ValueError:
                    continue
                usage = chunk.get("usage") or usage
                for choice in chunk.get("choices") or []:
                    piece = (choice.get("delta") or {}).get("content") or ""
                    reason = choice.get("finish_reason") or reason
                    if piece:
                        out = {"model": name, "created_at": _now(), "done": False}
                        out[field] = {"role": "assistant", "content": piece} if field == "message" else piece
                        self.wfile.write((json.dumps(out) + "\n").encode("utf-8"))
                        self.wfile.flush()
            final = self._final(name, field, "", usage, started)
            final["done_reason"] = "length" if reason == "length" else "stop"
            self.wfile.write((json.dumps(final) + "\n").encode("utf-8"))
            self.wfile.flush()

    @staticmethod
    def _final(name, field, text, usage, started):
        out = {"model": name, "created_at": _now(), "done": True, "done_reason": "stop",
               "total_duration": int((time.time() - started) * 1e9), "load_duration": 0,
               "prompt_eval_count": int(usage.get("prompt_tokens") or 0),
               "eval_count": int(usage.get("completion_tokens") or 0)}
        out[field] = {"role": "assistant", "content": text} if field == "message" else text
        return out

    def _embed(self, body, legacy):
        model = resolve(body.get("model"), embedding=True)
        if model is None:
            self._json({"error": "no embedding model is installed (put nomic-embed-text in E:\\LLM Models\\models)"}, 404)
            return
        texts = body.get("prompt") if legacy else body.get("input")
        texts = [texts] if isinstance(texts, str) else list(texts or [])
        with _post("/v1/embeddings", {"model": model.id, "input": texts}) as r:
            data = json.load(r)
        vectors = [item["embedding"] for item in sorted(data.get("data") or [], key=lambda d: d.get("index", 0))]
        if legacy:
            self._json({"embedding": vectors[0] if vectors else []})
        else:
            self._json({"model": body.get("model") or ollama_name(model), "embeddings": vectors})

    def _show(self, body):
        model = resolve(body.get("model") or body.get("name"), embedding="embed" in str(body.get("model") or ""))
        if model is None:
            self._json({"error": "model not found"}, 404)
            return
        context = 2048 if model.embedding else int(ai_models.config()["context"])
        family = "nomic-bert" if model.embedding else "llama"
        caps = ["embedding"] if model.embedding else ["completion"] + (["vision"] if model.vision else [])
        self._json({"modelfile": "", "parameters": "", "template": "",
                    "details": {"format": "gguf", "family": family, "parameter_size": "", "quantization_level": ""},
                    "model_info": {"general.architecture": family, f"{family}.context_length": context},
                    "capabilities": caps})
