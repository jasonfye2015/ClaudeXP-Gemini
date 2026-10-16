"""Canonical adult identities shared by simulated community applications."""

from dataclasses import dataclass, field, replace
import json
from pathlib import Path
from datetime import date
from itertools import product
from hashlib import sha256
import re

from .clock import LOCKED_YEAR
from .close_histories import CLOSE_HISTORIES
from .identity import (
    FursonaProfile,
    UserAccount,
    age_on_january_first,
    is_adult_in_simulated_year,
)

@dataclass(frozen=True)
class ContactIdentity:
    contact_id: str
    display_name: str
    online_name: str
    species: str
    pronouns: str
    date_of_birth: str
    bio: str
    location: str
    interests: tuple[str, ...]
    preferences: str
    relationship_history: str
    circle: str
    icon_path: str = ""
    gallery: tuple[str, ...] = ()
    source_profile: str = ""
    declared_age: int | None = None
    adult_confirmed: bool = False
    real_name: str = ""
    muck_profile: dict = field(default_factory=dict, compare=False, hash=False)

    @property
    def age_in_2011(self) -> int | None:
        if not self.date_of_birth:
            return self.declared_age
        return age_on_january_first(date.fromisoformat(self.date_of_birth), LOCKED_YEAR)

    @property
    def age_label(self) -> str:
        if self.date_of_birth:
            return f"{self.date_of_birth} · age {self.age_in_2011} in 2011"
        age = str(self.declared_age) if self.declared_age is not None else "21+"
        return f"Age {age} in 2011 · exact birthday not supplied"


MSN_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "msn"
SUPPLIED_PROFILES = {
    item["id"]: item
    for item in json.loads((MSN_ASSETS / "community.json").read_text(encoding="utf-8"))
}
SUPPLIED_CONTACTS = tuple(
    ContactIdentity(
        contact_id=item["id"], display_name=item["name"], online_name=item["name"],
        species=item["species"], pronouns=item["pronouns"], date_of_birth=item["dob"],
        bio=item["bio"], location=item["location"],
        interests=("See the supplied character profile for individual interests.",),
        preferences="Use the supplied character's personality and preferences.",
        relationship_history="Only the relationships described in the supplied profile.",
        circle="close", icon_path=item["icon"], gallery=tuple(item["gallery"]),
        source_profile=item["source_profile"], declared_age=item["declared_age"],
        adult_confirmed=True, real_name=item["real_name"],
        muck_profile=(
            dict(item.get("muck", {})) if isinstance(item.get("muck"), dict) else {}
        ),
    )
    for item in SUPPLIED_PROFILES.values()
)

# The four original Messenger identities keep their IDs and profile details.
_FOUNDING_CONTACTS = (
    ContactIdentity(
        "morgan-vale",
        "Morgan Vale",
        "morgan_v",
        "red fox",
        "she/her",
        "1986-04-18",
        "A patient digital artist who likes convention planning and old adventure games.",
        "Portland, Oregon",
        ("digital art", "conventions", "adventure games"),
        "Open to meeting new friends; prefers thoughtful one-to-one conversations.",
        "Has been part of the local furry scene since college and often helps "
        "friends plan convention trips.",
        "close",
    ),
    ContactIdentity(
        "eli-north",
        "Eli North",
        "northbound",
        "gray wolf",
        "he/him",
        "1984-11-02",
        "A friendly radio hobbyist who trades music recommendations and PC repair tips.",
        "Madison, Wisconsin",
        ("amateur radio", "music", "PC repair"),
        "Looks for long-term friendships built around shared hobbies.",
        "Keeps in touch with convention friends and is the person people call "
        "when a computer acts up.",
        "close",
    ),
    ContactIdentity(
        "rowan-ash",
        "Rowan Ash",
        "rowan_draws",
        "raccoon",
        "they/them",
        "1988-07-29",
        "A comic illustrator who enjoys sketching at local meetups and sharing "
        "work-in-progress art.",
        "Minneapolis, Minnesota",
        ("comics", "illustration", "local meetups"),
        "Enjoys low-pressure friendships and art-minded conversation.",
        "Met many close friends through an independent-comics table and stays "
        "connected through art swaps.",
        "close",
    ),
    ContactIdentity(
        "jules-river",
        "Jules River",
        "julesriver",
        "otter",
        "she/they",
        "1987-02-10",
        "An enthusiastic live-music fan who keeps friends in touch about weekend plans.",
        "Austin, Texas",
        ("live music", "weekend trips", "photography"),
        "Open to friendship and dating, with honesty and shared time as priorities.",
        "Recently ended a long-distance relationship amicably and is rebuilding "
        "a wider circle of local friends.",
        "close",
    ),
)

_CLOSE_FIRST_NAMES = (
    "Alex", "Avery", "Bailey", "Blake", "Casey", "Cameron", "Carmen", "Charlie",
    "Dani", "Drew", "Emery", "Finley", "Harper", "Jamie", "Jordan", "Kai",
    "Kendall", "Logan", "Micah", "Nico", "Parker", "Quinn", "Reese", "Riley",
)
_CLOSE_LAST_NAMES = (
    "Alder", "Bennett", "Caldwell", "Delaney", "Ellis", "Foster", "Greer",
    "Hayes", "Irwin", "Jensen", "Keating", "Lennox", "Mercer", "Nolan",
    "Ortega", "Perry", "Quill", "Sawyer", "Taylor", "Underwood", "Vaughn",
    "West", "Young", "Zimmer",
)
_COMMUNITY_FIRST_NAMES = (
    "Adrian", "Amara", "Anika", "Ben", "Briar", "Caleb", "Devon", "Eden",
    "Elena", "Felix", "Gabe", "Hana", "Imani", "Isaac", "Jae", "Jonah",
    "Lena", "Luca", "Mara", "Max", "Nadia", "Noah", "Owen", "Priya",
    "Rafael", "Sasha", "Talia", "Theo", "Uma", "Vera",
)
_COMMUNITY_LAST_NAMES = (
    "Abbott", "Bishop", "Chen", "Dawson", "Evans", "Fletcher", "Garcia",
    "Hughes", "Ibrahim", "Kim", "Lopez", "Miller", "Nguyen", "Owens",
    "Patel", "Reed", "Shah", "Turner", "Wilson", "Zuniga",
)
_SPECIES = (
    "red fox", "gray wolf", "raccoon", "river otter", "coyote", "snow leopard",
    "domestic cat", "husky", "deer", "rabbit", "dragon", "border collie",
    "skunk", "horse", "raven", "bobcat", "red panda", "badger", "lynx", "hyena",
)
_PRONOUNS = ("she/her", "he/him", "they/them", "she/they", "he/they")
_LOCATIONS = (
    "Seattle, Washington", "Denver, Colorado", "Chicago, Illinois",
    "Boston, Massachusetts", "San Diego, California", "Atlanta, Georgia",
    "Philadelphia, Pennsylvania", "Columbus, Ohio", "Raleigh, North Carolina",
    "Phoenix, Arizona", "Vancouver, Washington", "Boulder, Colorado",
    "Pittsburgh, Pennsylvania", "Baltimore, Maryland", "Sacramento, California",
    "Tucson, Arizona", "Milwaukee, Wisconsin", "Richmond, Virginia",
    "Orlando, Florida", "Buffalo, New York",
)
_HOBBIES = (
    "digital painting", "tabletop games", "live music", "photography",
    "costume making", "indie games", "science fiction", "hiking",
    "animation", "cooking", "web design", "record collecting",
    "convention volunteering", "creative writing", "PC building",
    "sketching", "role-playing games", "community theater",
)
_OCCUPATIONS = (
    "a library assistant", "a graphic designer", "a veterinary receptionist",
    "a community-college student", "a bookstore clerk", "a web developer",
    "a theater technician", "a radio producer", "a lab technician",
    "a freelance illustrator", "an office administrator", "a music teacher",
    "a computer repair technician", "a graduate student", "a print-shop worker",
)
_TEMPERAMENTS = (
    "warm and easygoing", "quiet at first but quick with a joke",
    "curious and enthusiastic", "thoughtful and dependable",
    "outgoing in a group and reflective one-to-one",
    "patient, practical, and encouraging",
)
_PREFERENCES = (
    "Mostly here for friendship and shared creative projects.",
    "Open to dating, but prefers to build trust as friends first.",
    "Interested in a committed relationship with someone nearby.",
    "Enjoys meeting people at conventions and keeping in touch online.",
    "Values direct communication, clear boundaries, and a relaxed pace.",
    "Looking for people to share hobbies with; not in a hurry to date.",
)
_RELATIONSHIPS = (
    "A past relationship ended on friendly terms; they still share a few mutual friends.",
    "Has mostly dated locally and is taking time to get to know new people.",
    "Recently moved and is rebuilding a social circle through shared interests.",
    "Has been single for a while and is comfortable meeting people without pressure.",
    "A long-distance relationship taught them to value regular, honest communication.",
    "Has had a few short relationships and is now looking for something steadier.",
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _generated_contact(name: str, index: int, circle: str) -> ContactIdentity:
    first, last = name.split(" ", 1)
    hobby_a = _HOBBIES[index % len(_HOBBIES)]
    hobby_b = _HOBBIES[(index * 7 + 3) % len(_HOBBIES)]
    year = 1980 + (index * 7 % 10)
    month = index % 12 + 1
    day = index % 27 + 1
    handle = f"{first.lower()}_{last.lower()}"
    bio = (
        f"{first} works as {_OCCUPATIONS[index % len(_OCCUPATIONS)]} and is "
        f"{_TEMPERAMENTS[index % len(_TEMPERAMENTS)]}. Away from work, "
        f"{first.lower()} spends time on {hobby_a} and {hobby_b}; they are "
        "happy to trade recommendations and hear what other people are making."
    )
    return ContactIdentity(
        contact_id=_slug(name),
        display_name=name,
        online_name=handle,
        species=_SPECIES[index % len(_SPECIES)],
        pronouns=_PRONOUNS[index % len(_PRONOUNS)],
        date_of_birth=f"{year:04d}-{month:02d}-{day:02d}",
        bio=bio,
        location=_LOCATIONS[index % len(_LOCATIONS)],
        interests=(hobby_a, hobby_b, "online community"),
        preferences=_PREFERENCES[index % len(_PREFERENCES)],
        relationship_history=_RELATIONSHIPS[index % len(_RELATIONSHIPS)],
        circle=circle,
    )


_close_names = [
    f"{first} {last}"
    for first, last in product(_CLOSE_FIRST_NAMES, _CLOSE_LAST_NAMES)
    if f"{first} {last}" not in {contact.display_name for contact in _FOUNDING_CONTACTS}
][:46]
_community_names = [
    f"{first} {last}"
    for first, last in product(_COMMUNITY_FIRST_NAMES, _COMMUNITY_LAST_NAMES)
][:150]

LEGACY_CONTACTS = (
    *_FOUNDING_CONTACTS,
    *(
        _generated_contact(name, index, "close")
        for index, name in enumerate(_close_names)
    ),
    *(
        _generated_contact(name, index + 46, "community")
        for index, name in enumerate(_community_names)
    ),
)

# Keep legacy IDs and transcripts, but give background people fandom-style handles.
_HANDLE_PREFIXES = (
    "Silver", "Velvet", "Neon", "Moss", "Copper", "Rain", "Pixel", "Moon",
    "Autumn", "Echo", "Cobalt", "Amber", "Clover", "Midnight", "Sunny",
)
_HANDLE_ENDINGS = (
    "Paw", "Tail", "Whisker", "Wing", "Muzzle", "Feather", "Claw", "Howl",
    "Bean", "Pounce",
)
_background = tuple(
    replace(
        contact,
        display_name=_HANDLE_PREFIXES[index // 10] + _HANDLE_ENDINGS[index % 10],
        online_name=_HANDLE_PREFIXES[index // 10] + _HANDLE_ENDINGS[index % 10],
        real_name=contact.display_name,
        icon_path=f"icons/{('furry', 'fursuit', 'basic')[index // 50]}{index % 50 + 1:03d}.jpg",
    )
    for index, contact in enumerate(c for c in LEGACY_CONTACTS if c.circle == "community")
)
# The basic set begins at 011, so select an existing icon for the first ten.
_background = tuple(
    replace(c, icon_path="icons/basic011.jpg")
    if not (MSN_ASSETS / c.icon_path).is_file() else c for c in _background
)
CONTACTS = (*LEGACY_CONTACTS[:50], *_background, *SUPPLIED_CONTACTS)
MSN_CONTACTS = (*SUPPLIED_CONTACTS, *_background)


@dataclass(frozen=True)
class PlayerRelationship:
    """Private fictional context bound to a contact and one selected fursona."""

    contact_id: str
    profile_id: str
    player_name: str
    shared_history: str
    boundaries: str

    def as_text(self) -> str:
        return (
            f"Friendship with {self.player_name}: {self.shared_history}\n"
            f"Boundaries: {self.boundaries}"
        )


_CATCH_UP_CUSTOMS = (
    "You usually start a catch-up by sharing one small good thing from the day.",
    "You often trade a lighthearted question before discussing bigger worries.",
    "You keep a friendly habit of comparing what each of you is working on.",
    "You sometimes open a chat with a recommendation and ask if the other wants it.",
    "You tend to ask whether the other wants advice or just someone to listen.",
    "You often pick up a conversation with a relaxed check-in rather than an introduction.",
)


def relationship_for(
    contact: ContactIdentity, profile: FursonaProfile | None,
) -> PlayerRelationship | None:
    """Resolve a repeatable backstory without modifying a public profile.

    A saved profile ID fixes the memory selection across restarts. Neither account
    login names nor another fursona's demographic details are used as substitutes.
    """
    if contact.circle != "close" or profile is None:
        return None
    seed = CLOSE_HISTORIES.get(contact.contact_id)
    if seed is None:
        return None
    key = sha256(f"{contact.contact_id}\0{profile.profile_id}".encode()).digest()
    memory = seed.memories[key[0] % len(seed.memories)]
    custom = _CATCH_UP_CUSTOMS[key[1] % len(_CATCH_UP_CUSTOMS)]
    return PlayerRelationship(
        contact.contact_id,
        profile.profile_id,
        profile.fursona_name,
        f"{seed.meeting} {memory} {custom}",
        seed.boundary,
    )


def messenger_system_prompt(contact: ContactIdentity, account: UserAccount) -> str:
    """Include private relationship context only for the active player identity."""
    profile = account.active_profile
    player = (
        f"Active player fursona: {profile.fursona_name}; species: {profile.species}; "
        f"pronouns: {profile.pronouns}; date of birth: {profile.date_of_birth}. "
        if profile is not None else
        "No active player fursona is available. Do not invent their identity or history. "
    )
    relationship = relationship_for(contact, profile)
    context = (
        "You are established platonic friends, not strangers. The following is "
        "fictional shared backstory predating this 2011 simulation, not live actions. "
        f"{relationship.as_text()} "
        "Use these memories naturally when relevant, not as a mandatory recital. "
        "Do not assume romance, consent, additional shared events, or a changed boundary. "
        "This context belongs only to the named active fursona; never transfer it "
        "to another player identity. "
        if relationship else
        "Use only the shared history explicitly described in the supplied character "
        "profile; do not assume additional romance or consent. "
        if contact.source_profile else
        "No established shared history is supplied for this player. Do not claim "
        "a pre-existing close friendship or shared experiences. "
    )
    pictures = ""
    if contact.gallery:
        supplied = SUPPLIED_PROFILES.get(contact.contact_id, {})
        pictures = (
            "You may offer your supplied pictures when relevant. To share one, use "
            "[share:filename] with exactly one of these filenames: "
            + ", ".join(Path(name).name for name in contact.gallery)
            + ". Never invent image filenames or claim to see images not described here. "
            + "Supplied captions: " + supplied.get("captions", "") + " "
        )
    return (
        f"You are {contact.display_name} ({contact.online_name}), a fictional adult "
        f"{contact.species} who uses {contact.pronouns}. Profile: {contact.bio} "
        f"Your real name is {contact.real_name or 'not supplied'}; use your furry "
        "screen name in online conversation, not an invented real-name handle. "
        f"Interests: {', '.join(contact.interests)}. Preferences: {contact.preferences} "
        f"Public relationship background: {contact.relationship_history} "
        f"{player}The online account name is {account.resolved_online_name}. {context}"
        f"Supplied character profile: {contact.source_profile} {pictures}"
        "Stay in character in the simulated year 2011, but do not claim real-world "
        "actions or knowledge you do not have. Respect boundaries and privacy."
    )


def validate_close_histories() -> list[str]:
    close_ids = {
        contact.contact_id for contact in CONTACTS
        if contact.circle == "close" and not contact.source_profile
    }
    errors = []
    if set(CLOSE_HISTORIES) != close_ids:
        errors.append("Friendship histories must cover exactly the close-contact circle.")
    for contact_id, seed in CLOSE_HISTORIES.items():
        if not seed.meeting or not seed.boundary or not all(seed.memories):
            errors.append(f"{contact_id}: friendship history or boundaries are incomplete.")
    meetings = [seed.meeting for seed in CLOSE_HISTORIES.values()]
    if len(meetings) != len(set(meetings)):
        errors.append("Close contacts must have distinct first-meeting histories.")
    return errors


def validate_community_contacts(
    contacts: tuple[ContactIdentity, ...] = CONTACTS,
) -> list[str]:
    """Return roster issues, including identities under 21 during any part of 2011."""
    errors: list[str] = []
    ids = [contact.contact_id for contact in contacts]
    names = [contact.display_name for contact in contacts]
    handles = [contact.online_name for contact in contacts]
    if len(ids) != len(set(ids)):
        errors.append("Community contact IDs must be unique.")
    if len(names) != len(set(names)):
        errors.append("Community display names must be unique.")
    if len(handles) != len(set(handles)):
        errors.append("Community online names must be unique.")
    for contact in contacts:
        label = contact.display_name or contact.contact_id
        if not contact.date_of_birth and contact.adult_confirmed:
            if contact.declared_age is not None and contact.declared_age < 21:
                errors.append(f"{label}: declared age is under 21.")
        else:
            try:
                birth_date = date.fromisoformat(contact.date_of_birth)
            except ValueError:
                errors.append(f"{label}: enter a valid date of birth (YYYY-MM-DD).")
                continue
            if not is_adult_in_simulated_year(birth_date, LOCKED_YEAR):
                age = age_on_january_first(birth_date, LOCKED_YEAR)
                errors.append(f"{label}: age {age} is under 21 during 2011.")
        if not all((
            contact.contact_id,
            contact.display_name,
            contact.online_name,
            contact.species,
            contact.pronouns,
            contact.location,
            contact.bio,
            contact.interests,
            contact.preferences,
            contact.relationship_history,
        )):
            errors.append(f"{label}: community profile details are incomplete.")
    return errors


_roster_errors = validate_community_contacts() + validate_close_histories()
if _roster_errors:
    raise ValueError("Invalid community roster: " + " ".join(_roster_errors))
