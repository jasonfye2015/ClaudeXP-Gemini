"""Prepare the pinned llama.cpp runtime for a Windows distribution.

This is a packaging-time downloader, not part of the simulator's startup path.
It writes only to the selected output directory after verifying both upstream
archives against their pinned SHA-256 digests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


RELEASE = "b11563"
RELEASE_PAGE = f"https://github.com/ggml-org/llama.cpp/releases/tag/{RELEASE}"
ASSETS = (
    {
        "name": f"llama-{RELEASE}-bin-win-cuda-12.4-x64.zip",
        "url": (
            "https://github.com/ggml-org/llama.cpp/releases/download/"
            f"{RELEASE}/llama-{RELEASE}-bin-win-cuda-12.4-x64.zip"
        ),
        "sha256": "df6f55cb4649b46b26aa3c8fdc92208ea43c0800c2a92f989581d22e7f8a9b5d",
        "size": 265_207_154,
    },
    {
        "name": "cudart-llama-bin-win-cuda-12.4-x64.zip",
        "url": (
            "https://github.com/ggml-org/llama.cpp/releases/download/"
            f"{RELEASE}/cudart-llama-bin-win-cuda-12.4-x64.zip"
        ),
        "sha256": "8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6",
        "size": 391_443_627,
    },
)
REQUIRED_CUDA_DLLS = frozenset(
    {"cublas64_12.dll", "cublaslt64_12.dll", "cudart64_12.dll"}
)
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "Storage" / "Runtime" / "llama.cpp"


def _download_asset(asset: dict, destination: Path) -> None:
    request = urllib.request.Request(
        asset["url"], headers={"User-Agent": "Win7-2011-runtime-packager"}
    )
    digest = hashlib.sha256()
    count = 0
    with urllib.request.urlopen(request, timeout=60) as response:
        with destination.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
                count += len(chunk)
    actual_digest = digest.hexdigest()
    if count != asset["size"] or actual_digest != asset["sha256"]:
        destination.unlink(missing_ok=True)
        raise ValueError(
            f"Checksum/size verification failed for {asset['name']}: "
            f"{count} bytes, SHA-256 {actual_digest}."
        )


def _safe_member_name(member_name: str) -> PurePosixPath:
    normalized = member_name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
        or re.match(r"^[A-Za-z]:", path.parts[0])
    ):
        raise ValueError(f"Unsafe path in llama.cpp archive: {member_name!r}")
    return path


def _copy_selected_member(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    stage: Path,
    copied_dlls: dict[str, str],
) -> None:
    path = _safe_member_name(member.filename)
    if stat.S_ISLNK(member.external_attr >> 16):
        raise ValueError(f"Symbolic link in llama.cpp archive: {member.filename!r}")

    filename = path.name
    is_server = filename.lower() == "llama-server.exe"
    is_dll = filename.lower().endswith(".dll")
    is_license = any(
        keyword in filename.lower() for keyword in ("license", "licence", "notice")
    )
    if not (is_server or is_dll or is_license):
        return

    if is_license:
        output_path = stage / "licenses" / f"{hashlib.sha256(member.filename.encode()).hexdigest()[:8]}-{filename}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = stage / filename

    digest = hashlib.sha256()
    temp_path = output_path.with_name(output_path.name + ".part")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with archive.open(member) as source, temp_path.open("wb") as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)
                digest.update(chunk)
        checksum = digest.hexdigest()

        if is_dll and filename.lower() in copied_dlls:
            temp_path.unlink(missing_ok=True)
            if copied_dlls[filename.lower()] != checksum:
                raise ValueError(
                    f"Different DLLs share the name {filename!r}; "
                    "the runtime was not assembled."
                )
            return

        if output_path.exists():
            temp_path.unlink(missing_ok=True)
            if is_server or checksum != hashlib.sha256(output_path.read_bytes()).hexdigest():
                raise ValueError(f"Duplicate runtime file: {filename!r}")
            return

        os.replace(temp_path, output_path)
        if is_dll:
            copied_dlls[filename.lower()] = checksum
    finally:
        temp_path.unlink(missing_ok=True)


def _assemble_runtime(archives: list[Path], stage: Path) -> None:
    copied_dlls: dict[str, str] = {}
    server_count = 0
    for archive_path in archives:
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                name = _safe_member_name(member.filename)
                if name.name.lower() == "llama-server.exe":
                    server_count += 1
                _copy_selected_member(archive, member, stage, copied_dlls)

    if server_count != 1 or not (stage / "llama-server.exe").is_file():
        raise ValueError(
            "Expected exactly one llama-server.exe in the pinned Windows release."
        )
    missing = REQUIRED_CUDA_DLLS - copied_dlls.keys()
    if missing:
        raise ValueError(
            "The matching CUDA runtime archives are missing required DLLs: "
            + ", ".join(sorted(missing))
        )


def prepare_runtime(output_dir: Path) -> Path:
    output_dir = output_dir.expanduser().resolve()
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Refusing to replace a non-empty runtime directory: {output_dir}. "
            "Move it aside first if you intend to replace it."
        )

    with tempfile.TemporaryDirectory(prefix="win7-llama-package-") as download_dir:
        download_root = Path(download_dir)
        archive_paths = []
        for asset in ASSETS:
            archive_path = download_root / asset["name"]
            print(f"Downloading and verifying {asset['name']}…")
            _download_asset(asset, archive_path)
            archive_paths.append(archive_path)

        stage = Path(tempfile.mkdtemp(
            prefix=f"{output_dir.name}.staging-", dir=output_dir.parent
        ))
        try:
            _assemble_runtime(archive_paths, stage)
            (stage / "runtime-manifest.json").write_text(
                json.dumps(
                    {
                        "project": "ggml-org/llama.cpp",
                        "release": RELEASE,
                        "release_page": RELEASE_PAGE,
                        "variant": "Windows x64 CUDA 12.4",
                        "assets": [
                            {
                                "name": asset["name"],
                                "url": asset["url"],
                                "sha256": asset["sha256"],
                                "size": asset["size"],
                            }
                            for asset in ASSETS
                        ],
                        "dll_policy": (
                            "All DLLs from both verified official archives are "
                            "placed beside llama-server.exe."
                        ),
                    },
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )
            if output_dir.exists():
                output_dir.rmdir()
            stage.rename(output_dir)
        except BaseException:
            shutil.rmtree(stage, ignore_errors=True)
            raise

    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download and checksum-verify the pinned Windows CUDA llama.cpp "
            "runtime for packaging. This does not run from the simulator."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"runtime output directory (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    try:
        output_dir = prepare_runtime(args.output_dir)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(f"Runtime prepared at {output_dir}")
    print("Copy this directory into the Windows distribution beside the app.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
