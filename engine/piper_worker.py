"""Run by the Timeline's voice runtime (Local Storage/LLM Models/voice/runtime312), not by the game: it holds one Piper
voice open and speaks what it's sent, a line of JSON at a time on stdin - {"text": ..., "out": path} - writing the
samples (float32, .npy) and answering a line of JSON on stdout - {"out": path, "rate": n} or {"error": ...}.

Each sentence is spoken on its own and joined here (Piper's own joining of sentences turned to noise)."""
import json
import re
import sys
from pathlib import Path

if sys.path and Path(sys.path[0]).resolve() == Path(__file__).resolve().parent:
    sys.path.pop(0)                                          # (nothing of the game's beside this is wanted here)

import numpy as np                                           # noqa: E402
from piper import PiperVoice                                 # noqa: E402
from piper.config import SynthesisConfig                     # noqa: E402

PAUSE = 0.42                                                 # (between her sentences: she is never in a hurry)


def main():
    voice = PiperVoice.load(sys.argv[1])
    rate = voice.config.sample_rate
    cfg = SynthesisConfig(length_scale=float(sys.argv[2]) if len(sys.argv) > 2 else 1.3, normalize_audio=False)
    print(json.dumps({"ready": rate}), flush=True)
    for line in sys.stdin:
        try:
            req = json.loads(line)
            parts = []
            for sentence in re.split(r"(?<=[.!?;])\s+", req["text"].strip()):
                if not sentence:
                    continue
                audio = [c.audio_float_array for c in voice.synthesize(sentence, syn_config=cfg)]
                if audio:
                    parts += [np.concatenate(audio), np.zeros(int(rate * PAUSE), np.float32)]
            x = np.concatenate(parts) if parts else np.zeros(rate // 4, np.float32)
            np.save(req["out"], x.astype(np.float32))
            print(json.dumps({"out": req["out"], "rate": rate}), flush=True)
        except Exception as exc:                             # (one bad line never ends her voice)
            print(json.dumps({"error": str(exc)}), flush=True)


if __name__ == "__main__":
    main()
