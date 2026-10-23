"""Downloading the base model for selfmodel/train.py: Gemma 3 4B (instruction-tuned), the safetensors weights, into
Local Storage/LLM Models/selfmodel/base. Google's own copy on Hugging Face is gated (it needs an account that has
accepted the Gemma terms), so this takes Unsloth's ungated copy of the same weights; the Gemma terms of use still
apply to the model and anything made from it.

    env\\Scripts\\python.exe -m selfmodel.fetch
"""
from pathlib import Path

REPO = "unsloth/gemma-3-4b-it"
BASE = Path(__file__).resolve().parents[2] / "Local Storage" / "LLM Models" / "selfmodel" / "base"


def main():
    from huggingface_hub import snapshot_download
    BASE.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(REPO, local_dir=str(BASE),
                             allow_patterns=["*.json", "*.safetensors", "tokenizer*", "*.model", "*.jinja"])
    print("base model in", path)


if __name__ == "__main__":
    main()
