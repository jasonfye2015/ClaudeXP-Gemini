"""ClaudeXP's stand-in for the 'ollama' Python package.

ClaudeAIM (left exactly as it is), the model broker and ClaudeAI all `import ollama`. ClaudeXP puts this folder
first on sys.path, so they get this module instead: the same few calls - list(), show() and chat() (plain or
streamed, with pictures) - answered by ClaudeXP's own llama.cpp server (claudexp/llm_server.py) and the model in
Local Storage/LLM Models. There is one model, so whatever model name a program asks for, it gets that one.
Without an engine or a model, every call fails at once with a plain message instead of hanging."""
import base64
import builtins
import json
from types import SimpleNamespace

__version__ = "claudexp"


class ResponseError(Exception):
    pass


def _server():
    from claudexp import llm_server
    return llm_server


# ---- list / show ------------------------------------------------------------------------------------------------

def list():  # noqa: A001 - same name as ollama's
    srv = _server()
    name = srv.model_name()
    models = [SimpleNamespace(model=name, name=name)] if srv.available() and name else []
    return SimpleNamespace(models=models)


def show(model=None):
    srv = _server()
    if not srv.available():
        raise ResponseError(srv.status())
    caps = ["completion"] + (["vision"] if srv.find_projector() is not None else [])
    family = srv.model_name().split(":")[0] or "llama"
    return SimpleNamespace(capabilities=caps, modelinfo={f"{family}.context_length": srv.train_context()},
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


def _body(messages, options, stream, think):
    options = options or {}
    body = {"messages": [_content(m) for m in messages], "stream": bool(stream), "cache_prompt": True,
            "_ctx": options.get("num_ctx")}
    for ours, theirs in (("temperature", "temperature"), ("top_p", "top_p"), ("top_k", "top_k"),
                         ("num_predict", "max_tokens"), ("stop", "stop"), ("repeat_penalty", "repeat_penalty"),
                         ("seed", "seed"), ("min_p", "min_p")):
        if options.get(ours) is not None:
            body[theirs] = options[ours]
    if think is False:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    return body


def _message(content="", thinking=""):
    return SimpleNamespace(message=SimpleNamespace(role="assistant", content=content, thinking=thinking or None),
                           done=True)


def chat(model=None, messages=(), options=None, stream=False, think=None, keep_alive=None, **_ignored):
    srv = _server()
    if not srv.available():
        raise ResponseError(srv.status())
    body = _body(builtins.list(messages), options, stream, think)
    try:
        if not stream:
            data = srv.post("/v1/chat/completions", body)
            msg = (data.get("choices") or [{}])[0].get("message") or {}
            return _message(msg.get("content") or "", msg.get("reasoning_content") or "")
        return _stream(srv.post("/v1/chat/completions", body, stream=True))
    except RuntimeError as e:
        raise ResponseError(str(e)) from None
    except OSError as e:
        raise ResponseError(f"The language model isn't answering ({e}).") from None


def _stream(resp):
    """Server-sent events -> ollama-style parts (each carrying only the new text)."""
    with resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                delta = (json.loads(payload).get("choices") or [{}])[0].get("delta") or {}
            except ValueError:
                continue
            content, thinking = delta.get("content") or "", delta.get("reasoning_content") or ""
            if content or thinking:
                part = _message(content, thinking)
                part.done = False
                yield part

