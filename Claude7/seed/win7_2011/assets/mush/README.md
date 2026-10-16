# PawPrints MUCK assets

These are the supplied PawPrints room map, regular-character data, community
profiles, Mush artwork, and a screenshot kept as a visual reference. The
simulator reads `map.json`, `regulars.json`, and the text files under
`Background Furry Profiles/` directly from this tracked assets folder.

Names shared by `regulars.json` and the profile archive are combined into one
resident. Adult MSN contacts are also added to the world; an optional `muck`
object in an MSN contact's source data can customize that character's species,
description, haunts, and current activity.

PawPrints is simulated locally and does not connect to an external MUCK.
Profiles explicitly under 21 are preserved in the source files but excluded
from the active resident list. Profiles without a confirmed age of at least 21
are excluded as well.
