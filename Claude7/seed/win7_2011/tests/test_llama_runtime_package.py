import tempfile
import unittest
import zipfile
from pathlib import Path

from win7_2011 import package_llama_runtime as runtime_package


class LlamaRuntimePackageTests(unittest.TestCase):
    def test_runtime_pin_is_windows_cuda_12_and_matches_project_baseline(self):
        self.assertEqual(runtime_package.RELEASE, "b11563")
        self.assertIn("cuda-12.4-x64.zip", runtime_package.ASSETS[0]["name"])
        self.assertIn("cudart-llama-bin-win-cuda-12.4-x64.zip",
                      runtime_package.ASSETS[1]["name"])
        self.assertEqual(len(runtime_package.ASSETS[0]["sha256"]), 64)
        self.assertEqual(len(runtime_package.ASSETS[1]["sha256"]), 64)
        self.assertEqual(
            runtime_package.REQUIRED_CUDA_DLLS,
            {"cublas64_12.dll", "cublaslt64_12.dll", "cudart64_12.dll"},
        )

    def test_assembles_server_and_cuda_dlls_from_verified_archive_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary_archive = root / "binary.zip"
            runtime_archive = root / "cuda.zip"
            with zipfile.ZipFile(binary_archive, "w") as archive:
                archive.writestr("release/bin/llama-server.exe", b"server")
                archive.writestr("release/bin/ggml-cuda.dll", b"backend")
                archive.writestr("release/LICENSE", b"MIT")
            with zipfile.ZipFile(runtime_archive, "w") as archive:
                archive.writestr("cuda/bin/cublas64_12.dll", b"cublas")
                archive.writestr("cuda/bin/cublasLt64_12.dll", b"cublasLt")
                archive.writestr("cuda/bin/cudart64_12.dll", b"cudart")

            stage = root / "stage"
            stage.mkdir()
            runtime_package._assemble_runtime(
                [binary_archive, runtime_archive], stage
            )

            self.assertEqual((stage / "llama-server.exe").read_bytes(), b"server")
            self.assertEqual((stage / "ggml-cuda.dll").read_bytes(), b"backend")
            actual_dll_names = {path.name.lower() for path in stage.glob("*.dll")}
            self.assertTrue(runtime_package.REQUIRED_CUDA_DLLS <= actual_dll_names)
            self.assertEqual(
                [path.read_bytes() for path in (stage / "licenses").iterdir()],
                [b"MIT"],
            )

    def test_rejects_path_traversal_and_conflicting_flattened_dlls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unsafe = root / "unsafe.zip"
            with zipfile.ZipFile(unsafe, "w") as archive:
                archive.writestr("../llama-server.exe", b"bad")
            stage = root / "stage"
            stage.mkdir()
            with self.assertRaisesRegex(ValueError, "Unsafe path"):
                runtime_package._assemble_runtime([unsafe], stage)

            first = root / "first.zip"
            second = root / "second.zip"
            with zipfile.ZipFile(first, "w") as archive:
                archive.writestr("a/shared.dll", b"one")
            with zipfile.ZipFile(second, "w") as archive:
                archive.writestr("b/shared.dll", b"two")
            with zipfile.ZipFile(first) as archive:
                runtime_package._copy_selected_member(
                    archive, archive.infolist()[0], stage, {}
                )
            copied = {"shared.dll": "digest-of-first"}
            with zipfile.ZipFile(second) as archive:
                with self.assertRaisesRegex(ValueError, "Different DLLs"):
                    runtime_package._copy_selected_member(
                        archive, archive.infolist()[0], stage, copied
                    )

    def test_does_not_overwrite_existing_runtime_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "runtime"
            destination.mkdir()
            marker = destination / "keep.txt"
            marker.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                runtime_package.prepare_runtime(destination)
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")


if __name__ == "__main__":
    unittest.main()
