"""Downloading a base model for selfmodel/train.py (the safetensors weights, not a GGUF) into
Local Storage/LLM Models/selfmodel/<folder>.

    env\\Scripts\\python.exe -m selfmodel.fetch                 Gemma 3 4B instruct -> base\\
    env\\Scripts\\python.exe -m selfmodel.fetch nemomix         NemoMix Unleashed 12B -> base-nemomix\\

Gemma: Google's own copy on Hugging Face is gated (it needs an account that has accepted the Gemma terms), so this
takes Unsloth's ungated copy of the same weights; the Gemma terms of use still apply to the model and anything made
from it. NemoMix Unleashed 12B (MarinaraSpaghetti, a merge of Mistral Nemo fine-tunes) is Apache 2.0, 24.5 GB.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "Local Storage" / "LLM Models" / "selfmodel"
BASES = {"gemma": ("unsloth/gemma-3-4b-it", ROOT / "base"),
         "nemomix": ("MarinaraSpaghetti/NemoMix-Unleashed-12B", ROOT / "base-nemomix")}
BASE = BASES["gemma"][1]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    key = argv[0] if argv else "gemma"
    repo, folder = BASES[key]
    from huggingface_hub import snapshot_download
    folder.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(repo, local_dir=str(folder),
                             allow_patterns=["*.json", "*.safetensors", "tokenizer*", "*.model", "*.jinja"])
    print("base model in", path)


if __name__ == "__main__":
    main()
