"""Pet names that fit. Kithylin's model learned his habit of calling people "kitty", "foxy", "wolfy" or "pup" from
his Telegram chats - but not who gets which: in the logs "kitty" went to a few cats, and the model hands it to
anyone. So his prompt says what each buddy is ('hun' or their name for anyone; a species pet name only if it fits),
and a reply that still calls a German Shepherd "kitty" has it swapped for one that fits ("pup"), or "hun".

The species comes from the buddy's persona ("whose fursona is Xavier, a fully anthro German Shepherd ...")."""
import random
import re

FAMILIES = {
    "cat": ("cat", "kitty", "kitten", "lion", "tiger", "lynx", "leopard", "cheetah", "panther", "ocelot", "serval",
            "caracal", "calico", "puma", "cougar", "jaguar", "feline", "tabby"),
    "fox": ("fox", "renamon", "kitsune", "fennec", "vulpine"),
    "wolf": ("wolf", "lupine"),
    "dog": ("dog", "husky", "shepherd", "malamute", "collie", "retriever", "corgi", "dingo", "pup", "canine",
            "doberman", "rottweiler", "coyote", "jackal", "beagle", "terrier", "samoyed", "akita", "shiba",
            "labrador", "dalmatian"),
}
PET_NAMES = {"cat": ["kitty", "kitty cat"], "fox": ["foxy"], "wolf": ["wolfy"], "dog": ["pup", "pupper", "doggo"]}
WORDS = {"cat": r"kitty(?:\s?cat)?|kitteh|kitten", "fox": r"foxy|foxxo", "wolf": r"wolfy|wolfie",
         "dog": r"pupper|puppy|pup|doggo"}
# a pet name used to address someone: not after "a/the/my new/..." and followed by the end of a clause
ADDRESS = r"(?<![Aa] )(?<![Tt]he )(?<![Nn]ew )(?<![Yy]our )(?<![Hh]is )(?<![Hh]er )\b({words})\b(?=\s*(?:[!?.,~:;)*]|<3|❤|:3|$))"
SPECIES = re.compile(r"fursona[^.]{0,60}?\b(?:an?)\s+(?:fully\s+)?(?:anthro(?:pomorphic)?\s+)?"
                     r"([A-Za-z][A-Za-z -]{1,30}?)(?=\s+(?:with|who|named|that)\b|[,.;(\n])", re.I)
_species = {}


def species_of(contact):
    """'german shepherd', 'calico cat', 'renamon' - or '' if the persona doesn't say."""
    if contact.id not in _species:
        m = SPECIES.search(contact.persona or "")
        species = m.group(1).strip().lower() if m else ""
        named = next((fam for fam, words in FAMILIES.items() if any(w in contact.id.lower() for w in words)), "")
        if not family(species) and named:                       # LazyFox: the name says it
            species = named
        _species[contact.id] = species
    return _species[contact.id]


def family(species):
    s = (species or "").lower()
    for fam, words in FAMILIES.items():
        if any(re.search(rf"\b{w}", s) for w in words):
            return fam
    return ""


def note(name, species):
    """A line for his prompt about what to call them."""
    fam = family(species)
    fits = f" ('{PET_NAMES[fam][0]}' fits them)" if fam else ""
    what = f"{name}'s fursona is a {species}. " if species else ""
    return (f"\n{what}Call {name} by name or 'hun'; a species pet name only if it fits what they are{fits} - "
            "'kitty' is just for cats, 'foxy' for foxes, 'wolfy' for wolves, 'pup' for dogs.")


VOCATIVE = re.compile(r"(?:\s*,)?\s+\b(?:" + "|".join(WORDS.values()) + r"|hun|hunny|babe|cutie|sweetie)\b"
                      r"(?=\s*(?:[!?.,~:;)*]|<3|❤|:3|$))", re.I)


def unaddress(text):
    """A post for everyone (his diary): no pet names aimed at one person ("Mornings kitty!" -> "Mornings!")."""
    return VOCATIVE.sub("", text or "")


def fit(text, species, rng=random):
    """Swap a species pet name that doesn't fit this buddy for one that does (or 'hun')."""
    fam = family(species)
    for other, words in WORDS.items():
        if other == fam:
            continue

        def swap(m):
            new = rng.choice(PET_NAMES[fam]) if fam else "hun"
            return new.capitalize() if m.group(1)[:1].isupper() else new
        text = re.sub(ADDRESS.format(words=words), swap, text, flags=re.I)
    return text
