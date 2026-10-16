"""Local desktop secrets, kept exclusively in Windows Credential Manager.

No file fallback: non-Windows hosts can use unauthenticated servers, but cannot
save credentials. The Linux test harness injects an in-memory store.
"""
from __future__ import annotations

import ctypes
import hashlib
import sys
from ctypes import wintypes


STORE_ERROR = "Windows Credential Manager is unavailable. No API key was read or saved."


def validate_api_key(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 2048 or any(
        ord(character) < 33 or ord(character) > 126 for character in value
    ):
        raise ValueError("Enter a non-empty API key using printable ASCII without spaces.")
    return value


def credential_target(backend: str, endpoint: str) -> str:
    # Import lazily to avoid transport/settings circular imports.
    from .ai_settings import normalize_endpoint
    endpoint = normalize_endpoint(backend, endpoint)
    digest = hashlib.sha256(f"{backend}\n{endpoint}".encode()).hexdigest()
    return f"win7-2011/local-ai/{digest}"


class _Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentialStore:
    def _api(self):
        if sys.platform != "win32":
            raise RuntimeError(STORE_ERROR)
        try:
            api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
            pointer = ctypes.POINTER(_Credential)
            api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                                     wintypes.DWORD, ctypes.POINTER(pointer)]
            api.CredWriteW.argtypes = [pointer, wintypes.DWORD]
            api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
            for name in ("CredReadW", "CredWriteW", "CredDeleteW"):
                getattr(api, name).restype = wintypes.BOOL
            api.CredFree.argtypes = [ctypes.c_void_p]
            api.CredFree.restype = None
            return api
        except (OSError, AttributeError):
            raise RuntimeError(STORE_ERROR) from None

    def get(self, backend: str, endpoint: str) -> str | None:
        target = credential_target(backend, endpoint)
        if sys.platform != "win32":
            return None
        api = self._api()
        pointer = ctypes.POINTER(_Credential)()
        if not api.CredReadW(target, 1, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == 1168:  # ERROR_NOT_FOUND
                return None
            raise RuntimeError(STORE_ERROR)
        try:
            blob = ctypes.string_at(pointer.contents.CredentialBlob,
                                    pointer.contents.CredentialBlobSize)
            return validate_api_key(blob.decode("utf-16-le"))
        except (UnicodeError, ValueError):
            raise RuntimeError("The saved API key is invalid. Replace it in Options.") from None
        finally:
            api.CredFree(pointer)

    def set(self, backend: str, endpoint: str, value: str) -> None:
        value = validate_api_key(value)
        target = credential_target(backend, endpoint)
        api = self._api()
        blob = value.encode("utf-16-le")
        buffer = (wintypes.BYTE * len(blob)).from_buffer_copy(blob)
        credential = _Credential()
        credential.Type = 1  # CRED_TYPE_GENERIC
        credential.TargetName = target
        credential.UserName = "local-ai"
        credential.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE (current Windows user)
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = buffer
        try:
            if not api.CredWriteW(ctypes.byref(credential), 0):
                raise RuntimeError(STORE_ERROR)
        finally:
            ctypes.memset(buffer, 0, len(blob))

    def delete(self, backend: str, endpoint: str) -> None:
        target = credential_target(backend, endpoint)
        api = self._api()
        if not api.CredDeleteW(target, 1, 0) and ctypes.get_last_error() != 1168:
            raise RuntimeError(STORE_ERROR)
