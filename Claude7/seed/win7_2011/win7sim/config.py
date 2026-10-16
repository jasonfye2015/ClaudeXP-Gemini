from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import secrets
import shutil
import tempfile
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
STORAGE_ROOT = APP_ROOT / "Storage"
SYSTEM_ROOT = STORAGE_ROOT / "System"
ACCOUNT_FILE = SYSTEM_ROOT / "account.json"
LLAMA_RUNTIME = STORAGE_ROOT / "Runtime" / "llama.cpp"
LLAMA_SERVER_EXECUTABLE = LLAMA_RUNTIME / (
    "llama-server.exe" if os.name == "nt" else "llama-server"
)
MODELS_ROOT = STORAGE_ROOT / "Models"
BIOS_SETTINGS_FILE = SYSTEM_ROOT / "bios.json"
BIOS_PASSWORDS_FILE = SYSTEM_ROOT / "bios-passwords.json"
WINDOWS_UPDATE_STATE_FILE = SYSTEM_ROOT / "windows-update.json"
BIOS_PASSWORD_HASH_ITERATIONS = 600_000
BIOS_PASSWORD_MAX_HASH_ITERATIONS = 5_000_000
BIOS_PASSWORD_ROLES = frozenset({"supervisor", "user"})
USER_PROFILES = STORAGE_ROOT / "Profiles"
USER_DOCUMENTS = STORAGE_ROOT / "UserData" / "Documents"
MESSENGER_HISTORY = STORAGE_ROOT / "UserData" / "Messenger"
STICKY_NOTES = STORAGE_ROOT / "UserData" / "Sticky Notes"
MEDIA_PLAYLISTS = STORAGE_ROOT / "UserData" / "Media Player Playlists"
SCREEN_SAVER_SETTINGS_DIR = STORAGE_ROOT / "UserData" / "Screen Saver"
SCREEN_SAVER_SETTINGS_FILE = SCREEN_SAVER_SETTINGS_DIR / "settings.json"
DEFRAGMENTER_SETTINGS_DIR = STORAGE_ROOT / "UserData" / "Disk Defragmenter"
DEFRAGMENTER_SETTINGS_FILE = DEFRAGMENTER_SETTINGS_DIR / "settings.json"
DEFRAGMENTER_MIN_CYCLE_DURATION_MS = 40_000
DEFRAGMENTER_MAX_CYCLE_DURATION_MS = 180_000
DEFRAGMENTER_MIN_RESET_PAUSE_MS = 100
DEFRAGMENTER_MAX_RESET_PAUSE_MS = 30_000
SCREEN_SAVER_TYPES = frozenset({"bubbles", "mystify"})
SCREEN_SAVER_TIMEOUTS = frozenset({0, 60, 300, 600, 900, 1800})
DEFAULT_SCREEN_SAVER_SETTINGS = {
    "saver": "bubbles",
    "timeout_seconds": 300,
}

STORAGE_FOLDERS = (
    SYSTEM_ROOT,
    LLAMA_RUNTIME,
    USER_PROFILES,
    STORAGE_ROOT / "Media" / "TV",
    STORAGE_ROOT / "Media" / "Movies",
    STORAGE_ROOT / "Media" / "Music",
    STORAGE_ROOT / "ROMs",
    MODELS_ROOT,
    USER_DOCUMENTS,
    MESSENGER_HISTORY,
    STICKY_NOTES,
    MEDIA_PLAYLISTS,
    SCREEN_SAVER_SETTINGS_DIR,
    DEFRAGMENTER_SETTINGS_DIR,
)


def load_bios_settings() -> dict[str, list[int]]:
    """Load BIOS choice indexes saved by the setup utility."""
    if not BIOS_SETTINGS_FILE.exists():
        return {}
    return _read_bios_settings(BIOS_SETTINGS_FILE)


def load_screen_saver_settings() -> dict[str, object]:
    """Load the Windows user's screen-saver choice and idle timeout."""
    if not SCREEN_SAVER_SETTINGS_FILE.exists():
        return DEFAULT_SCREEN_SAVER_SETTINGS.copy()
    try:
        settings = json.loads(SCREEN_SAVER_SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read screen-saver settings: {exc}") from exc
    _validate_screen_saver_settings(settings)
    return settings


def save_screen_saver_settings(settings: dict[str, object]) -> None:
    """Validate and atomically save the user's screen-saver preferences."""
    _validate_screen_saver_settings(settings)
    SCREEN_SAVER_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_write_private_json(
        SCREEN_SAVER_SETTINGS_FILE,
        json.dumps(settings, indent=2) + "\n",
    )


def load_defragmenter_settings(
    defaults: dict[str, int] | None = None,
) -> dict[str, int]:
    """Load defragmenter timing preferences, filling missing older fields."""
    defaults = defaults or {
        "cycle_duration_ms": 42_000,
        "reset_pause_ms": 1_400,
    }
    _validate_defragmenter_settings(defaults, allow_partial=False)
    merged = defaults.copy()
    if DEFRAGMENTER_SETTINGS_FILE.exists():
        try:
            settings = json.loads(DEFRAGMENTER_SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read defragmenter settings: {exc}") from exc
        if not isinstance(settings, dict) or set(settings) - set(defaults):
            raise ValueError("Defragmenter settings contain an invalid structure.")
        merged.update(settings)
    _validate_defragmenter_settings(merged, allow_partial=False)
    return {
        "cycle_duration_ms": max(
            DEFRAGMENTER_MIN_CYCLE_DURATION_MS,
            min(DEFRAGMENTER_MAX_CYCLE_DURATION_MS, merged["cycle_duration_ms"]),
        ),
        "reset_pause_ms": max(
            DEFRAGMENTER_MIN_RESET_PAUSE_MS,
            min(DEFRAGMENTER_MAX_RESET_PAUSE_MS, merged["reset_pause_ms"]),
        ),
    }


def save_defragmenter_settings(settings: dict[str, int]) -> None:
    """Validate and atomically save defragmenter timing preferences."""
    _validate_defragmenter_settings(settings, allow_partial=False)
    if not (
        DEFRAGMENTER_MIN_CYCLE_DURATION_MS
        <= settings["cycle_duration_ms"]
        <= DEFRAGMENTER_MAX_CYCLE_DURATION_MS
        and DEFRAGMENTER_MIN_RESET_PAUSE_MS
        <= settings["reset_pause_ms"]
        <= DEFRAGMENTER_MAX_RESET_PAUSE_MS
    ):
        raise ValueError("Defragmenter settings are outside supported limits.")
    DEFRAGMENTER_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_write_private_json(
        DEFRAGMENTER_SETTINGS_FILE,
        json.dumps(settings, indent=2) + "\n",
    )


def load_windows_update_state() -> dict[str, object] | None:
    """Load machine-level simulated Windows Update schedule and progress."""
    if not WINDOWS_UPDATE_STATE_FILE.exists():
        return None
    try:
        state = json.loads(WINDOWS_UPDATE_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read Windows Update state: {exc}") from exc
    _validate_windows_update_state(state)
    return state


def save_windows_update_state(state: dict[str, object]) -> None:
    """Validate and atomically save machine-level simulated update state."""
    _validate_windows_update_state(state)
    WINDOWS_UPDATE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_private_json(
        WINDOWS_UPDATE_STATE_FILE,
        json.dumps(state, indent=2) + "\n",
    )


def _validate_windows_update_state(state: object) -> None:
    required = {
        "automatic_enabled",
        "next_auto_check_at",
        "last_install_at",
        "last_installed_updates",
        "completed_batches",
        "pending_updates",
        "pending_index",
        "pending_stage",
    }
    if not isinstance(state, dict) or set(state) != required:
        raise ValueError("Windows Update state contains an invalid structure.")
    if type(state["automatic_enabled"]) is not bool:
        raise ValueError("Windows Update automatic setting must be true or false.")
    next_check = state["next_auto_check_at"]
    if (
        type(next_check) not in (int, float)
        or not math.isfinite(next_check)
        or next_check <= 0
    ):
        raise ValueError("Windows Update schedule contains an invalid time.")
    last_install = state["last_install_at"]
    if last_install is not None and (
        type(last_install) not in (int, float)
        or not math.isfinite(last_install)
        or last_install <= 0
    ):
        raise ValueError("Windows Update history contains an invalid time.")
    history = state["last_installed_updates"]
    if (
        not isinstance(history, list)
        or len(history) > 14
        or any(not isinstance(item, str) or not item or len(item) > 140 for item in history)
    ):
        raise ValueError("Windows Update history contains an invalid update name.")
    batches = state["completed_batches"]
    if type(batches) is not int or batches < 0:
        raise ValueError("Windows Update batch count is invalid.")
    pending = state["pending_updates"]
    index = state["pending_index"]
    stage = state["pending_stage"]
    if pending is None:
        if type(index) is not int or index != 0 or stage is not None:
            raise ValueError("Windows Update pending state is inconsistent.")
    elif (
        not isinstance(pending, list)
        or not 7 <= len(pending) <= 14
        or any(not isinstance(item, str) or not item or len(item) > 140 for item in pending)
        or type(index) is not int
        or not 0 <= index < len(pending)
        or not isinstance(stage, str)
        or stage not in {"downloading", "installing"}
    ):
        raise ValueError("Windows Update pending batch is invalid.")


def _validate_screen_saver_settings(settings: object) -> None:
    if (
        not isinstance(settings, dict)
        or set(settings) != {"saver", "timeout_seconds"}
        or not isinstance(settings["saver"], str)
        or settings["saver"] not in SCREEN_SAVER_TYPES
        or type(settings["timeout_seconds"]) is not int
        or settings["timeout_seconds"] not in SCREEN_SAVER_TIMEOUTS
    ):
        raise ValueError("Screen-saver settings contain an invalid value.")


def _validate_defragmenter_settings(
    settings: object,
    *,
    allow_partial: bool,
) -> None:
    required = {"cycle_duration_ms", "reset_pause_ms"}
    if (
        not isinstance(settings, dict)
        or (not allow_partial and set(settings) != required)
        or (allow_partial and set(settings) - required)
        or any(type(value) is not int for value in settings.values())
    ):
        raise ValueError("Defragmenter settings contain an invalid value.")


def load_bios_settings_backup() -> dict[str, list[int]]:
    """Read the known-good copy without repairing or modifying either file."""
    return _read_bios_settings(_bios_settings_backup_path())


def _bios_settings_backup_path() -> Path:
    return BIOS_SETTINGS_FILE.with_name("bios.backup.json")


def _read_bios_settings(path: Path) -> dict[str, list[int]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read local BIOS settings: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Local BIOS settings must be a JSON object.")

    settings: dict[str, list[int]] = {}
    for page, values in raw.items():
        if (
            not isinstance(page, str)
            or not isinstance(values, list)
            or any(type(value) is not int or value < 0 for value in values)
        ):
            raise ValueError("Local BIOS settings contain an invalid value.")
        settings[page] = values
    return settings


def save_bios_settings(
    settings: dict[str, list[int]], *, preserve_original: bool = False,
) -> None:
    """Save settings atomically, then refresh their known-good copy."""
    if not isinstance(settings, dict) or any(
        not isinstance(page, str)
        or not isinstance(values, list)
        or any(type(value) is not int or value < 0 for value in values)
        for page, values in settings.items()
    ):
        raise ValueError("BIOS settings contain an invalid value.")

    BIOS_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if preserve_original:
        _archive_bios_settings()
    serialized = json.dumps(settings, indent=2) + "\n"
    _atomic_write_private_json(BIOS_SETTINGS_FILE, serialized)
    # Never refresh the backup from unverified on-disk contents, or before a
    # failed primary save. A backup failure is reported rather than hidden.
    _atomic_write_private_json(_bios_settings_backup_path(), serialized)


def _archive_bios_settings() -> Path:
    """Keep the original bytes in a unique file before any recovery write."""
    original = BIOS_SETTINGS_FILE.read_bytes()
    descriptor, filename = tempfile.mkstemp(
        prefix="bios.damaged-", suffix=".json", dir=BIOS_SETTINGS_FILE.parent,
    )
    archive = Path(filename)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(original)
            handle.flush()
            os.fsync(handle.fileno())
        _sync_directory(BIOS_SETTINGS_FILE.parent)
    except BaseException:
        archive.unlink(missing_ok=True)
        raise
    return archive


def restore_bios_settings(
    verified_settings: dict[str, list[int]],
) -> Path:
    """Explicitly restore a UI-validated backup, preserving the damaged file."""
    settings = load_bios_settings_backup()
    if settings != verified_settings:
        raise ValueError("The BIOS settings backup changed; try recovery again.")
    archive = _archive_bios_settings()
    _atomic_write_private_json(
        BIOS_SETTINGS_FILE, json.dumps(settings, indent=2) + "\n",
    )
    return archive


def _messenger_history_path(contact_id: str, profile_id: str | None = None) -> Path:
    """Return the local transcript file for a stable community contact ID."""
    if not isinstance(contact_id, str) or not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*", contact_id
    ):
        raise ValueError("Messenger contact ID is invalid.")
    if profile_id is None:
        return MESSENGER_HISTORY / f"{contact_id}.json"
    if not isinstance(profile_id, str) or not re.fullmatch(
        r"[A-Za-z0-9_-]+", profile_id
    ):
        raise ValueError("Messenger fursona ID is invalid.")
    return MESSENGER_HISTORY / "Profiles" / profile_id / f"{contact_id}.json"


def clear_messenger_history(contact_id: str, profile_id: str | None = None) -> None:
    """Delete only this contact's saved transcript; missing files are already clear."""
    _messenger_history_path(contact_id, profile_id).unlink(missing_ok=True)


def load_messenger_history(
    contact_id: str, profile_id: str | None = None,
) -> list[dict[str, str]]:
    """Load and validate one contact's locally saved Messenger transcript."""
    path = _messenger_history_path(contact_id, profile_id)
    return _read_messenger_history(path, contact_id, profile_id)


def _read_messenger_history(
    path: Path, contact_id: str, profile_id: str | None,
) -> list[dict[str, str]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read saved conversation: {exc}") from exc

    if (
        not isinstance(raw, dict)
        or type(raw.get("version")) is not int
        or raw.get("version") != (1 if profile_id is None else 2)
        or (profile_id is not None and raw.get("profile_id") != profile_id)
        or raw.get("contact_id") != contact_id
        or not isinstance(raw.get("messages"), list)
    ):
        raise ValueError("The saved conversation file has an invalid format.")

    messages: list[dict[str, str]] = []
    for message in raw["messages"]:
        if (
            not isinstance(message, dict)
            or set(message) != {"role", "content"}
            or not isinstance(message["role"], str)
            or message["role"] not in {"user", "assistant"}
            or not isinstance(message["content"], str)
        ):
            raise ValueError("The saved conversation contains an invalid message.")
        messages.append({"role": message["role"], "content": message["content"]})
    return messages


def save_messenger_history(
    contact_id: str,
    messages: list[dict[str, str]],
    profile_id: str | None = None,
) -> None:
    """Atomically save a validated contact transcript in local Storage."""
    path = _messenger_history_path(contact_id, profile_id)
    if not isinstance(messages, list) or any(
        not isinstance(message, dict)
        or set(message) != {"role", "content"}
        or not isinstance(message["role"], str)
        or message["role"] not in {"user", "assistant"}
        or not isinstance(message["content"], str)
        for message in messages
    ):
        raise ValueError("Messenger conversation contains an invalid message.")

    serialized = json.dumps(
        {
            "version": 1 if profile_id is None else 2,
            **({"profile_id": profile_id} if profile_id is not None else {}),
            "contact_id": contact_id, "messages": messages,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_private_json(path, serialized)


def assign_legacy_messenger_history(contact_id: str, profile_id: str) -> None:
    """Assign an unowned chat once, preserving its original bytes as a backup.

    The original is moved to a claimed archive before writing the scoped copy.
    A failed save leaves that archive available for retry by the same owner only.
    """
    target = _messenger_history_path(contact_id, profile_id)
    source = _messenger_history_path(contact_id)
    archive = MESSENGER_HISTORY / "Legacy" / f"{contact_id}.json"
    owner_path = archive.with_suffix(".owner.json")
    if target.exists():
        raise ValueError("This fursona already has a saved conversation; it was not replaced.")
    # A single exclusive ownership record prevents distributing a legacy chat
    # to multiple identities, including after an interrupted assignment.
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    if owner_path.exists():
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
        if owner != {"profile_id": profile_id}:
            raise ValueError("This older conversation is already assigned to another fursona.")
    else:
        if not source.exists():
            raise ValueError("There is no unassigned older conversation.")
        _read_messenger_history(source, contact_id, None)
        with owner_path.open("x", encoding="utf-8") as file:
            json.dump({"profile_id": profile_id}, file)
            file.flush()
            os.fsync(file.fileno())
    if not archive.exists():
        source.rename(archive)
    messages = _read_messenger_history(archive, contact_id, None)
    save_messenger_history(contact_id, messages, profile_id)


def legacy_messenger_history_available(contact_id: str, profile_id: str) -> bool:
    """Report unclaimed chats, or an interrupted assignment for this owner."""
    _messenger_history_path(contact_id, profile_id)
    archive = MESSENGER_HISTORY / "Legacy" / f"{contact_id}.json"
    owner_path = archive.with_suffix(".owner.json")
    if owner_path.exists():
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
        return (
            owner == {"profile_id": profile_id}
            and not _messenger_history_path(contact_id, profile_id).exists()
        )
    return _messenger_history_path(contact_id).exists()


def preview_legacy_messenger_history(
    contact_id: str, profile_id: str,
) -> list[dict[str, str]]:
    """Read an unclaimed chat without writes, respecting interrupted ownership."""
    if not legacy_messenger_history_available(contact_id, profile_id):
        raise ValueError("There is no older conversation available to this fursona.")
    archive = MESSENGER_HISTORY / "Legacy" / f"{contact_id}.json"
    owner_path = archive.with_suffix(".owner.json")
    path = archive if owner_path.exists() and archive.exists() else _messenger_history_path(contact_id)
    return _read_messenger_history(path, contact_id, None)


def export_messenger_histories(
    destination: Path, contact_id: str | None = None, profile_id: str | None = None,
) -> int:
    """Export saved chats as readable JSON without writing to local histories."""
    from .contacts import CONTACTS

    destination = Path(destination)
    resolved = destination.resolve()
    for protected_root in (STORAGE_ROOT, MESSENGER_HISTORY):
        if resolved.is_relative_to(protected_root.resolve()):
            raise ValueError(
                "Choose a location outside the simulator's Storage folder "
                "and saved Messenger histories. Format and reinstall erases Storage."
            )
    contacts = CONTACTS
    if contact_id is not None:
        contacts = tuple(contact for contact in CONTACTS if contact.contact_id == contact_id)
        if not contacts:
            raise ValueError("Unknown Messenger contact.")

    conversations = []
    for contact in contacts:
        try:
            messages = load_messenger_history(contact.contact_id, profile_id)
        except (OSError, UnicodeError, ValueError) as exc:
            raise ValueError(
                f"Could not export {contact.display_name} ({contact.contact_id}): {exc}"
            ) from exc
        if messages:
            conversations.append({
                "contact_id": contact.contact_id,
                "display_name": contact.display_name,
                "online_name": contact.online_name,
                "messages": messages,
            })
    if not conversations:
        raise ValueError("There are no saved messages to export.")
    serialized = json.dumps(
        {
            "version": 1 if profile_id is None else 2,
            **({"profile_id": profile_id} if profile_id is not None else {}),
            "conversations": conversations,
        },
        ensure_ascii=False, indent=2,
    ) + "\n"
    # Read every source before writing; a damaged chat must not produce a
    # misleading partial backup or replace a previous export.
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent,
            prefix=".messenger-export-", suffix=".tmp", delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
        temporary_path.replace(destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return len(conversations)


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def validate_messenger_export(raw: object) -> dict:
    """Validate the complete export, including identities, before any writes."""
    from .contacts import CONTACTS

    if not isinstance(raw, dict) or type(raw.get("version")) is not int:
        raise ValueError("Not a Messenger JSON export.")
    version = raw["version"]
    expected = {"version", "conversations"} | ({"profile_id"} if version == 2 else set())
    if version not in {1, 2} or set(raw) != expected:
        raise ValueError("Unsupported Messenger export format or version.")
    if version == 2:
        _messenger_history_path("validation", raw["profile_id"])
        if raw["profile_id"] is None:
            raise ValueError("The export is missing its fursona ID.")
    conversations = raw["conversations"]
    if not isinstance(conversations, list) or not conversations:
        raise ValueError("The export must contain at least one conversation.")
    known_ids = {contact.contact_id for contact in CONTACTS}
    seen = set()
    for conversation in conversations:
        if (
            not isinstance(conversation, dict)
            or set(conversation) != {"contact_id", "display_name", "online_name", "messages"}
            or not isinstance(conversation["contact_id"], str)
            or conversation["contact_id"] not in known_ids
            or conversation["contact_id"] in seen
            or not isinstance(conversation["display_name"], str)
            or not isinstance(conversation["online_name"], str)
            or not isinstance(conversation["messages"], list)
        ):
            raise ValueError("The export contains an invalid, unknown or duplicate contact.")
        seen.add(conversation["contact_id"])
        for message in conversation["messages"]:
            if (
                not isinstance(message, dict)
                or set(message) != {"role", "content"}
                or not isinstance(message["role"], str)
                or message["role"] not in {"user", "assistant"}
                or not isinstance(message["content"], str)
            ):
                raise ValueError("The export contains an invalid message.")
    # Detach the validated snapshot from caller-owned mutable data.
    return json.loads(json.dumps(raw))


def read_messenger_export(source: Path) -> dict:
    """Read one immutable preview snapshot; reject ambiguous duplicate keys."""
    return validate_messenger_export(json.loads(
        Path(source).read_text(encoding="utf-8"), object_pairs_hook=_unique_json_object,
    ))


def import_messenger_histories(
    exported: dict, profile_id: str, conflict_policy: str,
) -> dict[str, list[dict[str, str]]]:
    """Restore a validated snapshot to an explicitly chosen owner as one batch.

    Stage a complete profile directory before swapping it in. On a failed swap,
    rename the untouched original back; never implement rollback by rewriting
    transcripts, which could itself fail on a full disk.
    """
    exported = validate_messenger_export(exported)
    if profile_id is None:
        raise ValueError("Choose the fursona that owns these imported chats.")
    profile_dir = _messenger_history_path("validation", profile_id).parent
    if conflict_policy not in {"skip", "append", "replace"}:
        raise ValueError("Choose how to handle existing histories.")
    updates = {}
    for conversation in exported["conversations"]:
        contact_id = conversation["contact_id"]
        path = _messenger_history_path(contact_id, profile_id)
        exists = path.exists()
        if exists and conflict_policy == "skip":
            continue
        # Do not replace a damaged history even with the replace policy.
        existing = load_messenger_history(contact_id, profile_id)
        messages = conversation["messages"]
        updates[contact_id] = existing + messages if conflict_policy == "append" else messages
    if not updates:
        return {}
    profile_dir.parent.mkdir(parents=True, exist_ok=True)
    transaction = Path(tempfile.mkdtemp(prefix=".messenger-import-", dir=profile_dir.parent))
    staged = transaction / "staged"
    backup = transaction / "original"
    preserve_recovery = False
    try:
        if profile_dir.exists():
            shutil.copytree(profile_dir, staged)
        else:
            staged.mkdir()
        for contact_id, messages in updates.items():
            _atomic_write_private_json(staged / f"{contact_id}.json", json.dumps({
                "version": 2, "profile_id": profile_id,
                "contact_id": contact_id, "messages": messages,
            }, ensure_ascii=False, indent=2) + "\n")
        if profile_dir.exists():
            os.rename(profile_dir, backup)
        try:
            os.rename(staged, profile_dir)
        except OSError:
            if backup.exists():
                try:
                    os.rename(backup, profile_dir)
                except OSError as recovery_error:
                    preserve_recovery = True
                    raise OSError(
                        f"Import failed. Original histories are preserved at {backup}; "
                        "restore that directory before using Messenger."
                    ) from recovery_error
            raise
        _sync_directory(profile_dir.parent)
    finally:
        if not preserve_recovery:
            shutil.rmtree(transaction, ignore_errors=True)
    return updates


def hash_bios_password(password: str) -> str:
    """Return a salted PBKDF2 hash suitable for local BIOS credential storage."""
    if not isinstance(password, str) or not password:
        raise ValueError("BIOS passwords must not be empty.")
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        BIOS_PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${BIOS_PASSWORD_HASH_ITERATIONS}"
        f"${salt.hex()}${password_hash.hex()}"
    )


def verify_bios_password(password: str, encoded_hash: str) -> bool:
    """Check a password against its versioned, salted PBKDF2 representation."""
    try:
        algorithm, iterations_text, salt_hex, expected_hex = encoded_hash.split("$")
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(expected_hex)
        if (
            algorithm != "pbkdf2_sha256"
            or iterations < 1
            or iterations > BIOS_PASSWORD_MAX_HASH_ITERATIONS
            or len(salt) != 16
            or len(expected_hash) != hashlib.sha256().digest_size
        ):
            return False
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
    except (AttributeError, TypeError, ValueError, UnicodeError):
        return False
    return hmac.compare_digest(actual_hash, expected_hash)


def load_bios_password_hashes() -> dict[str, str]:
    """Load validated hashes, falling back to the private validated backup."""
    password_hashes, _recovery_status = load_bios_password_hashes_with_status()
    return password_hashes


def load_bios_password_hashes_with_status() -> tuple[dict[str, str], str | None]:
    """Load validated hashes and report when the password backup was used."""
    try:
        return _read_bios_password_hashes(BIOS_PASSWORDS_FILE), None
    except FileNotFoundError:
        primary_error: Exception | None = None
    except (OSError, UnicodeError, ValueError) as exc:
        primary_error = exc

    try:
        password_hashes = _read_bios_password_hashes(_bios_password_backup_path())
    except FileNotFoundError:
        if primary_error is None:
            return {}, None
        backup_error: Exception = FileNotFoundError(
            "The BIOS password backup file is missing."
        )
    except (OSError, UnicodeError, ValueError) as exc:
        backup_error = exc
    else:
        try:
            _atomic_write_private_json(
                BIOS_PASSWORDS_FILE,
                json.dumps(password_hashes, indent=2) + "\n",
            )
        except OSError:
            return (
                password_hashes,
                "BIOS password backup recovery used; main file repair failed; backup remains active.",
            )
        return (
            password_hashes,
            "BIOS password backup recovery used; main file repaired.",
        )

    raise ValueError(
        "Neither the primary BIOS password file nor its backup could be verified. "
        "BIOS startup, setup, and F8 recovery remain locked; restore a valid "
        "password file from a trusted copy."
    ) from backup_error


def _read_bios_password_hashes(path: Path) -> dict[str, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read {path.name}: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) - BIOS_PASSWORD_ROLES:
        raise ValueError("Local BIOS password settings contain an invalid role.")
    hashes: dict[str, str] = {}
    for role, encoded_hash in raw.items():
        if (
            not isinstance(encoded_hash, str)
            or not _is_valid_bios_password_hash(encoded_hash)
        ):
            raise ValueError("Local BIOS password settings contain an invalid hash.")
        hashes[role] = encoded_hash
    return hashes


def _is_valid_bios_password_hash(encoded_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, digest_hex = encoded_hash.split("$")
        iterations = int(iterations_text)
        return (
            algorithm == "pbkdf2_sha256"
            and iterations >= 1
            and iterations <= BIOS_PASSWORD_MAX_HASH_ITERATIONS
            and len(bytes.fromhex(salt_hex)) == 16
            and len(bytes.fromhex(digest_hex)) == hashlib.sha256().digest_size
        )
    except (TypeError, ValueError):
        return False


def save_bios_password_hashes(password_hashes: dict[str, str]) -> None:
    """Atomically store validated hashes in private primary and backup files."""
    if (
        not isinstance(password_hashes, dict)
        or set(password_hashes) - BIOS_PASSWORD_ROLES
        or any(
            not isinstance(encoded_hash, str)
            or not _is_valid_bios_password_hash(encoded_hash)
            for encoded_hash in password_hashes.values()
        )
    ):
        raise ValueError("BIOS password settings contain an invalid value.")

    serialized = json.dumps(password_hashes, indent=2) + "\n"
    BIOS_PASSWORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    backup_file = _bios_password_backup_path()
    # Update the backup first: until the primary replacement succeeds, the old
    # primary remains authoritative. Both files contain only validated hashes.
    _atomic_write_private_json(backup_file, serialized)
    _atomic_write_private_json(BIOS_PASSWORDS_FILE, serialized)


def _bios_password_backup_path() -> Path:
    return BIOS_PASSWORDS_FILE.with_name("bios-passwords.backup.json")


def _atomic_write_private_json(path: Path, serialized: str) -> None:
    temporary_file = path.with_suffix(".json.tmp")
    try:
        temporary_file.write_text(serialized, encoding="utf-8")
        try:
            temporary_file.chmod(0o600)
        except OSError:
            # Some platforms do not expose POSIX file permissions.
            pass
        _sync_file(temporary_file)
        temporary_file.replace(path)
        _sync_directory(path.parent)
    finally:
        temporary_file.unlink(missing_ok=True)


def _sync_file(path: Path) -> None:
    with path.open("rb+") as file_handle:
        os.fsync(file_handle.fileno())


def _sync_directory(path: Path) -> None:
    """Persist directory entry changes where the platform supports it."""
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        # Windows and some filesystems do not support syncing directories.
        pass
    finally:
        os.close(descriptor)


def _write_bios_recovery_journal(
    password_hashes: dict[str, str],
    settings: dict[str, list[int]],
) -> None:
    journal = _bios_password_recovery_journal_path()
    journal.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = journal.with_suffix(".json.tmp")
    try:
        temporary_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "password_hashes": password_hashes,
                    "settings": settings,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            temporary_file.chmod(0o600)
        except OSError:
            # Some platforms do not expose POSIX file permissions.
            pass
        _sync_file(temporary_file)
        temporary_file.replace(journal)
        _sync_directory(journal.parent)
    finally:
        temporary_file.unlink(missing_ok=True)


def recover_interrupted_bios_password_recovery() -> str | None:
    """Restore pre-recovery BIOS state when a recovery journal is left behind."""
    journal = _bios_password_recovery_journal_path()
    if not journal.exists():
        return None
    try:
        raw = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "Could not verify the BIOS password recovery journal."
        ) from exc

    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise ValueError("The BIOS password recovery journal is invalid.")
    password_hashes = raw.get("password_hashes")
    settings = raw.get("settings")
    if (
        not isinstance(password_hashes, dict)
        or set(password_hashes) - BIOS_PASSWORD_ROLES
        or any(
            not isinstance(encoded_hash, str)
            or not _is_valid_bios_password_hash(encoded_hash)
            for encoded_hash in password_hashes.values()
        )
    ):
        raise ValueError("The BIOS password recovery journal is invalid.")
    if (
        not isinstance(settings, dict)
        or any(
            not isinstance(page, str)
            or not isinstance(values, list)
            or any(type(value) is not int or value < 0 for value in values)
            for page, values in settings.items()
        )
    ):
        raise ValueError("The BIOS password recovery journal is invalid.")

    # The journal remains in place until both restores are durably written.
    # Replaying these writes after another interruption is safe.
    save_bios_settings(settings)
    save_bios_password_hashes(password_hashes)
    journal.unlink()
    _sync_directory(journal.parent)
    return (
        "Interrupted BIOS recovery: previous password and BIOS settings restored."
    )


def _bios_password_recovery_journal_path() -> Path:
    return BIOS_PASSWORDS_FILE.with_name("bios-password-recovery.json")


def recover_bios_password(role: str) -> dict[str, str]:
    """Remove one BIOS password and reset saved setup choices to their defaults."""
    if role not in BIOS_PASSWORD_ROLES:
        raise ValueError("BIOS password recovery requires a valid password role.")

    password_hashes = load_bios_password_hashes()
    if role not in password_hashes:
        raise ValueError(f"No {role} password is installed.")

    previous_settings = load_bios_settings()
    updated_hashes = dict(password_hashes)
    del updated_hashes[role]

    # A durable journal makes the two atomic file replacements recoverable
    # even if the process or machine stops between them.
    _write_bios_recovery_journal(password_hashes, previous_settings)
    try:
        # Reset settings first so a failed password-file write cannot leave the
        # password removed without completing the advertised recovery procedure.
        save_bios_settings({})
        save_bios_password_hashes(updated_hashes)
    except (OSError, ValueError):
        try:
            save_bios_settings(previous_settings)
            save_bios_password_hashes(password_hashes)
            journal = _bios_password_recovery_journal_path()
            journal.unlink(missing_ok=True)
            _sync_directory(journal.parent)
        except (OSError, ValueError) as rollback_error:
            raise OSError(
                "BIOS password recovery could not be rolled back; the saved "
                "recovery journal will be retried on the next launch."
            ) from rollback_error
        raise
    journal = _bios_password_recovery_journal_path()
    journal.unlink(missing_ok=True)
    _sync_directory(journal.parent)
    return updated_hashes


def ensure_storage_folders() -> None:
    """Create missing local folders without touching existing archive contents."""
    for folder in STORAGE_FOLDERS:
        folder.mkdir(parents=True, exist_ok=True)


def _assert_no_symlink_components(path: Path, storage_root: Path) -> None:
    """Refuse to format through redirected storage paths."""
    try:
        relative_path = path.relative_to(storage_root)
    except ValueError as exc:
        raise OSError(f"Refusing to reset data outside {storage_root}.") from exc

    current = storage_root
    if current.is_symlink():
        raise OSError(f"Refusing to reset data through a symbolic link: {current}")
    for part in relative_path.parts:
        current /= part
        if current.is_symlink():
            raise OSError(f"Refusing to reset data through a symbolic link: {current}")


def reset_user_data() -> None:
    """Remove personal account data and chats while preserving installed content."""
    storage_root = STORAGE_ROOT.absolute()
    account_file = ACCOUNT_FILE.absolute()

    user_directories = (
        USER_PROFILES.absolute(),
        USER_DOCUMENTS.absolute(),
        MESSENGER_HISTORY.absolute(),
        STICKY_NOTES.absolute(),
        MEDIA_PLAYLISTS.absolute(),
        SCREEN_SAVER_SETTINGS_DIR.absolute(),
    )
    for directory in user_directories:
        _assert_no_symlink_components(directory, storage_root)
    _assert_no_symlink_components(account_file.parent, storage_root)

    for directory in user_directories:
        if not directory.exists():
            continue
        if not directory.is_dir():
            raise OSError(f"User data path is not a directory: {directory}")
        for child in directory.iterdir():
            if child.is_symlink() or not child.is_dir():
                child.unlink()
            else:
                shutil.rmtree(child)

    # Unlinking a final-component symlink removes only the link, never its target.
    account_file.unlink(missing_ok=True)
