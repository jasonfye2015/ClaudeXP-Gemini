The Fur Directory - resident records
====================================

One file per resident in residents\<Name>.json. These are written and kept by hand (never generated, never
editable inside ClaudeXP). Every field is optional: leave anything unknown as "" or [] and the card shows a dash.

Facts the system already keeps are read live and shown in grey "(from the system)" when a record leaves them
blank: AIM screen name, icon and profile; IRC nick, channels and hours; MUCK name, species and description; the
persona text the AI plays them from; sleep hours from the AIM schedule; pictures in their AIM contact folder;
their life journal. Anything written here wins over the system's value.

A record for someone with no AIM, IRC or MUCK account yet still gets a card ("No accounts yet"); give them a
screen name here once they join a system. The 60 background furs from ClaudeXP Profiles\Background Furry Profiles
were transcribed this way (tier "background", with "summary", "mannerisms", "interests", "roleplay_hooks" and
"roleplay_notes" sections).

Fields
------
  "fur_name"      the name shown on the card (defaults to their screen name)
  "tier"          which gallery section they're in: "main", "support" or "background". Blank = automatic:
                  an AIM account makes them a Main Fur; an IRC/MUCK regular who chats (or anyone on more than
                  one system) is a Support Fur; MUCK wizards, bots, idlers and IRC lurkers are Background Furs.
  "icon"          a picture for residents without an AIM icon, relative to this folder (e.g. "icons/Zeph.png")
  "screen_names"  { "aim": "", "irc": "", "muck": "", "email": "", ...any others, e.g. "icq": "" }
  "personal"      { "real_name", "location", "sex", "age", "dob", "job", "work_hours", "sleep_hours",
                    "online_hours", ...any others }
  "favorites"     { "movies": [], "music": [], "food": [], ...any others }
  "fursona"       { "species", "colors", "markings", "clothing", "description", ...any others }
  "personality"   text, in their own words
  "relationship"  { "status": "Single / Dating / Mated / ...", "partner": "<resident name>" }
  "friends"       [ "<resident name>", ... ]           (names become links to their cards)
  "relationships" [ { "type": "Ex", "name": "<resident>", "note": "" }, ... ]
  "files"         [ { "path": "relative to the ClaudeXP folder, or absolute", "caption": "" }, ... ]
  "webpages"      [ { "title": "", "url": "" }, ... ]  (open in Netscape Navigator)
  "notes"         text

Any other top-level key you add later shows up on the card as its own section (a {} becomes a table,
text or a list becomes a paragraph), so new content needs no code changes.
