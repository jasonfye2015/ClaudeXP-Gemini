"""The Claude Timeline's stand-in for the 'ollama' Python package.

ClaudeAIM (left exactly as it is), the model broker and ClaudeAI all `import ollama`. ClaudeCore (claudecore.ai) puts this folder
first on sys.path, so they get this module instead: the same few calls - list(), show() and chat() (plain or
streamed, with pictures) - answered by ClaudeXP's own llama.cpp router (claudexp/llm_server.py) and the models in
Local Storage/LLM Models/models. Model names are matched to the installed models (ai_models.resolve: 'gemma3:4b'
finds the gemma3-4b folder; unknown names get the job's model). A message with a picture goes to the Pictures model
when the chosen one can't see. Without an engine or a model, every call fails at once with a plain message."""
import base64
import builtins
import json
import time
from types import SimpleNamespace

__version__ = "claudecore"


class ResponseError(Exception):
    pass


def _server():
    from claudecore.ai import llm_server
    return llm_server


def _models():
    from claudecore.ai import ai_models
    return ai_models


# ---- list / show ------------------------------------------------------------------------------------------------

def list():  # noqa: A001 - same name as ollama's
    srv, am = _server(), _models()
    if not srv.available():
        return SimpleNamespace(models=[])
    return SimpleNamespace(models=[SimpleNamespace(model=m.id, name=m.id, size=m.size) for m in am.installed()])


def show(model=None):
    srv, am = _server(), _models()
    if not srv.available():
        raise ResponseError(srv.status())
    m = am.get(am.resolve(model))
    caps = ["completion"] + (["vision"] if m.vision else []) + (["thinking"] if m.thinking else [])
    family = m.id.split("-")[0]
    return SimpleNamespace(capabilities=caps, modelinfo={f"{family}.context_length": srv.train_context(m.id)},
                           details=SimpleNamespace(family=family))


# ---- chat ---------------------------------------------------------------------------------------------------------

def _content(message):
    """An ollama message (with optional images: bytes or paths) -> an OpenAI-style message."""
    images = message.get("images") or []
    text = message.get("content", "")
    if not images:
        return {"role": message.get("role", "user"), "content": text}
    parts = [{"type": "text", "text": text}]
    for img in images:
        if isinstance(img, (bytes, bytearray)):
            data = bytes(img)
        else:
            with open(img, "rb") as f:
                data = f.read()
        mime = "image/png" if data[:4] == b"\x89PNG" else "image/gif" if data[:3] == b"GIF" else "image/jpeg"
        parts.append({"type": "image_url",
                      "image_url": {"url": f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"}})
    return {"role": message.get("role", "user"), "content": parts}


def _body(model_id, messages, options, stream, think):
    options = options or {}
    body = {"model": model_id, "messages": [_content(m) for m in messages], "stream": bool(stream),
            "cache_prompt": True}
    for ours, theirs in (("temperature", "temperature"), ("top_p", "top_p"), ("top_k", "top_k"),
                         ("num_predict", "max_tokens"), ("stop", "stop"), ("repeat_penalty", "repeat_penalty"),
                         ("seed", "seed"), ("min_p", "min_p")):
        if options.get(ours) is not None:
            body[theirs] = options[ours]
    if options.get("lora"):                 # an add-on loaded on the model at scale 0, switched on for this request
        body["lora"] = options["lora"]      # ([{"id": 0, "scale": 1.0}]; see llm_server.addons)
    if think is False:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    if stream:
        body["stream_options"] = {"include_usage": True}
    return body


def _message(content="", thinking=""):
    return SimpleNamespace(message=SimpleNamespace(role="assistant", content=content, thinking=thinking or None),
                           done=True)


def _note(model_id, timings, started):
    timings = timings or {}
    _models().record(model_id, int(timings.get("predicted_n") or 0), float(timings.get("predicted_per_second") or 0),
                     time.time() - started)


def _furlog():
    try:
        from claudecore.ai import llmlog as furlog
        return furlog
    except Exception:
        return None


def chat(model=None, messages=(), options=None, stream=False, think=None, keep_alive=None, **_ignored):
    srv, am = _server(), _models()
    log = _furlog()
    if not srv.available():
        if log is not None:
            log.event("MODEL UNAVAILABLE", srv.status(), asked=model)
        raise ResponseError(srv.status())
    messages = builtins.list(messages)
    model_id = am.resolve(model)
    if any(m.get("images") for m in messages) and not am.get(model_id).vision:
        model_id = am.vision_model()                           # it can't see: let the Pictures model look
    body = _body(model_id, messages, options, stream, think)
    extra_stop = am.get(model_id).info.get("stop") or []      # e.g. ChatML's <|im_end|> for a model that types it
    if extra_stop:
        stops = body.get("stop") or []
        body["stop"] = ([stops] if isinstance(stops, str) else builtins.list(stops)) + builtins.list(extra_stop)
    rid = log.request(model, model_id, messages, options, stream, think) if log is not None else None
    started = time.time()
    try:
        if not stream:
            data = srv.post("/v1/chat/completions", body)
            msg = (data.get("choices") or [{}])[0].get("message") or {}
            _note(model_id, data.get("timings"), started)
            if log is not None:
                log.response(rid, msg.get("content") or "", msg.get("reasoning_content") or "",
                             time.time() - started, timings=data.get("timings"))
            return _message(msg.get("content") or "", msg.get("reasoning_content") or "")
        info = {}
        return _logged_stream(_stream(srv.post("/v1/chat/completions", body, stream=True), model_id, started, info),
                              log, rid, started, info)
    except RuntimeError as e:
        if log is not None:
            log.response(rid, "", "", time.time() - started, str(e))
        raise ResponseError(str(e)) from None
    except OSError as e:
        if log is not None:
            log.response(rid, "", "", time.time() - started, f"The language model isn't answering ({e}).")
        raise ResponseError(f"The language model isn't answering ({e}).") from None


def _logged_stream(parts, log, rid, started, info):
    """Pass the streamed parts through, then log the whole reply once the stream ends (or is cut off)."""
    text, thinking, error = [], [], ""
    try:
        for part in parts:
            text.append(part.message.content or "")
            thinking.append(part.message.thinking or "")
            yield part
    except GeneratorExit:
        error = "stopped before the reply finished"
        raise
    except Exception as e:
        error = str(e) or e.__class__.__name__
        raise
    finally:
        if log is not None:
            log.response(rid, "".join(text), "".join(thinking), time.time() - started, error, info.get("timings"))


def _stream(resp, model_id, started, info=None):
    """Server-sent events -> ollama-style parts (each carrying only the new text)."""
    timings = None
    with resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                data = json.loads(payload)
            except ValueError:
                continue
            timings = data.get("timings") or timings
            delta = (data.get("choices") or [{}])[0].get("delta") or {}
            content, thinking = delta.get("content") or "", delta.get("reasoning_content") or ""
            if content or thinking:
                part = _message(content, thinking)
                part.done = False
                yield part
    if info is not None:
        info["timings"] = timings
    _note(model_id, timings, started)
