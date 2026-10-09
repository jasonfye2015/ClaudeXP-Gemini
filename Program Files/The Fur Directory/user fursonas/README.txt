User fursonas
=============

The ready-made identities offered in Setup's "Choose your fursona" page (alongside "Be unique"). Each one is a
folder here; add as many as you like (5-10 is plenty). They also show in The Fur Directory's "User Fursonas"
section, and the one chosen in Setup is marked "This is you". Only reinstalling Windows changes the choice.

  <Name>\profile.json     the details (below)
  <Name>\account.png      Windows account picture (48x48 or bigger, square)    - optional
  <Name>\buddy_icon.jpg   AIM buddy icon                                         - optional (falls back to account)
  <Name>\photos\          personal photos; files here go to My Pictures\Photos, and each sub-folder becomes its
                          own album (e.g. photos\Fursuit\, photos\Con Photos\). A captions.txt in any of them
                          ("file.jpg: caption" per line) captions the pictures on the Fur Directory card.

profile.json uses the same fields as a resident record (see ..\README.txt), plus:
  "handle"        the online name (AIM / IRC / MUCK / e-mail); defaults to fur_name
  "summary"       one or two lines for the Setup page
  "fursuit"       text, e.g. "He owns a husky fursuit"
  "conventions"   text, e.g. "He has been to several furry conventions"
  "online"        { "away_message": AIM away message,
                    "irc_realname": IRC 'Full Name',
                    "muck_desc":    the MUCK character's description (what 'look' shows) }
  "knows"         [ { "name": "<resident>", "closeness": "close" | "friend" | "acquaintance",
                      "how_met": "Met at Anthrocon 2000." }, ... ]

What residents know about you comes from "knows": close friends know your life (real name, job, hours,
personality, favourites, relationship status); friends know your fursona, age, where you live, fursuit and cons;
acquaintances and anyone not listed only know what they can see (your fursona).
