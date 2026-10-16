"""Local PawPrints MUCK data and deterministic, adult-only resident scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import random
import re

from .clock import LOCKED_YEAR
from .contacts import ContactIdentity, MSN_CONTACTS
from .identity import UserAccount, age_on_january_first


MUSH_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "mush"


class MushWorldError(ValueError):
    """Invalid or unavailable local PawPrints world data."""


@dataclass
class MushResident:
    resident_id: str
    name: str
    species: str
    description: str
    persona: str
    haunts: tuple[str, ...]
    doing: str = ""
    hours: tuple[str, str] | None = None
    start_chance: float = 0.1
    idle_only: bool = False
    moves: bool = True
    profile_text: str = ""
    source: str = "PawPrints resident"
    contacts: list[ContactIdentity] = field(default_factory=list)
    muck_profile: dict = field(default_factory=dict)
    online: bool = False
    room_id: str = ""


def _first_match(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else default


def _profile_name(path: Path) -> str:
    return re.sub(r"^\d+_", "", path.stem).replace("_", " ").strip()


def _stable_fraction(key: str) -> float:
    number = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
    return number / 2**64


class MushWorld:
    """One local server session backed by the supplied map and character files."""

    def __init__(
        self,
        account: UserAccount,
        presence=None,
        *,
        data_root: Path = MUSH_ASSETS,
        now_provider=None,
        rng=None,
    ):
        self.account = account
        self.presence = presence
        self.data_root = Path(data_root)
        self.now_provider = now_provider or datetime.now
        self.rng = rng or random.Random()
        self.rooms, self.start_room = self._load_map()
        self.home_room = next(
            (
                room_id for room_id, room in self.rooms.items()
                if room.get("public", True) is False
                and "{player}" in str(room.get("name", ""))
            ),
            self.start_room,
        )
        self.residents: list[MushResident] = []
        self.excluded_minor_names: set[str] = set()
        self.excluded_unverified_names: set[str] = set()
        self._resident_by_id: dict[str, MushResident] = {}
        self._resident_by_name: dict[str, MushResident] = {}
        self._resident_by_contact_id: dict[str, MushResident] = {}
        self._load_residents()
        self.connected = False
        self.player_name = ""
        self.player_description = ""
        self.current_room = self.start_room
        self.online_residents: dict[str, MushResident] = {}

    def _load_map(self):
        path = self.data_root / "map.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise MushWorldError(f"Could not load the PawPrints room map: {exc}") from exc
        rooms = raw.get("rooms") if isinstance(raw, dict) else None
        start = raw.get("start") if isinstance(raw, dict) else None
        if (
            not isinstance(rooms, dict) or not rooms
            or not isinstance(start, str) or start not in rooms
        ):
            raise MushWorldError("The PawPrints map has no valid starting room.")
        valid = {}
        for room_id, room in rooms.items():
            if not isinstance(room_id, str) or not isinstance(room, dict):
                continue
            exits = room.get("exits", {})
            if not isinstance(exits, dict) or any(
                destination not in rooms for destination in exits.values()
            ):
                raise MushWorldError(f"The PawPrints map has invalid exits in {room_id}.")
            valid[room_id] = room
        if start not in valid:
            raise MushWorldError("The PawPrints starting room is invalid.")
        return valid, start

    def _load_residents(self):
        profiles_dir = self.data_root / "Background Furry Profiles"
        try:
            profile_files = sorted(profiles_dir.glob("*.txt"))
            profiles = {
                _profile_name(path).casefold(): path.read_text(encoding="utf-8")
                for path in profile_files
            }
        except (OSError, UnicodeError) as exc:
            raise MushWorldError(f"Could not load PawPrints character profiles: {exc}") from exc
        if not profiles:
            raise MushWorldError("The PawPrints resident profile archive is empty.")

        regulars_path = self.data_root / "regulars.json"
        try:
            raw = json.loads(regulars_path.read_text(encoding="utf-8"))
            regulars = raw.get("regulars") if isinstance(raw, dict) else None
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise MushWorldError(f"Could not load PawPrints regulars: {exc}") from exc
        if not isinstance(regulars, list):
            raise MushWorldError("The PawPrints regulars file has no character list.")

        regular_names = set()
        for item in regulars:
            if not isinstance(item, dict) or not str(item.get("name", "")).strip():
                continue
            name = str(item["name"]).strip()
            key = name.casefold()
            regular_names.add(key)
            profile_text = profiles.get(key, "")
            age = self._age_assessment(str(item.get("persona", "")), profile_text)
            if age is not None and age < 21:
                self.excluded_minor_names.add(name)
                continue
            if age is None:
                self.excluded_unverified_names.add(name)
                continue
            self._add_resident(MushResident(
                resident_id=f"regular:{key}",
                name=name,
                species=str(item.get("species", "furry")),
                description=str(item.get("desc", "")),
                persona=str(item.get("persona", "")),
                haunts=self._valid_haunts(item.get("haunts")),
                doing=str(item.get("doing", "")),
                hours=self._valid_hours(item.get("hours")),
                start_chance=self._chance(item.get("start_chance", 0.1)),
                idle_only=bool(item.get("idle_only", False)),
                moves=bool(item.get("moves", True)),
                profile_text=profile_text,
                source="PawPrints regular",
            ))

        for name_key, text in profiles.items():
            if name_key in regular_names:
                continue
            name = next(
                (_profile_name(path) for path in profile_files
                 if _profile_name(path).casefold() == name_key),
                name_key.title(),
            )
            age = self._age_assessment("", text)
            if age is not None and age < 21:
                self.excluded_minor_names.add(name)
                continue
            if age is None:
                self.excluded_unverified_names.add(name)
                continue
            species = _first_match(r"^\*\*Species:\*\*\s*(.+)$", text, "furry")
            description = _first_match(r"^\*\*In short:\*\*\s*(.+)$", text)
            if not description:
                description = _first_match(
                    r"^\*\*Distinguishing Features:\*\*\s*(.+)$", text,
                    "A PawPrints community member.",
                )
            self._add_resident(MushResident(
                resident_id=f"profile:{name_key}",
                name=name,
                species=species,
                description=description,
                persona="Use the following supplied adult character profile as roleplay context.",
                haunts=(self._room_for_key(name_key),),
                start_chance=0.12,
                profile_text=text,
                source="PawPrints community profile",
            ))

        self._load_msn_residents()

    @staticmethod
    def _age_assessment(persona: str, profile_text: str) -> int | None:
        ages = [
            int(age) for age in re.findall(
                r"\b(\d{1,2})[- ]year[- ]old\b", persona, flags=re.IGNORECASE
            )
        ]
        dob = _first_match(
            r"^\*\*DOB:\*\*\s*(\d{4}-\d{2}-\d{2})", profile_text
        )
        if dob:
            try:
                ages.append(age_on_january_first(date.fromisoformat(dob), LOCKED_YEAR))
            except ValueError:
                pass
        return min(ages) if ages else None

    @staticmethod
    def _chance(value) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.1

    def _valid_haunts(self, value) -> tuple[str, ...]:
        if not isinstance(value, list):
            return ()
        return tuple(dict.fromkeys(
            place for place in value
            if (
                isinstance(place, str) and place in self.rooms
                and self.rooms[place].get("public", True)
            )
        ))

    @staticmethod
    def _valid_hours(value) -> tuple[str, str] | None:
        if (
            isinstance(value, list) and len(value) == 2
            and all(isinstance(part, str) for part in value)
        ):
            return value[0], value[1]
        return None

    def _room_for_key(self, key: str) -> str:
        public_rooms = [
            room_id for room_id, room in self.rooms.items()
            if room.get("public", True)
        ]
        if not public_rooms:
            return self.start_room
        public_rooms.sort()
        weighted = [
            (
                room_id,
                max(0.01, float(self.rooms[room_id].get("popularity", 1))),
            )
            for room_id in public_rooms
        ]
        total = sum(weight for _room_id, weight in weighted)
        target = _stable_fraction("room:" + key) * total
        for room_id, weight in weighted:
            target -= weight
            if target < 0:
                return room_id
        return weighted[-1][0]

    def _add_resident(self, resident: MushResident):
        key = resident.name.casefold()
        if key in self._resident_by_name:
            return
        resident.haunts = resident.haunts or (self._room_for_key(resident.resident_id),)
        resident.room_id = resident.haunts[0]
        self.residents.append(resident)
        self._resident_by_id[resident.resident_id] = resident
        self._resident_by_name[key] = resident

    def _load_msn_residents(self):
        for contact in MSN_CONTACTS:
            try:
                age = contact.age_in_2011
            except ValueError:
                age = None
            if (age is not None and age < 21) or (age is None and not contact.adult_confirmed):
                if age is not None:
                    self.excluded_minor_names.add(contact.online_name)
                else:
                    self.excluded_unverified_names.add(contact.online_name)
                continue
            name = contact.online_name.strip()
            if not name:
                continue
            key = name.casefold()
            custom = contact.muck_profile if isinstance(contact.muck_profile, dict) else {}
            if key in self._resident_by_name:
                existing = self._resident_by_name[key]
                existing.contacts.append(contact)
                self._resident_by_contact_id[contact.contact_id] = existing
                continue
            species = str(custom.get("species") or contact.species)
            description = str(custom.get("desc") or contact.bio)
            interests = ", ".join(contact.interests)
            persona = (
                f"{name} is an adult {species} ({contact.pronouns}) and a member "
                "of the PawPrints MUCK community. "
                f"Public profile: {description} Interests: {interests}"
            )
            haunts = self._valid_haunts(custom.get("haunts"))
            room_id = self._room_for_key("msn:" + contact.contact_id)
            resident = MushResident(
                resident_id=f"msn:{contact.contact_id}",
                name=name,
                species=species,
                description=description,
                persona=persona,
                haunts=haunts or (room_id,),
                doing=str(custom.get("doing", "")),
                start_chance=0.28 if contact.circle == "close" else 0.1,
                profile_text=contact.source_profile,
                source="MSN contact",
                contacts=[contact],
                muck_profile=custom,
            )
            self._add_resident(resident)
            self._resident_by_contact_id[contact.contact_id] = resident

    @staticmethod
    def _parse_minutes(value: str) -> int | None:
        try:
            hour, minute = (int(part) for part in value.split(":", maxsplit=1))
            if hour < 0 or minute < 0 or minute > 59:
                return None
            return hour * 60 + minute
        except (ValueError, AttributeError):
            return None

    @classmethod
    def _in_hours(cls, hours: tuple[str, str] | None, now: datetime) -> bool:
        if not hours:
            return True
        start, end = (cls._parse_minutes(part) for part in hours)
        if start is None or end is None or end - start >= 24 * 60:
            return True
        now_minute = now.hour * 60 + now.minute
        return any(start <= now_minute + offset * 1440 < end for offset in (-1, 0, 1))

    def _resident_attends(self, resident: MushResident, now: datetime) -> bool:
        if not self._in_hours(resident.hours, now):
            return False
        chance = resident.start_chance
        if resident.contacts and self.presence:
            for contact in resident.contacts:
                state = self.presence.state(contact.contact_id)
                if state in ("Online", "Away", "Do not disturb"):
                    chance = max(chance, 0.35)
        day = now.strftime("%m-%d")
        return _stable_fraction(f"{LOCKED_YEAR}:{day}:{resident.resident_id}") < chance

    def connect(self, character_name: str = "") -> list[MushResident]:
        profile = self.account.active_profile
        if profile is None:
            raise MushWorldError("Select a Windows fursona profile before connecting.")
        requested = character_name.strip()
        if requested and requested.casefold() != profile.fursona_name.casefold():
            raise MushWorldError(
                f"Only the selected Windows fursona, {profile.fursona_name}, can connect."
            )
        if self.connected:
            raise MushWorldError(f"{self.player_name} is already connected.")
        now = self.now_provider()
        self.player_name = profile.fursona_name
        self.player_description = profile.bio.strip()
        self.current_room = self.start_room
        self.online_residents = {}
        for resident in self.residents:
            resident.online = (
                resident.name.casefold() != self.player_name.casefold()
                and self._resident_attends(resident, now)
            )
            if resident.online:
                resident.room_id = resident.haunts[
                    int(_stable_fraction(f"{resident.resident_id}:{now:%m-%d}") * len(resident.haunts))
                ]
                self.online_residents[resident.resident_id] = resident
        self.connected = True
        return list(self.online_residents.values())

    def advance(self):
        """Advance one active-session tick; never replay time spent closed."""
        if not self.connected:
            return []
        now = self.now_provider()
        events = []
        for resident in self.residents:
            if resident.name.casefold() == self.player_name.casefold():
                continue
            old_room = resident.room_id
            awake = self._in_hours(resident.hours, now)
            if resident.online:
                if not awake or self.rng.random() < 0.008:
                    resident.online = False
                    self.online_residents.pop(resident.resident_id, None)
                    events.append((resident.name, "disconnect", old_room, ""))
                elif resident.moves and self.rng.random() < 0.1:
                    destinations = list(dict.fromkeys(
                        destination for destination in self.exits(old_room).values()
                        if self.rooms[destination].get("public", True)
                    ))
                    if destinations:
                        resident.room_id = self.rng.choice(destinations)
                        events.append((resident.name, "move", old_room, resident.room_id))
            elif awake and self.rng.random() < resident.start_chance * 0.01:
                resident.online = True
                resident.room_id = self.rng.choice(resident.haunts)
                self.online_residents[resident.resident_id] = resident
                events.append((resident.name, "connect", "", resident.room_id))
        return events

    def disconnect(self):
        self.connected = False
        self.player_name = ""
        self.player_description = ""
        self.online_residents.clear()
        for resident in self.residents:
            resident.online = False

    def room(self, room_id: str | None = None) -> dict:
        room_id = room_id or self.current_room
        return self.rooms[room_id]

    def room_name(self, room_id: str | None = None) -> str:
        name = str(self.room(room_id).get("name", room_id or self.current_room))
        return name.replace("{player}", self.player_name)

    def exits(self, room_id: str | None = None) -> dict[str, str]:
        result = {}
        for names, destination in self.room(room_id).get("exits", {}).items():
            aliases = [alias.strip() for alias in names.split(";") if alias.strip()]
            if aliases:
                result[aliases[0]] = destination
        return result

    def move(self, direction: str) -> str | None:
        requested = direction.casefold().strip()
        for aliases, destination in self.room().get("exits", {}).items():
            if requested in (alias.strip().casefold() for alias in aliases.split(";")):
                self.current_room = destination
                return destination
        return None

    def people_here(self) -> list[MushResident]:
        return sorted(
            (resident for resident in self.online_residents.values()
             if resident.room_id == self.current_room),
            key=lambda resident: resident.name.casefold(),
        )

    def find_resident(self, name: str) -> MushResident | None:
        needle = name.casefold().strip()
        if not needle:
            return None
        exact = self._resident_by_name.get(needle)
        if exact:
            return exact
        matches = [
            resident for resident in self.residents
            if resident.name.casefold().startswith(needle)
        ]
        return matches[0] if len(matches) == 1 else None

    def online_resident(self, name: str) -> MushResident | None:
        resident = self.find_resident(name)
        return resident if resident and resident.online else None
