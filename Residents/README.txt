Residents - the cast of the Claude Timeline
============================================

One folder per resident, shared by every computer (EPOCH-2001, SYSTEM-2011, WORKSTATION-2025). Each era reads a
resident through ClaudeCore's loader (ClaudeCore/residents), which only ever opens the era files up to its own year:
nothing from a later era can reach an earlier one.

  Residents/<Name>/
    resident.json        who they are in any era
    eras/2001.json       their life and accounts in October 2001 (2011.json and 2025.json come later)
    media/2001/          their buddy icon, photos (with captions.txt) and files they can share in that era
    sources/             the original files they were made from (for reference; never read by the eras)

The folder name is their name everywhere: AIM screen name, IRC nick and MUCK name all started as the same.

resident.json
-------------
  "name"          the folder name
  "fur_name"      the name shown on their card
  "tier"          "main" (IM contacts with icons, photos and webpages), "support" (IRC/MUCK regulars who chat) or
                  "background" (the crowd: bots, idlers, lurkers)
  "born"          "YYYY-MM-DD". Their age in any era follows from it.
  "born_source"   "profile" (written in their character profile), "persona" (worked out from an age in their
                  persona) or "assigned" (picked at random, making them an adult in 2001)
  "identity"      { "real_name", "gender", "pronouns", "height", "build" }
  "fursona"       { "species", "colors", "eyes", "markings", "accessories", "description" }
  "summary"       one line about them
  "personality", "mannerisms", "interests", "roleplay_hooks", "roleplay_notes"   text
  "favorites"     { "movies": [], "music": [], "food": [], ... }
  "how_met"       how they met the user (from their persona), if known
  "relationship", "friends", "relationships", "notes"   as in The Fur Directory
  "history"       dated facts about their life and their life with the user:
                    [ {"from": 1999, "text": "Met the user on a furry forum"},
                      {"from": 2017, "to": 2023, "text": "Was in a relationship with the user"} ]
                  An era sees only what has started by its year: an ongoing fact has no end yet, and a finished
                  one is told in the past tense.
  "flags"         notes for the user to review (e.g. "minor-in-persona": their 2001 text gave an under-18 age)

eras/<year>.json
----------------
  "year"          the era
  "persona"       the text the model plays them from in that era
  "occupation", "work_schedule", "sleep_schedule", "residence", "location", "timezone"
  "services"      their accounts in that era, as each program reads them:
                    "aim"        the ClaudeAIM contact (screen name, icon, profile, away message, presence, ...)
                    "irc"        their FurNet IRC regular entry      "muck"   their PawPrints MUCK regular entry
                    "directory"  The Fur Directory's screen_names, webpages, files and icon
  A resident with no file for an era wasn't around then. Later eras see earlier eras only as "used to be on ...".

Made by ClaudeCore/tools/migrate_xp_residents.py from ClaudeXP's files on 2026-10-17. Edit these by hand freely;
the script won't overwrite a resident unless told to (--force).
