"""The Claude Timeline's AI: the llama.cpp engine (llm_server), the request queue every program shares (broker),
which model does which job (ai_models), the model downloader (llm_setup) and the request log (llmlog).

Importing it puts ClaudeCore/stubs first on sys.path, so `import ollama` anywhere (ClaudeAIM included) gets the
Timeline's own stand-in, answered by this engine."""
import sys
from pathlib import Path

_STUBS = str(Path(__file__).resolve().parents[2] / "stubs")
if _STUBS not in sys.path:
    sys.path.insert(0, _STUBS)
