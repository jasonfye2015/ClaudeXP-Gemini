from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from uuid import uuid4

from .clock import LOCKED_YEAR
from .config import ACCOUNT_FILE

ACCOUNT_SCHEMA_VERSION = 1
MINIMUM_ADULT_AGE = 21


class AccountStoreError(RuntimeError):
    """A local account file exists but cannot safely be read or written."""


@dataclass(slots=True)
class FursonaProfile:
    fursona_name: str = ""
    species: str = ""
    pronouns: str = ""
    date_of_birth: str = ""
    gender: str = ""
    location: str = ""
    bio: str = ""
    avatar_path: str = ""
    profile_id: str = field(default_factory=lambda: str(uuid4()))

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> FursonaProfile:
        return cls(
            fursona_name=str(value.get("fursona_name", "")),
            species=str(value.get("species", "")),
            pronouns=str(value.get("pronouns", "")),
            date_of_birth=str(value.get("date_of_birth", "")),
            gender=str(value.get("gender", "")),
            location=str(value.get("location", "")),
            bio=str(value.get("bio", "")),
            avatar_path=str(value.get("avatar_path", "")),
            profile_id=str(value.get("profile_id") or uuid4()),
        )


@dataclass(slots=True)
class UserAccount:
    desktop_name: str = ""
    online_name: str = ""
    use_desktop_name_online: bool = True
    fursonas: list[FursonaProfile] = field(default_factory=list)
    active_profile_id: str = ""

    @property
    def resolved_online_name(self) -> str:
        return self.desktop_name if self.use_desktop_name_online else self.online_name

    @property
    def active_profile(self) -> FursonaProfile | None:
        """The selected fursona, never a replacement desktop-account identity."""
        return self.profile_by_id(self.active_profile_id)

    def profile_by_id(self, profile_id: str) -> FursonaProfile | None:
        return next(
            (profile for profile in self.fursonas if profile.profile_id == profile_id),
            None,
        )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> UserAccount:
        raw_profiles = value.get("fursonas", [])
        if not isinstance(raw_profiles, list):
            raise AccountStoreError("The saved fursona list is not valid.")
        return cls(
            desktop_name=str(value.get("desktop_name", "")),
            online_name=str(value.get("online_name", "")),
            use_desktop_name_online=bool(value.get("use_desktop_name_online", True)),
            fursonas=[
                FursonaProfile.from_dict(item)
                for item in raw_profiles
                if isinstance(item, dict)
            ],
            active_profile_id=str(value.get("active_profile_id", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": ACCOUNT_SCHEMA_VERSION,
            "desktop_name": self.desktop_name,
            "online_name": self.online_name,
            "use_desktop_name_online": self.use_desktop_name_online,
            "active_profile_id": self.active_profile_id,
            "fursonas": [asdict(profile) for profile in self.fursonas],
        }


def age_on_january_first(birth_date: date, year: int = LOCKED_YEAR) -> int:
    """Return age at the start of the simulated year.

    Checking January 1 makes the 21+ rule hold throughout the entire simulated
    year, regardless of today's real month and day.
    """
    reference = date(year, 1, 1)
    return reference.year - birth_date.year - (
        (reference.month, reference.day) < (birth_date.month, birth_date.day)
    )


def is_adult_in_simulated_year(birth_date: date, year: int = LOCKED_YEAR) -> bool:
    """Whether someone is at least 21 for every day in the simulated year."""
    return age_on_january_first(birth_date, year) >= MINIMUM_ADULT_AGE


def validate_account(account: UserAccount) -> list[str]:
    errors: list[str] = []
    if not account.desktop_name.strip():
        errors.append("Enter a Windows desktop account name.")
    if not account.use_desktop_name_online and not account.online_name.strip():
        errors.append("Enter an online name or enable the shared-name option.")
    if not account.fursonas:
        errors.append("Add at least one fursona profile.")

    for index, profile in enumerate(account.fursonas, start=1):
        label = profile.fursona_name.strip() or f"Fursona profile {index}"
        if not profile.fursona_name.strip():
            errors.append(f"{label}: enter a fursona name.")
        if not profile.species.strip():
            errors.append(f"{label}: enter a species.")
        if not profile.pronouns.strip():
            errors.append(f"{label}: enter pronouns.")
        try:
            birth_date = date.fromisoformat(profile.date_of_birth.strip())
        except ValueError:
            errors.append(f"{label}: enter a valid date of birth (YYYY-MM-DD).")
            continue
        age = age_on_january_first(birth_date)
        if not is_adult_in_simulated_year(birth_date):
            errors.append(
                f"{label}: profiles must be at least 21 for all of 2011 "
                f"(age on January 1, 2011: {age})."
            )

    if account.active_profile_id and account.profile_by_id(account.active_profile_id) is None:
        errors.append("The selected fursona is not in this account.")
    return errors


def save_account(account: UserAccount, path: Path = ACCOUNT_FILE) -> None:
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(account.to_dict(), indent=2, ensure_ascii=False) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(encoded)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    except OSError as exc:
        try:
            temporary_path.unlink(missing_ok=True)
        except (UnboundLocalError, OSError):
            pass
        raise AccountStoreError(f"Could not save the local account: {exc}") from exc


def load_account(path: Path = ACCOUNT_FILE) -> UserAccount | None:
    path = Path(path)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise AccountStoreError("The saved account file has an invalid format.")
        version = value.get("schema_version")
        if version != ACCOUNT_SCHEMA_VERSION:
            raise AccountStoreError(
                f"Unsupported account data version: {version!r}. "
                "The file was left unchanged."
            )
        return UserAccount.from_dict(value)
    except AccountStoreError:
        raise
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AccountStoreError(
            f"Could not read the local account at {path}: {exc}"
        ) from exc
