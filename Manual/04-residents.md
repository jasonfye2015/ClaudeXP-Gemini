# 4. The residents and the community

The Timeline exists first to show the archive, and second to put a living community around it: the same furs in
every era, older each time, played by a language model that runs on your own graphics card.

## Who lives here

About 260 residents, in `Residents\<Name>\`, in three tiers:

- **Main furs** (34 of them): your IM contacts, with icons, web pages and pictures, and hand-written lives in every
  era.
- **Support furs**: the IRC and MUCK regulars who chat.
- **Background furs**: the crowd.

Each resident has a timeless file, `resident.json` (fur name, tier, fursona, personality, mannerisms, how they met
you, birth date, friends), and one file per era they were around for: `eras\2001.json`, `eras\2011.json`,
`eras\2025.json`. An era file holds their accounts on that era's services (screen names, icons, profiles, away
messages, e-mail, web pages), their job, where they live, their situation and schedule, and a paragraph about their
life then. **No era file means they weren't around then**: they joined the fandom later, or left it.

**Birth dates** were drawn once so that everyone was an adult (18 to 36) in 2001. A 26-year-old on the XP machine is
36 on the Windows 7 machine and 50 on the Windows 11 machine, and their lives follow: retirements, marriages,
children, businesses, the pandemic years.

**Dated history** is what makes the eras hang together. A resident's history is a list of dated entries
("Met you on a furry forum" from 1999; "In a relationship with you" from 2017 to 2023). Each computer shows only what
has started by its own year, as it stood then: something ongoing has no end date, something finished is in the past
tense, and nothing from a later year can leak backwards. Past eras appear as "used to": "used to be on AIM as ...".

**Memory.** Each era's memories are its own: no chat logs carry between computers. Within a computer, every log,
diary note and e-mail keeps its real timestamp underneath; the model sees relative dates ("3 days ago"), and a rolling
window of about eleven months is kept so that a month never repeats as the real years go by.

## Where to meet them

| Era | Messengers and chat | Mail | The social web |
|---|---|---|---|
| 2001 | ClaudeAIM, MSN Messenger, Yahoo! Messenger, ICQ, Trillian, Windows Messenger, FurNet IRC, PawPrints MUCK, Claudecadia | MSN Hotmail, Outlook Express | LiveJournal, the residents' home pages on the Furry Web |
| 2011 | Windows Live Messenger, AIM, Yahoo! Messenger 11, ICQ 7, Skype 5, Trillian 5, Kik, IRC, the MUCK, Claudecadia | Windows Live Hotmail, Windows Live Mail | LiveJournal, Facebook (autumn 2011) |
| 2025 | Telegram, Discord, Trillian, Kik, IRC, the MUCK, Claudecadia | Outlook.com, Outlook | LiveJournal, Facebook (2025), Bluesky |

A service exists in an era only if it really existed in October of that year (XP keeps a few anachronisms it already
had: Skype, Kik, Telegram, Discord). The residents lead lives of their own: they keep diaries, write to you, remember
what you talked about, and talk among themselves on IRC and the MUCK whether you're there or not.

**The Fur Directory** (Furry Programs) is who's who: every resident's card, with their fursona, their accounts in
this era and their picture. **Furry Proximity Locator** puts a pin on a world map where each one lives. **Furry Log**
is a diary of everything the language model does, if you want to watch the machinery.

**The Furry Web** is two things. The website rips in the archive (FurAffinity, HousePets, Hardblush, Jay Naylor,
SexyFur, YiffStar, clubstripes) are served read-only at their own addresses in every era. The rest of the web is
written by the model as you browse: Netscape's Netcenter and MSN in 2001, the residents' home pages, journals and
shouts, and the generated social sites, which stay in that era's `data` so 2001 never sees a 2025 post. Pages are
cached after the first visit; Disk Cleanup clears the cache.

## How your codes change things

Your **Furry Code** and **YIFF Code** (set in the launcher, or in **FurCoder** inside a computer) tell the residents
who you are: species, interests, what you're open to. They decide attraction, whether someone roleplays with you, and
what you have in common. Each resident has codes of their own too (their YIFF Code only if they choose to show it);
FurCoder reads them in words.

Changes apply from the next time a computer starts.

## Contact Persona Styles

How the residents are made and prompted has versions. **V1.0** and **V1.1** are frozen in `Persona Styles\`;
"Development" is whatever the code does right now. The style is chosen only when EPOCH-2001 is set up (Load and
Format) and stays until the next format; choosing a different one also starts the residents' memories afresh.
**Fur Persona Profiles** (on the XP machine) shows the styles side by side: residents, prompts, tests.

## Kithylin

Kithylin, the Angelic Husky, is you: your fursona, and the name of the models trained on your own chat logs. He has
his own program, [Kithylin AI](08-kithylin.md), rather than a seat in the messengers.
