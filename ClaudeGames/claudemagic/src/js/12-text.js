"use strict";
// Text as data: the words the player reads, keyed, so a translation is one file that sets CM.TEXT over this one.
// Only the newest screens are written through CM.t so far (the statistics, the link, installing, the gamepad); the
// older strings still live where they are used and move here as they are touched. No translation is shipped.
//
//   CM.t("stats.runs", { n: 12 })   ->  "12 expeditions"
CM.TEXT = {
  "farm.title": "The farm, in the fields below the town", "farm.fallow": "A fallow field, fenced long ago. The farm is raised at the town's board, with renown: a field first, then an orchard, a mill, hens, a cow.", "farm.back": "Back to the path",
  "hut.title": "The hermit's hut", "hut.lead": "\"Hides I'll take, by daylight. Trouble I won't.\" The hermit tans and stitches for 20 gold a piece.", "hut.walk": "Walk on",
  "stats.title": "Statistics",
  "stats.none": "No expedition has ended yet. The numbers begin with the first.",
  "stats.runs": "{n} expeditions, {crowns} crowned, {bottoms} to the bottom of the world, {fell} that fell",
  "stats.first": "The first set out {first}; the last ended {last}.",
  "stats.deepest": "Deepest: floor {n}.",
  "stats.totals": "{steps} steps, {fights} fights, {kills} slain, {fled} fled, {chests} chests opened.",
  "stats.bands": "Where parties fell",
  "stats.callings": "The callings, and how they fared",
  "stats.calling.row": "{n} took it, {crowns} crowned",
  "stats.spent": "Gold, and where it went",
  "stats.spent.total": "{n} gold spent in all",
  "stats.difficulty": "By difficulty",
  "stats.difficulty.row": "{n} runs, {crowns} crowned, best Ascension {a}",
  "stats.old": "({n} of these were read back from the Hall of Fame: no steps, fights or gold are known for them.)",
  "link.title": "A link came in",
  "link.save": "This link carries a save: the runs in its slots, its Hall of Fame and its settings. Import it, and they replace what this browser holds (Export first to keep what is here).",
  "link.film": "This link carries the film of a run. Watch it?",
  "link.bad": "The link's save couldn't be read.",
  "link.made": "A link to this save is in the box (and copied, where the browser allows). It opens the game with the save in it; nothing is stored anywhere but the link.",
  "link.film.made": "A link to this film is in the box. Anyone who opens it watches the run.",
  "install.button": "Install",
  "install.note": "Installed: the game opens from its own icon, and works without the network.",
  "pad.title": "Gamepad",
  "pad.note": "Change sets a button: press the one you want on the pad. The stick and the pad move, always.",
  "pad.press": "press a button...",
  "pad.help": "A gamepad works too: the stick or pad moves; the buttons as set below. On a touch screen, tap the view: the sides turn, the top walks, the bottom steps back.",
  "layout.handheld": "Handheld layout - thumb-sized buttons and larger text, as on a Steam Deck (Auto: by the screen's shape)",
  "hud.heavy": "Heavy-laden",
  "hud.overloaded": "Overloaded",
  "hud.blessed": "blessed",
  "hud.automatic": "automatic",
  "town.name": "Caer Duin, above",
  "town.compass": "The town",
  "town.where": "{name} - the town",
  "town.card": "The town on the hill, and the shaft the hill was never asked about.",
  "town.card.night": "The lanterns are lit on the hill, and the shaft is dark at the end of the lane.",
  "town.arrive": "{name}: Lantern Street from the gate to the Square, and the Keep-yard beyond it, where the shaft is.",
  "town.open": "Four adventurers step out of their own door into the morning. Lantern Street runs to the Square, and past it the shaft waits in the Keep-yard; somewhere below, the Lich King stirs.",
  "town.home": "Back to town",
  "town.foundation": "a foundation, waiting for a roof",
  "town.door": "(Space to go in)",
  "bag.weight": "Weight: {n}/{cap}",
  "bag.title.shop": "The Merchant",
  "bag.title.pack": "Inventory",
  "bag.gold": "Gold: {n}",
  "bag.insure": "Insure ({n} gold)",
  "bag.insure.worn": "Insure {who}'s {what} ({n} gold)",
  "bag.order": "Order for the next camp (a tenth over)...",
  "bag.ordered": "ordered: {list}",
  "camp.bounty": "Bounty board",
  "fence.head": "The fence, in the corner",
  "fence.unknown": "{what} (unknown): {n} gold",
  "fence.cursed": "{what} (cursed): takes it for nothing",
  "fence.rumour": "A rumour of a strongbox ({n} gold)",
  "fence.rumour.bought": "A rumour, bought: floor {n}",
};
CM.t = function (key, vars) {
  let s = CM.TEXT[key];
  if (s === undefined) return key;
  for (const [k, v] of Object.entries(vars || {})) s = s.split(`{${k}}`).join(typeof v === "number" ? v.toLocaleString() : String(v));
  return s;
};
