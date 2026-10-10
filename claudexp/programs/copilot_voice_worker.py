"""Offline speech-model setup, transcription, and synthesis worker."""
import argparse
import sys
from pathlib import Path

if sys.path and Path(sys.path[0]).resolve() == Path(__file__).resolve().parent:
    sys.path.pop(0)

WHISPER_REPO = "Systran/faster-whisper-base.en"
WHISPER_REVISION = "3d3d5dee26484f91867d81cb899cfcf72b96be6c"
PIPER_VOICE = "en_US-lessac-medium"


def _catalog():
    import json
    try:
        data = json.loads(Path(__file__).with_name("piper_voices.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    revision = data.get("revision", "v1.0.0")
    return revision, {v["id"]: (v["path"], v["id"]) for v in data.get("voices", [])}


PIPER_REVISION, VOICES = _catalog()
if PIPER_VOICE not in VOICES:
    VOICES[PIPER_VOICE] = ("en/en_US/lessac/medium", PIPER_VOICE)


def install_voice(models_root, voice_id):
    if voice_id not in VOICES:
        raise ValueError(f"Unsupported Piper voice: {voice_id}")
    relative_path, filename = VOICES[voice_id]
    voice_dir = Path(models_root) / voice_id
    voice_dir.mkdir(parents=True, exist_ok=True)
    import urllib.request

    base = f"https://huggingface.co/rhasspy/piper-voices/resolve/{PIPER_REVISION}/{relative_path}/"
    for suffix in (".onnx", ".onnx.json"):
        destination = voice_dir / f"{filename}{suffix}"
        if not destination.is_file():
            print(f"Downloading local Piper voice file {destination.name}...", flush=True)
            temporary = destination.with_name(destination.name + ".download")
            try:
                urllib.request.urlretrieve(base + destination.name, temporary)
                if not temporary.is_file() or temporary.stat().st_size == 0:
                    raise OSError(f"The Piper voice download was empty: {destination.name}")
                temporary.replace(destination)
            finally:
                temporary.unlink(missing_ok=True)
    print("VOICE_READY:" + voice_id, flush=True)
    card = voice_dir / "MODEL_CARD"
    if not card.is_file():
        try:
            urllib.request.urlretrieve(base + "MODEL_CARD", card)     # its license terms, kept for offline reading
        except Exception:
            card.unlink(missing_ok=True)


def install(models_root):
    from huggingface_hub import snapshot_download

    root = Path(models_root)
    whisper_dir = root / "whisper-base.en"
    whisper_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading local Whisper model {WHISPER_REPO}...", flush=True)
    snapshot_download(
        repo_id=WHISPER_REPO,
        revision=WHISPER_REVISION,
        local_dir=str(whisper_dir),
        allow_patterns=("config.json", "model.bin", "tokenizer.json", "vocabulary.txt"),
    )
    if not (whisper_dir / "model.bin").is_file():
        raise FileNotFoundError(f"The Whisper model download is incomplete: {whisper_dir}")
    install_voice(root, PIPER_VOICE)
    print("MODELS_READY", flush=True)


def transcribe(audio_path, models_root):
    from faster_whisper import WhisperModel

    model_path = Path(models_root) / "whisper-base.en"
    if not (model_path / "model.bin").is_file():
        raise FileNotFoundError(f"The local Whisper model is not installed: {model_path}")
    model = WhisperModel(str(model_path), device="cpu", compute_type="int8")
    segments, _info = model.transcribe(audio_path, language="en", beam_size=5, vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    print("TRANSCRIPT:" + text, flush=True)


def speak(text, output, models_root, voice_id=PIPER_VOICE, length_scale=1.0):
    import wave
    from piper import PiperVoice, SynthesisConfig

    if voice_id not in VOICES:
        raise ValueError(f"Unsupported Piper voice: {voice_id}")
    voice_path = Path(models_root) / voice_id / f"{voice_id}.onnx"
    if not voice_path.is_file():
        raise FileNotFoundError(f"The local Piper voice is not installed: {voice_path}")
    voice = PiperVoice.load(str(voice_path))
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destination), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file, syn_config=SynthesisConfig(length_scale=length_scale))
    print("AUDIO_READY:" + str(destination), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("install", "install-voice", "transcribe", "speak"))
    parser.add_argument("--models-root", required=True)
    parser.add_argument("--audio", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--voice-id", default=PIPER_VOICE)
    parser.add_argument("--length-scale", type=float, default=1.0)
    args = parser.parse_args()
    try:
        if args.operation == "install":
            install(args.models_root)
        elif args.operation == "install-voice":
            install_voice(args.models_root, args.voice_id)
        elif args.operation == "transcribe":
            transcribe(args.audio, args.models_root)
        else:
            speak(args.text, args.output, args.models_root, args.voice_id, args.length_scale)
    except Exception as exc:
        print(f"ERROR:{type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
