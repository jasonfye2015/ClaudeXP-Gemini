"""Offline audio/video converting for Python Studio using a bundled ffmpeg.exe (no Qt here)."""
import os
import re
import subprocess
from pathlib import Path

MEDIA_EXT = {".wav", ".mp3", ".ogg", ".m4a", ".flac", ".aac", ".wma", ".opus",
             ".mp4", ".mkv", ".avi", ".mov", ".webm", ".gif", ".wmv"}
VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".gif", ".wmv"}


def ffmpeg_exe():
    from .app import studio_root
    return studio_root() / "ffmpeg" / "ffmpeg.exe"


def available():
    return ffmpeg_exe().exists()


# key, label, what it does, which options it uses, output kind
PRESETS = [
    ("wav", "Convert to WAV (always works in pygame)", "44.1 kHz stereo WAV.", (), "file"),
    ("ogg", "Convert to OGG (small, good for music)", "Compressed OGG Vorbis.", (), "file"),
    ("mp3", "Convert to MP3", "MP3 at good quality.", (), "file"),
    ("small", "Shrink for a game (mono OGG)", "Mono, 22 kHz OGG. Tiny files, fine for sound effects.", (), "file"),
    ("trim", "Trim (keep part of it)", "Keeps the part from Start for Length seconds.", ("start", "length"), "file"),
    ("fade", "Fade in and out", "Fades the start and end over Fade seconds.", ("fade",), "file"),
    ("normalize", "Even out the volume", "Makes quiet and loud clips similar in loudness.", (), "file"),
    ("loop", "Repeat (make a longer loop)", "Plays the clip Repeat times in one file.", ("repeat",), "file"),
    ("audio", "Pull the sound out of a video (WAV)", "Saves only the audio track.", (), "file"),
    ("frames", "Video to picture frames (PNG)", "One PNG per frame, at Frames per second.", ("fps",), "folder"),
    ("gif", "Video to animated GIF", "A looping GIF at Frames per second.", ("fps", "start", "length"), "file"),
]


def preset(key):
    return next(p for p in PRESETS if p[0] == key)


def output_name(source, key):
    stem = re.sub(r"[^\w\- ]", "_", Path(source).stem)
    return {"wav": stem + ".wav", "ogg": stem + ".ogg", "mp3": stem + ".mp3", "small": stem + "_small.ogg",
            "trim": stem + "_trim.wav", "fade": stem + "_fade.wav", "normalize": stem + "_even.wav",
            "loop": stem + "_loop.wav", "audio": stem + ".wav", "frames": stem + "_frames",
            "gif": stem + ".gif"}[key]


def unique(path):
    path = Path(path)
    if not path.exists():
        return path
    for n in range(2, 1000):
        cand = path.with_name(f"{path.stem}-{n}{path.suffix}")
        if not cand.exists():
            return cand
    return path


def build(key, source, out, start=0.0, length=0.0, fade=1.0, repeat=2, fps=10, duration=None):
    """Returns the ffmpeg arguments (without the exe) for a preset. `duration` (seconds of the source) is only
    needed for the fade preset, so the fade-out begins at the right time."""
    base = ["-y", "-hide_banner", "-loglevel", "error"]
    src, out = str(source), str(out)
    audio_wav = ["-vn", "-ar", "44100", "-ac", "2"]
    if key in ("wav", "audio"):
        return base + ["-i", src] + audio_wav + [out]
    if key == "ogg":
        return base + ["-i", src, "-vn", "-c:a", "libvorbis", "-q:a", "5", out]
    if key == "mp3":
        return base + ["-i", src, "-vn", "-c:a", "libmp3lame", "-q:a", "2", out]
    if key == "small":
        return base + ["-i", src, "-vn", "-ac", "1", "-ar", "22050", "-c:a", "libvorbis", "-q:a", "3", out]
    if key == "trim":
        args = base + (["-ss", str(start)] if start else []) + ["-i", src]
        if length and length > 0:
            args += ["-t", str(length)]
        return args + audio_wav + [out]
    if key == "fade":
        fade = max(0.05, float(fade))
        filt = f"afade=t=in:st=0:d={fade}"
        if duration and duration > fade * 2:
            filt += f",afade=t=out:st={max(0.0, duration - fade):.3f}:d={fade}"
        return base + ["-i", src, "-af", filt] + audio_wav + [out]
    if key == "normalize":
        return base + ["-i", src, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11"] + audio_wav + [out]
    if key == "loop":
        return base + ["-stream_loop", str(max(0, int(repeat) - 1)), "-i", src] + audio_wav + [out]
    if key == "frames":
        return base + ["-i", src, "-vf", f"fps={fps}", str(Path(out) / "frame_%04d.png")]
    if key == "gif":
        args = base + (["-ss", str(start)] if start else []) + ["-i", src]
        if length and length > 0:
            args += ["-t", str(length)]
        return args + ["-vf", f"fps={fps},split[a][b];[a]palettegen[p];[b][p]paletteuse", "-loop", "0", out]
    raise ValueError(key)


def _env():
    env = dict(os.environ)
    for var in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(var, None)
    return env


def length_of(source):
    """Seconds of audio/video in a file, or None. ffmpeg prints the duration when given only an input."""
    try:
        done = subprocess.run([str(ffmpeg_exe()), "-hide_banner", "-i", str(source)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=30, env=_env())
    except Exception:
        return None
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", done.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else None


def convert(key, source, out_dir, timeout=600, **options):
    """Runs a preset. Returns (ok, output_path_or_message)."""
    if not available():
        return False, "ffmpeg.exe was not found in Local Storage\\Python Studio\\ffmpeg."
    source = Path(source)
    if not source.is_file():
        return False, "That file does not exist."
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = unique(out_dir / output_name(source, key))
    if preset(key)[4] == "folder":
        out.mkdir(parents=True, exist_ok=True)
    if key == "fade" and options.get("duration") is None:
        options["duration"] = length_of(source)
    args = build(key, source, out, **options)
    try:
        done = subprocess.run([str(ffmpeg_exe())] + args, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout, env=_env())
    except subprocess.TimeoutExpired:
        return False, "That took too long and was stopped."
    if done.returncode != 0 or not out.exists():
        lines = [ln for ln in done.stderr.strip().splitlines() if ln.strip()]
        reason = lines[-1] if lines else "unknown error"
        if "does not contain any stream" in reason or "Output file does not contain" in reason or (
                "Invalid argument" in reason and key in ("wav", "audio", "ogg", "mp3", "small")):
            reason = "This file has no sound to use."
        return False, "ffmpeg could not do that: " + reason
    if out.is_dir() and not any(out.iterdir()):
        return False, "No pictures were produced. Is this a video?"
    return True, str(out)
